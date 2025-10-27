"""Django Admin configuration for F1 models."""
from django.contrib import admin
from .models import (
    Team, Driver, Circuit, Season, Event, Session,
    RaceResult, QualifyingResult, SprintResult,
    DriverStanding, ConstructorStanding,
    LapTime, TyreStrategy, PitStop, WeatherData, TelemetryData
)


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['name', 'team_id', 'color', 'created_at']
    search_fields = ['name', 'team_id']
    list_filter = ['created_at']


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ['last_name', 'first_name', 'code', 'number', 'nationality']
    search_fields = ['first_name', 'last_name', 'code']
    list_filter = ['nationality']


@admin.register(Circuit)
class CircuitAdmin(admin.ModelAdmin):
    list_display = ['name', 'country', 'location', 'length_km']
    search_fields = ['name', 'country', 'location']
    list_filter = ['country']


@admin.register(Season)
class SeasonAdmin(admin.ModelAdmin):
    list_display = ['year', 'created_at']
    ordering = ['-year']


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['event_name', 'season', 'round_number', 'circuit', 'event_date', 'event_type']
    search_fields = ['event_name']
    list_filter = ['season', 'event_type', 'circuit']
    ordering = ['-season', 'round_number']


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ['event', 'session_type', 'session_date', 'is_complete', 'data_collected']
    search_fields = ['event__event_name']
    list_filter = ['session_type', 'is_complete', 'data_collected', 'event__season']
    ordering = ['-session_date']


@admin.register(RaceResult)
class RaceResultAdmin(admin.ModelAdmin):
    list_display = ['position', 'driver', 'team', 'session', 'points', 'status']
    search_fields = ['driver__last_name', 'team__name']
    list_filter = ['session__event__season', 'team', 'dnf']
    ordering = ['session', 'position']


@admin.register(QualifyingResult)
class QualifyingResultAdmin(admin.ModelAdmin):
    list_display = ['position', 'driver', 'team', 'session', 'q1_time', 'q2_time', 'q3_time']
    search_fields = ['driver__last_name', 'team__name']
    list_filter = ['session__event__season', 'team']
    ordering = ['session', 'position']


@admin.register(SprintResult)
class SprintResultAdmin(admin.ModelAdmin):
    list_display = ['position', 'driver', 'team', 'session', 'points', 'status']
    search_fields = ['driver__last_name', 'team__name']
    list_filter = ['session__event__season', 'team']
    ordering = ['session', 'position']


@admin.register(DriverStanding)
class DriverStandingAdmin(admin.ModelAdmin):
    list_display = ['season', 'event', 'position', 'driver', 'team', 'points', 'wins']
    search_fields = ['driver__last_name']
    list_filter = ['season', 'team']
    ordering = ['-season', 'event', 'position']


@admin.register(ConstructorStanding)
class ConstructorStandingAdmin(admin.ModelAdmin):
    list_display = ['season', 'event', 'position', 'team', 'points', 'wins']
    search_fields = ['team__name']
    list_filter = ['season']
    ordering = ['-season', 'event', 'position']


@admin.register(LapTime)
class LapTimeAdmin(admin.ModelAdmin):
    list_display = ['session', 'driver', 'lap_number', 'lap_time', 'compound', 'is_personal_best']
    search_fields = ['driver__last_name']
    list_filter = ['session__event__season', 'session__session_type', 'compound', 'is_personal_best']
    ordering = ['session', 'lap_number']


@admin.register(TyreStrategy)
class TyreStrategyAdmin(admin.ModelAdmin):
    list_display = ['session', 'driver', 'stint_number', 'compound', 'start_lap', 'end_lap', 'stint_length']
    search_fields = ['driver__last_name']
    list_filter = ['session__event__season', 'compound']
    ordering = ['session', 'driver', 'stint_number']


@admin.register(PitStop)
class PitStopAdmin(admin.ModelAdmin):
    list_display = ['session', 'driver', 'stop_number', 'lap', 'duration']
    search_fields = ['driver__last_name']
    list_filter = ['session__event__season']
    ordering = ['session', 'lap']


@admin.register(WeatherData)
class WeatherDataAdmin(admin.ModelAdmin):
    list_display = ['session', 'timestamp', 'air_temp', 'track_temp', 'humidity', 'rainfall']
    list_filter = ['session__event__season', 'rainfall']
    ordering = ['-timestamp']


@admin.register(TelemetryData)
class TelemetryDataAdmin(admin.ModelAdmin):
    list_display = ['lap_time', 'distance', 'speed', 'gear', 'throttle', 'brake']
    list_filter = ['lap_time__session__event__season']
    ordering = ['lap_time', 'distance']
