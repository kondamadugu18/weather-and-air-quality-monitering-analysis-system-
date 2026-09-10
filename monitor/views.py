"""
Web Views and Controller Logic for AeroWatch.
"""

import csv
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.conf import settings
from .models import City, WeatherRecord, AQIRecord, Alert
from .services import WeatherAQIService
from .analytics import EnvironmentalAnalyticsEngine


def global_context(request):
    """Global template context processor."""
    return {
        'all_cities': City.objects.all(),
        'active_alerts_count': Alert.objects.filter(is_active=True).count(),
        'has_api_keys': bool(
            settings.OPENWEATHER_API_KEY and settings.OPENWEATHER_API_KEY != 'your_openweather_api_key_here'
        )
    }


def dashboard_view(request):
    """Main executive monitoring dashboard."""
    cities = City.objects.all()
    selected_city_id = request.GET.get('city_id')
    selected_city = City.objects.filter(id=selected_city_id).first() if selected_city_id else cities.first()

    # If database is completely empty, populate default seed cities
    if not cities.exists():
        default_names = [('Hyderabad', 'IN'), ('Mumbai', 'IN'), ('Delhi', 'IN'), ('Bangalore', 'IN'), ('New York', 'US'), ('London', 'GB')]
        service = WeatherAQIService()
        for name, country in default_names:
            c = City.objects.create(name=name, country=country)
            service.fetch_and_save_city_data(c)
        cities = City.objects.all()
        selected_city = cities.first()

    kpis = EnvironmentalAnalyticsEngine.calculate_kpis()
    rankings = EnvironmentalAnalyticsEngine.get_city_rankings()
    insights = EnvironmentalAnalyticsEngine.generate_dynamic_insights(kpis, rankings)

    context = {
        'cities': cities,
        'selected_city': selected_city,
        'kpis': kpis,
        'rankings': rankings,
        'insights': insights,
    }
    return render(request, 'monitor/dashboard.html', context)


def weather_view(request):
    """Detailed atmospheric weather dashboard."""
    cities = City.objects.all()
    selected_city_id = request.GET.get('city_id')
    selected_city = City.objects.filter(id=selected_city_id).first() if selected_city_id else cities.first()

    history = selected_city.weather_records.all()[:24] if selected_city else []

    context = {
        'cities': cities,
        'selected_city': selected_city,
        'history': history,
        'history_json': json.dumps([
            {
                'time': r.recorded_at.strftime('%H:%M (%d %b)'),
                'temp': r.temperature,
                'humidity': r.humidity,
                'wind': r.wind_speed,
                'pressure': r.pressure
            } for r in reversed(list(history))
        ])
    }
    return render(request, 'monitor/weather.html', context)


def air_quality_view(request):
    """Air Quality Index and pollutant monitoring dashboard."""
    cities = City.objects.all()
    selected_city_id = request.GET.get('city_id')
    selected_city = City.objects.filter(id=selected_city_id).first() if selected_city_id else cities.first()

    history = selected_city.aqi_records.all()[:24] if selected_city else []

    context = {
        'cities': cities,
        'selected_city': selected_city,
        'history': history,
        'history_json': json.dumps([
            {
                'time': r.recorded_at.strftime('%H:%M (%d %b)'),
                'aqi': r.aqi,
                'pm25': r.pm25,
                'pm10': r.pm10,
                'no2': r.no2,
                'so2': r.so2,
                'co': r.co,
                'o3': r.o3
            } for r in reversed(list(history))
        ])
    }
    return render(request, 'monitor/air_quality.html', context)


