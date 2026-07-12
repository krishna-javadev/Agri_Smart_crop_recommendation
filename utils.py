import pickle
import numpy as np
import requests
import os

try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# Load crop prediction model
def load_crop_model():
    try:
        with open('C:\\Users\\Viren\\Documents\\Qriocity2\\Farmer Ontogeny\\models\\RandomForest.pkl', 'rb') as file:
            model = pickle.load(file)
        return model
    except (ModuleNotFoundError, ImportError) as e:
        print(f"Error loading crop model: {e}")
        return None

# Weather API integration
def get_weather_data(location):
    api_key = "585c16e678fc74a01145af155437ec10"
    if not api_key:
        return None
    
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        'q': location,
        'appid': api_key,
        'units': 'metric'
    }
    
    try:
        response = requests.get(base_url, params=params)
        data = response.json()
        
        if response.status_code == 200:
            return {
                'temperature': data['main']['temp'],
                'humidity': data['main']['humidity'],
                'rainfall': data.get('rain', {}).get('1h', 0) * 24,  # Convert to daily
                'description': data['weather'][0]['description']
            }
    except Exception as e:
        print(f"Error fetching weather data: {e}")
    
    return None

# Crop prediction
def predict_crop(model, n, p, k, temperature, humidity, ph, rainfall):
    if model is None:
        # Fallback crop recommendations based on basic conditions
        if ph < 6.0:
            return "rice"  # Acidic soil
        elif ph > 7.5:
            return "wheat"  # Alkaline soil
        elif temperature < 15:
            return "wheat"  # Cool climate
        elif temperature > 30:
            return "maize"  # Hot climate
        elif rainfall < 500:
            return "millet"  # Low rainfall
        elif rainfall > 1000:
            return "rice"  # High rainfall
        else:
            return "soybean"  # Moderate conditions
    
    input_data = np.array([[n, p, k, temperature, humidity, ph, rainfall]])
    prediction = model.predict(input_data)
    return prediction[0]

