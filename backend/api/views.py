"""
API ViewSets for F1 data endpoints.
"""
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Max, Prefetch
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from core.models import (
    Team, Driver, Circuit, Season, Event, Session,
    RaceResult, QualifyingResult, SprintResult,
    DriverStanding, ConstructorStanding,
    LapTime, TyreStrategy, PitStop, WeatherData
)
from .serializers import (
    TeamSerializer, DriverSerializer, CircuitSerializer, SeasonSerializer,
    EventSerializer, SessionSerializer, RaceResultSerializer,
    QualifyingResultSerializer, SprintResultSerializer,
    DriverStandingSerializer, ConstructorStandingSerializer,
    LapTimeSerializer, TyreStrategySerializer, PitStopSerializer,
    WeatherDataSerializer
)


class TeamViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for F1 teams.

    list: Get all teams
    retrieve: Get specific team by ID
    """
    queryset = Team.objects.all()
    serializer_class = TeamSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'team_id']
    ordering_fields = ['name']
    ordering = ['name']


class DriverViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for F1 drivers.

    list: Get all drivers
    retrieve: Get specific driver by ID
    """
    queryset = Driver.objects.all()
    serializer_class = DriverSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['first_name', 'last_name', 'code']
    ordering_fields = ['last_name', 'number']
    ordering = ['last_name']


class CircuitViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for F1 circuits.

    list: Get all circuits
    retrieve: Get specific circuit by ID
    """
    queryset = Circuit.objects.all()
    serializer_class = CircuitSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['country']
    search_fields = ['name', 'location', 'country']
    ordering_fields = ['name', 'country']
    ordering = ['name']


class SeasonViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for F1 seasons.

    list: Get all seasons
    retrieve: Get specific season by ID
    """
    queryset = Season.objects.all()
    serializer_class = SeasonSerializer
    ordering = ['-year']


class EventViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for F1 events/grands prix.

    list: Get all events with optional filters
    retrieve: Get specific event by ID
    """
    queryset = Event.objects.select_related('season', 'circuit').all()
    serializer_class = EventSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['season', 'season__year', 'event_type', 'circuit']
    search_fields = ['event_name']
    ordering_fields = ['event_date', 'round_number']
    ordering = ['-season', 'round_number']


class SessionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for F1 sessions.

    list: Get all sessions with optional filters
    retrieve: Get specific session by ID
    """
    queryset = Session.objects.select_related('event', 'event__season', 'event__circuit').all()
    serializer_class = SessionSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['event', 'event__season__year', 'session_type', 'is_complete', 'data_collected']
    ordering_fields = ['session_date']
    ordering = ['-session_date']


class RaceResultViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for race results.

    list: Get all race results with optional filters
    retrieve: Get specific race result by ID
    latest: Get latest race results
    """
    queryset = RaceResult.objects.select_related(
        'session', 'driver', 'team', 'session__event', 'session__event__season'
    ).all()
    serializer_class = RaceResultSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['session', 'driver', 'team', 'session__event__season__year']
    ordering_fields = ['position', 'points']
    ordering = ['session', 'position']

    @action(detail=False, methods=['get'])
    @method_decorator(cache_page(60 * 5))  # Cache for 5 minutes
    def latest(self, request):
        """Get latest race results."""
        season_year = request.query_params.get('year')

        # If no year specified, try to get the current year's latest race
        if not season_year:
            from datetime import datetime
            season_year = datetime.now().year

        try:
            season = Season.objects.get(year=season_year)

            # Get the latest completed race session
            latest_session = Session.objects.filter(
                event__season=season,
                session_type='R',
                is_complete=True
            ).order_by('-session_date').first()

            if not latest_session:
                return Response(
                    {'error': 'No completed race found for this season'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Get race results for this session
            results = RaceResult.objects.filter(
                session=latest_session
            ).select_related('driver', 'team').order_by('position')

            serializer = self.get_serializer(results, many=True)
            return Response({
                'status': 'success',
                'raceInfo': {
                    'eventName': latest_session.event.event_name,
                    'location': latest_session.event.circuit.location,
                    'date': latest_session.session_date.strftime('%Y-%m-%d'),
                    'round': latest_session.event.round_number
                },
                'results': serializer.data
            })

        except Season.DoesNotExist:
            return Response({'error': 'Season not found'}, status=status.HTTP_404_NOT_FOUND)


class QualifyingResultViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for qualifying results.

    list: Get all qualifying results with optional filters
    retrieve: Get specific qualifying result by ID
    latest: Get latest qualifying results
    """
    queryset = QualifyingResult.objects.select_related(
        'session', 'driver', 'team', 'session__event', 'session__event__season'
    ).all()
    serializer_class = QualifyingResultSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['session', 'driver', 'team', 'session__event__season__year']
    ordering_fields = ['position']
    ordering = ['session', 'position']

    @action(detail=False, methods=['get'])
    @method_decorator(cache_page(60 * 5))  # Cache for 5 minutes
    def latest(self, request):
        """Get latest qualifying results."""
        season_year = request.query_params.get('year')

        # If no year specified, try to get the current year's latest qualifying
        if not season_year:
            from datetime import datetime
            season_year = datetime.now().year

        try:
            season = Season.objects.get(year=season_year)

            # Get the latest completed qualifying session
            latest_session = Session.objects.filter(
                event__season=season,
                session_type='Q',
                is_complete=True
            ).order_by('-session_date').first()

            if not latest_session:
                return Response(
                    {'error': 'No completed qualifying found for this season'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Get qualifying results for this session
            results = QualifyingResult.objects.filter(
                session=latest_session
            ).select_related('driver', 'team').order_by('position')

            serializer = self.get_serializer(results, many=True)
            return Response({
                'status': 'success',
                'raceInfo': {
                    'eventName': latest_session.event.event_name,
                    'location': latest_session.event.circuit.location,
                    'date': latest_session.session_date.strftime('%Y-%m-%d'),
                    'round': latest_session.event.round_number
                },
                'results': serializer.data
            })

        except Season.DoesNotExist:
            return Response({'error': 'Season not found'}, status=status.HTTP_404_NOT_FOUND)


class SprintResultViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for sprint results.

    list: Get all sprint results with optional filters
    retrieve: Get specific sprint result by ID
    """
    queryset = SprintResult.objects.select_related(
        'session', 'driver', 'team', 'session__event', 'session__event__season'
    ).all()
    serializer_class = SprintResultSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['session', 'driver', 'team', 'session__event__season__year']
    ordering_fields = ['position', 'points']
    ordering = ['session', 'position']


class DriverStandingViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for driver championship standings.

    list: Get driver standings with optional filters
    retrieve: Get specific standing by ID
    latest: Get latest standings for a season
    """
    queryset = DriverStanding.objects.select_related(
        'season', 'event', 'driver', 'team'
    ).all()
    serializer_class = DriverStandingSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['season', 'season__year', 'event', 'driver', 'team']
    ordering_fields = ['position', 'points']
    ordering = ['season', 'event', 'position']

    @action(detail=False, methods=['get'])
    @method_decorator(cache_page(60 * 5))  # Cache for 5 minutes
    def latest(self, request):
        """Get latest standings for specified season."""
        season_year = request.query_params.get('year')

        if not season_year:
            return Response(
                {'error': 'Year parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            season = Season.objects.get(year=season_year)
            latest_event = Event.objects.filter(season=season).order_by('-round_number').first()

            if not latest_event:
                return Response({'error': 'No events found for this season'}, status=status.HTTP_404_NOT_FOUND)

            standings = DriverStanding.objects.filter(
                season=season,
                event=latest_event
            ).select_related('driver', 'team').order_by('position')

            serializer = self.get_serializer(standings, many=True)
            return Response(serializer.data)

        except Season.DoesNotExist:
            return Response({'error': 'Season not found'}, status=status.HTTP_404_NOT_FOUND)


class ConstructorStandingViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for constructor championship standings.

    list: Get constructor standings with optional filters
    retrieve: Get specific standing by ID
    latest: Get latest standings for a season
    """
    queryset = ConstructorStanding.objects.select_related(
        'season', 'event', 'team'
    ).all()
    serializer_class = ConstructorStandingSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['season', 'season__year', 'event', 'team']
    ordering_fields = ['position', 'points']
    ordering = ['season', 'event', 'position']

    @action(detail=False, methods=['get'])
    @method_decorator(cache_page(60 * 5))  # Cache for 5 minutes
    def latest(self, request):
        """Get latest standings for specified season."""
        season_year = request.query_params.get('year')

        if not season_year:
            return Response(
                {'error': 'Year parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            season = Season.objects.get(year=season_year)
            latest_event = Event.objects.filter(season=season).order_by('-round_number').first()

            if not latest_event:
                return Response({'error': 'No events found for this season'}, status=status.HTTP_404_NOT_FOUND)

            standings = ConstructorStanding.objects.filter(
                season=season,
                event=latest_event
            ).select_related('team').order_by('position')

            serializer = self.get_serializer(standings, many=True)
            return Response(serializer.data)

        except Season.DoesNotExist:
            return Response({'error': 'Season not found'}, status=status.HTTP_404_NOT_FOUND)


class LapTimeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for lap times.

    list: Get all lap times with optional filters
    retrieve: Get specific lap time by ID
    """
    queryset = LapTime.objects.select_related('session', 'driver', 'team').all()
    serializer_class = LapTimeSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['session', 'driver', 'team', 'lap_number', 'compound', 'is_personal_best']
    ordering_fields = ['lap_number', 'lap_time']
    ordering = ['session', 'lap_number']


class TyreStrategyViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for tyre strategies.

    list: Get all tyre strategies with optional filters
    retrieve: Get specific tyre strategy by ID
    """
    queryset = TyreStrategy.objects.select_related('session', 'driver', 'team').all()
    serializer_class = TyreStrategySerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['session', 'driver', 'team', 'compound']
    ordering_fields = ['stint_number']
    ordering = ['session', 'driver', 'stint_number']


class PitStopViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for pit stops.

    list: Get all pit stops with optional filters
    retrieve: Get specific pit stop by ID
    """
    queryset = PitStop.objects.select_related('session', 'driver', 'team').all()
    serializer_class = PitStopSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['session', 'driver', 'team']
    ordering_fields = ['lap', 'duration']
    ordering = ['session', 'lap']


class WeatherDataViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for weather data.

    list: Get all weather data with optional filters
    retrieve: Get specific weather data by ID
    """
    queryset = WeatherData.objects.select_related('session').all()
    serializer_class = WeatherDataSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['session', 'rainfall']
    ordering_fields = ['timestamp']
    ordering = ['session', 'timestamp']


@api_view(['GET'])
def data_status(request):
    """
    Get database population status and Celery task information.
    """
    from datetime import datetime
    from django.utils import timezone

    # Count records in each table
    stats = {
        'database': {
            'seasons': Season.objects.count(),
            'events': Event.objects.count(),
            'sessions': Session.objects.count(),
            'drivers': Driver.objects.count(),
            'teams': Team.objects.count(),
            'circuits': Circuit.objects.count(),
            'race_results': RaceResult.objects.count(),
            'qualifying_results': QualifyingResult.objects.count(),
            'sprint_results': SprintResult.objects.count(),
            'driver_standings': DriverStanding.objects.count(),
            'constructor_standings': ConstructorStanding.objects.count(),
            'lap_times': LapTime.objects.count(),
            'tyre_strategies': TyreStrategy.objects.count(),
            'pit_stops': PitStop.objects.count(),
            'weather_data': WeatherData.objects.count(),
        },
        'sessions_by_type': {
            'races': Session.objects.filter(session_type='R').count(),
            'qualifying': Session.objects.filter(session_type='Q').count(),
            'sprints': Session.objects.filter(session_type='S').count(),
        },
        'sessions_status': {
            'complete': Session.objects.filter(is_complete=True).count(),
            'incomplete': Session.objects.filter(is_complete=False).count(),
            'data_collected': Session.objects.filter(data_collected=True).count(),
        },
        'latest_updates': {}
    }

    # Get latest updates for each session type
    for session_type, label in [('R', 'race'), ('Q', 'qualifying'), ('S', 'sprint')]:
        latest_session = Session.objects.filter(
            session_type=session_type,
            data_collected=True
        ).order_by('-collection_date').first()

        if latest_session:
            stats['latest_updates'][label] = {
                'event_name': latest_session.event.event_name,
                'round': latest_session.event.round_number,
                'session_date': latest_session.session_date.isoformat(),
                'collection_date': latest_session.collection_date.isoformat() if latest_session.collection_date else None,
            }

    # Try to get Celery task info
    try:
        from celery import current_app

        inspector = current_app.control.inspect()

        # Get active tasks
        active_tasks = inspector.active()
        scheduled_tasks = inspector.scheduled()

        stats['celery'] = {
            'active_tasks': active_tasks or {},
            'scheduled_tasks': scheduled_tasks or {},
            'workers_online': list(active_tasks.keys()) if active_tasks else [],
        }
    except Exception as e:
        stats['celery'] = {
            'error': str(e),
            'message': 'Could not connect to Celery workers'
        }

    # Check Celery Beat schedule
    try:
        from django_celery_beat.models import PeriodicTask
        periodic_tasks = PeriodicTask.objects.filter(enabled=True).values(
            'name', 'task', 'enabled', 'last_run_at'
        )
        stats['celery_beat'] = {
            'periodic_tasks': list(periodic_tasks),
        }
    except Exception as e:
        stats['celery_beat'] = {
            'error': str(e),
            'message': 'Celery Beat not configured or django-celery-beat not installed'
        }

    return Response({
        'status': 'success',
        'timestamp': timezone.now().isoformat(),
        'stats': stats
    })