def combined_analysis_view(request):
    """Weather + AQI relationship and cross-metric analysis."""
    cities = City.objects.all()
    selected_city_id = request.GET.get('city_id')
    selected_city = City.objects.filter(id=selected_city_id).first() if selected_city_id else cities.first()

    combined_df = EnvironmentalAnalyticsEngine.get_combined_dataframe(
        city_ids=[selected_city.id] if selected_city else None
    )
    corr_data = EnvironmentalAnalyticsEngine.compute_correlation_matrix(combined_df)

    # Prepare chart points
    chart_points = []
    if not combined_df.empty:
        for _, row in combined_df.tail(30).iterrows():
            chart_points.append({
                'time': row['recorded_at_w'].strftime('%H:%M (%d %b)'),
                'temp': row.get('temperature', 0),
                'humidity': row.get('humidity', 0),
                'wind': row.get('wind_speed', 0),
                'aqi': row.get('aqi', 0),
                'pm25': row.get('pm25', 0),
                'pm10': row.get('pm10', 0),
            })

    context = {
        'cities': cities,
        'selected_city': selected_city,
        'chart_points_json': json.dumps(chart_points),
        'correlations': corr_data
    }
    return render(request, 'monitor/combined_analysis.html', context)


def forecast_view(request):
    """7-Day weather projection view."""
    cities = City.objects.all()
    selected_city_id = request.GET.get('city_id')
    selected_city = City.objects.filter(id=selected_city_id).first() if selected_city_id else cities.first()

    forecast_data = []
    if selected_city:
        service = WeatherAQIService()
        forecast_data = service.get_7day_forecast(selected_city)

    context = {
        'cities': cities,
        'selected_city': selected_city,
        'forecast_data': forecast_data,
        'forecast_json': json.dumps(forecast_data)
    }
    return render(request, 'monitor/forecast.html', context)


def analytics_view(request):
    """Data Analyst exploratory analysis and correlation dashboard."""
    kpis = EnvironmentalAnalyticsEngine.calculate_kpis()
    rankings = EnvironmentalAnalyticsEngine.get_city_rankings()
    combined_df = EnvironmentalAnalyticsEngine.get_combined_dataframe(days=60)
    corr_data = EnvironmentalAnalyticsEngine.compute_correlation_matrix(combined_df)
    insights = EnvironmentalAnalyticsEngine.generate_dynamic_insights(kpis, rankings)

    context = {
        'kpis': kpis,
        'rankings': rankings,
        'correlations': corr_data,
        'insights': insights,
        'has_data': not combined_df.empty
    }
    return render(request, 'monitor/analytics.html', context)


def city_comparison_view(request):
    """Side-by-side comparison across monitored cities."""
    cities = City.objects.all()
    city1_id = request.GET.get('city1')
    city2_id = request.GET.get('city2')

    city1 = City.objects.filter(id=city1_id).first() if city1_id else cities.first()
    city2 = City.objects.filter(id=city2_id).first() if city2_id else (cities.exclude(id=city1.id).first() if city1 else None)
    if not city2:
        city2 = city1

    w1 = city1.latest_weather if city1 else None
    w2 = city2.latest_weather if city2 else None
    a1 = city1.latest_aqi if city1 else None
    a2 = city2.latest_aqi if city2 else None

    diff = {
        'aqi': (a1.aqi - a2.aqi) if (a1 and a2) else 0,
        'temp': (w1.temperature - w2.temperature) if (w1 and w2) else 0.0,
        'pm25': (a1.pm25 - a2.pm25) if (a1 and a2) else 0.0,
        'wind': (w1.wind_speed - w2.wind_speed) if (w1 and w2) else 0.0,
    }

    rankings = EnvironmentalAnalyticsEngine.get_city_rankings()

    context = {
        'cities': cities,
        'city1': city1,
        'city2': city2,
        'w1': w1,
        'w2': w2,
        'a1': a1,
        'a2': a2,
        'diff': diff,
        'rankings': rankings,
        'comparison_json': json.dumps(rankings.get('all_cities', []))
    }
    return render(request, 'monitor/city_comparison.html', context)