# Fallback agricultural knowledge base
AGRICULTURAL_RESPONSES = {
    "high yield": "🌾 <strong>High Yield Crop Recommendations</strong><br><br>🌱 <strong>Top High-Yield Options:</strong><br><br><span class='text-yellow-300 font-semibold'>1) Hybrid Rice</span> - 6-8 tons/hectare<br>📍 Best for: Warm, humid climates<br>💡 Key: Use certified hybrid seeds<br><br><span class='text-yellow-300 font-semibold'>2) Hybrid Maize</span> - 8-10 tons/hectare<br>📍 Best for: Temperate to warm climates<br>💡 Key: Proper plant population density<br><br><span class='text-yellow-300 font-semibold'>3) High-yield Wheat</span> - 5-6 tons/hectare<br>📍 Best for: Cool, dry climates<br>💡 Key: Timely nitrogen application<br><br><span class='text-yellow-300 font-semibold'>4) Vegetables:</span> Tomatoes, Peppers, Cucumbers<br>📍 Greenhouse potential: 2-3x higher yields<br><br><span class='text-yellow-300 font-semibold'>5) Legumes:</span> Soybeans, Chickpeas<br>📍 Bonus: Nitrogen fixation for soil<br><br>✅ <strong>Universal Success Factors:</strong><br><span class='text-blue-300 font-medium'>• Proper soil preparation</span><br><span class='text-blue-300 font-medium'>• Balanced fertilization</span><br><span class='text-blue-300 font-medium'>• Irrigation management</span><br><span class='text-blue-300 font-medium'>• Pest control</span><br><span class='text-blue-300 font-medium'>• Quality certified seeds</span><br><br>🎯 <strong>Which crop interests you most? I can provide detailed guidance!",
    
    "pest control": "🐛 <strong>Comprehensive Pest Control Guide</strong><br><br>🛡️ <strong>Integrated Pest Management (IPM) Strategy:</strong><br><br><span class=\"text-emerald-300 font-bold\">1) Monitor</span> - Weekly crop inspection<br>📅 Check: Leaf undersides, stem bases, soil<br>🔍 Look: Eggs, larvae, feeding damage<br><br><span class=\"text-emerald-300 font-bold\">2) Prevent</span> - Crop rotation & hygiene<br>🔄 Rotate: 3-4 year cycles<br>🧹 Clean: Remove plant debris<br>🚪 Barrier: Row covers, companion planting<br><br><span class=\"text-emerald-300 font-bold\">3) Natural Controls</span><br>🐞 Predators: Ladybugs, lacewings, parasitic wasps<br>🦠 Pathogens: BT bacteria, beneficial nematodes<br>🌿 Botanicals: Neem oil, garlic spray, chili extract<br><br><span class=\"text-emerald-300 font-bold\">4) Targeted Treatment</span><br>⚠️ <strong>Last resort:</strong> Selective pesticides<br>🎯 Timing: Early morning/evening<br>🧤 Safety: Proper protective equipment<br><br>⚡ <strong>Quick Action Guide:</strong><br>🕐 <span class=\"text-red-300\">Weekly monitoring is critical!</span><br>📱 Document: Photos, damage patterns<br>🆘 Emergency: Isolate affected plants immediately<br><br>🎯 <strong>What specific pest are you dealing with? Send me photos if possible!",
    
    "irrigation": "💧 <strong>Smart Irrigation Management</strong><br><br>🕐 <strong>Optimal Timing:</strong><br>⏰ <span class=\"text-blue-300 font-medium\">Early Morning: 5-7 AM</span><br>✅ Minimal evaporation loss<br>✅ Reduces disease risk<br><br>⏰ <span class=\"text-orange-300 font-medium\">Avoid: Evening watering</span><br>⚠️ Increases fungal disease risk<br>⚠️ Attracts nocturnal pests<br><br>🎯 <strong>Irrigation Methods Comparison:</strong><br><br><span class=\"text-emerald-300 font-bold\">1) Drip Irrigation</span> - Most Efficient<br>💧 Water use: 30-50% less<br>💰 Cost: Medium installation<br>🎯 Best for: Vegetables, orchards<br>⚡ Efficiency: 90-95%<br><br><span class=\"text-blue-300 font-bold\">2) Sprinkler Systems</span> - Good Coverage<br>💧 Water use: Moderate<br>💰 Cost: Low-Medium<br>🎯 Best for: Lawns, field crops<br>⚡ Efficiency: 75-85%<br><br><span class=\"text-yellow-300 font-bold\">3) Furrow Irrigation</span> - Traditional<br>💧 Water use: Higher<br>💰 Cost: Very low<br>🎯 Best for: Row crops<br>⚡ Efficiency: 40-60%<br><br>💡 <strong>Pro Tips:</strong><br><span class=\"text-purple-300 font-medium\">• Mulch 2-3 inches deep</span> - Reduces water need 25%<br><span class=\"text-purple-300 font-medium\">• Check soil moisture at 4-inch depth</span><br><span class=\"text-purple-300 font-medium\">• Water at root zone, not leaves</span><br><span class=\"text-purple-300 font-medium\">• Use rain sensors for automation</span><br><br>🌱 <strong>What crop are you irrigating? I can provide specific guidelines!",
    
    "planting": "🌱 <strong>Complete Planting Guide</strong><br><br>📋 <strong>Pre-Planting Checklist:</strong><br><br><span class=\"text-emerald-300 font-bold\">1) Soil Testing</span><br>🧪 Test: pH, NPK, organic matter<br>📊 Ideal pH: 6.0-7.5 (most crops)<br>🌡️ Soil temp: 15-25°C for germination<br><br><span class=\"text-emerald-300 font-bold\">2) Site Preparation</span><br>🚜 Tillage: 6-8 inches deep<br>🧹 Remove: Weeds, debris, rocks<br>🌿 Add: Compost (2-4 inches)<br><br><span class=\"text-emerald-300 font-bold\">3) Variety Selection</span><br>🌡️ Climate match: Heat/cold tolerance<br>📅 Days to maturity: Match growing season<br>🦠 Disease resistance: Check local issues<br><br>🎯 <strong>Planting Technique:</strong><br><br>📏 <strong>Depth Rule:</strong> 2-3x seed diameter<br>⚠️ Exception: Lettuce needs light - surface sow<br><br>📐 <strong>Spacing Guidelines:</strong><br>🌱 Small seeds: 2-4 inches apart<br>🌿 Medium plants: 8-12 inches apart<br>🌳 Large plants: 18-36 inches apart<br><br>🌡️ <strong>Timing Strategy:</strong><br>📅 After last frost date<br>🌡️ Soil temp 15-25°C minimum<br>🌧️ Avoid: Waterlogged conditions<br><br>💧 <strong>Post-Planting Care:</strong><br>🌊 Gentle watering: Keep moist, not soggy<br>🌡️ Warmth: Row covers for cool weather<br>👀 Monitor: Germination in 7-14 days<br><br>🌾 <strong>What are you planting? I can provide specific instructions!",
    
    "soil": "🌍 <strong>Soil Health Management System</strong><br><br>🧪 <strong>Annual Testing Protocol:</strong><br><br><span class=\"text-blue-300 font-medium\">• pH Level:</span> 6.0-7.5 optimal range<br><span class=\"text-blue-300 font-medium\">• NPK Ratios:</span> Varies by crop need<br><span class=\"text-blue-300 font-medium\">• Organic Matter:</span> 3-5% target<br><span class=\"text-blue-300 font-medium\">• Micronutrients:</span> Fe, Zn, B, Mn, Cu<br><br>🌿 <strong>Improvement Strategy:</strong><br><br><span class=\"text-emerald-300 font-bold\">1) Organic Matter Addition</span><br>🌱 Compost: 2-4 inches annually<br>🐄 Aged manure: 1-2 inches<br>🌾 Green manure: Cover crops<br><br><span class=\"text-emerald-300 font-bold\">2) pH Management</span><br>📈 Too acidic (<6.0): Add lime<br>📉 Too alkaline (>7.5): Add sulfur<br>🧪 Rate: Based on soil test<br><br><span class=\"text-emerald-300 font-bold\">3) Physical Improvement</span><br>🚜 Avoid working wet soil<br>🌱 Use cover crops year-round<br>🚶 Reduce foot traffic in beds<br><br><span class=\"text-emerald-300 font-bold\">4) Biological Health</span><br>🦠 Beneficial microbes: Compost tea<br>🐛 Earthworms: Encourage with organic matter<br>🌿 Mycorrhizae: Avoid over-tillage<br><br>🔄 <strong>Rotation System:</strong><br>📅 3-4 year cycles minimum<br>🌱 Include legumes every 3rd year<br>🦠 Different plant families<br><br>⚡ <strong>Quick Fixes:</strong><br><span class=\"text-purple-300 font-medium\">• Raised beds for poor drainage</span><br><span class=\"text-purple-300 font-medium\">• Mulch to prevent erosion</span><br><span class=\"text-purple-300 font-medium\">• Test strips for amendments</span><br><br>🤔 <strong>What's your specific soil concern? I can provide targeted solutions!",
    
    "fertilizer": "🌿 <strong>Smart Fertilization System</strong><br><br>🧪 <strong>Soil Test-Based Approach:</strong><br><br><span class=\"text-yellow-300 font-medium\">N-P-K Requirements:</span><br>🌱 Nitrogen (N): Leaf growth<br>🌸 Phosphorus (P): Root & flower development<br>🍃 Potassium (K): Disease resistance<br><br><span class=\"text-yellow-300 font-medium\">Micronutrients:</span><br>🟤 Iron (Fe): Chlorophyll synthesis<br>🔵 Zinc (Zn): Enzyme function<br>🟢 Boron (B): Cell division<br>🟡 Manganese (Mn): Photosynthesis<br><br>📅 <strong>Application Timing:</strong><br><br><span class=\"text-emerald-300 font-bold\">1) Pre-Plant</span> - Base application<br>💧 Incorporate 4-6 inches deep<br>📏 Rate: Based on soil test<br>⏰ Timing: 2-3 weeks before planting<br><br><span class=\"text-emerald-300 font-bold\">2) Side-Dress</span> - During growth<br>🌱 When: 3-4 weeks after emergence<br>📍 Placement: 4-6 inches from stems<br>💧 Water after application<br><br><span class=\"text-emerald-300 font-bold\">3) Foliar Feeding</span> - Quick fix<br>⚡ Speed: Absorbed in 24-48 hours<br>🌅 Time: Early morning<br>💧 Rate: 1-2 lbs per 100 gallons<br><br>🌱 <strong>Fertilizer Options:</strong><br><br><span class=\"text-blue-300 font-bold\">Chemical Fertilizers</span><br>✅ Pros: Precise, fast-acting<br>⚠️ Cons: Can burn if over-applied<br>🎯 Best for: Quick correction<br><br><span class=\"text-green-300 font-bold\">Organic Options</span><br>✅ Pros: Slow-release, soil-building<br>📈 Release: 4-8 weeks<br>🎯 Best for: Long-term health<br><br><span class=\"text-orange-300 font-bold\">Slow-Release</span><br>✅ Pros: Steady feeding 2-6 months<br>💰 Cost: Higher initial<br>🎯 Best for: Container plants<br><br>⚠️ <strong>Critical Warnings:</strong><br><span class=\"text-red-300\">• Over-fertilizing burns roots</span><br><span class=\"text-red-300\">• Can pollute groundwater</span><br><span class=\"text-red-300\">• Always follow label rates</span><br><br>🌾 <strong>What crop needs fertilizing? I can provide a detailed feeding schedule!",
    
    "default": "👋 <strong>Welcome to Your AI Farming Assistant!</strong><br><br>🌾 <strong>I'm Here to Help You With:</strong><br><br><span class='text-emerald-300 text-xl mr-2'>•</span><span class='text-blue-300 font-medium'>Crop Selection & Planting Guides</span><br><span class='text-emerald-300 text-xl mr-2'>•</span><span class='text-blue-300 font-medium'>Pest & Disease Management</span><br><span class='text-emerald-300 text-xl mr-2'>•</span><span class='text-blue-300 font-medium'>Irrigation & Water Management</span><br><span class='text-emerald-300 text-xl mr-2'>•</span><span class='text-blue-300 font-medium'>Soil Health & Fertilization</span><br><span class='text-emerald-300 text-xl mr-2'>•</span><span class='text-blue-300 font-medium'>Weather-Based Farming Advice</span><br><span class='text-emerald-300 text-xl mr-2'>•</span><span class='text-blue-300 font-medium'>Seasonal Cultivation Tips</span><br><br>💡 <strong>Try These Questions:</strong><br><span class='text-yellow-300 font-semibold'>\"What are the best high-yield crops for my area?\"</span><br><span class='text-yellow-300 font-semibold'>\"How do I control aphids organically?\"</span><br><span class='text-yellow-300 font-semibold'>\"When should I plant tomatoes?\"</span><br><span class='text-yellow-300 font-semibold'>\"What's wrong with my soil?\"</span><br><br>🤔 <strong>What would you like to know about farming? I'm ready to help!"
}

