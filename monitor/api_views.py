"""
REST API ViewSets and Endpoints for AeroWatch.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import City, WeatherRecord, AQIRecord, Alert
from .serializers import CitySerializer, WeatherRecordSerializer, AQIRecordSerializer, AlertSerializer
from .services import WeatherAQIService
from .analytics import EnvironmentalAnalyticsEngine


class CityViewSet(viewsets.ModelViewSet):
    """API endpoint for managing monitored cities."""
    queryset = City.objects.all()
    serializer_class = CitySerializer

    def create(self, request, *args, **kwargs):
        name = request.data.get('name', '').strip()
        country = request.data.get('country', 'US').strip()
        if not name:
            return Response({'error': 'City name is required.'}, status=status.HTTP_400_BAD_REQUEST)

        city, created = City.objects.get_or_create(name=name, defaults={'country': country})
        if created:
            # Trigger immediate data fetch
            service = WeatherAQIService()
            service.fetch_and_save_city_data(city)

        serializer = self.get_serializer(city)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def refresh(self, request, pk=None):
        """Fetch latest live observation for this city."""
        city = self.get_object()
        service = WeatherAQIService()
        result = service.fetch_and_save_city_data(city)
        return Response({
            'status': 'success',
            'city': city.name,
            'is_simulated': result['is_simulated'],
            'weather': WeatherRecordSerializer(result['weather']).data,
            'aqi': AQIRecordSerializer(result['aqi']).data
        })

    @action(detail=True, methods=['post'])
    def toggle_favorite(self, request, pk=None):
        """Toggle city favorite pin."""
        city = self.get_object()
        city.is_favorite = not city.is_favorite
        city.save()
        return Response({'status': 'success', 'is_favorite': city.is_favorite})


class WeatherRecordViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for historical and latest weather records."""
    queryset = WeatherRecord.objects.all()
    serializer_class = WeatherRecordSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        city_id = self.request.query_params.get('city_id')
        if city_id:
            qs = qs.filter(city_id=city_id)
        return qs[:100]


class AQIRecordViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for historical and latest air quality records."""
    queryset = AQIRecord.objects.all()
    serializer_class = AQIRecordSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        city_id = self.request.query_params.get('city_id')
        if city_id:
            qs = qs.filter(city_id=city_id)
        return qs[:100]


class AlertViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for active environmental alerts."""
    queryset = Alert.objects.filter(is_active=True)
    serializer_class = AlertSerializer


@api_view(['GET'])
def api_forecast(request):
    """Get 7-day daily weather forecast for a specified city."""
    city_name = request.query_params.get('city', '').strip()
    city_id = request.query_params.get('city_id')

    if city_id:
        city = get_object_or_404(City, id=city_id)
    elif city_name:
        if city_name.isdigit():
            city = get_object_or_404(City, id=int(city_name))
        else:
            city = get_object_or_404(City, name__iexact=city_name)
    else:
        city = City.objects.first()
        if not city:
            return Response({'error': 'No monitored cities found.'}, status=status.HTTP_404_NOT_FOUND)

    service = WeatherAQIService()
    forecast_data = service.get_7day_forecast(city)
    return Response({
        'city': city.name,
        'country': city.country,
        'forecast': forecast_data
    })


@api_view(['GET'])
def api_analytics(request):
    """Get summary KPIs, correlation matrix, and city rankings."""
    kpis = EnvironmentalAnalyticsEngine.calculate_kpis()
    rankings = EnvironmentalAnalyticsEngine.get_city_rankings()
    combined_df = EnvironmentalAnalyticsEngine.get_combined_dataframe()
    corr_data = EnvironmentalAnalyticsEngine.compute_correlation_matrix(combined_df)
    insights = EnvironmentalAnalyticsEngine.generate_dynamic_insights(kpis, rankings)

    return Response({
        'kpis': kpis,
        'rankings': rankings,
        'correlations': corr_data,
        'insights': insights
    })
