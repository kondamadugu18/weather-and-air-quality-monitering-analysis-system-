"""
Models for AeroWatch Environmental Monitoring System.
"""

from django.db import models
from django.utils import timezone


class City(models.Model):
    """Monitored geographical city."""
    name = models.CharField(max_length=100)
    country = models.CharField(max_length=10, default='US')
    lat = models.FloatField(null=True, blank=True)
    lon = models.FloatField(null=True, blank=True)
    is_favorite = models.BooleanField(default=False)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Cities'
        ordering = ['-is_favorite', 'name']

    def __str__(self):
        return f"{self.name}, {self.country}"

    @property
    def latitude(self):
        return self.lat

    @property
    def longitude(self):
        return self.lon

    @property
    def latest_weather(self):
        return self.weather_records.order_by('-recorded_at').first()

    @property
    def latest_aqi(self):
        return self.aqi_records.order_by('-recorded_at').first()


class WeatherRecord(models.Model):
    """Atmospheric weather observation."""
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='weather_records')
    temperature = models.FloatField(help_text="Temperature in Celsius")
    feels_like = models.FloatField(help_text="Feels-like temperature in Celsius")
    humidity = models.FloatField(help_text="Relative humidity percentage")
    pressure = models.FloatField(help_text="Atmospheric pressure in hPa")
    wind_speed = models.FloatField(help_text="Wind speed in m/s")
    wind_direction = models.FloatField(default=0.0, help_text="Wind direction in degrees")
    visibility = models.FloatField(default=10.0, help_text="Visibility in km")
    description = models.CharField(max_length=200, default='Clear Sky')
    icon = models.CharField(max_length=50, default='01d')
    uv_index = models.FloatField(default=0.0)
    recorded_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-recorded_at']
        indexes = [
            models.Index(fields=['city', '-recorded_at']),
        ]

    @property
    def condition(self):
        return self.description

    def __str__(self):
        return f"{self.city.name} Weather @ {self.recorded_at.strftime('%Y-%m-%d %H:%M')}: {self.temperature}°C"


class AQIRecord(models.Model):
    """Air Quality Index and pollutant concentrations."""
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='aqi_records')
    aqi = models.IntegerField(help_text="Air Quality Index")
    category = models.CharField(max_length=100, default='Good')
    pm25 = models.FloatField(default=0.0, help_text="PM2.5 concentration in µg/m³")
    pm10 = models.FloatField(default=0.0, help_text="PM10 concentration in µg/m³")
    co = models.FloatField(default=0.0, help_text="Carbon Monoxide in µg/m³")
    no2 = models.FloatField(default=0.0, help_text="Nitrogen Dioxide in µg/m³")
    o3 = models.FloatField(default=0.0, help_text="Ozone in µg/m³")
    so2 = models.FloatField(default=0.0, help_text="Sulfur Dioxide in µg/m³")
    recorded_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-recorded_at']
        indexes = [
            models.Index(fields=['city', '-recorded_at']),
        ]

    def __str__(self):
        return f"{self.city.name} AQI @ {self.recorded_at.strftime('%Y-%m-%d %H:%M')}: {self.aqi} ({self.category})"

    @property
    def aqi_color_class(self):
        if self.aqi <= 50:
            return 'success'    # Good (Green)
        elif self.aqi <= 100:
            return 'warning'    # Moderate (Yellow)
        elif self.aqi <= 150:
            return 'orange'     # Unhealthy for Sensitive Groups (Orange)
        elif self.aqi <= 200:
            return 'danger'     # Unhealthy (Red)
        elif self.aqi <= 300:
            return 'purple'     # Very Unhealthy (Purple)
        else:
            return 'maroon'     # Hazardous (Maroon)


class Alert(models.Model):
    """Environmental alert for extreme weather or dangerous air pollution."""
    SEVERITY_CHOICES = [
        ('Low', 'Low'),
        ('Moderate', 'Moderate'),
        ('High', 'High'),
        ('Critical', 'Critical'),
    ]

    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='alerts')
    alert_type = models.CharField(max_length=50, default='AQI')
    message = models.TextField()
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='Moderate')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.severity}] {self.city.name} - {self.alert_type}: {self.message[:40]}"
