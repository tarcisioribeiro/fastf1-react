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
    driver = serializers.CharField(source='driver.full_name', read_only=True)
    driver_code = serializers.CharField(source='driver.code', read_only=True)
    driver_number = serializers.IntegerField(source='driver.number', read_only=True)
    team = serializers.CharField(source='team.name', read_only=True)
    teamColor = serializers.CharField(source='team.color', read_only=True)
    event_name = serializers.CharField(source='session.event.event_name', read_only=True)
    time = serializers.SerializerMethodField()

    class Meta:
        model = RaceResult
        fields = ['id', 'session', 'driver', 'driver_code', 'driver_number',
                  'team', 'teamColor', 'event_name', 'position',
                  'grid_position', 'points', 'laps_completed', 'time',
                  'total_race_time', 'fastest_lap_time', 'fastest_lap_number',
                  'status', 'dnf']

    def get_time(self, obj):
        """Format race time for display."""
        if obj.total_race_time:
            total_seconds = obj.total_race_time.total_seconds()
            if total_seconds > 0:
                hours = int(total_seconds // 3600)
                minutes = int((total_seconds % 3600) // 60)
                seconds = total_seconds % 60
                if hours > 0:
                    return f"{hours}:{minutes:02d}:{seconds:06.3f}"
                else:
                    return f"{minutes}:{seconds:06.3f}"
        return obj.status if obj.status != 'Finished' else '-'


class QualifyingResultSerializer(serializers.ModelSerializer):
    driver = serializers.CharField(source='driver.full_name', read_only=True)
    driver_code = serializers.CharField(source='driver.code', read_only=True)
    driver_number = serializers.IntegerField(source='driver.number', read_only=True)
    team = serializers.CharField(source='team.name', read_only=True)
    teamColor = serializers.CharField(source='team.color', read_only=True)
    event_name = serializers.CharField(source='session.event.event_name', read_only=True)
    q1 = serializers.SerializerMethodField()
    q2 = serializers.SerializerMethodField()
    q3 = serializers.SerializerMethodField()

    class Meta:
        model = QualifyingResult
        fields = ['id', 'session', 'driver', 'driver_code', 'driver_number',
                  'team', 'teamColor', 'event_name', 'position',
                  'q1', 'q2', 'q3', 'q1_time', 'q2_time', 'q3_time']

    def _format_time(self, time_delta):
        """Format qualifying time for display."""
        if time_delta:
            total_seconds = time_delta.total_seconds()
            if total_seconds > 0:
                minutes = int(total_seconds // 60)
                seconds = total_seconds % 60
                return f"{minutes}:{seconds:06.3f}"
        return None

    def get_q1(self, obj):
        return self._format_time(obj.q1_time)

    def get_q2(self, obj):
        return self._format_time(obj.q2_time)

    def get_q3(self, obj):
        return self._format_time(obj.q3_time)


class SprintResultSerializer(serializers.ModelSerializer):
    driver_name = serializers.CharField(source='driver.full_name', read_only=True)
    driver_code = serializers.CharField(source='driver.code', read_only=True)
    driver_number = serializers.IntegerField(source='driver.number', read_only=True)
    team_name = serializers.CharField(source='team.name', read_only=True)
    team_color = serializers.CharField(source='team.color', read_only=True)
    event_name = serializers.CharField(source='session.event.event_name', read_only=True)
    time = serializers.SerializerMethodField()

    class Meta:
        model = SprintResult
        fields = ['id', 'session', 'driver', 'driver_name', 'driver_code', 'driver_number',
                  'team', 'team_name', 'team_color', 'event_name', 'position',
                  'grid_position', 'points', 'laps_completed', 'time', 'total_sprint_time',
                  'fastest_lap_time', 'status']

    def get_time(self, obj):
        """Format sprint time for display."""
        if obj.total_sprint_time:
            total_seconds = obj.total_sprint_time.total_seconds()
            if total_seconds > 0:
                hours = int(total_seconds // 3600)
                minutes = int((total_seconds % 3600) // 60)
                seconds = total_seconds % 60
                if hours > 0:
                    return f"{hours}:{minutes:02d}:{seconds:06.3f}"
                else:
                    return f"{minutes}:{seconds:06.3f}"
        return obj.status if obj.status != 'Finished' else '-'


class DriverStandingSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='driver.full_name', read_only=True)
    driver_code = serializers.CharField(source='driver.code', read_only=True)
    driver_number = serializers.IntegerField(source='driver.number', read_only=True)
    team = serializers.CharField(source='team.name', read_only=True)
    teamColor = serializers.CharField(source='team.color', read_only=True)
    season_year = serializers.IntegerField(source='season.year', read_only=True)
    event_name = serializers.CharField(source='event.event_name', read_only=True)
    round_number = serializers.IntegerField(source='event.round_number', read_only=True)
    class Meta:
        model = DriverStanding
        fields = ['id', 'season', 'season_year', 'event', 'event_name', 'round_number',
                  'name', 'driver_code', 'driver_number', 'team', 'teamColor', 'position', 'points', 'wins', 'podiums']


class ConstructorStandingSerializer(serializers.ModelSerializer):
    team = serializers.CharField(source='team.name', read_only=True)
    teamColor = serializers.CharField(source='team.color', read_only=True)
    season_year = serializers.IntegerField(source='season.year', read_only=True)
    event_name = serializers.CharField(source='event.event_name', read_only=True)
    round_number = serializers.IntegerField(source='event.round_number', read_only=True)

    class Meta:
        model = ConstructorStanding
        fields = ['id', 'season', 'season_year', 'event', 'event_name', 'round_number',
                  'team', 'teamColor', 'position', 'points', 'wins', 'podiums']


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
    driver = serializers.CharField(source='driver.full_name', read_only=True)
    driver_code = serializers.CharField(source='driver.code', read_only=True)
    driver_number = serializers.IntegerField(source='driver.number', read_only=True)
    team = serializers.CharField(source='team.name', read_only=True)
    team_color = serializers.CharField(source='team.color', read_only=True)

    class Meta:
        model = PitStop
        fields = ['id', 'session', 'driver', 'driver_code', 'driver_number', 'team', 'team_color',
                  'stop_number', 'lap', 'duration']


class WeatherDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeatherData
        fields = ['id', 'session', 'timestamp', 'air_temp', 'track_temp',
                  'humidity', 'pressure', 'rainfall', 'wind_speed', 'wind_direction']
