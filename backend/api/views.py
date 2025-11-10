"""
API ViewSets for F1 data endpoints.
"""
from datetime import datetime
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Max, Min, Avg, Prefetch
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.utils import timezone

from core.models import (
    Team, Driver, Circuit, Season, Event, Session,
    RaceResult, QualifyingResult, SprintResult,
    DriverStanding, ConstructorStanding,
    LapTime, TyreStrategy, PitStop, WeatherData,
    DataAuditReport, DataAuditSuggestion
)
from .serializers import (
    TeamSerializer, DriverSerializer, CircuitSerializer, SeasonSerializer,
    EventSerializer, SessionSerializer, RaceResultSerializer,
    QualifyingResultSerializer, SprintResultSerializer,
    DriverStandingSerializer, ConstructorStandingSerializer,
    LapTimeSerializer, TyreStrategySerializer, PitStopSerializer,
    WeatherDataSerializer, DataAuditReportSerializer, DataAuditReportListSerializer,
    DataAuditSuggestionSerializer
)

# ML imports
try:
    from ml.predictor import get_predictor
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False


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

    @action(detail=False, methods=['get'])
    @method_decorator(cache_page(60 * 10))  # Cache for 10 minutes
    def history(self, request):
        """Get historical race results with filters."""
        year = request.query_params.get('year')
        circuit = request.query_params.get('circuit')
        driver = request.query_params.get('driver')
        team = request.query_params.get('team')

        # Base query
        sessions = Session.objects.filter(
            session_type='R',
            is_complete=True
        ).select_related('event', 'event__season', 'event__circuit')

        # Apply filters
        if year:
            sessions = sessions.filter(event__season__year=year)
        if circuit:
            sessions = sessions.filter(event__circuit__id=circuit)

        sessions = sessions.order_by('-session_date')

        # Get results for these sessions
        results_by_session = []
        for session in sessions:
            results_query = RaceResult.objects.filter(
                session=session
            ).select_related('driver', 'team')

            # Apply driver/team filters
            if driver:
                results_query = results_query.filter(driver__id=driver)
            if team:
                results_query = results_query.filter(team__id=team)

            results_query = results_query.order_by('position')

            if results_query.exists():
                serializer = self.get_serializer(results_query, many=True)
                results_by_session.append({
                    'sessionId': session.id,
                    'eventName': session.event.event_name,
                    'circuit': session.event.circuit.name,
                    'location': session.event.circuit.location,
                    'country': session.event.circuit.country,
                    'date': session.session_date.strftime('%Y-%m-%d'),
                    'year': session.event.season.year,
                    'round': session.event.round_number,
                    'results': serializer.data
                })

        return Response({
            'status': 'success',
            'count': len(results_by_session),
            'races': results_by_session
        })


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

    @action(detail=False, methods=['get'])
    @method_decorator(cache_page(60 * 10))  # Cache for 10 minutes
    def history(self, request):
        """
        Get historical qualifying results with optional filters.

        Query params:
        - year: Filter by season year
        - circuit: Filter by circuit name
        - driver: Filter by driver code
        - team: Filter by team name
        """
        # Get filter parameters
        year = request.query_params.get('year')
        circuit = request.query_params.get('circuit')
        driver = request.query_params.get('driver')
        team = request.query_params.get('team')

        # Start with completed qualifying sessions
        sessions = Session.objects.filter(
            session_type='Q',
            is_complete=True
        ).select_related(
            'event', 'event__circuit', 'event__season'
        )

        # Apply filters
        if year:
            sessions = sessions.filter(event__season__year=year)
        if circuit:
            sessions = sessions.filter(event__circuit__name__icontains=circuit)

        # Get all qualifying results for these sessions
        results_query = QualifyingResult.objects.filter(
            session__in=sessions
        ).select_related('driver', 'team', 'session', 'session__event', 'session__event__circuit')

        # Apply driver and team filters if specified
        if driver:
            results_query = results_query.filter(driver__code__icontains=driver)
        if team:
            results_query = results_query.filter(team__name__icontains=team)

        # Group results by session
        results_by_session = {}
        for result in results_query.order_by('session__session_date', 'position'):
            session_id = result.session.id
            if session_id not in results_by_session:
                results_by_session[session_id] = {
                    'session': result.session,
                    'results': []
                }
            results_by_session[session_id]['results'].append(result)

        # Format response
        formatted_results = []
        for session_id, data in results_by_session.items():
            session = data['session']
            serializer = self.get_serializer(data['results'], many=True)
            formatted_results.append({
                'sessionId': session.id,
                'eventName': session.event.event_name,
                'circuit': session.event.circuit.name,
                'location': session.event.circuit.location,
                'country': session.event.circuit.country,
                'date': session.session_date.strftime('%Y-%m-%d'),
                'year': session.event.season.year,
                'round': session.event.round_number,
                'results': serializer.data
            })

        # Sort by date (most recent first)
        formatted_results.sort(key=lambda x: x['date'], reverse=True)

        return Response({
            'status': 'success',
            'count': len(formatted_results),
            'qualifyings': formatted_results
        })


class SprintResultViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for sprint results.

    list: Get all sprint results with optional filters
    retrieve: Get specific sprint result by ID
    latest: Get latest sprint results
    history: Get historical sprint results with filters
    """
    queryset = SprintResult.objects.select_related(
        'session', 'driver', 'team', 'session__event', 'session__event__season'
    ).all()
    serializer_class = SprintResultSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['session', 'driver', 'team', 'session__event__season__year']
    ordering_fields = ['position', 'points']
    ordering = ['session', 'position']

    @action(detail=False, methods=['get'])
    @method_decorator(cache_page(60 * 5))  # Cache for 5 minutes
    def latest(self, request):
        """Get latest sprint results."""
        season_year = request.query_params.get('year')

        # If no year specified, try to get the current year's latest sprint
        if not season_year:
            from datetime import datetime
            season_year = datetime.now().year

        try:
            season = Season.objects.get(year=season_year)

            # Get the latest completed sprint session
            latest_session = Session.objects.filter(
                event__season=season,
                session_type='S',
                is_complete=True
            ).order_by('-session_date').first()

            if not latest_session:
                return Response(
                    {'error': 'No completed sprint found for this season'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Get sprint results for this session
            results = SprintResult.objects.filter(
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

    @action(detail=False, methods=['get'])
    @method_decorator(cache_page(60 * 10))  # Cache for 10 minutes
    def history(self, request):
        """
        Get historical sprint results with optional filters.

        Query params:
        - year: Filter by season year
        - circuit: Filter by circuit name
        - driver: Filter by driver code
        - team: Filter by team name
        """
        # Get filter parameters
        year = request.query_params.get('year')
        circuit = request.query_params.get('circuit')
        driver = request.query_params.get('driver')
        team = request.query_params.get('team')

        # Start with completed sprint sessions
        sessions = Session.objects.filter(
            session_type='S',
            is_complete=True
        ).select_related(
            'event', 'event__circuit', 'event__season'
        )

        # Apply filters
        if year:
            sessions = sessions.filter(event__season__year=year)
        if circuit:
            sessions = sessions.filter(event__circuit__name__icontains=circuit)

        # Get all sprint results for these sessions
        results_query = SprintResult.objects.filter(
            session__in=sessions
        ).select_related('driver', 'team', 'session', 'session__event', 'session__event__circuit')

        # Apply driver and team filters if specified
        if driver:
            results_query = results_query.filter(driver__code__icontains=driver)
        if team:
            results_query = results_query.filter(team__name__icontains=team)

        # Group results by session
        results_by_session = {}
        for result in results_query.order_by('session__session_date', 'position'):
            session_id = result.session.id
            if session_id not in results_by_session:
                results_by_session[session_id] = {
                    'session': result.session,
                    'results': []
                }
            results_by_session[session_id]['results'].append(result)

        # Format response
        formatted_results = []
        for session_id, data in results_by_session.items():
            session = data['session']
            serializer = self.get_serializer(data['results'], many=True)
            formatted_results.append({
                'sessionId': session.id,
                'eventName': session.event.event_name,
                'circuit': session.event.circuit.name,
                'location': session.event.circuit.location,
                'country': session.event.circuit.country,
                'date': session.session_date.strftime('%Y-%m-%d'),
                'year': session.event.season.year,
                'round': session.event.round_number,
                'results': serializer.data
            })

        # Sort by date (most recent first)
        formatted_results.sort(key=lambda x: x['date'], reverse=True)

        return Response({
            'status': 'success',
            'count': len(formatted_results),
            'sprints': formatted_results
        })


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

    @action(detail=False, methods=['get'])
    @method_decorator(cache_page(60 * 10))  # Cache for 10 minutes
    def evolution(self, request):
        """
        Get points evolution over race rounds for drivers.

        Query params:
        - year: Season year (required)
        - drivers: Comma-separated driver codes (optional, returns all if not specified)
        - start_round: Starting round (optional, default 1)
        - end_round: Ending round (optional, default latest)
        """
        season_year = request.query_params.get('year')
        driver_codes = request.query_params.get('drivers', '').split(',') if request.query_params.get('drivers') else None
        start_round = int(request.query_params.get('start_round', 1))
        end_round = request.query_params.get('end_round')

        if not season_year:
            return Response(
                {'error': 'Year parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            season = Season.objects.get(year=season_year)

            # Get events in the specified range
            events_query = Event.objects.filter(season=season, round_number__gte=start_round)
            if end_round:
                events_query = events_query.filter(round_number__lte=int(end_round))
            events = events_query.order_by('round_number')

            # Get standings for all events
            standings_query = DriverStanding.objects.filter(
                season=season,
                event__in=events
            ).select_related('driver', 'event', 'team')

            # Filter by drivers if specified
            if driver_codes:
                driver_codes = [code.strip().upper() for code in driver_codes if code.strip()]
                standings_query = standings_query.filter(driver__code__in=driver_codes)

            standings = standings_query.order_by('event__round_number', 'position')

            # Organize data by driver
            evolution_data = {}
            for standing in standings:
                driver_code = standing.driver.code
                if driver_code not in evolution_data:
                    evolution_data[driver_code] = {
                        'driver': {
                            'code': standing.driver.code,
                            'fullName': standing.driver.full_name,
                            'number': standing.driver.number
                        },
                        'team': {
                            'name': standing.team.name if standing.team else 'Unknown',
                            'color': standing.team.color if standing.team else '#CCCCCC'
                        },
                        'points_by_round': []
                    }

                evolution_data[driver_code]['points_by_round'].append({
                    'round': standing.event.round_number,
                    'eventName': standing.event.event_name,
                    'points': standing.points,
                    'position': standing.position,
                    'wins': standing.wins,
                    'podiums': standing.podiums
                })

            return Response({
                'status': 'success',
                'year': season_year,
                'drivers': list(evolution_data.values())
            })

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

    @action(detail=False, methods=['get'])
    @method_decorator(cache_page(60 * 10))  # Cache for 10 minutes
    def evolution(self, request):
        """
        Get points evolution over race rounds for constructors.

        Query params:
        - year: Season year (required)
        - teams: Comma-separated team names (optional, returns all if not specified)
        - start_round: Starting round (optional, default 1)
        - end_round: Ending round (optional, default latest)
        """
        season_year = request.query_params.get('year')
        team_names = request.query_params.get('teams', '').split(',') if request.query_params.get('teams') else None
        start_round = int(request.query_params.get('start_round', 1))
        end_round = request.query_params.get('end_round')

        if not season_year:
            return Response(
                {'error': 'Year parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            season = Season.objects.get(year=season_year)

            # Get events in the specified range
            events_query = Event.objects.filter(season=season, round_number__gte=start_round)
            if end_round:
                events_query = events_query.filter(round_number__lte=int(end_round))
            events = events_query.order_by('round_number')

            # Get standings for all events
            standings_query = ConstructorStanding.objects.filter(
                season=season,
                event__in=events
            ).select_related('team', 'event')

            # Filter by teams if specified
            if team_names:
                team_names = [name.strip() for name in team_names if name.strip()]
                standings_query = standings_query.filter(team__name__in=team_names)

            standings = standings_query.order_by('event__round_number', 'position')

            # Organize data by team
            evolution_data = {}
            for standing in standings:
                team_name = standing.team.name
                if team_name not in evolution_data:
                    evolution_data[team_name] = {
                        'team': {
                            'name': standing.team.name,
                            'color': standing.team.color
                        },
                        'points_by_round': []
                    }

                evolution_data[team_name]['points_by_round'].append({
                    'round': standing.event.round_number,
                    'eventName': standing.event.event_name,
                    'points': standing.points,
                    'position': standing.position,
                    'wins': standing.wins,
                    'podiums': standing.podiums
                })

            return Response({
                'status': 'success',
                'year': season_year,
                'teams': list(evolution_data.values())
            })

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
    latest: Get pit stops for latest race
    """
    queryset = PitStop.objects.select_related('session', 'driver', 'team').all()
    serializer_class = PitStopSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['session', 'driver', 'team']
    ordering_fields = ['lap', 'duration']
    ordering = ['session', 'lap']

    @action(detail=False, methods=['get'])
    @method_decorator(cache_page(60 * 5))  # Cache for 5 minutes
    def latest(self, request):
        """Get pit stops for latest race."""
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

            # Get pit stops for this session
            pit_stops = PitStop.objects.filter(
                session=latest_session
            ).select_related('driver', 'team').order_by('lap', 'duration')

            serializer = self.get_serializer(pit_stops, many=True)
            return Response({
                'status': 'success',
                'raceInfo': {
                    'eventName': latest_session.event.event_name,
                    'location': latest_session.event.circuit.location,
                    'date': latest_session.session_date.strftime('%Y-%m-%d'),
                    'round': latest_session.event.round_number
                },
                'pitStops': serializer.data
            })

        except Season.DoesNotExist:
            return Response({'error': 'Season not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'])
    @method_decorator(cache_page(60 * 10))  # Cache for 10 minutes
    def analytics(self, request):
        """
        Get pit stop analytics for a specific session or season.

        Query params:
        - year: Season year (required)
        - round: Round number (optional, if not specified returns all for season)
        - team: Filter by team name (optional)
        """
        season_year = request.query_params.get('year')
        round_number = request.query_params.get('round')
        team_name = request.query_params.get('team')

        if not season_year:
            return Response(
                {'error': 'Year parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            season = Season.objects.filter(year=season_year).first()

            if not season:
                return Response({
                    'status': 'success',
                    'year': season_year,
                    'message': 'No data available for this season',
                    'data': {
                        'sessions': [],
                        'team_stats': [],
                        'driver_stats': []
                    }
                })

            # Get sessions
            sessions_query = Session.objects.filter(
                event__season=season,
                session_type='R',
                is_complete=True
            )

            if round_number:
                sessions_query = sessions_query.filter(event__round_number=round_number)

            sessions = sessions_query.select_related('event', 'event__circuit')

            # If no sessions found, return empty data instead of error
            if not sessions.exists():
                return Response({
                    'status': 'success',
                    'year': season_year,
                    'message': 'No completed race sessions found',
                    'data': {
                        'sessions': [],
                        'team_stats': [],
                        'driver_stats': []
                    }
                })

            # Get pit stops for these sessions
            pit_stops_query = PitStop.objects.filter(
                session__in=sessions
            ).select_related('driver', 'team', 'session', 'session__event')

            if team_name:
                pit_stops_query = pit_stops_query.filter(team__name__icontains=team_name)

            pit_stops = pit_stops_query.order_by('session__event__round_number', 'lap')

            # Get tyre strategies for correlating with pit stops
            tyre_strategies = TyreStrategy.objects.filter(
                session__in=sessions
            ).select_related('driver', 'team').order_by('driver', 'stint_number')

            # Create a map of driver -> tyre strategies per session
            tyre_map = {}
            for strategy in tyre_strategies:
                key = (strategy.session.id, strategy.driver.id)
                if key not in tyre_map:
                    tyre_map[key] = []
                tyre_map[key].append({
                    'stint': strategy.stint_number,
                    'compound': strategy.compound,
                    'start_lap': strategy.start_lap,
                    'end_lap': strategy.end_lap,
                    'stint_length': strategy.stint_length,
                })

            # Organize data for analytics
            analytics_data = {
                'sessions': [],
                'team_stats': {},
                'driver_stats': {},
                'tyre_usage': {}  # New: track tyre compound usage
            }

            # Group by session
            sessions_data = {}
            for pit_stop in pit_stops:
                session_id = pit_stop.session.id
                if session_id not in sessions_data:
                    sessions_data[session_id] = {
                        'sessionId': session_id,
                        'eventName': pit_stop.session.event.event_name,
                        'round': pit_stop.session.event.round_number,
                        'pit_stops': []
                    }

                duration_seconds = pit_stop.duration.total_seconds() if pit_stop.duration else None

                # Find tyre compounds used around this pit stop
                tyre_key = (session_id, pit_stop.driver.id)
                tyre_before = None
                tyre_after = None

                if tyre_key in tyre_map:
                    strategies = tyre_map[tyre_key]
                    for i, strategy in enumerate(strategies):
                        # Tyre before pit stop (stint that ended around this lap)
                        if strategy['end_lap'] >= pit_stop.lap - 1 and strategy['end_lap'] <= pit_stop.lap + 1:
                            tyre_before = strategy['compound']
                        # Tyre after pit stop (stint that started around this lap)
                        if strategy['start_lap'] >= pit_stop.lap - 1 and strategy['start_lap'] <= pit_stop.lap + 1:
                            tyre_after = strategy['compound']

                # Track tyre usage statistics
                if tyre_after:
                    compound_key = tyre_after
                    if compound_key not in analytics_data['tyre_usage']:
                        analytics_data['tyre_usage'][compound_key] = {
                            'compound': compound_key,
                            'count': 0,
                            'total_duration': 0,
                            'avg_duration': 0,
                        }
                    analytics_data['tyre_usage'][compound_key]['count'] += 1
                    if duration_seconds:
                        analytics_data['tyre_usage'][compound_key]['total_duration'] += duration_seconds

                sessions_data[session_id]['pit_stops'].append({
                    'lap': pit_stop.lap,
                    'driver': pit_stop.driver.code,
                    'team': pit_stop.team.name,
                    'duration': duration_seconds,
                    'stopNumber': pit_stop.stop_number,
                    'tyreBefore': tyre_before,
                    'tyreAfter': tyre_after,
                })

                # Team stats
                team_key = pit_stop.team.name
                if team_key not in analytics_data['team_stats']:
                    analytics_data['team_stats'][team_key] = {
                        'team': pit_stop.team.name,
                        'color': pit_stop.team.color,
                        'total_stops': 0,
                        'avg_duration': 0,
                        'durations': []
                    }

                analytics_data['team_stats'][team_key]['total_stops'] += 1
                if duration_seconds:
                    analytics_data['team_stats'][team_key]['durations'].append(duration_seconds)

                # Driver stats
                driver_key = pit_stop.driver.code
                if driver_key not in analytics_data['driver_stats']:
                    analytics_data['driver_stats'][driver_key] = {
                        'driver': pit_stop.driver.code,
                        'total_stops': 0,
                        'avg_duration': 0,
                        'durations': []
                    }

                analytics_data['driver_stats'][driver_key]['total_stops'] += 1
                if duration_seconds:
                    analytics_data['driver_stats'][driver_key]['durations'].append(duration_seconds)

            # Calculate averages
            for team_stats in analytics_data['team_stats'].values():
                if team_stats['durations']:
                    team_stats['avg_duration'] = sum(team_stats['durations']) / len(team_stats['durations'])
                    team_stats['min_duration'] = min(team_stats['durations'])
                    team_stats['max_duration'] = max(team_stats['durations'])
                del team_stats['durations']  # Remove raw data

            for driver_stats in analytics_data['driver_stats'].values():
                if driver_stats['durations']:
                    driver_stats['avg_duration'] = sum(driver_stats['durations']) / len(driver_stats['durations'])
                    driver_stats['min_duration'] = min(driver_stats['durations'])
                    driver_stats['max_duration'] = max(driver_stats['durations'])
                del driver_stats['durations']  # Remove raw data

            # Calculate tyre usage averages
            for tyre_stats in analytics_data['tyre_usage'].values():
                if tyre_stats['count'] > 0 and tyre_stats['total_duration'] > 0:
                    tyre_stats['avg_duration'] = tyre_stats['total_duration'] / tyre_stats['count']
                del tyre_stats['total_duration']  # Remove raw total

            analytics_data['sessions'] = list(sessions_data.values())
            analytics_data['team_stats'] = list(analytics_data['team_stats'].values())
            analytics_data['driver_stats'] = list(analytics_data['driver_stats'].values())
            analytics_data['tyre_usage'] = list(analytics_data['tyre_usage'].values())

            return Response({
                'status': 'success',
                'year': season_year,
                'data': analytics_data
            })

        except Season.DoesNotExist:
            return Response({'error': 'Season not found'}, status=status.HTTP_404_NOT_FOUND)


class WeatherDataViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for weather data.

    list: Get all weather data with optional filters
    retrieve: Get specific weather data by ID
    latest: Get weather data for latest race
    """
    queryset = WeatherData.objects.select_related('session').all()
    serializer_class = WeatherDataSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['session', 'rainfall']
    ordering_fields = ['timestamp']
    ordering = ['session', 'timestamp']

    @action(detail=False, methods=['get'])
    @method_decorator(cache_page(60 * 5))  # Cache for 5 minutes
    def latest(self, request):
        """Get weather data for latest race."""
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

            # Get weather data for this session
            weather_data = WeatherData.objects.filter(
                session=latest_session
            ).order_by('timestamp')

            serializer = self.get_serializer(weather_data, many=True)
            return Response({
                'status': 'success',
                'raceInfo': {
                    'eventName': latest_session.event.event_name,
                    'location': latest_session.event.circuit.location,
                    'date': latest_session.session_date.strftime('%Y-%m-%d'),
                    'round': latest_session.event.round_number
                },
                'weatherData': serializer.data
            })

        except Season.DoesNotExist:
            return Response({'error': 'Season not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'])
    @method_decorator(cache_page(60 * 10))  # Cache for 10 minutes
    def analytics(self, request):
        """
        Get weather analytics for a specific session.

        Query params:
        - year: Season year (required)
        - round: Round number (required)
        - session_type: Session type (optional, default 'R' for race)
        """
        season_year = request.query_params.get('year')
        round_number = request.query_params.get('round')
        session_type = request.query_params.get('session_type', 'R')

        if not season_year or not round_number:
            return Response(
                {'error': 'Year and round parameters are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            season = Season.objects.filter(year=season_year).first()

            if not season:
                return Response({
                    'status': 'success',
                    'message': 'No data available for this season',
                    'sessionInfo': None,
                    'data': [],
                    'stats': {
                        'airTemp': {'avg': 0, 'min': 0, 'max': 0},
                        'trackTemp': {'avg': 0, 'min': 0, 'max': 0},
                        'humidity': {'avg': 0, 'min': 0, 'max': 0},
                        'rainfall': False
                    }
                })

            # Get the specific session
            session = Session.objects.filter(
                event__season=season,
                event__round_number=round_number,
                session_type=session_type,
                is_complete=True
            ).select_related('event', 'event__circuit').first()

            if not session:
                return Response({
                    'status': 'success',
                    'message': f'Session not found for round {round_number}, session type {session_type}',
                    'sessionInfo': None,
                    'data': [],
                    'stats': {
                        'airTemp': {'avg': 0, 'min': 0, 'max': 0},
                        'trackTemp': {'avg': 0, 'min': 0, 'max': 0},
                        'humidity': {'avg': 0, 'min': 0, 'max': 0},
                        'rainfall': False
                    }
                })

            # Get weather data for this session
            weather_data = WeatherData.objects.filter(
                session=session
            ).order_by('timestamp')

            # Transform data for charts
            chart_data = []
            for idx, data_point in enumerate(weather_data):
                chart_data.append({
                    'index': idx,
                    'timestamp': data_point.timestamp.isoformat() if data_point.timestamp else None,
                    'airTemp': data_point.air_temp,
                    'trackTemp': data_point.track_temp,
                    'humidity': data_point.humidity,
                    'pressure': data_point.pressure,
                    'windSpeed': data_point.wind_speed,
                    'windDirection': data_point.wind_direction,
                    'rainfall': data_point.rainfall
                })

            # Calculate statistics
            temps_air = [d['airTemp'] for d in chart_data if d['airTemp'] is not None]
            temps_track = [d['trackTemp'] for d in chart_data if d['trackTemp'] is not None]
            humidities = [d['humidity'] for d in chart_data if d['humidity'] is not None]

            stats = {
                'airTemp': {
                    'avg': sum(temps_air) / len(temps_air) if temps_air else 0,
                    'min': min(temps_air) if temps_air else 0,
                    'max': max(temps_air) if temps_air else 0
                },
                'trackTemp': {
                    'avg': sum(temps_track) / len(temps_track) if temps_track else 0,
                    'min': min(temps_track) if temps_track else 0,
                    'max': max(temps_track) if temps_track else 0
                },
                'humidity': {
                    'avg': sum(humidities) / len(humidities) if humidities else 0,
                    'min': min(humidities) if humidities else 0,
                    'max': max(humidities) if humidities else 0
                },
                'rainfall': any(d['rainfall'] for d in chart_data)
            }

            return Response({
                'status': 'success',
                'sessionInfo': {
                    'eventName': session.event.event_name,
                    'circuit': session.event.circuit.name,
                    'round': session.event.round_number,
                    'sessionType': session.session_type,
                    'date': session.session_date.strftime('%Y-%m-%d')
                },
                'data': chart_data,
                'stats': stats
            })

        except Season.DoesNotExist:
            return Response({'error': 'Season not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@cache_page(60 * 15)  # Cache for 15 minutes
def driver_prediction(request):
    """
    Predict driver performance at a specific circuit using ML models and historical data.

    Query params:
    - driver: Driver code (required)
    - circuit: Circuit name (required)
    - year: Year to predict for (optional, defaults to current year)
    - params: JSON string with selected parameters (optional)
      {positions, points, wins, podiums, fastestLaps, pitStops, weather}
    - use_ml: Use ML model if available (optional, default: True)
    """
    driver_code = request.GET.get('driver')
    circuit_name = request.GET.get('circuit')
    year = request.GET.get('year', str(datetime.now().year))
    use_ml = request.GET.get('use_ml', 'true').lower() == 'true'

    # Parse selected parameters (default: all enabled)
    import json
    params_str = request.GET.get('params', '{}')
    try:
        selected_params = json.loads(params_str) if params_str else {}
    except json.JSONDecodeError:
        selected_params = {}

    # Default params if not provided
    params = {
        'positions': selected_params.get('positions', True),
        'points': selected_params.get('points', True),
        'wins': selected_params.get('wins', True),
        'podiums': selected_params.get('podiums', True),
        'fastestLaps': selected_params.get('fastestLaps', True),
        'pitStops': selected_params.get('pitStops', False),
        'weather': selected_params.get('weather', False),
    }

    if not driver_code or not circuit_name:
        return Response(
            {'error': 'Driver and circuit parameters are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # Get driver
        driver = Driver.objects.filter(code__iexact=driver_code).first()
        if not driver:
            return Response({'error': 'Driver not found'}, status=status.HTTP_404_NOT_FOUND)

        # Get circuit
        circuit = Circuit.objects.filter(name__icontains=circuit_name).first()
        if not circuit:
            return Response({'error': 'Circuit not found'}, status=status.HTTP_404_NOT_FOUND)

        # TRY ML PREDICTION FIRST
        ml_prediction = None
        ml_metadata = None

        if use_ml and ML_AVAILABLE:
            try:
                predictor = get_predictor()
                if predictor.is_ready():
                    # Get weather data (use latest or defaults)
                    latest_weather = WeatherData.objects.filter(
                        session__event__circuit=circuit
                    ).order_by('-timestamp').first()

                    weather_params = {}
                    if latest_weather:
                        weather_params = {
                            'air_temp': latest_weather.air_temp,
                            'track_temp': latest_weather.track_temp,
                            'humidity': latest_weather.humidity,
                            'rainfall': latest_weather.rainfall
                        }

                    # Get ML prediction
                    ml_result = predictor.predict_driver_performance(
                        driver=driver,
                        circuit=circuit,
                        year=int(year),
                        **weather_params
                    )

                    if ml_result and ml_result['predictions']['predicted_position']:
                        ml_prediction = ml_result['predictions']
                        ml_metadata = ml_result.get('model_info', {})

                        import logging
                        logger = logging.getLogger('api')
                        logger.info(f"ML prediction for {driver.code} at {circuit.name}: {ml_prediction}")
            except Exception as e:
                import logging
                logger = logging.getLogger('api')
                logger.warning(f"ML prediction failed for {driver.code} at {circuit.name}: {e}")

        # Get historical race results for this driver at this circuit
        historical_results = RaceResult.objects.filter(
            driver=driver,
            session__event__circuit=circuit,
            session__session_type='R'
        ).select_related('session', 'session__event', 'team').order_by('-session__event__season__year')

        if not historical_results.exists():
            return Response({
                'status': 'success',
                'driver': {'code': driver.code, 'fullName': driver.full_name},
                'circuit': {'name': circuit.name, 'location': circuit.location},
                'message': 'No historical data available for this driver at this circuit',
                'prediction': None
            })

        # Calculate statistics
        positions = [r.position for r in historical_results if r.position]
        points_list = [r.points for r in historical_results if r.points is not None]

        total_races = len(historical_results)
        avg_position = sum(positions) / len(positions) if positions else None
        avg_points = sum(points_list) / len(points_list) if points_list else 0

        wins = sum(1 for r in historical_results if r.position == 1)
        podiums = sum(1 for r in historical_results if r.position in [1, 2, 3])
        points_finishes = sum(1 for r in historical_results if r.points and r.points > 0)

        # Build historical data
        history = []
        for result in historical_results[:10]:  # Last 10 races at this circuit
            history.append({
                'year': result.session.event.season.year,
                'position': result.position,
                'points': result.points,
                'team': result.team.name if result.team else 'Unknown'
            })

        # IMPROVED ALGORITHM: Calculate weighted probabilities with recency bias
        # More recent races get higher weights (exponential decay)
        weighted_positions = []
        weighted_points = []
        for i, result in enumerate(historical_results):
            # Weight decreases exponentially: most recent = 1.0, oldest ≈ 0.1
            weight = pow(0.7, i)  # Each older race is worth 70% of the previous
            if result.position:
                weighted_positions.append((result.position, weight))
            if result.points is not None:
                weighted_points.append((result.points, weight))

        # Calculate weighted averages
        if weighted_positions:
            weighted_avg_pos = sum(pos * w for pos, w in weighted_positions) / sum(w for _, w in weighted_positions)
        else:
            weighted_avg_pos = avg_position

        # Calculate standard deviation for position range
        if positions and len(positions) > 1:
            import math
            mean = avg_position
            variance = sum((x - mean) ** 2 for x in positions) / len(positions)
            std_dev = math.sqrt(variance)
        else:
            std_dev = 2  # Default uncertainty

        # Adjust probabilities with form consideration (boost for consistency)
        consistency_factor = 1.0
        if len(positions) >= 3:
            recent_positions = positions[:3]  # Last 3 races
            # If consistently good (all in top 10), boost probabilities
            if all(p <= 10 for p in recent_positions):
                consistency_factor = 1.2
            # If consistently podium, boost even more
            if all(p <= 3 for p in recent_positions):
                consistency_factor = 1.5

        # Calculate base probabilities
        win_probability = (wins / total_races * 100 * consistency_factor) if total_races > 0 else 0
        podium_probability = (podiums / total_races * 100 * consistency_factor) if total_races > 0 else 0
        points_probability = (points_finishes / total_races * 100 * consistency_factor) if total_races > 0 else 0

        # APPLY PARAMETER WEIGHTS: Adjust probabilities based on selected params
        param_multiplier = 1.0
        active_params_count = sum([
            params['positions'],
            params['points'],
            params['wins'],
            params['podiums']
        ])

        # If fewer params selected, boost the confidence in those params
        if active_params_count > 0:
            param_multiplier = 4.0 / active_params_count  # Base: 4 params, scales inversely

        # Adjust individual probabilities based on what's selected
        if not params['wins']:
            win_probability *= 0.5  # Reduce confidence if wins not considered
        else:
            win_probability *= param_multiplier

        if not params['podiums']:
            podium_probability *= 0.5
        else:
            podium_probability *= param_multiplier

        if not params['points']:
            points_probability *= 0.5
        else:
            points_probability *= param_multiplier

        # Boost based on fastest laps if selected
        if params['fastestLaps']:
            # Check if driver had fastest lap in race (fastest_lap_time exists and is not null)
            fastest_laps_count = sum(1 for r in historical_results if r.fastest_lap_time is not None)
            if fastest_laps_count > 0:
                fl_boost = (fastest_laps_count / total_races) * 15  # Up to 15% boost
                win_probability += fl_boost
                podium_probability += fl_boost * 0.7

        # Boost based on pit stop performance if selected
        if params['pitStops']:
            # Get pit stop data for this driver at this circuit
            pit_stops = PitStop.objects.filter(
                driver=driver,
                session__event__circuit=circuit,
                duration__isnull=False
            )
            if pit_stops.exists():
                avg_duration = pit_stops.aggregate(Avg('duration'))['duration__avg']
                if avg_duration:
                    # Faster pit stops = better, typical range 20-30s
                    # If avg < 24s, boost; if > 26s, reduce
                    if avg_duration.total_seconds() < 24:
                        pitstop_boost = 5  # 5% boost for fast stops
                    elif avg_duration.total_seconds() < 25:
                        pitstop_boost = 2
                    elif avg_duration.total_seconds() > 26:
                        pitstop_boost = -3  # Penalty for slow stops
                    else:
                        pitstop_boost = 0

                    win_probability += pitstop_boost
                    podium_probability += pitstop_boost * 0.8

        # Weather consideration if selected
        if params['weather']:
            # Get weather data for historical races at this circuit
            weather_sessions = WeatherData.objects.filter(
                session__event__circuit=circuit,
                session__session_type='R'
            ).values('session_id').distinct()

            if weather_sessions.exists():
                # Check if driver performed well in varied conditions
                varied_condition_races = 0
                for ws in weather_sessions[:5]:  # Last 5 races with weather data
                    session_weather = WeatherData.objects.filter(session_id=ws['session_id'])
                    if session_weather.exists():
                        # Check for rainfall or temp variations
                        has_rain = session_weather.filter(rainfall=True).exists()
                        temp_range = session_weather.aggregate(
                            min_temp=Min('air_temp'),
                            max_temp=Max('air_temp')
                        )
                        varied_conditions = has_rain or (
                            temp_range['max_temp'] and temp_range['min_temp'] and
                            (temp_range['max_temp'] - temp_range['min_temp']) > 5
                        )
                        if varied_conditions:
                            varied_condition_races += 1

                # If driver raced in varied conditions here, slight boost
                if varied_condition_races > 0:
                    weather_boost = min(varied_condition_races * 2, 8)  # Max 8% boost
                    win_probability += weather_boost * 0.5
                    podium_probability += weather_boost * 0.7

        # Cap probabilities at 100%
        win_probability = min(100, win_probability)
        podium_probability = min(100, podium_probability)
        points_probability = min(100, points_probability)

        # Determine predicted position range using weighted average and std deviation
        if weighted_avg_pos:
            predicted_position_min = max(1, int(weighted_avg_pos - std_dev))
            predicted_position_max = min(20, int(weighted_avg_pos + std_dev))
        else:
            predicted_position_min = None
            predicted_position_max = None

        # Build response
        response_data = {
            'status': 'success',
            'driver': {
                'code': driver.code,
                'fullName': driver.full_name,
                'number': driver.number
            },
            'circuit': {
                'name': circuit.name,
                'location': circuit.location,
                'country': circuit.country
            },
            'prediction': {
                'averagePosition': weighted_avg_pos if weighted_avg_pos else avg_position,
                'averagePoints': avg_points,
                'predictedPositionRange': {
                    'min': predicted_position_min,
                    'max': predicted_position_max
                },
                'probabilities': {
                    'win': round(win_probability, 1),
                    'podium': round(podium_probability, 1),
                    'points': round(points_probability, 1)
                }
            },
            'statistics': {
                'totalRaces': total_races,
                'wins': wins,
                'podiums': podiums,
                'pointsFinishes': points_finishes
            },
            'history': history
        }

        # Add ML prediction if available
        if ml_prediction:
            response_data['mlPrediction'] = {
                'predictedPosition': ml_prediction.get('predicted_position'),
                'positionRange': ml_prediction.get('position_range'),
                'raceLapTime': ml_prediction.get('race_lap_time'),
                'qualifyingLapTime': ml_prediction.get('qualifying_lap_time'),
                'modelInfo': ml_metadata
            }
            # Blend ML with statistical prediction for more robust result
            if ml_prediction.get('predicted_position') and weighted_avg_pos:
                # Use weighted average: 60% ML, 40% statistical
                blended_position = (0.6 * ml_prediction['predicted_position']) + (0.4 * weighted_avg_pos)
                response_data['prediction']['blendedPosition'] = round(blended_position, 1)

        return Response(response_data)

    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@cache_page(60 * 15)  # Cache for 15 minutes
def constructor_prediction(request):
    """
    Predict constructor performance at a specific circuit using ML models and historical data.

    Query params:
    - team: Team name (required)
    - circuit: Circuit name (required)
    - year: Year to predict for (optional, defaults to current year)
    - params: JSON string with selected parameters (optional)
      {positions, points, wins, podiums, fastestLaps, pitStops, weather}
    - use_ml: Use ML model if available (optional, default: True)
    """
    team_name = request.GET.get('team')
    circuit_name = request.GET.get('circuit')
    year = request.GET.get('year', str(datetime.now().year))
    use_ml = request.GET.get('use_ml', 'true').lower() == 'true'

    # Parse selected parameters (default: all enabled)
    import json
    params_str = request.GET.get('params', '{}')
    try:
        selected_params = json.loads(params_str) if params_str else {}
    except json.JSONDecodeError:
        selected_params = {}

    # Default params if not provided
    params = {
        'positions': selected_params.get('positions', True),
        'points': selected_params.get('points', True),
        'wins': selected_params.get('wins', True),
        'podiums': selected_params.get('podiums', True),
        'fastestLaps': selected_params.get('fastestLaps', True),
        'pitStops': selected_params.get('pitStops', False),
        'weather': selected_params.get('weather', False),
    }

    if not team_name or not circuit_name:
        return Response(
            {'error': 'Team and circuit parameters are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # Get team
        team = Team.objects.filter(name__icontains=team_name).first()
        if not team:
            return Response({'error': 'Team not found'}, status=status.HTTP_404_NOT_FOUND)

        # Get circuit
        circuit = Circuit.objects.filter(name__icontains=circuit_name).first()
        if not circuit:
            return Response({'error': 'Circuit not found'}, status=status.HTTP_404_NOT_FOUND)

        # TRY ML PREDICTION FIRST
        ml_prediction = None
        ml_metadata = None

        if use_ml and ML_AVAILABLE:
            try:
                predictor = get_predictor()
                if predictor.is_ready():
                    # Get weather data (use latest or defaults)
                    latest_weather = WeatherData.objects.filter(
                        session__event__circuit=circuit
                    ).order_by('-timestamp').first()

                    weather_params = {}
                    if latest_weather:
                        weather_params = {
                            'air_temp': latest_weather.air_temp,
                            'track_temp': latest_weather.track_temp,
                            'humidity': latest_weather.humidity,
                            'rainfall': latest_weather.rainfall
                        }

                    # Get ML prediction
                    ml_result = predictor.predict_constructor_performance(
                        team=team,
                        circuit=circuit,
                        year=int(year),
                        **weather_params
                    )

                    if ml_result and ml_result['predictions']['average_position']:
                        ml_prediction = ml_result['predictions']
                        ml_metadata = ml_result.get('model_info', {})

                        import logging
                        logger = logging.getLogger('api')
                        logger.info(f"ML prediction for {team.name} at {circuit.name}: {ml_prediction}")
            except Exception as e:
                import logging
                logger = logging.getLogger('api')
                logger.warning(f"ML prediction failed for {team.name} at {circuit.name}: {e}")

        # Get historical race results for this team at this circuit
        historical_results = RaceResult.objects.filter(
            team=team,
            session__event__circuit=circuit,
            session__session_type='R'
        ).select_related('session', 'session__event', 'driver').order_by('-session__event__season__year')

        if not historical_results.exists():
            return Response({
                'status': 'success',
                'team': {'name': team.name, 'color': team.color},
                'circuit': {'name': circuit.name, 'location': circuit.location},
                'message': 'No historical data available for this team at this circuit',
                'prediction': None
            })

        # Calculate statistics
        positions = [r.position for r in historical_results if r.position]
        points_list = [r.points for r in historical_results if r.points is not None]

        total_races = len(set(r.session.id for r in historical_results))  # Count unique races
        avg_position = sum(positions) / len(positions) if positions else None
        total_points = sum(points_list)
        avg_points_per_race = total_points / total_races if total_races > 0 else 0

        wins = sum(1 for r in historical_results if r.position == 1)
        podiums = sum(1 for r in historical_results if r.position in [1, 2, 3])

        # Build historical data (group by year)
        history_by_year = {}
        for result in historical_results:
            year_key = result.session.event.season.year
            if year_key not in history_by_year:
                history_by_year[year_key] = {
                    'year': year_key,
                    'results': [],
                    'totalPoints': 0
                }
            history_by_year[year_key]['results'].append({
                'driver': result.driver.code,
                'position': result.position,
                'points': result.points
            })
            if result.points:
                history_by_year[year_key]['totalPoints'] += result.points

        history = sorted(history_by_year.values(), key=lambda x: x['year'], reverse=True)[:10]

        # IMPROVED ALGORITHM: Calculate weighted probabilities for constructors
        weighted_positions = []
        for i, result in enumerate(historical_results):
            weight = pow(0.7, i // 2)  # Slower decay for teams (group by race)
            if result.position:
                weighted_positions.append((result.position, weight))

        # Calculate weighted average position
        if weighted_positions:
            weighted_avg_pos = sum(pos * w for pos, w in weighted_positions) / sum(w for _, w in weighted_positions)
        else:
            weighted_avg_pos = avg_position

        # Calculate standard deviation
        if positions and len(positions) > 2:
            import math
            mean = avg_position
            variance = sum((x - mean) ** 2 for x in positions) / len(positions)
            std_dev = math.sqrt(variance)
        else:
            std_dev = 3  # Default higher uncertainty for teams

        # Team consistency factor (based on both drivers performing well)
        consistency_factor = 1.0
        if len(positions) >= 6:  # At least 3 races with both drivers
            recent_positions = positions[:6]
            top_10_rate = sum(1 for p in recent_positions if p <= 10) / len(recent_positions)
            if top_10_rate >= 0.7:  # 70% of recent results in top 10
                consistency_factor = 1.3
            if top_10_rate >= 0.9:  # 90% in top 10
                consistency_factor = 1.5

        # Calculate base probabilities
        win_probability = (wins / total_races * 100 * consistency_factor) if total_races > 0 else 0
        podium_probability = (podiums / len(positions) * 100 * consistency_factor) if positions else 0

        # APPLY PARAMETER WEIGHTS: Adjust probabilities based on selected params
        param_multiplier = 1.0
        active_params_count = sum([
            params['positions'],
            params['points'],
            params['wins'],
            params['podiums']
        ])

        # If fewer params selected, boost the confidence in those params
        if active_params_count > 0:
            param_multiplier = 4.0 / active_params_count

        # Adjust individual probabilities based on what's selected
        if not params['wins']:
            win_probability *= 0.5
        else:
            win_probability *= param_multiplier

        if not params['podiums']:
            podium_probability *= 0.5
        else:
            podium_probability *= param_multiplier

        # Boost based on fastest laps if selected
        if params['fastestLaps']:
            # Check if team had fastest lap in race (fastest_lap_time exists and is not null)
            fastest_laps_count = sum(1 for r in historical_results if r.fastest_lap_time is not None)
            if fastest_laps_count > 0:
                fl_boost = (fastest_laps_count / len(historical_results)) * 12
                win_probability += fl_boost
                podium_probability += fl_boost * 0.7

        # Boost based on pit stop performance if selected
        if params['pitStops']:
            # Get pit stop data for this team at this circuit
            pit_stops = PitStop.objects.filter(
                team=team,
                session__event__circuit=circuit,
                duration__isnull=False
            )
            if pit_stops.exists():
                avg_duration = pit_stops.aggregate(Avg('duration'))['duration__avg']
                if avg_duration:
                    # Team average pit stops
                    if avg_duration.total_seconds() < 24:
                        pitstop_boost = 6  # 6% boost for fast stops
                    elif avg_duration.total_seconds() < 25:
                        pitstop_boost = 3
                    elif avg_duration.total_seconds() > 26:
                        pitstop_boost = -4
                    else:
                        pitstop_boost = 0

                    win_probability += pitstop_boost
                    podium_probability += pitstop_boost * 0.8

        # Weather consideration if selected
        if params['weather']:
            weather_sessions = WeatherData.objects.filter(
                session__event__circuit=circuit,
                session__session_type='R'
            ).values('session_id').distinct()

            if weather_sessions.exists():
                varied_condition_races = 0
                for ws in weather_sessions[:5]:
                    session_weather = WeatherData.objects.filter(session_id=ws['session_id'])
                    if session_weather.exists():
                        has_rain = session_weather.filter(rainfall=True).exists()
                        temp_range = session_weather.aggregate(
                            min_temp=Min('air_temp'),
                            max_temp=Max('air_temp')
                        )
                        varied_conditions = has_rain or (
                            temp_range['max_temp'] and temp_range['min_temp'] and
                            (temp_range['max_temp'] - temp_range['min_temp']) > 5
                        )
                        if varied_conditions:
                            varied_condition_races += 1

                if varied_condition_races > 0:
                    weather_boost = min(varied_condition_races * 2, 10)
                    win_probability += weather_boost * 0.6
                    podium_probability += weather_boost * 0.8

        # Cap probabilities at 100%
        win_probability = min(100, win_probability)
        podium_probability = min(100, podium_probability)

        # Determine predicted position range using weighted average and std deviation
        if weighted_avg_pos:
            predicted_position_min = max(1, int(weighted_avg_pos - std_dev))
            predicted_position_max = min(20, int(weighted_avg_pos + std_dev))
        else:
            predicted_position_min = None
            predicted_position_max = None

        # Build response
        response_data = {
            'status': 'success',
            'team': {
                'name': team.name,
                'color': team.color
            },
            'circuit': {
                'name': circuit.name,
                'location': circuit.location,
                'country': circuit.country
            },
            'prediction': {
                'averagePosition': weighted_avg_pos if weighted_avg_pos else avg_position,
                'averagePointsPerRace': avg_points_per_race,
                'predictedPositionRange': {
                    'min': predicted_position_min,
                    'max': predicted_position_max
                },
                'probabilities': {
                    'win': round(win_probability, 1),
                    'podium': round(podium_probability, 1)
                }
            },
            'statistics': {
                'totalRaces': total_races,
                'wins': wins,
                'podiums': podiums,
                'totalPoints': total_points
            },
            'history': history
        }

        # Add ML prediction if available
        if ml_prediction:
            response_data['mlPrediction'] = {
                'averagePosition': ml_prediction.get('average_position'),
                'drivers': ml_prediction.get('drivers'),
                'modelInfo': ml_metadata
            }
            # Blend ML with statistical prediction for more robust result
            if ml_prediction.get('average_position') and weighted_avg_pos:
                # Use weighted average: 60% ML, 40% statistical
                blended_position = (0.6 * ml_prediction['average_position']) + (0.4 * weighted_avg_pos)
                response_data['prediction']['blendedPosition'] = round(blended_position, 1)

        return Response(response_data)

    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@cache_page(60 * 5)  # Cache for 5 minutes
def available_drivers(request):
    """
    Get list of available drivers for dropdowns.
    Returns only drivers active in the current season (2025).
    """
    from django.db.models import Max, Q

    # Get current year - fixo em 2025 para o contexto da aplicação
    current_year = 2025

    # Buscar pilotos que têm resultados em 2025 (Race, Qualifying ou Sprint)
    # Usamos Q objects para combinar queries de diferentes modelos
    active_driver_ids = set()

    # Pilotos em corridas de 2025
    race_drivers = RaceResult.objects.filter(
        session__event__season__year=current_year
    ).values_list('driver_id', flat=True).distinct()
    active_driver_ids.update(race_drivers)

    # Pilotos em qualifyings de 2025
    quali_drivers = QualifyingResult.objects.filter(
        session__event__season__year=current_year
    ).values_list('driver_id', flat=True).distinct()
    active_driver_ids.update(quali_drivers)

    # Pilotos em sprints de 2025
    sprint_drivers = SprintResult.objects.filter(
        session__event__season__year=current_year
    ).values_list('driver_id', flat=True).distinct()
    active_driver_ids.update(sprint_drivers)

    # Buscar dados dos pilotos ativos
    drivers = Driver.objects.filter(id__in=active_driver_ids).order_by('code')

    # Build response with full_name property
    drivers_data = [
        {
            'code': driver.code,
            'full_name': driver.full_name,
            'number': driver.number
        }
        for driver in drivers
    ]

    return Response({
        'status': 'success',
        'drivers': drivers_data
    })


@api_view(['GET'])
@cache_page(60 * 5)  # Cache for 5 minutes
def available_teams(request):
    """
    Get list of available teams for dropdowns (consolidated).
    Returns only teams active in the current season (2025).
    """
    # Get current year - fixo em 2025 para o contexto da aplicação
    current_year = 2025

    # Buscar equipes que têm resultados em 2025 (Race, Qualifying ou Sprint)
    active_team_ids = set()

    # Equipes em corridas de 2025
    race_teams = RaceResult.objects.filter(
        session__event__season__year=current_year
    ).values_list('team_id', flat=True).distinct()
    active_team_ids.update(race_teams)

    # Equipes em qualifyings de 2025
    quali_teams = QualifyingResult.objects.filter(
        session__event__season__year=current_year
    ).values_list('team_id', flat=True).distinct()
    active_team_ids.update(quali_teams)

    # Equipes em sprints de 2025
    sprint_teams = SprintResult.objects.filter(
        session__event__season__year=current_year
    ).values_list('team_id', flat=True).distinct()
    active_team_ids.update(sprint_teams)

    # Buscar dados das equipes ativas
    teams = Team.objects.filter(id__in=active_team_ids)

    # Consolidar equipes por nome canônico
    teams_dict = {}
    for team in teams:
        canonical_name = team.get_consolidated_name()
        if canonical_name not in teams_dict:
            teams_dict[canonical_name] = {
                'name': canonical_name,
                'color': team.color,
            }

    teams_list = list(teams_dict.values())
    # Ordenar por nome canônico
    teams_list.sort(key=lambda x: x['name'])

    return Response({
        'status': 'success',
        'teams': teams_list
    })


@api_view(['GET'])
@cache_page(60 * 5)  # Cache for 5 minutes
def available_circuits(request):
    """
    Get list of available circuits for dropdowns.
    Returns only circuits in the current season calendar (2025).
    """
    from django.db.models import Max

    # Get current year - fixo em 2025 para o contexto da aplicação
    current_year = 2025

    # Buscar circuitos com eventos em 2025
    circuit_ids_2025 = Event.objects.filter(
        season__year=current_year
    ).values_list('circuit_id', flat=True).distinct()

    # Para cada circuito, pegar a entrada mais recente
    circuit_ids = Circuit.objects.filter(
        id__in=circuit_ids_2025
    ).values('name').annotate(
        max_id=Max('id')
    ).values_list('max_id', flat=True)

    circuits = Circuit.objects.filter(id__in=circuit_ids).order_by('name').values('name', 'location', 'country')

    return Response({
        'status': 'success',
        'circuits': list(circuits)
    })


@api_view(['GET'])
@cache_page(60 * 5)  # Cache for 5 minutes
def available_years(request):
    """
    Get list of available years for dropdowns.
    Returns all years that have data in the database.
    """
    years = Season.objects.all().order_by('-year').values_list('year', flat=True)

    return Response({
        'status': 'success',
        'years': list(years)
    })


@api_view(['GET'])
@cache_page(60 * 5)  # Cache for 5 minutes
def circuit_race_status(request):
    """
    Check if a circuit has already had a race in a given year.
    Query params:
    - circuit: Circuit name
    - year: Year to check

    Returns:
    - has_race: True if the circuit had a race session in the year
    - race_date: Date of the race if it happened (None otherwise)
    """
    circuit_name = request.GET.get('circuit')
    year = request.GET.get('year')

    if not circuit_name or not year:
        return Response({
            'error': 'Both circuit and year parameters are required'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        year = int(year)
    except ValueError:
        return Response({
            'error': 'Year must be a valid integer'
        }, status=status.HTTP_400_BAD_REQUEST)

    # Verificar se existe uma sessão de corrida (session_type='R') para este circuito no ano
    race_session = Session.objects.filter(
        event__circuit__name=circuit_name,
        event__season__year=year,
        session_type='R'
    ).select_related('event').first()

    if race_session:
        # Verificar se há resultados de corrida (indica que a corrida já aconteceu)
        has_results = RaceResult.objects.filter(session=race_session).exists()

        return Response({
            'status': 'success',
            'has_race': has_results,
            'race_date': race_session.session_date.date() if has_results else None,
            'circuit': circuit_name,
            'year': year
        })
    else:
        # Não há evento de corrida agendado para este circuito neste ano
        return Response({
            'status': 'success',
            'has_race': False,
            'race_date': None,
            'circuit': circuit_name,
            'year': year
        })


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


# ============================================================================
# FILTER OPTIONS ENDPOINTS
# ============================================================================

@api_view(['GET'])
def get_filter_options(request):
    """
    Get all available filter options for dropdowns (consolidated).
    Returns years, GPs, teams (consolidated), drivers, session types, etc.
    """
    # Get available years
    years = list(Season.objects.values_list('year', flat=True).order_by('-year'))

    # Get all teams - consolidated
    all_teams = Team.objects.all().order_by('name')
    teams_dict = {}
    for team in all_teams:
        canonical_name = team.get_consolidated_name()
        if canonical_name not in teams_dict:
            teams_dict[canonical_name] = {
                'id': team.id,
                'name': canonical_name,
                'color': team.color,
            }

    teams = list(teams_dict.values())
    teams.sort(key=lambda x: x['name'])

    # Session types
    session_types = [
        {'value': 'R', 'label': 'Corrida'},
        {'value': 'Q', 'label': 'Classificação'},
        {'value': 'S', 'label': 'Sprint'},
        {'value': 'FP1', 'label': 'Treino Livre 1'},
        {'value': 'FP2', 'label': 'Treino Livre 2'},
        {'value': 'FP3', 'label': 'Treino Livre 3'},
    ]

    return Response({
        'status': 'success',
        'years': years,
        'teams': teams,
        'sessionTypes': session_types,
    })


@api_view(['GET'])
def get_grands_prix(request):
    """
    Get all Grands Prix for a specific year.
    Maps round numbers to GP names.

    Query params:
    - year: Season year (required)
    """
    year = request.query_params.get('year')

    if not year:
        return Response(
            {'error': 'Year parameter is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        season = Season.objects.filter(year=year).first()

        if not season:
            return Response({
                'status': 'success',
                'grandsPrix': []
            })

        # Get all events for this season
        events = Event.objects.filter(season=season).select_related('circuit').order_by('round_number')

        grands_prix = [
            {
                'round': event.round_number,
                'name': event.event_name,
                'location': event.circuit.location if event.circuit else 'Unknown',
                'country': event.circuit.country if event.circuit else 'Unknown',
                'date': event.event_date.strftime('%d/%m/%Y') if event.event_date else None,
            }
            for event in events
        ]

        return Response({
            'status': 'success',
            'grandsPrix': grands_prix
        })

    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def get_drivers_by_year(request):
    """
    Get all drivers that participated in a specific year.

    Query params:
    - year: Season year (required)
    """
    year = request.query_params.get('year')

    if not year:
        return Response(
            {'error': 'Year parameter is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        season = Season.objects.filter(year=year).first()

        if not season:
            return Response({
                'status': 'success',
                'drivers': []
            })

        # Get unique drivers from race results for this season
        driver_ids = RaceResult.objects.filter(
            session__event__season=season
        ).values_list('driver', flat=True).distinct()

        drivers = Driver.objects.filter(id__in=driver_ids).order_by('last_name', 'first_name')

        drivers_list = [
            {
                'id': driver.id,
                'code': driver.code,
                'fullName': driver.full_name,
                'number': driver.number,
            }
            for driver in drivers
        ]

        return Response({
            'status': 'success',
            'drivers': drivers_list
        })

    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def get_teams_by_year(request):
    """
    Get all teams that participated in a specific year (consolidated).

    Query params:
    - year: Season year (required)
    """
    year = request.query_params.get('year')

    if not year:
        return Response(
            {'error': 'Year parameter is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        season = Season.objects.filter(year=year).first()

        if not season:
            return Response({
                'status': 'success',
                'teams': []
            })

        # Get unique teams from race results for this season
        team_ids = RaceResult.objects.filter(
            session__event__season=season
        ).values_list('team', flat=True).distinct()

        teams = Team.objects.filter(id__in=team_ids).order_by('name')

        # Consolidar equipes por nome canônico
        teams_dict = {}
        for team in teams:
            canonical_name = team.get_consolidated_name()
            if canonical_name not in teams_dict:
                teams_dict[canonical_name] = {
                    'id': team.id,
                    'name': canonical_name,
                    'color': team.color,
                }

        teams_list = list(teams_dict.values())
        # Ordenar por nome canônico
        teams_list.sort(key=lambda x: x['name'])

        return Response({
            'status': 'success',
            'teams': teams_list
        })

    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@cache_page(60 * 10)  # Cache for 10 minutes
def team_history(request):
    """
    Get complete historical data for a team (consolidated across name changes).

    Query params:
    - team: Team name (required) - can be current or historical name
    - start_year: Starting year (optional)
    - end_year: Ending year (optional)
    """
    team_name = request.query_params.get('team')
    start_year = request.query_params.get('start_year')
    end_year = request.query_params.get('end_year')

    if not team_name:
        return Response(
            {'error': 'Team parameter is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # Get canonical name for consolidation
        canonical_name = Team.get_canonical_name(team_name)

        # Get all teams that map to this canonical name
        team_names = [canonical_name]
        for canon, aliases in Team.TEAM_CONSOLIDATION_MAP.items():
            if canon == canonical_name:
                team_names.extend(aliases)

        # Get all teams matching these names
        teams = Team.objects.filter(name__in=team_names)

        if not teams.exists():
            return Response(
                {'error': 'Team not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Build query for constructor standings
        standings_query = ConstructorStanding.objects.filter(
            team__in=teams
        ).select_related('season', 'event', 'team')

        # Apply year filters
        if start_year:
            standings_query = standings_query.filter(season__year__gte=start_year)
        if end_year:
            standings_query = standings_query.filter(season__year__lte=end_year)

        # Get standings ordered by season and event
        standings = standings_query.order_by('season__year', 'event__round_number')

        # Organize data by season
        seasons_data = {}
        for standing in standings:
            year = standing.season.year
            if year not in seasons_data:
                seasons_data[year] = {
                    'year': year,
                    'final_position': None,
                    'final_points': 0,
                    'wins': 0,
                    'podiums': 0,
                    'team_name': standing.team.name,  # Nome usado naquele ano
                    'evolution': []
                }

            # Update to latest standing for the season
            seasons_data[year]['final_position'] = standing.position
            seasons_data[year]['final_points'] = standing.points
            seasons_data[year]['wins'] = standing.wins
            seasons_data[year]['podiums'] = standing.podiums

            # Add evolution point
            seasons_data[year]['evolution'].append({
                'round': standing.event.round_number,
                'event_name': standing.event.event_name,
                'position': standing.position,
                'points': standing.points,
                'wins': standing.wins,
                'podiums': standing.podiums
            })

        # Get race results for additional statistics
        race_results = RaceResult.objects.filter(
            team__in=teams,
            session__session_type='R'
        ).select_related('session__event__season', 'driver')

        if start_year:
            race_results = race_results.filter(session__event__season__year__gte=start_year)
        if end_year:
            race_results = race_results.filter(session__event__season__year__lte=end_year)

        # Calculate additional statistics per season
        for result in race_results:
            year = result.session.event.season.year
            if year in seasons_data:
                # We'll track best results, poles, fastest laps, etc.
                if not hasattr(seasons_data[year], 'best_result'):
                    seasons_data[year]['best_result'] = result.position
                else:
                    if result.position < seasons_data[year]['best_result']:
                        seasons_data[year]['best_result'] = result.position

        # Format response
        history = sorted(seasons_data.values(), key=lambda x: x['year'], reverse=True)

        # Get team info (use most recent team object)
        latest_team = teams.order_by('-updated_at').first()

        return Response({
            'status': 'success',
            'team': {
                'canonical_name': canonical_name,
                'current_name': latest_team.name,
                'color': latest_team.color,
                'historical_names': team_names
            },
            'history': history
        })

    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@cache_page(60 * 10)  # Cache for 10 minutes
def driver_career(request):
    """
    Get complete career data for a driver showing trajectory across teams.

    Query params:
    - driver: Driver code (required)
    - start_year: Starting year (optional)
    - end_year: Ending year (optional)
    """
    driver_code = request.query_params.get('driver')
    start_year = request.query_params.get('start_year')
    end_year = request.query_params.get('end_year')

    if not driver_code:
        return Response(
            {'error': 'Driver parameter is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # Get driver
        driver = Driver.objects.filter(code__iexact=driver_code).first()
        if not driver:
            return Response(
                {'error': 'Driver not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get driver standings
        standings_query = DriverStanding.objects.filter(
            driver=driver
        ).select_related('season', 'event', 'team')

        # Apply year filters
        if start_year:
            standings_query = standings_query.filter(season__year__gte=start_year)
        if end_year:
            standings_query = standings_query.filter(season__year__lte=end_year)

        standings = standings_query.order_by('season__year', 'event__round_number')

        # Organize data by season
        seasons_data = {}
        for standing in standings:
            year = standing.season.year
            team_name = standing.team.name if standing.team else 'Unknown'
            canonical_team = Team.get_canonical_name(team_name)

            if year not in seasons_data:
                seasons_data[year] = {
                    'year': year,
                    'team': team_name,
                    'canonical_team': canonical_team,
                    'team_color': standing.team.color if standing.team else '#CCCCCC',
                    'final_position': None,
                    'final_points': 0,
                    'wins': 0,
                    'podiums': 0,
                    'evolution': []
                }

            # Update to latest standing for the season
            seasons_data[year]['final_position'] = standing.position
            seasons_data[year]['final_points'] = standing.points
            seasons_data[year]['wins'] = standing.wins
            seasons_data[year]['podiums'] = standing.podiums

            # Add evolution point
            seasons_data[year]['evolution'].append({
                'round': standing.event.round_number,
                'event_name': standing.event.event_name,
                'position': standing.position,
                'points': standing.points,
                'wins': standing.wins,
                'podiums': standing.podiums
            })

        # Get race results for additional statistics
        race_results = RaceResult.objects.filter(
            driver=driver,
            session__session_type='R'
        ).select_related('session__event__season', 'team')

        if start_year:
            race_results = race_results.filter(session__event__season__year__gte=start_year)
        if end_year:
            race_results = race_results.filter(session__event__season__year__lte=end_year)

        # Calculate additional statistics per season
        race_count_by_year = {}
        dnf_count_by_year = {}
        fastest_laps_by_year = {}

        for result in race_results:
            year = result.session.event.season.year

            # Count races
            race_count_by_year[year] = race_count_by_year.get(year, 0) + 1

            # Count DNFs
            if result.dnf:
                dnf_count_by_year[year] = dnf_count_by_year.get(year, 0) + 1

            # Count fastest laps
            if result.fastest_lap_time and result.fastest_lap_number:
                fastest_laps_by_year[year] = fastest_laps_by_year.get(year, 0) + 1

            # Add stats to seasons_data
            if year in seasons_data:
                seasons_data[year]['races'] = race_count_by_year.get(year, 0)
                seasons_data[year]['dnfs'] = dnf_count_by_year.get(year, 0)
                seasons_data[year]['fastest_laps'] = fastest_laps_by_year.get(year, 0)

        # Group by teams (consolidated)
        teams_history = {}
        for year_data in seasons_data.values():
            canonical_team = year_data['canonical_team']
            if canonical_team not in teams_history:
                teams_history[canonical_team] = {
                    'canonical_team': canonical_team,
                    'team_color': year_data['team_color'],
                    'years': [],
                    'total_races': 0,
                    'total_wins': 0,
                    'total_podiums': 0,
                    'total_points': 0,
                    'best_championship_position': None
                }

            teams_history[canonical_team]['years'].append(year_data['year'])
            teams_history[canonical_team]['total_races'] += year_data.get('races', 0)
            teams_history[canonical_team]['total_wins'] += year_data['wins']
            teams_history[canonical_team]['total_podiums'] += year_data['podiums']
            teams_history[canonical_team]['total_points'] += year_data['final_points']

            # Track best championship position
            if year_data['final_position']:
                if (teams_history[canonical_team]['best_championship_position'] is None or
                    year_data['final_position'] < teams_history[canonical_team]['best_championship_position']):
                    teams_history[canonical_team]['best_championship_position'] = year_data['final_position']

        # Format response
        career_by_season = sorted(seasons_data.values(), key=lambda x: x['year'], reverse=True)
        career_by_team = list(teams_history.values())

        # Calculate career totals
        total_stats = {
            'total_races': sum(race_count_by_year.values()),
            'total_wins': sum(s['wins'] for s in seasons_data.values()),
            'total_podiums': sum(s['podiums'] for s in seasons_data.values()),
            'total_points': sum(s['final_points'] for s in seasons_data.values()),
            'total_dnfs': sum(dnf_count_by_year.values()),
            'total_fastest_laps': sum(fastest_laps_by_year.values()),
            'championships': sum(1 for s in seasons_data.values() if s['final_position'] == 1),
            'best_championship_position': min((s['final_position'] for s in seasons_data.values() if s['final_position']), default=None),
            'seasons': len(seasons_data)
        }

        return Response({
            'status': 'success',
            'driver': {
                'code': driver.code,
                'full_name': driver.full_name,
                'number': driver.number,
                'nationality': driver.nationality,
                'date_of_birth': driver.date_of_birth.strftime('%Y-%m-%d') if driver.date_of_birth else None
            },
            'career_totals': total_stats,
            'career_by_season': career_by_season,
            'career_by_team': career_by_team
        })

    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ============================================================================
# CELERY TASKS MONITORING
# ============================================================================

@api_view(['GET'])
def celery_tasks_status(request):
    """
    Get detailed Celery tasks status for real-time monitoring.
    Returns active, scheduled, reserved tasks, worker info, and queue statistics.
    """
    from celery import current_app
    from datetime import datetime
    from django.utils import timezone

    result = {
        'timestamp': timezone.now().isoformat(),
        'status': 'success',
        'workers': [],
        'tasks': {
            'active': [],
            'scheduled': [],
            'reserved': [],
        },
        'stats': {
            'total_active': 0,
            'total_scheduled': 0,
            'total_reserved': 0,
            'total_workers': 0,
            'workers_online': [],
        }
    }

    try:
        inspector = current_app.control.inspect()

        # Get worker stats
        stats = inspector.stats()
        if stats:
            result['stats']['total_workers'] = len(stats)
            result['stats']['workers_online'] = list(stats.keys())

            for worker_name, worker_stats in stats.items():
                result['workers'].append({
                    'name': worker_name,
                    'status': 'online',
                    'pool': worker_stats.get('pool', {}).get('implementation', 'unknown'),
                    'max_concurrency': worker_stats.get('pool', {}).get('max-concurrency', 0),
                    'total_tasks': worker_stats.get('total', {}),
                })

        # Get active tasks
        active_tasks = inspector.active()
        if active_tasks:
            for worker, tasks in active_tasks.items():
                for task in tasks:
                    result['tasks']['active'].append({
                        'id': task.get('id'),
                        'name': task.get('name'),
                        'args': task.get('args', ''),
                        'kwargs': task.get('kwargs', {}),
                        'worker': worker,
                        'time_start': task.get('time_start'),
                        'acknowledged': task.get('acknowledged', False),
                        'delivery_info': task.get('delivery_info', {}),
                    })
            result['stats']['total_active'] = sum(len(tasks) for tasks in active_tasks.values())

        # Get scheduled tasks
        scheduled_tasks = inspector.scheduled()
        if scheduled_tasks:
            for worker, tasks in scheduled_tasks.items():
                for task in tasks:
                    result['tasks']['scheduled'].append({
                        'id': task.get('request', {}).get('id'),
                        'name': task.get('request', {}).get('name'),
                        'args': task.get('request', {}).get('args', ''),
                        'kwargs': task.get('request', {}).get('kwargs', {}),
                        'worker': worker,
                        'eta': task.get('eta'),
                        'priority': task.get('priority', 0),
                    })
            result['stats']['total_scheduled'] = sum(len(tasks) for tasks in scheduled_tasks.values())

        # Get reserved tasks (in queue)
        reserved_tasks = inspector.reserved()
        if reserved_tasks:
            for worker, tasks in reserved_tasks.items():
                for task in tasks:
                    result['tasks']['reserved'].append({
                        'id': task.get('id'),
                        'name': task.get('name'),
                        'args': task.get('args', ''),
                        'kwargs': task.get('kwargs', {}),
                        'worker': worker,
                        'priority': task.get('priority', 0),
                    })
            result['stats']['total_reserved'] = sum(len(tasks) for tasks in reserved_tasks.values())

        # Get periodic tasks from django-celery-beat
        try:
            from django_celery_beat.models import PeriodicTask
            periodic_tasks = PeriodicTask.objects.filter(enabled=True).values(
                'name', 'task', 'enabled', 'last_run_at', 'total_run_count'
            )
            result['periodic_tasks'] = list(periodic_tasks)
        except Exception as e:
            result['periodic_tasks_error'] = str(e)

    except Exception as e:
        result['status'] = 'error'
        result['error'] = str(e)
        result['message'] = 'Could not connect to Celery workers. Make sure Celery is running.'

    return Response(result)


# ============================================================================
# HISTORICAL DATA ENDPOINTS (PRE-2018)
# ============================================================================

@api_view(['GET'])
@cache_page(60 * 5)  # Cache for 5 minutes
def historical_data_status(request):
    """
    Get status of historical F1 data (pre-2018 ONLY).
    Shows collection progress, statistics, and recent logs.

    IMPORTANT: This endpoint ONLY shows data from years < 2018.
    Data from 2018+ comes from FastF1 and should NOT appear here.
    """
    from core.models import DataCollectionLog
    from datetime import datetime, timedelta
    from django.utils import timezone
    from django.db.models import Count, Q

    try:
        # CRITICAL: Only consider data before 2018
        historical_seasons = Season.objects.filter(year__lt=2018).order_by('year')

        # Build statistics
        stats = {
            'coverage': {
                'first_year': historical_seasons.first().year if historical_seasons.exists() else None,
                'last_year': historical_seasons.last().year if historical_seasons.exists() else None,
                'total_seasons': historical_seasons.count(),
                'seasons_with_data': [],
                'missing_seasons': [],
            },
            'totals': {
                'seasons': 0,
                'events': 0,
                'race_results': 0,
                'qualifying_results': 0,
                'driver_standings': 0,
                'constructor_standings': 0,
                'pit_stops': 0,
            },
            'by_year': [],
            'collection_logs': []
        }

        # Expected years range (1950-2017)
        expected_years = set(range(1950, 2018))
        existing_years = set(historical_seasons.values_list('year', flat=True))
        stats['coverage']['missing_seasons'] = sorted(expected_years - existing_years)

        # Analyze each season
        for season in historical_seasons:
            year = season.year

            # Count data for this season
            events = Event.objects.filter(season=season)
            race_results = RaceResult.objects.filter(
                session__event__season=season,
                session__session_type='R'
            )
            qual_results = QualifyingResult.objects.filter(
                session__event__season=season
            )
            driver_standings = DriverStanding.objects.filter(season=season)
            constructor_standings = ConstructorStanding.objects.filter(season=season)
            pit_stops = PitStop.objects.filter(
                session__event__season=season
            )

            year_data = {
                'year': year,
                'events': events.count(),
                'race_results': race_results.count(),
                'qualifying_results': qual_results.count(),
                'driver_standings': driver_standings.count(),
                'constructor_standings': constructor_standings.count(),
                'pit_stops': pit_stops.count(),
                'is_complete': events.count() > 0 and race_results.count() > 0,
            }

            stats['by_year'].append(year_data)
            stats['coverage']['seasons_with_data'].append(year)

            # Update totals
            stats['totals']['seasons'] += 1
            stats['totals']['events'] += year_data['events']
            stats['totals']['race_results'] += year_data['race_results']
            stats['totals']['qualifying_results'] += year_data['qualifying_results']
            stats['totals']['driver_standings'] += year_data['driver_standings']
            stats['totals']['constructor_standings'] += year_data['constructor_standings']
            stats['totals']['pit_stops'] += year_data['pit_stops']

        # Get recent collection logs (last 24 hours)
        yesterday = timezone.now() - timedelta(hours=24)
        all_recent_logs = DataCollectionLog.objects.filter(
            source='JOLPICA',
            created_at__gte=yesterday
        ).order_by('-created_at')

        # Convert to list before slicing
        recent_logs_list = list(all_recent_logs[:50])

        for log in recent_logs_list:
            stats['collection_logs'].append({
                'timestamp': log.created_at.isoformat(),
                'level': log.level,
                'task_name': log.task_name,
                'message': log.message,
                'year': log.year,
                'round_number': log.round_number,
            })

        # Check if any errors occurred recently
        error_count = DataCollectionLog.objects.filter(
            source='JOLPICA',
            level='ERROR',
            created_at__gte=yesterday
        ).count()

        warning_count = DataCollectionLog.objects.filter(
            source='JOLPICA',
            level='WARNING',
            created_at__gte=yesterday
        ).count()

        # Check if collection is active
        collection_active = any(
            log.task_name in [
                'collect_historical_race',
                'collect_historical_standings',
                'collect_historical_season'
            ]
            for log in recent_logs_list
        )

        return Response({
            'status': 'success',
            'timestamp': timezone.now().isoformat(),
            'stats': stats,
            'health': {
                'recent_errors': error_count,
                'recent_warnings': warning_count,
                'collection_active': collection_active,
            }
        })

    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def trigger_historical_collection(request):
    """
    Manually trigger historical data collection.

    Body params:
    - start_year: Starting year (default: 1950)
    - end_year: Ending year (MUST be < 2018, default: 2017)
    - year: Collect specific year only (optional)

    IMPORTANT: end_year MUST be < 2018. The system will enforce this limit.
    """
    from data_collector.historical_tasks import (
        collect_historical_season,
        collect_all_historical_data,
        collect_historical_metadata
    )

    try:
        # Get parameters
        start_year = request.data.get('start_year', 1950)
        end_year = request.data.get('end_year', 2017)
        specific_year = request.data.get('year')

        # CRITICAL VALIDATION: Enforce year < 2018
        if end_year >= 2018:
            return Response({
                'status': 'error',
                'message': f'end_year ({end_year}) must be < 2018. Data from 2018+ comes from FastF1.',
                'corrected_end_year': 2017
            }, status=status.HTTP_400_BAD_REQUEST)

        if specific_year and specific_year >= 2018:
            return Response({
                'status': 'error',
                'message': f'Year ({specific_year}) must be < 2018. Data from 2018+ comes from FastF1.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Collect specific year
        if specific_year:
            task = collect_historical_season.delay(int(specific_year))
            return Response({
                'status': 'success',
                'message': f'Historical data collection started for {specific_year}',
                'task_id': task.id,
                'year': specific_year
            })

        # Collect range of years
        else:
            # First collect metadata
            metadata_task = collect_historical_metadata.delay()

            # Then collect all historical data (with metadata task ID as prerequisite)
            task = collect_all_historical_data.apply_async(
                kwargs={'start_year': int(start_year), 'end_year': int(end_year)},
                countdown=60  # Wait 1 minute for metadata
            )

            return Response({
                'status': 'success',
                'message': f'Historical data collection started: {start_year}-{end_year}',
                'task_id': task.id,
                'metadata_task_id': metadata_task.id,
                'start_year': start_year,
                'end_year': end_year
            })

    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class DataAuditReportViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint para relatórios de auditoria de dados.

    list: Lista todos os relatórios de auditoria
    retrieve: Obtém um relatório específico com todas as sugestões
    latest: Obtém o relatório mais recente
    run_audit: Executa uma auditoria manual
    """
    queryset = DataAuditReport.objects.all().prefetch_related('suggestions')
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status']
    ordering_fields = ['execution_date', 'total_suggestions_found']
    ordering = ['-execution_date']

    def get_serializer_class(self):
        """Usa serializer simplificado para listagem."""
        if self.action == 'list':
            return DataAuditReportListSerializer
        return DataAuditReportSerializer

    @action(detail=False, methods=['get'])
    def latest(self, request):
        """
        Retorna o relatório de auditoria mais recente.
        GET /api/data-audit-reports/latest/
        """
        try:
            latest_report = DataAuditReport.objects.filter(
                status='completed'
            ).order_by('-execution_date').first()

            if not latest_report:
                return Response(
                    {'message': 'Nenhum relatório de auditoria encontrado'},
                    status=status.HTTP_404_NOT_FOUND
                )

            serializer = DataAuditReportSerializer(latest_report)
            return Response(serializer.data)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def run_audit(self, request):
        """
        Executa uma auditoria manual.
        POST /api/data-audit-reports/run_audit/
        """
        try:
            from data_auditor.tasks import run_manual_audit

            # Executar auditoria em background
            task = run_manual_audit.delay()

            return Response({
                'status': 'started',
                'message': 'Auditoria de dados iniciada. Isso pode levar alguns minutos.',
                'task_id': task.id
            }, status=status.HTTP_202_ACCEPTED)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DataAuditSuggestionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint para sugestões de auditoria de dados.

    list: Lista todas as sugestões
    retrieve: Obtém uma sugestão específica
    pending: Lista sugestões pendentes
    by_table: Lista sugestões agrupadas por tabela
    """
    queryset = DataAuditSuggestion.objects.all().select_related('report')
    serializer_class = DataAuditSuggestionSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['table_name', 'field_name', 'applied', 'rejected', 'source_name']
    ordering_fields = ['created_at', 'confidence_score']
    ordering = ['-created_at']

    @action(detail=False, methods=['get'])
    def pending(self, request):
        """
        Retorna apenas sugestões pendentes (não aplicadas nem rejeitadas).
        GET /api/data-audit-suggestions/pending/
        """
        try:
            pending_suggestions = DataAuditSuggestion.objects.filter(
                applied=False,
                rejected=False
            ).select_related('report').order_by('-confidence_score', '-created_at')

            # Paginar resultados
            page = self.paginate_queryset(pending_suggestions)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(pending_suggestions, many=True)
            return Response(serializer.data)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def by_table(self, request):
        """
        Retorna sugestões agrupadas por tabela.
        GET /api/data-audit-suggestions/by_table/
        """
        try:
            from django.db.models import Count, Q

            suggestions_by_table = DataAuditSuggestion.objects.values(
                'table_name'
            ).annotate(
                total=Count('id'),
                pending=Count('id', filter=Q(applied=False, rejected=False)),
                applied=Count('id', filter=Q(applied=True)),
                rejected=Count('id', filter=Q(rejected=True))
            ).order_by('table_name')

            return Response(list(suggestions_by_table))

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ============================================================================
# DATABASE MAINTENANCE ENDPOINTS
# ============================================================================

@api_view(['POST'])
def clean_database_duplicates(request):
    """
    Trigger database duplicate cleaning task.
    
    Body params:
    - dry_run: Boolean (default: true) - If true, only report duplicates without removing
    
    POST /api/clean-duplicates/
    {
        "dry_run": false  // Set to false to actually remove duplicates
    }
    """
    from data_collector.tasks import clean_database_duplicates as clean_task
    
    try:
        dry_run = request.data.get('dry_run', True)
        
        # Execute cleanup task
        task = clean_task.delay(dry_run=dry_run)
        
        return Response({
            'status': 'started',
            'message': 'Varredura de duplicatas iniciada' if dry_run else 'Limpeza de duplicatas iniciada',
            'task_id': task.id,
            'dry_run': dry_run,
            'note': 'A tarefa está executando em background. Verifique os logs para resultados.'
        }, status=status.HTTP_202_ACCEPTED)
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def database_health(request):
    """
    Get database health information including potential duplicates count.
    
    GET /api/database-health/
    """
    from django.db.models import Count
    
    try:
        health_info = {
            'timestamp': timezone.now().isoformat(),
            'status': 'healthy',
            'tables': {},
            'potential_issues': []
        }
        
        # Check each model for potential duplicates
        models_to_check = [
            ('drivers', Driver, ['driver_id']),
            ('teams', Team, ['team_id']),
            ('circuits', Circuit, ['circuit_id']),
            ('sessions', Session, ['session_id']),
            ('events', Event, ['season', 'round_number']),
        ]
        
        for table_name, model, unique_fields in models_to_check:
            total_count = model.objects.count()
            
            # Check for duplicates
            if len(unique_fields) == 1:
                duplicates = model.objects.values(unique_fields[0]).annotate(
                    count=Count('id')
                ).filter(count__gt=1).count()
            else:
                duplicates = model.objects.values(*unique_fields).annotate(
                    count=Count('id')
                ).filter(count__gt=1).count()
            
            health_info['tables'][table_name] = {
                'total_records': total_count,
                'potential_duplicates': duplicates,
                'status': 'ok' if duplicates == 0 else 'warning'
            }
            
            if duplicates > 0:
                health_info['potential_issues'].append({
                    'table': table_name,
                    'issue': f'{duplicates} grupos de registros duplicados encontrados',
                    'severity': 'medium'
                })
                health_info['status'] = 'warning'
        
        return Response(health_info)
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
