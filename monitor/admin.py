"""
Django Admin registrations for AeroWatch models.
"""

from django.contrib import admin
from .models import City, WeatherRecord, AQIRecord, Alert


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', 'lat', 'lon', 'is_favorite', 'added_at')
    search_fields = ('name', 'country')
    list_filter = ('is_favorite', 'country')


@admin.register(WeatherRecord)
class WeatherRecordAdmin(admin.ModelAdmin):
    list_display = ('city', 'temperature', 'feels_like', 'humidity', 'wind_speed', 'description', 'recorded_at')
    search_fields = ('city__name', 'description')
    list_filter = ('city', 'recorded_at')


@admin.register(AQIRecord)
class AQIRecordAdmin(admin.ModelAdmin):
    list_display = ('city', 'aqi', 'category', 'pm25', 'pm10', 'no2', 'recorded_at')
    search_fields = ('city__name', 'category')
    list_filter = ('category', 'city', 'recorded_at')


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ('city', 'alert_type', 'severity', 'is_active', 'created_at')
    search_fields = ('city__name', 'message', 'alert_type')
    list_filter = ('severity', 'alert_type', 'is_active')
