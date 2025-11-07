"""API URL Configuration."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TeamViewSet, DriverViewSet, CircuitViewSet, SeasonViewSet,
    EventViewSet, SessionViewSet, RaceResultViewSet,
    QualifyingResultViewSet, SprintResultViewSet,
    DriverStandingViewSet, ConstructorStandingViewSet,
    LapTimeViewSet, TyreStrategyViewSet, PitStopViewSet,
    WeatherDataViewSet, data_status, driver_prediction, constructor_prediction,
    available_drivers, available_teams, available_circuits, available_years
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

urlpatterns = [
    path('', include(router.urls)),
    path('status/', data_status, name='data-status'),
    path('predictions/driver/', driver_prediction, name='driver-prediction'),
    path('predictions/constructor/', constructor_prediction, name='constructor-prediction'),
    path('options/drivers/', available_drivers, name='available-drivers'),
    path('options/teams/', available_teams, name='available-teams'),
    path('options/circuits/', available_circuits, name='available-circuits'),
    path('options/years/', available_years, name='available-years'),
]
