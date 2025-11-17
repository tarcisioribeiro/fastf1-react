"""Django Admin configuration for F1 models."""
from django.contrib import admin
from .models import (
    Team, Driver, Circuit, Season, Event, Session,
    RaceResult, QualifyingResult, SprintResult,
    DriverStanding, ConstructorStanding,
    LapTime, TyreStrategy, PitStop, WeatherData, TelemetryData,
    DataCollectionLog, DataAuditReport, DataAuditSuggestion,
    HistoricalDataCollectionConfig, HistoricalDataGap
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


@admin.register(DataCollectionLog)
class DataCollectionLogAdmin(admin.ModelAdmin):
    list_display = ['created_at', 'level', 'source', 'task_name', 'year', 'round_number', 'resolved']
    list_filter = ['level', 'source', 'resolved', 'created_at']
    search_fields = ['task_name', 'message', 'exception_type']
    readonly_fields = ['created_at', 'task_id', 'traceback']
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('level', 'source', 'task_name', 'task_id')
        }),
        ('Mensagem', {
            'fields': ('message', 'exception_type', 'traceback')
        }),
        ('Contexto', {
            'fields': ('year', 'round_number', 'session_type')
        }),
        ('Resolução', {
            'fields': ('resolved', 'resolved_at', 'resolution_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )
    ordering = ['-created_at']
    list_per_page = 50

    def get_queryset(self, request):
        """Otimizar queries do admin."""
        qs = super().get_queryset(request)
        return qs

    actions = ['mark_as_resolved', 'mark_as_unresolved']

    def mark_as_resolved(self, request, queryset):
        """Marcar logs selecionados como resolvidos."""
        from django.utils import timezone
        count = queryset.update(resolved=True, resolved_at=timezone.now())
        self.message_user(request, f'{count} log(s) marcado(s) como resolvido(s).')
    mark_as_resolved.short_description = "Marcar como resolvido"

    def mark_as_unresolved(self, request, queryset):
        """Marcar logs selecionados como não resolvidos."""
        count = queryset.update(resolved=False, resolved_at=None)
        self.message_user(request, f'{count} log(s) marcado(s) como não resolvido(s).')
    mark_as_unresolved.short_description = "Marcar como não resolvido"


@admin.register(DataAuditSuggestion)
class DataAuditSuggestionAdmin(admin.ModelAdmin):
    list_display = ['table_name', 'field_name', 'record_identifier', 'suggested_value', 'source_name', 'confidence_score', 'applied', 'rejected']
    list_filter = ['table_name', 'field_name', 'source_name', 'applied', 'rejected', 'report__execution_date']
    search_fields = ['record_identifier', 'suggested_value']
    readonly_fields = ['source_timestamp', 'created_at', 'applied_at']
    ordering = ['-created_at']
    list_per_page = 50

    fieldsets = (
        ('Localização do Campo', {
            'fields': ('report', 'table_name', 'field_name', 'record_id', 'record_identifier')
        }),
        ('Valores', {
            'fields': ('current_value', 'suggested_value', 'confidence_score')
        }),
        ('Fonte', {
            'fields': ('source_name', 'source_url', 'source_timestamp')
        }),
        ('Status', {
            'fields': ('applied', 'applied_at', 'rejected', 'rejection_reason')
        }),
    )


@admin.register(DataAuditReport)
class DataAuditReportAdmin(admin.ModelAdmin):
    list_display = ['execution_date', 'status', 'total_tables_scanned', 'total_empty_fields_found', 'total_suggestions_found', 'execution_time_seconds']
    list_filter = ['status', 'execution_date']
    readonly_fields = ['execution_date', 'execution_time_seconds', 'audit_results']
    ordering = ['-execution_date']

    fieldsets = (
        ('Informações da Execução', {
            'fields': ('execution_date', 'status', 'execution_time_seconds')
        }),
        ('Estatísticas', {
            'fields': ('total_tables_scanned', 'total_fields_scanned', 'total_empty_fields_found', 'total_suggestions_found')
        }),
        ('Resultados', {
            'fields': ('audit_results',),
            'classes': ('collapse',)
        }),
        ('Erros', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
    )


@admin.register(HistoricalDataCollectionConfig)
class HistoricalDataCollectionConfigAdmin(admin.ModelAdmin):
    list_display = ['enabled', 'max_workers', 'tasks_per_batch', 'scan_interval_minutes', 'start_year', 'end_year', 'last_scan_at', 'total_records_collected']
    readonly_fields = ['last_scan_at', 'last_year_processed', 'total_records_collected', 'created_at', 'updated_at']

    fieldsets = (
        ('Status', {
            'fields': ('enabled',)
        }),
        ('Controle de Workers e Paralelismo', {
            'fields': ('max_workers', 'tasks_per_batch', 'scan_interval_minutes'),
            'description': 'Configure quantos workers rodam em paralelo e quantas tarefas por lote.'
        }),
        ('Período de Coleta', {
            'fields': ('start_year', 'end_year'),
            'description': 'Define o intervalo de anos para coleta (do mais recente para o mais antigo).'
        }),
        ('Tipos de Dados', {
            'fields': ('collect_races', 'collect_qualifying', 'collect_sprints', 'collect_standings', 'collect_drivers', 'collect_teams', 'collect_circuits'),
            'description': 'Selecione quais tipos de dados devem ser coletados.'
        }),
        ('Fontes de Dados', {
            'fields': ('use_wikipedia', 'use_ergast_api'),
            'description': 'Selecione as fontes de dados para coleta histórica.'
        }),
        ('Estatísticas', {
            'fields': ('last_scan_at', 'last_year_processed', 'total_records_collected'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def has_add_permission(self, request):
        """Permitir apenas uma configuração (singleton)."""
        return not HistoricalDataCollectionConfig.objects.exists()

    def has_delete_permission(self, request, obj=None):
        """Não permitir deletar a configuração."""
        return False


@admin.register(HistoricalDataGap)
class HistoricalDataGapAdmin(admin.ModelAdmin):
    list_display = ['gap_type', 'year', 'round_number', 'status', 'priority', 'attempt_count', 'created_at']
    list_filter = ['gap_type', 'status', 'year']
    search_fields = ['description', 'error_message']
    readonly_fields = ['created_at', 'updated_at', 'last_attempt_at', 'collected_at']
    ordering = ['-priority', '-year', 'round_number']
    list_per_page = 50

    fieldsets = (
        ('Identificação', {
            'fields': ('gap_type', 'status', 'year', 'round_number', 'session_type')
        }),
        ('Descrição', {
            'fields': ('description',)
        }),
        ('Prioridade', {
            'fields': ('priority',)
        }),
        ('Tentativas', {
            'fields': ('attempt_count', 'max_attempts', 'last_attempt_at')
        }),
        ('Resultado', {
            'fields': ('collected_at', 'error_message'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['mark_as_pending', 'mark_as_completed', 'delete_selected']

    def mark_as_pending(self, request, queryset):
        """Marcar gaps como pendentes para reprocessamento."""
        count = queryset.update(status='pending', attempt_count=0)
        self.message_user(request, f'{count} gap(s) marcado(s) como pendente(s).')
    mark_as_pending.short_description = "Marcar como pendente"

    def mark_as_completed(self, request, queryset):
        """Marcar gaps como concluídos."""
        from django.utils import timezone
        count = queryset.update(status='completed', collected_at=timezone.now())
        self.message_user(request, f'{count} gap(s) marcado(s) como concluído(s).')
    mark_as_completed.short_description = "Marcar como concluído"