def map_view(request):
    """Interactive geospatial map displaying monitored cities with AQI & weather dials."""
    cities = City.objects.all()
    map_markers = []

    for c in cities:
        lw = c.latest_weather
        la = c.latest_aqi
        if c.lat and c.lon:
            map_markers.append({
                'id': c.id,
                'name': c.name,
                'country': c.country,
                'lat': c.lat,
                'lon': c.lon,
                'temp': lw.temperature if lw else 'N/A',
                'humidity': lw.humidity if lw else 'N/A',
                'condition': lw.description if lw else 'N/A',
                'aqi': la.aqi if la else 0,
                'category': la.category if la else 'N/A',
                'pm25': la.pm25 if la else 'N/A',
                'aqi_color': la.aqi_color_class if la else 'secondary'
            })

    context = {
        'cities': cities,
        'map_data_json': json.dumps(map_markers),
        'map_markers_json': json.dumps(map_markers)
    }
    return render(request, 'monitor/map_view.html', context)


def alerts_view(request):
    """Active environmental alerts log."""
    alerts = Alert.objects.all()
    active_alerts = alerts.filter(is_active=True)

    context = {
        'alerts': alerts,
        'active_alerts': active_alerts,
    }
    return render(request, 'monitor/alerts.html', context)


def city_management_view(request):
    """Manage monitored cities (Search, Add, Delete, Refresh, Toggle Favorites)."""
    cities = City.objects.all()

    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add':
            city_name = request.POST.get('city_name', '').strip()
            country = request.POST.get('country', 'US').strip()
            if city_name:
                city, created = City.objects.get_or_create(
                    name__iexact=city_name,
                    defaults={'name': city_name.title(), 'country': country.upper()}
                )
                service = WeatherAQIService()
                service.fetch_and_save_city_data(city)
                if created:
                    messages.success(request, f"City '{city.name}' added and synced successfully.")
                else:
                    messages.info(request, f"City '{city.name}' is already monitored. Data refreshed.")
            return redirect('city_management')

        elif action == 'delete':
            city_id = request.POST.get('city_id')
            city = get_object_or_404(City, id=city_id)
            c_name = city.name
            city.delete()
            messages.success(request, f"City '{c_name}' removed from monitoring.")
            return redirect('city_management')

        elif action == 'refresh_all':
            service = WeatherAQIService()
            for c in cities:
                service.fetch_and_save_city_data(c)
            messages.success(request, "All monitored cities refreshed successfully.")
            return redirect('city_management')

    context = {
        'cities': cities,
    }
    return render(request, 'monitor/city_management.html', context)


def data_download_view(request):
    """Download historical Weather and AQI datasets in CSV format."""
    dataset_type = request.GET.get('type', 'weather')
    city_id = request.GET.get('city_id')

    response = HttpResponse(content_type='text/csv')
    
    if dataset_type == 'weather':
        response['Content-Disposition'] = 'attachment; filename="aerowatch_weather_data.csv"'
        writer = csv.writer(response)
        writer.writerow(['Record_ID', 'City', 'Country', 'Temperature_C', 'Feels_Like_C', 'Humidity_Pct', 'Pressure_hPa', 'Wind_Speed_ms', 'Visibility_km', 'Condition', 'Recorded_At'])
        
        qs = WeatherRecord.objects.select_related('city').all()
        if city_id:
            qs = qs.filter(city_id=city_id)
            
        for r in qs[:500]:
            writer.writerow([r.id, r.city.name, r.city.country, r.temperature, r.feels_like, r.humidity, r.pressure, r.wind_speed, r.visibility, r.description, r.recorded_at.isoformat()])
        return response

    elif dataset_type == 'aqi':
        response['Content-Disposition'] = 'attachment; filename="aerowatch_aqi_data.csv"'
        writer = csv.writer(response)
        writer.writerow(['Record_ID', 'City', 'Country', 'AQI', 'Category', 'PM2.5', 'PM10', 'CO', 'NO2', 'O3', 'SO2', 'Recorded_At'])
        
        qs = AQIRecord.objects.select_related('city').all()
        if city_id:
            qs = qs.filter(city_id=city_id)
            
        for r in qs[:500]:
            writer.writerow([r.id, r.city.name, r.city.country, r.aqi, r.category, r.pm25, r.pm10, r.co, r.no2, r.o3, r.so2, r.recorded_at.isoformat()])
        return response

    context = {
        'cities': City.objects.all(),
    }
    return render(request, 'monitor/data_download.html', context)


