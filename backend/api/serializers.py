"""
Serializers for F1 API endpoints.
"""
from rest_framework import serializers
from core.models import (
    Team, Driver, Circuit, Season, Event, Session,
    RaceResult, QualifyingResult, SprintResult,
    DriverStanding, ConstructorStanding,
    LapTime, TyreStrategy, PitStop, WeatherData,
    DataAuditReport, DataAuditSuggestion, TeamOperation
)
from django_celery_beat.models import PeriodicTask, CrontabSchedule, IntervalSchedule


class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ['id', 'team_id', 'name', 'full_name', 'color', 'color_secondary',
                  'canonical_name', 'operation_line_id', 'current_name',
                  'display_in_filters', 'years_active', 'team_status']


class TeamFilterSerializer(serializers.ModelSerializer):
    """Serializer simplificado para filtros - inclui equipes ativas e extintas."""
    succession_line = serializers.SerializerMethodField()
    display_name = serializers.SerializerMethodField()
    team_status = serializers.SerializerMethodField()

    class Meta:
        model = Team
        fields = ['id', 'current_name', 'display_name', 'color', 'operation_line_id', 'team_status', 'years_active', 'succession_line']

    def get_succession_line(self, obj):
        """Retorna a linha de sucessão para exibir no tooltip."""
        return obj.get_succession_line()

    def get_display_name(self, obj):
        """Retorna o nome de exibição: current_name ou canonical_name ou name."""
        return obj.current_name or obj.canonical_name or obj.name

    def get_team_status(self, obj):
        """
        Retorna o status correto da equipe:
        - ACTIVE apenas para equipes com operation_line_id entre 1-10
        - EXTINCT para todas as outras
        """
        if obj.operation_line_id and 1 <= obj.operation_line_id <= 10:
            return 'ACTIVE'
        return 'EXTINCT'