def get_agricultural_response(user_message):
    """Simple keyword-based response system for agricultural queries"""
    user_message = user_message.lower()
    
    # Check for specific keywords
    if "yield" in user_message or "high yield" in user_message:
        return AGRICULTURAL_RESPONSES["high yield"]
    elif "pest" in user_message or "insect" in user_message or "bug" in user_message:
        return AGRICULTURAL_RESPONSES["pest control"]
    elif "water" in user_message or "irrigation" in user_message or "watering" in user_message:
        return AGRICULTURAL_RESPONSES["irrigation"]
    elif "plant" in user_message or "sow" in user_message or "seed" in user_message:
        return AGRICULTURAL_RESPONSES["planting"]
    elif "soil" in user_message or "dirt" in user_message or "earth" in user_message:
        return AGRICULTURAL_RESPONSES["soil"]
    elif "fertilizer" in user_message or "nutrient" in user_message or "feed" in user_message:
        return AGRICULTURAL_RESPONSES["fertilizer"]
    else:
        return AGRICULTURAL_RESPONSES["default"]

# Gemini Chatbot
def gemini_chatbot(user_message):
    if not GEMINI_AVAILABLE:
        # Use fallback agricultural responses
        return get_agricultural_response(user_message)
    
    api_key = "AIzaSyALQl3IlQPXT_dD8k5kvBA9j3aXenmfDAg"
    if not api_key:
        return get_agricultural_response(user_message)
    
    try:
        client = genai.Client(api_key=api_key)
        model = "gemini-2.0-flash"
        
        system_prompt = """You are an agricultural expert assistant helping farmers with cultivation guidance. 
        Provide step-by-step advice on crop cultivation, pest management, irrigation, and farming best practices. 
        Keep responses concise, practical, and easy to understand."""
        
        contents = [
            genai.types.Content(
                role="user",
                parts=[
                    genai.types.Part.from_text(text=f"{system_prompt}\n\nFarmer's question: {user_message}"),
                ],
            ),
        ]
        
        generate_content_config = genai.types.GenerateContentConfig(
            temperature=0.7,
            max_output_tokens=500,
        )
        
        response_text = ""
        for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config,
        ):
            if chunk.text:
                response_text += chunk.text
        
        return response_text if response_text else get_agricultural_response(user_message)
        
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return get_agricultural_response(user_message)

# Notification helper
def send_notification(user_id, message, notification_type):
    from app import db, Notification
    notification = Notification(
        user_id=user_id,
        message=message,
        type=notification_type
    )
    db.session.add(notification)
    db.session.commit()