def refresh_city_data(request, city_id):
    """Trigger manual data refresh for a specific city."""
    city = get_object_or_404(City, id=city_id)
    service = WeatherAQIService()
    service.fetch_and_save_city_data(city)
    messages.success(request, f"Telemetry refreshed for {city.name}.")
    referer = request.META.get('HTTP_REFERER')
    return redirect(referer if referer else 'dashboard')


def delete_city(request, city_id):
    """Delete a city and its records."""
    city = get_object_or_404(City, id=city_id)
    name = city.name
    city.delete()
    messages.success(request, f"Station {name} removed successfully.")
    return redirect('city_management')


def resolve_alert(request, alert_id):
    """Mark an environmental alert as resolved."""
    alert = get_object_or_404(Alert, id=alert_id)
    alert.is_active = False
    alert.save()
    messages.success(request, f"Alert for {alert.city.name} marked as resolved.")
    return redirect('alerts')


def export_data_csv(request, dataset_type):
    """Export weather or AQI records as CSV."""
    city_id = request.GET.get('city')
    response = HttpResponse(content_type='text/csv')

    if dataset_type == 'weather':
        response['Content-Disposition'] = 'attachment; filename="aerowatch_weather.csv"'
        writer = csv.writer(response)
        writer.writerow(['Record_ID', 'City', 'Country', 'Temperature_C', 'Feels_Like_C', 'Humidity_Pct', 'Pressure_hPa', 'Wind_Speed_ms', 'Condition', 'Recorded_At'])
        qs = WeatherRecord.objects.select_related('city').all()
        if city_id:
            qs = qs.filter(city_id=city_id)
        for r in qs[:1000]:
            writer.writerow([r.id, r.city.name, r.city.country, r.temperature, r.feels_like, r.humidity, r.pressure, r.wind_speed, r.description, r.recorded_at.isoformat()])
        return response

    elif dataset_type == 'aqi':
        response['Content-Disposition'] = 'attachment; filename="aerowatch_aqi.csv"'
        writer = csv.writer(response)
        writer.writerow(['Record_ID', 'City', 'Country', 'AQI', 'Category', 'PM2.5', 'PM10', 'CO', 'NO2', 'O3', 'SO2', 'Recorded_At'])
        qs = AQIRecord.objects.select_related('city').all()
        if city_id:
            qs = qs.filter(city_id=city_id)
        for r in qs[:1000]:
            writer.writerow([r.id, r.city.name, r.city.country, r.aqi, r.category, r.pm25, r.pm10, r.co, r.no2, r.o3, r.so2, r.recorded_at.isoformat()])
        return response

    else:
        # Combined / all
        response['Content-Disposition'] = 'attachment; filename="aerowatch_all_data.csv"'
        writer = csv.writer(response)
        writer.writerow(['City', 'Country', 'Temp_C', 'Humidity_Pct', 'Wind_Speed', 'AQI', 'Category', 'PM2.5', 'PM10'])
        for c in City.objects.all():
            w = c.latest_weather
            a = c.latest_aqi
            writer.writerow([
                c.name, c.country,
                w.temperature if w else '',
                w.humidity if w else '',
                w.wind_speed if w else '',
                a.aqi if a else '',
                a.category if a else '',
                a.pm25 if a else '',
                a.pm10 if a else ''
            ])
        return response


def about_view(request):
    """Project architecture, REST API documentation, methodology, and medical disclaimers."""
    return render(request, 'monitor/about.html')
