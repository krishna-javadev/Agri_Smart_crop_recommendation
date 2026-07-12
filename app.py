from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from utils import (
    get_weather_data, 
    predict_crop, 
    gemini_chatbot, 
    send_notification,
    load_crop_model
)

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.root_path, 'database', 'farming_platform.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Load ML Model
crop_model = load_crop_model()
if crop_model is None:
    print("Warning: Crop prediction model not loaded. Using fallback recommendations.")

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'farmer' or 'owner'
    location = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    rentals = db.relationship('Rental', backref='user', lazy=True)
    notifications = db.relationship('Notification', backref='user', lazy=True)

class Equipment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    price_per_day = db.Column(db.Float, nullable=False)
    availability = db.Column(db.Boolean, default=True)
    usage_type = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    rentals = db.relationship('Rental', backref='equipment', lazy=True)

class Rental(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    duration = db.Column(db.Integer, nullable=False)  # in days
    total_cost = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, completed, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50))  # weather, rental, crop
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class CropRecommendation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    recommended_crop = db.Column(db.String(50), nullable=False)
    n_value = db.Column(db.Float)
    p_value = db.Column(db.Float)
    k_value = db.Column(db.Float)
    temperature = db.Column(db.Float)
    humidity = db.Column(db.Float)
    ph = db.Column(db.Float)
    rainfall = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        location = request.form.get('location')
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'error')
            return redirect(url_for('register'))
        
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(name=name, email=email, password=hashed_password, role=role, location=location)
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            if user.role == 'farmer':
                return redirect(url_for('farmer_dashboard'))
            else:
                return redirect(url_for('owner_dashboard'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/farmer/dashboard')
@login_required
def farmer_dashboard():
    if current_user.role != 'farmer':
        return redirect(url_for('owner_dashboard'))
    
    rentals = Rental.query.filter_by(user_id=current_user.id).order_by(Rental.created_at.desc()).limit(5).all()
    notifications = Notification.query.filter_by(user_id=current_user.id, is_read=False).order_by(Notification.created_at.desc()).limit(5).all()
    
    return render_template('farmer_dashboard.html', rentals=rentals, notifications=notifications)

@app.route('/owner/dashboard')
@login_required
def owner_dashboard():
    if current_user.role != 'owner':
        return redirect(url_for('farmer_dashboard'))
    
    all_rentals = Rental.query.order_by(Rental.created_at.desc()).limit(10).all()
    equipment_count = Equipment.query.count()
    active_rentals = Rental.query.filter_by(status='confirmed').count()
    
    earnings = db.session.query(db.func.sum(Rental.total_cost)).filter_by(status='completed').scalar() or 0
    
    return render_template('owner_dashboard.html', 
                         rentals=all_rentals, 
                         equipment_count=equipment_count,
                         active_rentals=active_rentals,
                         earnings=earnings)

@app.route('/equipment')
@login_required
def equipment_list():
    category = request.args.get('category', '')
    if category:
        equipment = Equipment.query.filter_by(category=category, availability=True).all()
    else:
        equipment = Equipment.query.filter_by(availability=True).all()
    
    categories = db.session.query(Equipment.category).distinct().all()
    return render_template('equipment_list.html', equipment=equipment, categories=categories)

@app.route('/equipment/<int:id>')
@login_required
def equipment_detail(id):
    equipment = Equipment.query.get_or_404(id)
    return render_template('equipment_detail.html', equipment=equipment)

@app.route('/rental/request/<int:equipment_id>', methods=['GET', 'POST'])
@login_required
def rental_request(equipment_id):
    from datetime import datetime, timedelta
    
    equipment = Equipment.query.get_or_404(equipment_id)
    
    if request.method == 'POST':
        start_date_str = request.form.get('start_date')
        duration = int(request.form.get('duration'))
        
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        total_cost = equipment.price_per_day * duration
        
        rental = Rental(
            user_id=current_user.id,
            equipment_id=equipment_id,
            start_date=start_date,
            duration=duration,
            total_cost=total_cost,
            status='confirmed'
        )
        
        equipment.availability = False
        db.session.add(rental)
        db.session.commit()
        
        notification = Notification(
            user_id=current_user.id,
            message=f'Rental confirmed for {equipment.name}. Start date: {start_date}',
            type='rental'
        )
        db.session.add(notification)
        db.session.commit()
        
        flash('Rental request confirmed!', 'success')
        return redirect(url_for('farmer_dashboard'))
    
    return render_template('rental_request.html', 
                         equipment=equipment,
                         now=datetime.now,
                         timedelta=timedelta)

@app.route('/crop-recommendation', methods=['GET', 'POST'])
@login_required
def crop_recommendation():
    if request.method == 'POST':
        location = request.form.get('location', current_user.location)
        n = float(request.form.get('n', 0))
        p = float(request.form.get('p', 0))
        k = float(request.form.get('k', 0))
        ph = float(request.form.get('ph', 7.0))
        
        weather_data = get_weather_data(location)
        
        if weather_data:
            temperature = weather_data['temperature']
            humidity = weather_data['humidity']
            rainfall = weather_data['rainfall']
            
            crop = predict_crop(crop_model, n, p, k, temperature, humidity, ph, rainfall)
            
            recommendation = CropRecommendation(
                user_id=current_user.id,
                location=location,
                recommended_crop=crop,
                n_value=n,
                p_value=p,
                k_value=k,
                temperature=temperature,
                humidity=humidity,
                ph=ph,
                rainfall=rainfall
            )
            db.session.add(recommendation)
            db.session.commit()
            
            notification = Notification(
                user_id=current_user.id,
                message=f'Recommended crop for {location}: {crop}',
                type='crop'
            )
            db.session.add(notification)
            db.session.commit()
            
            return render_template('crop_recommendation.html', 
                                 crop=crop, 
                                 weather=weather_data,
                                 show_result=True)
        else:
            flash('Unable to fetch weather data', 'error')
    
    return render_template('crop_recommendation.html', show_result=False)

@app.route('/chatbot', methods=['GET', 'POST'])
@login_required
def chatbot():
    if request.method == 'POST':
        data = request.get_json()
        user_message = data.get('message', '')
        
        response = gemini_chatbot(user_message)
        return jsonify({'response': response})
    
    return render_template('chatbot.html')

@app.route('/notifications')
@login_required
def notifications():
    all_notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).all()
    return render_template('notifications.html', notifications=all_notifications)

@app.route('/notifications/mark-read/<int:id>')
@login_required
def mark_notification_read(id):
    notification = Notification.query.get_or_404(id)
    if notification.user_id == current_user.id:
        notification.is_read = True
        db.session.commit()
    return redirect(url_for('notifications'))

# Owner Equipment Management Routes
@app.route('/owner/equipment')
@login_required
def owner_equipment():
    if current_user.role != 'owner':
        return redirect(url_for('farmer_dashboard'))
    
    equipment = Equipment.query.all()
    return render_template('equipment_list.html', equipment=equipment, owner_view=True)

@app.route('/owner/equipment/add', methods=['GET', 'POST'])
@login_required
def add_equipment():
    if current_user.role != 'owner':
        return redirect(url_for('farmer_dashboard'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        category = request.form.get('category')
        description = request.form.get('description')
        price_per_day = float(request.form.get('price_per_day'))
        usage_type = request.form.get('usage_type')
        
        equipment = Equipment(
            name=name,
            category=category,
            description=description,
            price_per_day=price_per_day,
            usage_type=usage_type,
            availability=True
        )
        
        db.session.add(equipment)
        db.session.commit()
        
        flash('Equipment added successfully!', 'success')
        return redirect(url_for('owner_equipment'))
    
    return render_template('equipment_detail.html', add_mode=True)

@app.route('/owner/equipment/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_equipment(id):
    if current_user.role != 'owner':
        return redirect(url_for('farmer_dashboard'))
    
    equipment = Equipment.query.get_or_404(id)
    
    if request.method == 'POST':
        equipment.name = request.form.get('name')
        equipment.category = request.form.get('category')
        equipment.description = request.form.get('description')
        equipment.price_per_day = float(request.form.get('price_per_day'))
        equipment.usage_type = request.form.get('usage_type')
        equipment.availability = request.form.get('availability') == 'on'
        
        db.session.commit()
        
        flash('Equipment updated successfully!', 'success')
        return redirect(url_for('owner_equipment'))
    
    return render_template('equipment_detail.html', equipment=equipment, edit_mode=True)

@app.route('/owner/bookings')
@login_required
def owner_bookings():
    if current_user.role != 'owner':
        return redirect(url_for('farmer_dashboard'))
    
    bookings = Rental.query.order_by(Rental.created_at.desc()).all()
    return render_template('owner_dashboard.html', bookings=bookings, bookings_mode=True, owner_view=True)

@app.route('/owner/analytics')
@login_required
def owner_analytics():
    if current_user.role != 'owner':
        return redirect(url_for('farmer_dashboard'))
    
    # Get analytics data
    total_equipment = Equipment.query.count()
    total_bookings = Rental.query.count()
    active_rentals = Rental.query.filter_by(status='confirmed').count()
    completed_rentals = Rental.query.filter_by(status='completed').count()
    
    total_revenue = db.session.query(db.func.sum(Rental.total_cost)).filter_by(status='completed').scalar() or 0
    
    # Get monthly revenue data
    monthly_data = db.session.query(
        db.func.strftime('%Y-%m', Rental.created_at),
        db.func.sum(Rental.total_cost)
    ).filter_by(status='completed').group_by(db.func.strftime('%Y-%m', Rental.created_at)).all()
    
    return render_template('owner_dashboard.html', 
                         analytics_mode=True,
                         equipment_count=total_equipment,
                         total_equipment=total_equipment,
                         total_bookings=total_bookings,
                         active_rentals=active_rentals,
                         completed_rentals=completed_rentals,
                         earnings=total_revenue,
                         rentals=Rental.query.all(),
                         total_revenue=total_revenue,
                         monthly_data=monthly_data)

@app.route('/owner/settings')
@login_required
def owner_settings():
    if current_user.role != 'owner':
        return redirect(url_for('farmer_dashboard'))
    
    # Get basic dashboard data for settings page
    equipment_count = Equipment.query.count()
    active_rentals = Rental.query.filter_by(status='confirmed').count()
    total_revenue = db.session.query(db.func.sum(Rental.total_cost)).filter_by(status='completed').scalar() or 0
    rentals = Rental.query.all()
    
    return render_template('owner_dashboard.html', 
                         settings_mode=True,
                         equipment_count=equipment_count,
                         active_rentals=active_rentals,
                         earnings=total_revenue,
                         rentals=rentals)

# Scheduler for weather alerts
def check_weather_alerts():
    with app.app_context():
        users = User.query.filter_by(role='farmer').all()
        for user in users:
            if user.location:
                weather_data = get_weather_data(user.location)
                if weather_data:
                    if weather_data['temperature'] > 35 or weather_data['rainfall'] > 100:
                        notification = Notification(
                            user_id=user.id,
                            message=f"Weather Alert: Temperature: {weather_data['temperature']}°C, Rainfall: {weather_data['rainfall']}mm",
                            type='weather'
                        )
                        db.session.add(notification)
        db.session.commit()

scheduler = BackgroundScheduler()
scheduler.add_job(func=check_weather_alerts, trigger="interval", hours=6)
scheduler.start()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Add sample equipment if database is empty
        if Equipment.query.count() == 0:
            sample_equipment = [
                Equipment(name='Tractor', category='Heavy Machinery', description='High-power tractor for field operations', price_per_day=500.0, usage_type='Plowing, Tilling'),
                Equipment(name='Harvester', category='Heavy Machinery', description='Combine harvester for grain crops', price_per_day=800.0, usage_type='Harvesting'),
                Equipment(name='Irrigation Pump', category='Irrigation', description='High-capacity water pump', price_per_day=150.0, usage_type='Watering'),
                Equipment(name='Seed Drill', category='Planting', description='Precision seed planting equipment', price_per_day=200.0, usage_type='Sowing'),
                Equipment(name='Sprayer', category='Pest Control', description='Agricultural sprayer for pesticides', price_per_day=100.0, usage_type='Spraying'),
            ]
            db.session.bulk_save_objects(sample_equipment)
            db.session.commit()
    
    app.run(debug=True,port=5001)