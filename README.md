# Agri_Smart_crop_recommendation
# 🌾 Farmer Ontogeny - Smart Agriculture Equipment Rental & Crop Recommendation Platform

## 📌 Overview

Farmer Ontogeny is an AI-powered web application designed to support farmers by combining agricultural equipment rental, intelligent crop recommendation, weather monitoring, and an AI farming assistant into a single platform.

The system enables farmers to rent farming equipment, receive crop recommendations based on soil and weather conditions, obtain weather alerts, and interact with an AI chatbot for agricultural guidance. Equipment owners can manage their inventory, monitor rentals, and analyze business performance through an owner dashboard.

---

## 🚀 Features

### 👨‍🌾 Farmer Module

* User Registration & Login
* Browse available agricultural equipment
* Rent farming equipment
* View rental history
* AI-powered crop recommendation
* Weather-based crop suggestions
* Personalized notifications
* AI Agricultural Chatbot
* Weather alerts

### 🏢 Equipment Owner Module

* Secure authentication
* Add/Edit equipment
* Manage equipment availability
* View rental bookings
* Revenue analytics
* Equipment management dashboard

---

## 🤖 AI Features

### 🌱 Crop Recommendation

The application predicts suitable crops using:

* Nitrogen (N)
* Phosphorus (P)
* Potassium (K)
* Soil pH
* Temperature
* Humidity
* Rainfall

A trained Random Forest model is used for prediction. If the model is unavailable, the system provides intelligent fallback recommendations based on environmental conditions.

---

### 🌦 Weather Integration

Real-time weather information is retrieved using the OpenWeather API, including:

* Temperature
* Humidity
* Rainfall
* Weather description

Weather data is used for:

* Crop prediction
* Weather alerts
* Farming recommendations

---

### 🤖 AI Farming Assistant

An agricultural chatbot assists users with:

* Crop cultivation
* Pest management
* Irrigation methods
* Fertilizer usage
* Soil health
* High-yield crop suggestions
* General farming practices

The chatbot uses Google's Gemini API when available and falls back to a built-in agricultural knowledge base if necessary.

---

## 🔔 Notification System

The platform automatically generates notifications for:

* Equipment rental confirmation
* Crop recommendations
* Extreme weather alerts

A background scheduler periodically checks weather conditions and notifies farmers of severe weather.

---

## 🏗 Tech Stack

### Backend

* Python
* Flask
* Flask SQLAlchemy
* Flask Login
* Flask Bcrypt

### Database

* SQLite

### Machine Learning

* Scikit-learn
* Random Forest Classifier
* NumPy
* Pickle

### APIs

* OpenWeather API
* Google Gemini API

### Scheduler

* APScheduler

### Frontend

* HTML
* CSS
* JavaScript
* Jinja2 Templates

---

## 📂 Project Structure

```
Farmer-Ontogeny/
│
├── app.py
├── utils.py
├── requirements.txt
│
├── database/
│   └── farming_platform.db
│
├── models/
│   └── RandomForest.pkl
│
├── templates/
│
├── static/
│
└── README.md
```

---

## ⚙ Installation

### 1. Clone the repository

```bash
git clone https://github.com/your-username/Farmer-Ontogeny.git

cd Farmer-Ontogeny
```

### 2. Create a virtual environment

Windows

```bash
python -m venv venv
venv\Scripts\activate
```

Linux/Mac

```bash
python3 -m venv venv

source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file:

```env
SECRET_KEY=your_secret_key
OPENWEATHER_API_KEY=your_api_key
GEMINI_API_KEY=your_api_key
```

### 5. Run the application

```bash
python app.py
```

The application will be available at

```
http://localhost:5001
```

---

## 📊 Database Models

The system consists of the following entities:

* User
* Equipment
* Rental
* Notification
* CropRecommendation

---

## 👥 User Roles

### Farmer

* Rent equipment
* Receive crop recommendations
* View notifications
* Chat with AI assistant

### Equipment Owner

* Manage equipment
* View bookings
* Monitor revenue
* Analyze rentals

---

## 🔄 Application Workflow

```
User Login
      │
      ▼
Select Role
      │
      ├─────────────┐
      ▼             ▼
 Farmer         Equipment Owner
      │             │
      ▼             ▼
Rent Equipment   Manage Equipment
      │             │
      ▼             ▼
Crop Prediction  View Analytics
      │
      ▼
Weather Alerts
      │
      ▼
AI Chatbot Assistance
```

---

## 📦 Major Libraries

* Flask
* Flask SQLAlchemy
* Flask Login
* Flask Bcrypt
* APScheduler
* NumPy
* Requests
* Scikit-learn
* python-dotenv

---

## Future Enhancements

* Online payment gateway
* Equipment availability calendar
* GPS tracking for rented equipment
* SMS and Email notifications
* Multi-language support
* Farmer-to-farmer marketplace
* Image-based crop disease detection
* Mobile application (Android/iOS)
* Recommendation system for fertilizers
* Yield prediction analytics

---

## Contributors

Developed as an AI-enabled Smart Agriculture Platform integrating Machine Learning, Weather Intelligence, Equipment Rental Management, and Generative AI to improve farming productivity and equipment accessibility.

---

## License

This project is developed for educational and research purposes.

Feel free to modify and extend it according to your requirements.
