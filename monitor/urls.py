"""
URL routing for monitor application and REST API routes.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views, api_views

router = DefaultRouter()
router.register(r'cities', api_views.CityViewSet, basename='api_city')
router.register(r'weather', api_views.WeatherRecordViewSet, basename='api_weather')
router.register(r'air-quality', api_views.AQIRecordViewSet, basename='api_aqi')
router.register(r'alerts', api_views.AlertViewSet, basename='api_alert')

urlpatterns = [
    # Web UI Pages
    path('', views.dashboard_view, name='dashboard'),
    path('weather/', views.weather_view, name='weather'),
    path('city-weather/', views.weather_view, name='city_weather'),
    path('air-quality/', views.air_quality_view, name='air_quality'),
    path('combined/', views.combined_analysis_view, name='combined'),
    path('combined-analysis/', views.combined_analysis_view, name='combined_analysis'),
    path('forecast/', views.forecast_view, name='forecast'),
    path('analytics/', views.analytics_view, name='analytics'),
    path('comparison/', views.city_comparison_view, name='comparison'),
    path('city-comparison/', views.city_comparison_view, name='city_comparison'),
    path('map/', views.map_view, name='map_view'),
    path('alerts/', views.alerts_view, name='alerts'),
    path('cities/', views.city_management_view, name='cities'),
    path('city-management/', views.city_management_view, name='city_management'),
    path('download/', views.data_download_view, name='download'),
    path('data-download/', views.data_download_view, name='data_download'),
    path('about/', views.about_view, name='about'),

    # Actions
    path('cities/<int:city_id>/refresh/', views.refresh_city_data, name='refresh_city_data'),
    path('cities/<int:city_id>/delete/', views.delete_city, name='delete_city'),
    path('alerts/<int:alert_id>/resolve/', views.resolve_alert, name='resolve_alert'),
    path('download/csv/<str:dataset_type>/', views.export_data_csv, name='export_data_csv'),

    # REST API Routes
    path('api/', include(router.urls)),
    path('api/forecast/', api_views.api_forecast, name='api_forecast'),
    path('api/analytics/', api_views.api_analytics, name='api_analytics'),
]
