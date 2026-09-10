"""
Data Analysis, Time-Series Analytics, and Correlation Engine using Pandas and NumPy.
"""

import pandas as pd
import numpy as np
from datetime import timedelta
from typing import Dict, Any, List, Optional
from django.utils import timezone
from .models import City, WeatherRecord, AQIRecord


class EnvironmentalAnalyticsEngine:
    """Core analytics engine powering AeroWatch EDA, correlation, and insight dashboards."""

    @staticmethod
    def get_combined_dataframe(city_ids: Optional[List[int]] = None, days: int = 30) -> pd.DataFrame:
        """Join Weather and AQI observation tables into a unified Pandas DataFrame."""
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # Query weather records
        w_qs = WeatherRecord.objects.filter(recorded_at__gte=cutoff_date).select_related('city')
        if city_ids:
            w_qs = w_qs.filter(city_id__in=city_ids)

        w_records = list(w_qs.values(
            'id', 'city_id', 'city__name', 'city__country',
            'temperature', 'feels_like', 'humidity', 'pressure',
            'wind_speed', 'visibility', 'uv_index', 'recorded_at'
        ))

        # Query AQI records
        a_qs = AQIRecord.objects.filter(recorded_at__gte=cutoff_date).select_related('city')
        if city_ids:
            a_qs = a_qs.filter(city_id__in=city_ids)

        a_records = list(a_qs.values(
            'city_id', 'aqi', 'category', 'pm25', 'pm10',
            'co', 'no2', 'o3', 'so2', 'recorded_at'
        ))

        if not w_records or not a_records:
            return pd.DataFrame()

        w_df = pd.DataFrame(w_records)
        a_df = pd.DataFrame(a_records)

        # Truncate timestamps to hour for robust inner joining
        w_df['time_hour'] = pd.to_datetime(w_df['recorded_at']).dt.floor('h')
        a_df['time_hour'] = pd.to_datetime(a_df['recorded_at']).dt.floor('h')

        merged = pd.merge(w_df, a_df, on=['city_id', 'time_hour'], suffixes=('_w', '_a'))
        if merged.empty:
            # Fallback join on city if precise hourly match is sparse
            merged = pd.merge(w_df, a_df, on='city_id', suffixes=('_w', '_a'))

        merged.rename(columns={'city__name': 'city_name', 'city__country': 'country'}, inplace=True)
        return merged

    @staticmethod
    def calculate_kpis(city_ids: Optional[List[int]] = None) -> Dict[str, Any]:
        """Compute top-level summary metrics across monitored cities."""
        w_qs = WeatherRecord.objects.all()
        a_qs = AQIRecord.objects.all()
        if city_ids:
            w_qs = w_qs.filter(city_id__in=city_ids)
            a_qs = a_qs.filter(city_id__in=city_ids)

        if not w_qs.exists() or not a_qs.exists():
            return {
                'avg_temp': 0.0, 'avg_aqi': 0, 'max_aqi': 0, 'min_aqi': 0,
                'avg_pm25': 0.0, 'avg_pm10': 0.0, 'avg_humidity': 0.0, 'avg_wind': 0.0,
                'total_observations': 0
            }

        w_df = pd.DataFrame(list(w_qs.values('temperature', 'humidity', 'wind_speed')))
        a_df = pd.DataFrame(list(a_qs.values('aqi', 'pm25', 'pm10')))

        return {
            'avg_temp': round(float(w_df['temperature'].mean()), 1),
            'avg_aqi': int(round(float(a_df['aqi'].mean()))),
            'max_aqi': int(a_df['aqi'].max()),
            'min_aqi': int(a_df['aqi'].min()),
            'avg_pm25': round(float(a_df['pm25'].mean()), 1),
            'avg_pm10': round(float(a_df['pm10'].mean()), 1),
            'avg_humidity': round(float(w_df['humidity'].mean()), 1),
            'avg_wind': round(float(w_df['wind_speed'].mean()), 1),
            'total_observations': len(w_df) + len(a_df)
        }

    @staticmethod
    def compute_correlation_matrix(df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate Pearson correlation matrix between weather and AQI parameters."""
        cols = ['temperature', 'humidity', 'pressure', 'wind_speed', 'aqi', 'pm25', 'pm10', 'no2']
        available_cols = [c for c in cols if c in df.columns]

        if len(df) < 3 or len(available_cols) < 2:
            return {'variables': [], 'matrix': [], 'insights': []}

        corr_df = df[available_cols].corr(method='pearson').round(2)
        corr_matrix = corr_df.values.tolist()

        # Extract notable correlations
        corr_insights = []
        if 'wind_speed' in corr_df and 'aqi' in corr_df:
            w_aqi = corr_df.loc['wind_speed', 'aqi']
            if w_aqi < -0.2:
                corr_insights.append(f"**Wind Speed & AQI (r = {w_aqi}):** Higher wind speeds exhibit a negative correlation with AQI, aiding particulate dispersion.")
        if 'humidity' in corr_df and 'pm25' in corr_df:
            h_pm = corr_df.loc['humidity', 'pm25']
            if h_pm > 0.2:
                corr_insights.append(f"**Humidity & PM2.5 (r = {h_pm}):** Moisture trap particles leading to higher particulate retention during stagnant weather.")

        return {
            'variables': [c.replace('_', ' ').title() for c in available_cols],
            'raw_variables': available_cols,
            'matrix': corr_matrix,
            'insights': corr_insights
        }

    @staticmethod
    def get_city_rankings() -> Dict[str, Any]:
        """Rank cities by cleanest, most polluted, hottest, and coolest."""
        cities = City.objects.all()
        rankings = []

        for city in cities:
            lw = city.latest_weather
            la = city.latest_aqi
            if lw and la:
                rankings.append({
                    'city': city.name,
                    'country': city.country,
                    'temp': lw.temperature,
                    'aqi': la.aqi,
                    'category': la.category,
                    'pm25': la.pm25,
                    'humidity': lw.humidity,
                    'wind': lw.wind_speed
                })

        if not rankings:
            return {}

        df_rank = pd.DataFrame(rankings)
        cleanest = df_rank.sort_values(by='aqi', ascending=True).iloc[0].to_dict()
        polluted = df_rank.sort_values(by='aqi', ascending=False).iloc[0].to_dict()
        hottest = df_rank.sort_values(by='temp', ascending=False).iloc[0].to_dict()
        coolest = df_rank.sort_values(by='temp', ascending=True).iloc[0].to_dict()

        return {
            'cleanest': cleanest,
            'most_polluted': polluted,
            'hottest': hottest,
            'coolest': coolest,
            'all_cities': df_rank.to_dict('records')
        }

    @staticmethod
    def generate_dynamic_insights(kpis: dict, rankings: dict) -> List[str]:
        """Synthesize automatic environmental intelligence takeaways."""
        insights = []

        if rankings.get('cleanest'):
            c = rankings['cleanest']
            insights.append(f"🌱 **Cleanest Air Quality:** **{c['city']}** currently records the lowest AQI index of **{c['aqi']}** ({c['category']}) with PM2.5 at **{c['pm25']} µg/m³**.")

        if rankings.get('most_polluted'):
            p = rankings['most_polluted']
            insights.append(f"⚠️ **Pollution Hotspot:** **{p['city']}** registers the highest AQI at **{p['aqi']}** ({p['category']}), requiring sensitive groups to minimize prolonged exposure.")

        if rankings.get('hottest') and rankings.get('coolest'):
            h = rankings['hottest']
            co = rankings['coolest']
            insights.append(f"🌡️ **Thermal Variance:** Regional temperatures range from **{co['temp']}°C** in **{co['city']}** to **{h['temp']}°C** in **{h['city']}**.")

        if kpis.get('avg_pm25', 0) > 35.0:
            insights.append(f"💨 **Particulate Baseline:** Overall network average PM2.5 stands at **{kpis['avg_pm25']} µg/m³**, exceeding WHO guideline thresholds.")

        return insights
