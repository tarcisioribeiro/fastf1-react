"""
Serializers for F1 API endpoints.
"""
from rest_framework import serializers
from core.models import (
    Team, Driver, Circuit, Season, Event, Session,
    RaceResult, QualifyingResult, SprintResult,
    DriverStanding, ConstructorStanding,
    LapTime, TyreStrategy, PitStop, WeatherData
)


class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ['id', 'team_id', 'name', 'full_name', 'color', 'color_secondary']


class DriverSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()

    class Meta:
        model = Driver
        fields = ['id', 'driver_id', 'code', 'number', 'first_name', 'last_name',
                  'full_name', 'nationality', 'date_of_birth']


class CircuitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Circuit
        fields = ['id', 'circuit_id', 'name', 'location', 'country',
                  'latitude', 'longitude', 'length_km']


class SeasonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Season
        fields = ['id', 'year']


class EventSerializer(serializers.ModelSerializer):
    season_year = serializers.IntegerField(source='season.year', read_only=True)
    circuit_name = serializers.CharField(source='circuit.name', read_only=True)
    circuit_country = serializers.CharField(source='circuit.country', read_only=True)

    class Meta:
        model = Event
        fields = ['id', 'event_id', 'season', 'season_year', 'round_number',
                  'circuit', 'circuit_name', 'circuit_country', 'event_name',
                  'event_type', 'event_date']


class SessionSerializer(serializers.ModelSerializer):
    event_name = serializers.CharField(source='event.event_name', read_only=True)
    season_year = serializers.IntegerField(source='event.season.year', read_only=True)

    class Meta:
        model = Session
        fields = ['id', 'session_id', 'event', 'event_name', 'season_year',
                  'session_type', 'session_date', 'is_complete', 'data_collected']


class RaceResultSerializer(serializers.ModelSerializer):
    driver_name = serializers.CharField(source='driver.full_name', read_only=True)
    driver_code = serializers.CharField(source='driver.code', read_only=True)
    team_name = serializers.CharField(source='team.name', read_only=True)
    team_color = serializers.CharField(source='team.color', read_only=True)
    event_name = serializers.CharField(source='session.event.event_name', read_only=True)

    class Meta:
        model = RaceResult
        fields = ['id', 'session', 'driver', 'driver_name', 'driver_code',
                  'team', 'team_name', 'team_color', 'event_name', 'position',
                  'grid_position', 'points', 'laps_completed', 'total_race_time',
                  'fastest_lap_time', 'fastest_lap_number', 'status', 'dnf']


class QualifyingResultSerializer(serializers.ModelSerializer):
    driver_name = serializers.CharField(source='driver.full_name', read_only=True)
    driver_code = serializers.CharField(source='driver.code', read_only=True)
    team_name = serializers.CharField(source='team.name', read_only=True)
    team_color = serializers.CharField(source='team.color', read_only=True)
    event_name = serializers.CharField(source='session.event.event_name', read_only=True)

    class Meta:
        model = QualifyingResult
        fields = ['id', 'session', 'driver', 'driver_name', 'driver_code',
                  'team', 'team_name', 'team_color', 'event_name', 'position',
                  'q1_time', 'q2_time', 'q3_time']


class SprintResultSerializer(serializers.ModelSerializer):
    driver_name = serializers.CharField(source='driver.full_name', read_only=True)
    driver_code = serializers.CharField(source='driver.code', read_only=True)
    team_name = serializers.CharField(source='team.name', read_only=True)
    team_color = serializers.CharField(source='team.color', read_only=True)
    event_name = serializers.CharField(source='session.event.event_name', read_only=True)

    class Meta:
        model = SprintResult
        fields = ['id', 'session', 'driver', 'driver_name', 'driver_code',
                  'team', 'team_name', 'team_color', 'event_name', 'position',
                  'grid_position', 'points', 'laps_completed', 'total_sprint_time',
                  'fastest_lap_time', 'status']


class DriverStandingSerializer(serializers.ModelSerializer):
    driver_name = serializers.CharField(source='driver.full_name', read_only=True)
    driver_code = serializers.CharField(source='driver.code', read_only=True)
    team_name = serializers.CharField(source='team.name', read_only=True)
    team_color = serializers.CharField(source='team.color', read_only=True)
    season_year = serializers.IntegerField(source='season.year', read_only=True)
    event_name = serializers.CharField(source='event.event_name', read_only=True)
    round_number = serializers.IntegerField(source='event.round_number', read_only=True)

    class Meta:
        model = DriverStanding
        fields = ['id', 'season', 'season_year', 'event', 'event_name', 'round_number',
                  'driver', 'driver_name', 'driver_code', 'team', 'team_name',
                  'team_color', 'position', 'points', 'wins']


class ConstructorStandingSerializer(serializers.ModelSerializer):
    team_name = serializers.CharField(source='team.name', read_only=True)
    team_color = serializers.CharField(source='team.color', read_only=True)
    season_year = serializers.IntegerField(source='season.year', read_only=True)
    event_name = serializers.CharField(source='event.event_name', read_only=True)
    round_number = serializers.IntegerField(source='event.round_number', read_only=True)

    class Meta:
        model = ConstructorStanding
        fields = ['id', 'season', 'season_year', 'event', 'event_name', 'round_number',
                  'team', 'team_name', 'team_color', 'position', 'points', 'wins']


class LapTimeSerializer(serializers.ModelSerializer):
    driver_name = serializers.CharField(source='driver.full_name', read_only=True)
    driver_code = serializers.CharField(source='driver.code', read_only=True)
    team_name = serializers.CharField(source='team.name', read_only=True)

    class Meta:
        model = LapTime
        fields = ['id', 'session', 'driver', 'driver_name', 'driver_code',
                  'team', 'team_name', 'lap_number', 'lap_time', 'sector1_time',
                  'sector2_time', 'sector3_time', 'is_personal_best', 'is_accurate',
                  'compound', 'tyre_life']


class TyreStrategySerializer(serializers.ModelSerializer):
    driver_name = serializers.CharField(source='driver.full_name', read_only=True)
    driver_code = serializers.CharField(source='driver.code', read_only=True)
    team_name = serializers.CharField(source='team.name', read_only=True)
    team_color = serializers.CharField(source='team.color', read_only=True)

    class Meta:
        model = TyreStrategy
        fields = ['id', 'session', 'driver', 'driver_name', 'driver_code',
                  'team', 'team_name', 'team_color', 'stint_number', 'compound',
                  'start_lap', 'end_lap', 'stint_length', 'avg_lap_time',
                  'fastest_lap_time']


class PitStopSerializer(serializers.ModelSerializer):
    driver_name = serializers.CharField(source='driver.full_name', read_only=True)
    driver_code = serializers.CharField(source='driver.code', read_only=True)
    team_name = serializers.CharField(source='team.name', read_only=True)

    class Meta:
        model = PitStop
        fields = ['id', 'session', 'driver', 'driver_name', 'driver_code',
                  'team', 'team_name', 'stop_number', 'lap', 'duration']


class WeatherDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeatherData
        fields = ['id', 'session', 'timestamp', 'air_temp', 'track_temp',
                  'humidity', 'pressure', 'rainfall', 'wind_speed', 'wind_direction']
