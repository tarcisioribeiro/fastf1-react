"""API URL Configuration."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TeamViewSet, DriverViewSet, CircuitViewSet, SeasonViewSet,
    EventViewSet, SessionViewSet, RaceResultViewSet,
    QualifyingResultViewSet, SprintResultViewSet,
    DriverStandingViewSet, ConstructorStandingViewSet,
    LapTimeViewSet, TyreStrategyViewSet, PitStopViewSet,
    WeatherDataViewSet, DataAuditReportViewSet, DataAuditSuggestionViewSet,
    data_status, ml_models_status, driver_prediction, constructor_prediction,
    available_drivers, available_teams, available_circuits, available_years,
    active_drivers_grid, active_teams_grid,
    circuit_race_status,
    get_filter_options, get_grands_prix, get_drivers_by_year, get_teams_by_year,
    team_history, driver_career, celery_tasks_status,
    historical_data_status, trigger_historical_collection,
    clean_database_duplicates, database_health
)

# Create router and register viewsets
router = DefaultRouter()
router.register(r'teams', TeamViewSet, basename='team')
router.register(r'drivers', DriverViewSet, basename='driver')
router.register(r'circuits', CircuitViewSet, basename='circuit')
router.register(r'seasons', SeasonViewSet, basename='season')
router.register(r'events', EventViewSet, basename='event')
router.register(r'sessions', SessionViewSet, basename='session')
router.register(r'races', RaceResultViewSet, basename='race')
router.register(r'qualifying', QualifyingResultViewSet, basename='qualifying')
router.register(r'sprints', SprintResultViewSet, basename='sprint')
router.register(r'driver-standings', DriverStandingViewSet, basename='driver-standing')
router.register(r'constructor-standings', ConstructorStandingViewSet, basename='constructor-standing')
router.register(r'lap-times', LapTimeViewSet, basename='lap-time')
router.register(r'tyre-strategies', TyreStrategyViewSet, basename='tyre-strategy')
router.register(r'pit-stops', PitStopViewSet, basename='pit-stop')
router.register(r'weather', WeatherDataViewSet, basename='weather')
router.register(r'data-audit-reports', DataAuditReportViewSet, basename='data-audit-report')
router.register(r'data-audit-suggestions', DataAuditSuggestionViewSet, basename='data-audit-suggestion')

urlpatterns = [
    path('', include(router.urls)),
    path('status/', data_status, name='data-status'),
    path('ml/status/', ml_models_status, name='ml-models-status'),
    path('tasks/status/', celery_tasks_status, name='celery-tasks-status'),
    path('predictions/driver/', driver_prediction, name='driver-prediction'),
    path('predictions/constructor/', constructor_prediction, name='constructor-prediction'),
    path('options/drivers/', available_drivers, name='available-drivers'),
    path('options/teams/', available_teams, name='available-teams'),
    path('options/circuits/', available_circuits, name='available-circuits'),
    path('options/years/', available_years, name='available-years'),
    path('options/circuit-race-status/', circuit_race_status, name='circuit-race-status'),
    # Grid-specific options (current season only, for predictions)
    path('options/grid/drivers/', active_drivers_grid, name='active-drivers-grid'),
    path('options/grid/teams/', active_teams_grid, name='active-teams-grid'),
    # New filter options endpoints
    path('filters/options/', get_filter_options, name='filter-options'),
    path('filters/grands-prix/', get_grands_prix, name='grands-prix'),
    path('filters/drivers/', get_drivers_by_year, name='drivers-by-year'),
    path('filters/teams/', get_teams_by_year, name='teams-by-year'),
    # Team and driver history endpoints
    path('history/team/', team_history, name='team-history'),
    path('history/driver/', driver_career, name='driver-career'),
    # Historical data endpoints (pre-2018)
    path('historical/status/', historical_data_status, name='historical-data-status'),
    path('historical/collect/', trigger_historical_collection, name='trigger-historical-collection'),
    # Database maintenance endpoints
    path('maintenance/clean-duplicates/', clean_database_duplicates, name='clean-duplicates'),
    path('maintenance/health/', database_health, name='database-health'),
]
