import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'weatheraqi.settings')
django.setup()

from django.test import Client, TestCase
from monitor.models import City, WeatherRecord, AQIRecord, Alert
from monitor.services import WeatherAQIService
from monitor.analytics import EnvironmentalAnalyticsEngine
from django.urls import reverse

def run_tests():
    print("=" * 70)
    print("AEROWATCH — AUTOMATED TEST SUITE & VERIFICATION")
    print("=" * 70)
    
    # 1. Test Model Persistence
    print("\n[1/5] Testing Model Persistence...")
    city, created = City.objects.get_or_create(
        name="Tokyo",
        defaults={"country": "Japan", "lat": 35.6762, "lon": 139.6503}
    )
    assert city.id is not None, "City persistence failed"
    print(f"  [OK] City '{city.name}, {city.country}' validated (ID: {city.id})")

    # 2. Test WeatherAQIService
    print("\n[2/5] Testing WeatherAQIService Ingestion & Simulation...")
    service = WeatherAQIService()
    result = service.fetch_and_save_city_data(city)
    w_rec = result['weather']
    a_rec = result['aqi']
    assert w_rec is not None, "WeatherRecord generation failed"
    assert a_rec is not None, "AQIRecord generation failed"
    assert 0 <= a_rec.aqi <= 500, f"AQI out of realistic bounds: {a_rec.aqi}"
    print(f"  [OK] Ingested Weather: {w_rec.temperature:.1f} C, Condition: {w_rec.condition}")
    print(f"  [OK] Ingested AQI: {a_rec.aqi} ({a_rec.category}), PM2.5: {a_rec.pm25:.1f} ug/m3")

    # 3. Test 7-Day Forecast Service
    print("\n[3/5] Testing 7-Day Forecast Engine...")
    forecast = service.get_7day_forecast(city)
    assert len(forecast) == 7, f"Expected 7 forecast days, got {len(forecast)}"
    print(f"  [OK] Forecast generated 7 days: {forecast[0]['day_name']} to {forecast[6]['day_name']}")

    # 4. Test Analytics Engine
    print("\n[4/5] Testing Pandas Environmental Analytics Engine...")
    analytics = EnvironmentalAnalyticsEngine()
    df = analytics.get_combined_dataframe()
    kpis = analytics.calculate_kpis()
    corr_info = analytics.compute_correlation_matrix(df)
    rankings = analytics.get_city_rankings()
    insights = analytics.generate_dynamic_insights(kpis, rankings)
    print(f"  [OK] Summary KPIs calculated: {kpis.get('total_observations', 0)} total observations")
    print(f"  [OK] Pearson correlation variables: {corr_info.get('variables', [])}")
    print(f"  [OK] City rankings computed for {len(rankings.get('all_cities', []))} stations")
    print(f"  [OK] Algorithmic insights derived: {len(insights)} finding(s)")

    # 5. Test Django Web Views & DRF Endpoints
    print("\n[5/5] Testing Web Views & REST Endpoints (HTTP 200)...")
    c = Client()
    routes = [
        ('/', 'Dashboard View'),
        ('/weather/', 'Weather View'),
        ('/air-quality/', 'Air Quality View'),
        ('/combined/', 'Combined Analysis View'),
        ('/forecast/', '7-Day Forecast View'),
        ('/analytics/', 'Analytics & Pearson Correlation View'),
        ('/comparison/', 'City Comparison View'),
        ('/map/', 'Leaflet Geospatial Map View'),
        ('/alerts/', 'Alerts & Dispatch Feed View'),
        ('/cities/', 'City Management View'),
        ('/download/', 'Data Export View'),
        ('/about/', 'About & Architecture View'),
        ('/api/cities/', 'DRF API Cities List'),
        ('/api/weather/', 'DRF API Weather List'),
        ('/api/air-quality/', 'DRF API AQI List'),
        ('/api/alerts/', 'DRF API Alerts List'),
        ('/api/forecast/?city=' + str(city.id), 'DRF API 7-Day Forecast'),
        ('/api/analytics/', 'DRF API Analytics'),
    ]

    passed = 0
    for route, label in routes:
        response = c.get(route)
        if response.status_code in [200, 302]:
            print(f"  [OK] [{response.status_code}] {label:40} ({route})")
            passed += 1
        else:
            print(f"  [FAIL] [{response.status_code}] {label:40} ({route})")
            raise AssertionError(f"Route {route} failed with status {response.status_code}")

    print("\n" + "=" * 70)
    print(f"ALL {passed}/{len(routes)} VIEWS & ENGINE COMPONENTS PASSED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == '__main__':
    run_tests()