class TeamOperationFilterSerializer(serializers.ModelSerializer):
    """
    Serializer para TeamOperation usado nos filtros da UI.
    Retorna operações de equipes com suas equipes associadas agrupadas.
    """
    teams = serializers.SerializerMethodField()
    display_name = serializers.CharField(source='operation_name')
    color = serializers.SerializerMethodField()
    succession_line = serializers.SerializerMethodField()

    class Meta:
        model = TeamOperation
        fields = ['id', 'display_name', 'color', 'is_active', 'teams', 'succession_line']

    def get_teams(self, obj):
        """Retorna lista de equipes que fazem parte desta operação."""
        teams = obj.teams.all().order_by('id')
        return [{
            'id': team.id,
            'name': team.name,
            'years_active': team.years_active or '',
            'is_current': team.display_in_filters,
            'status': team.team_status
        } for team in teams]

    def get_color(self, obj):
        """Retorna a cor da equipe principal ou da primeira equipe da operação."""
        if obj.primary_team:
            return obj.primary_team.color
        # Fallback: pegar a cor da primeira equipe da operação
        first_team = obj.teams.first()
        return first_team.color if first_team else '#000000'

    def get_succession_line(self, obj):
        """
        Retorna a linha de sucessão das equipes da operação.
        Ordenado cronologicamente (mais antiga primeiro).
        """
        teams = obj.teams.all().order_by('id')
        return [{
            'name': team.name,
            'years_active': team.years_active or '',
            'is_current': team.display_in_filters,
            'status': team.team_status
        } for team in teams]


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
        """Format race time for display with gap calculation."""
        # Se não completou a corrida, não mostrar tempo
        if obj.status != 'Finished' or not obj.total_race_time:
            return None

        total_seconds = obj.total_race_time.total_seconds()
        if total_seconds <= 0:
            return None

        # Se é o vencedor (P1), mostrar o tempo total formatado
        if obj.position == 1:
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            seconds = total_seconds % 60
            if hours > 0:
                return f"{hours}:{minutes:02d}:{seconds:06.3f}"
            else:
                return f"{minutes:02d}:{seconds:06.3f}"

        # Para outros pilotos, calcular e mostrar o gap
        try:
            # Buscar o tempo do vencedor da mesma sessão
            winner = RaceResult.objects.filter(
                session=obj.session,
                position=1
            ).first()

            if winner and winner.total_race_time:
                winner_seconds = winner.total_race_time.total_seconds()
                gap_seconds = total_seconds - winner_seconds

                # Se o gap for menor que 60 segundos, mostrar apenas segundos
                if gap_seconds < 60:
                    return f"+{gap_seconds:.3f}s"
                else:
                    # Se for maior, mostrar no formato +MM:SS.sss
                    gap_minutes = int(gap_seconds // 60)
                    gap_secs = gap_seconds % 60
                    return f"+{gap_minutes}:{gap_secs:06.3f}"

            # Fallback: se não conseguir obter o vencedor, mostrar o tempo total
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            seconds = total_seconds % 60
            if hours > 0:
                return f"{hours}:{minutes:02d}:{seconds:06.3f}"
            else:
                return f"{minutes:02d}:{seconds:06.3f}"
        except Exception:
            # Em caso de erro, retornar None
            return None


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
        """Format sprint time for display with gap calculation."""
        # Se não completou a corrida, não mostrar tempo
        if obj.status != 'Finished' or not obj.total_sprint_time:
            return None

        total_seconds = obj.total_sprint_time.total_seconds()
        if total_seconds <= 0:
            return None

        # Se é o vencedor (P1), mostrar o tempo total formatado
        if obj.position == 1:
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            seconds = total_seconds % 60
            if hours > 0:
                return f"{hours}:{minutes:02d}:{seconds:06.3f}"
            else:
                return f"{minutes:02d}:{seconds:06.3f}"

        # Para outros pilotos, calcular e mostrar o gap
        try:
            # Buscar o tempo do vencedor da mesma sessão
            winner = SprintResult.objects.filter(
                session=obj.session,
                position=1
            ).first()

            if winner and winner.total_sprint_time:
                winner_seconds = winner.total_sprint_time.total_seconds()
                gap_seconds = total_seconds - winner_seconds

                # Se o gap for menor que 60 segundos, mostrar apenas segundos
                if gap_seconds < 60:
                    return f"+{gap_seconds:.3f}s"
                else:
                    # Se for maior, mostrar no formato +MM:SS.sss
                    gap_minutes = int(gap_seconds // 60)
                    gap_secs = gap_seconds % 60
                    return f"+{gap_minutes}:{gap_secs:06.3f}"

            # Fallback: se não conseguir obter o vencedor, mostrar o tempo total
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            seconds = total_seconds % 60
            if hours > 0:
                return f"{hours}:{minutes:02d}:{seconds:06.3f}"
            else:
                return f"{minutes:02d}:{seconds:06.3f}"
        except Exception:
            # Em caso de erro, retornar None
            return None


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


class DataAuditSuggestionSerializer(serializers.ModelSerializer):
    """Serializer para sugestões individuais de preenchimento de dados."""

    class Meta:
        model = DataAuditSuggestion
        fields = [
            'id', 'table_name', 'field_name', 'record_id', 'record_identifier',
            'current_value', 'suggested_value', 'confidence_score',
            'source_name', 'source_url', 'source_timestamp',
            'applied', 'applied_at', 'rejected', 'rejection_reason', 'created_at'
        ]


class DataAuditReportSerializer(serializers.ModelSerializer):
    """Serializer para relatórios de auditoria de dados."""
    suggestions = DataAuditSuggestionSerializer(many=True, read_only=True)
    suggestions_count = serializers.SerializerMethodField()

    class Meta:
        model = DataAuditReport
        fields = [
            'id', 'execution_date', 'status', 'execution_time_seconds',
            'total_tables_scanned', 'total_fields_scanned',
            'total_empty_fields_found', 'total_suggestions_found',
            'audit_results', 'error_message', 'suggestions', 'suggestions_count'
        ]

    def get_suggestions_count(self, obj):
        """Retorna contagem de sugestões por status."""
        return {
            'total': obj.suggestions.count(),
            'pending': obj.suggestions.filter(applied=False, rejected=False).count(),
            'applied': obj.suggestions.filter(applied=True).count(),
            'rejected': obj.suggestions.filter(rejected=True).count(),
        }


class DataAuditReportListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listagem de relatórios (sem sugestões)."""
    suggestions_count = serializers.SerializerMethodField()

    class Meta:
        model = DataAuditReport
        fields = [
            'id', 'execution_date', 'status', 'execution_time_seconds',
            'total_tables_scanned', 'total_fields_scanned',
            'total_empty_fields_found', 'total_suggestions_found',
            'suggestions_count'
        ]

    def get_suggestions_count(self, obj):
        """Retorna contagem de sugestões por status."""
        return {
            'total': obj.suggestions.count(),
            'pending': obj.suggestions.filter(applied=False, rejected=False).count(),
            'applied': obj.suggestions.filter(applied=True).count(),
            'rejected': obj.suggestions.filter(rejected=True).count(),
        }


# Celery Beat Serializers

class CrontabScheduleSerializer(serializers.ModelSerializer):
    """Serializer para agendamento crontab."""
    human_readable = serializers.SerializerMethodField()
    timezone = serializers.SerializerMethodField()

    class Meta:
        model = CrontabSchedule
        fields = ['id', 'minute', 'hour', 'day_of_week', 'day_of_month', 'month_of_year', 'timezone', 'human_readable']

    def get_timezone(self, obj):
        """Converte ZoneInfo para string."""
        return str(obj.timezone) if obj.timezone else 'UTC'

    def get_human_readable(self, obj):
        """Retorna uma descrição legível do crontab em português."""
        from .utils import explain_crontab
        crontab_str = f"{obj.minute} {obj.hour} {obj.day_of_month} {obj.month_of_year} {obj.day_of_week}"
        return explain_crontab(crontab_str)


class IntervalScheduleSerializer(serializers.ModelSerializer):
    """Serializer para agendamento por intervalo."""
    human_readable = serializers.SerializerMethodField()

    class Meta:
        model = IntervalSchedule
        fields = ['id', 'every', 'period', 'human_readable']

    def get_human_readable(self, obj):
        """Retorna descrição legível do intervalo em português."""
        period_map = {
            'days': 'dia(s)',
            'hours': 'hora(s)',
            'minutes': 'minuto(s)',
            'seconds': 'segundo(s)',
            'microseconds': 'microssegundo(s)',
        }
        period_pt = period_map.get(obj.period, obj.period)
        return f"A cada {obj.every} {period_pt}"


class PeriodicTaskSerializer(serializers.ModelSerializer):
    """Serializer para tarefas periódicas."""
    crontab = CrontabScheduleSerializer(read_only=True)
    interval = IntervalScheduleSerializer(read_only=True)
    crontab_id = serializers.PrimaryKeyRelatedField(
        queryset=CrontabSchedule.objects.all(),
        source='crontab',
        write_only=True,
        required=False,
        allow_null=True
    )
    interval_id = serializers.PrimaryKeyRelatedField(
        queryset=IntervalSchedule.objects.all(),
        source='interval',
        write_only=True,
        required=False,
        allow_null=True
    )
    schedule_display = serializers.SerializerMethodField()

    class Meta:
        model = PeriodicTask
        fields = [
            'id', 'name', 'task', 'crontab', 'interval', 'crontab_id', 'interval_id',
            'args', 'kwargs', 'queue', 'exchange', 'routing_key',
            'expires', 'enabled', 'last_run_at', 'total_run_count',
            'date_changed', 'description', 'schedule_display'
        ]
        read_only_fields = ['last_run_at', 'total_run_count', 'date_changed']

    def get_schedule_display(self, obj):
        """Retorna descrição legível do agendamento."""
        if obj.crontab:
            from .utils import explain_crontab
            crontab_str = f"{obj.crontab.minute} {obj.crontab.hour} {obj.crontab.day_of_month} {obj.crontab.month_of_year} {obj.crontab.day_of_week}"
            return explain_crontab(crontab_str)
        elif obj.interval:
            period_map = {
                'days': 'dia(s)',
                'hours': 'hora(s)',
                'minutes': 'minuto(s)',
                'seconds': 'segundo(s)',
                'microseconds': 'microssegundo(s)',
            }
            period_pt = period_map.get(obj.interval.period, obj.interval.period)
            return f"A cada {obj.interval.every} {period_pt}"
        return "Sem agendamento definido"

    def validate(self, data):
        """Valida que apenas um tipo de agendamento foi fornecido."""
        crontab = data.get('crontab')
        interval = data.get('interval')

        if crontab and interval:
            raise serializers.ValidationError(
                "Apenas um tipo de agendamento pode ser definido: crontab ou interval."
            )

        if not crontab and not interval:
            raise serializers.ValidationError(
                "É necessário definir um agendamento: crontab ou interval."
            )

        return data
