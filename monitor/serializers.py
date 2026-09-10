"""
Django REST Framework Serializers for AeroWatch.
"""

from rest_framework import serializers
from .models import City, WeatherRecord, AQIRecord, Alert


class WeatherRecordSerializer(serializers.ModelSerializer):
    city_name = serializers.CharField(source='city.name', read_only=True)

    class Meta:
        model = WeatherRecord
        fields = [
            'id', 'city', 'city_name', 'temperature', 'feels_like',
            'humidity', 'pressure', 'wind_speed', 'wind_direction',
            'visibility', 'description', 'icon', 'uv_index', 'recorded_at'
        ]


class AQIRecordSerializer(serializers.ModelSerializer):
    city_name = serializers.CharField(source='city.name', read_only=True)
    aqi_color = serializers.CharField(source='aqi_color_class', read_only=True)

    class Meta:
        model = AQIRecord
        fields = [
            'id', 'city', 'city_name', 'aqi', 'category', 'aqi_color',
            'pm25', 'pm10', 'co', 'no2', 'o3', 'so2', 'recorded_at'
        ]


class AlertSerializer(serializers.ModelSerializer):
    city_name = serializers.CharField(source='city.name', read_only=True)

    class Meta:
        model = Alert
        fields = [
            'id', 'city', 'city_name', 'alert_type', 'message',
            'severity', 'is_active', 'created_at'
        ]


class CitySerializer(serializers.ModelSerializer):
    latest_weather = WeatherRecordSerializer(read_only=True)
    latest_aqi = AQIRecordSerializer(read_only=True)
    active_alerts_count = serializers.SerializerMethodField()

    class Meta:
        model = City
        fields = [
            'id', 'name', 'country', 'lat', 'lon', 'is_favorite',
            'added_at', 'latest_weather', 'latest_aqi', 'active_alerts_count'
        ]

    def get_active_alerts_count(self, obj):
        return obj.alerts.filter(is_active=True).count()
