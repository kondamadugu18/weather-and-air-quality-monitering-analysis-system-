# AeroWatch — Weather & Air Quality Monitoring System

Real-time weather and AQI monitoring platform built with Python Django.

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run migrations
python manage.py migrate

# 3. Start server
python manage.py runserver
```
Open: http://127.0.0.1:8000

## 🌤️ Features
- **Live Dashboard** — Monitor multiple cities simultaneously
- **AQI Tracking** — Real-time Air Quality Index with pollutant breakdown (PM2.5, PM10, CO, NO2, O3, SO2)
- **7-Day Forecast** — Weather forecast per city
- **Analytics & EDA** — Charts, comparisons, correlation analysis, trend overlays
- **Environmental Alerts** — Auto-generated alerts for poor AQI, high UV, etc.
- **City Management** — Search and add any city worldwide

## 🔑 Using Real APIs (Optional)

Edit `weatheraqi/settings.py`:

```python
OPENWEATHER_API_KEY = 'your_key_here'   # https://openweathermap.org/api (free)
WAQI_API_KEY = 'your_key_here'          # https://aqicn.org/api/ (free)
```

Without API keys, the app runs on realistic simulated data.

## 🛠️ Tech Stack
- **Backend**: Python, Django, Django REST Framework
- **APIs**: OpenWeatherMap, WAQI (World Air Quality Index)
- **Frontend**: HTML/CSS/JS + Chart.js
- **Database**: SQLite (swap PostgreSQL for production)
- **Data Analysis**: EDA dashboard with correlation, trends, comparisons
