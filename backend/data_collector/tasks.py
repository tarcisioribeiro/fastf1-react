"""
Celery tasks for async F1 data collection.
These tasks run in parallel to collect data from FastF1 API.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, Any
from celery import shared_task, group
from django.utils import timezone
import fastf1
import pandas as pd
import numpy as np
from django.conf import settings

from core.models import (
    Season, Event, Session, Driver, Team, Circuit,
    RaceResult, QualifyingResult, SprintResult,
    DriverStanding, ConstructorStanding,
    LapTime, TyreStrategy, PitStop, WeatherData
)

logger = logging.getLogger('data_collector')


def safe_value(value: Any) -> Any:
    """Convert NaN, NaT and None values to None for MySQL compatibility."""
    if pd.isna(value) or (isinstance(value, float) and np.isnan(value)):
        return None
    return value

# Configure FastF1
fastf1.Cache.enable_cache(str(settings.FASTF1_CACHE_DIR))


def get_or_create_season(year: int) -> Season:
    """Get or create a season."""
    season, created = Season.objects.get_or_create(year=year)
    if created:
        logger.info(f"Created new season: {year}")
    return season


def get_or_create_team(team_name: str, team_color: str = None, **kwargs) -> Team:
    """Get or create a team with color information."""
    team_id = team_name.lower().replace(' ', '_')

    # Default team colors (F1 2024/2025 season)
    default_colors = {
        'red_bull_racing': '#3671C6',
        'ferrari': '#E8002D',
        'mclaren': '#FF8000',
        'mercedes': '#27F4D2',
        'aston_martin': '#229971',
        'alpine': '#FF87BC',
        'williams': '#64C4FF',
        'alphatauri': '#6692FF',
        'rb': '#6692FF',  # RB (formerly AlphaTauri)
        'racing_bulls': '#6692FF',
        'alfa_romeo': '#C92D4B',
        'sauber': '#52E252',
        'kick_sauber': '#52E252',
        'haas_f1_team': '#B6BABD',
        'haas': '#B6BABD',
    }

    # Get color from parameter or default
    if not team_color:
        team_color = default_colors.get(team_id, '#FFFFFF')

    team, created = Team.objects.get_or_create(
        team_id=team_id,
        defaults={
            'name': team_name,
            'color': team_color,
            **kwargs
        }
    )

    # Update color if team exists but color is missing or default
    if not created and (not team.color or team.color == '#FFFFFF'):
        team.color = team_color
        team.save()

    return team


def get_or_create_driver(driver_info: dict) -> Driver:
    """Get or create a driver."""
    driver, created = Driver.objects.get_or_create(
        driver_id=driver_info.get('driver_id'),
        defaults=driver_info
    )
    return driver


def get_or_create_circuit(circuit_info: dict) -> Circuit:
    """Get or create a circuit."""
    circuit, created = Circuit.objects.get_or_create(
        circuit_id=circuit_info.get('circuit_id'),
        defaults=circuit_info
    )
    return circuit


@shared_task(bind=True, max_retries=3)
def collect_session_data(self, year: int, round_num: int, session_type: str):
    """
    Collect data for a specific session.

    Args:
        year: Season year
        round_num: Round number
        session_type: Session type ('R', 'Q', 'S', etc.)
    """
    try:
        logger.info(f"Collecting {session_type} data for {year} Round {round_num}")

        # Load session
        session = fastf1.get_session(year, round_num, session_type)
        session.load()

        # Get or create season and event
        season_obj = get_or_create_season(year)

        # Create event if not exists
        event_id = f"{year}_{round_num}"
        event, created = Event.objects.get_or_create(
            event_id=event_id,
            defaults={
                'season': season_obj,
                'round_number': round_num,
                'event_name': session.event['EventName'],
                'event_date': session.event['EventDate'],
                'circuit': get_or_create_circuit({
                    'circuit_id': session.event['Location'].lower().replace(' ', '_'),
                    'name': session.event['Location'],
                    'country': session.event['Country'],
                })
            }
        )

        # Create session object
        session_id = f"{event_id}_{session_type}"

        # Determine if session is complete (has already happened)
        is_complete = session.date < timezone.now()

        session_obj, created = Session.objects.get_or_create(
            session_id=session_id,
            defaults={
                'event': event,
                'session_type': session_type,
                'session_date': session.date,
                'is_complete': is_complete,
                'data_collected': True,
                'collection_date': timezone.now(),
            }
        )

        # Update is_complete for existing sessions
        if not created:
            session_obj.is_complete = is_complete
            session_obj.save()

        # Process results based on session type
        if session_type == 'R':
            process_race_results(session, session_obj)
        elif session_type == 'Q':
            process_qualifying_results(session, session_obj)
        elif session_type == 'S':
            process_sprint_results(session, session_obj)

        # Collect lap times
        process_lap_times(session, session_obj)

        # Collect pit stops (only for race sessions)
        if session_type == 'R':
            process_pit_stops(session, session_obj)

        # Collect weather data
        process_weather_data(session, session_obj)

        logger.info(f"Successfully collected {session_type} data for {year} Round {round_num}")
        return f"Collected {session_type} data for {year} Round {round_num}"

    except Exception as exc:
        logger.error(f"Error collecting session data: {exc}")
        raise self.retry(exc=exc, countdown=60)


def process_race_results(session, session_obj: Session):
    """Process race results."""
    results = session.results

    for idx, row in results.iterrows():
        driver = get_or_create_driver({
            'driver_id': row['Abbreviation'].lower(),
            'code': row['Abbreviation'],
            'number': int(row['DriverNumber']),
            'first_name': row['FirstName'],
            'last_name': row['LastName'],
        })

        team = get_or_create_team(row['TeamName'])

        # Get time data
        total_race_time = safe_value(row.get('Time'))
        fastest_lap_time = safe_value(row.get('FastestLapTime'))
        fastest_lap_number = safe_value(row.get('FastestLap'))

        RaceResult.objects.update_or_create(
            session=session_obj,
            driver=driver,
            defaults={
                'team': team,
                'position': safe_value(row['Position']),
                'grid_position': safe_value(row.get('GridPosition')),
                'points': safe_value(row.get('Points', 0)),
                'laps_completed': safe_value(row.get('Laps', 0)),
                'total_race_time': total_race_time,
                'fastest_lap_time': fastest_lap_time,
                'fastest_lap_number': fastest_lap_number,
                'status': safe_value(row.get('Status', 'Finished')),
                'dnf': row.get('Status') != 'Finished',
            }
        )


def process_qualifying_results(session, session_obj: Session):
    """Process qualifying results."""
    results = session.results

    for idx, row in results.iterrows():
        driver = get_or_create_driver({
            'driver_id': row['Abbreviation'].lower(),
            'code': row['Abbreviation'],
            'number': int(row['DriverNumber']),
            'first_name': row['FirstName'],
            'last_name': row['LastName'],
        })

        team = get_or_create_team(row['TeamName'])

        QualifyingResult.objects.update_or_create(
            session=session_obj,
            driver=driver,
            defaults={
                'team': team,
                'position': safe_value(row['Position']),
                'q1_time': safe_value(row.get('Q1')),
                'q2_time': safe_value(row.get('Q2')),
                'q3_time': safe_value(row.get('Q3')),
            }
        )


def process_sprint_results(session, session_obj: Session):
    """Process sprint results."""
    results = session.results

    for idx, row in results.iterrows():
        driver = get_or_create_driver({
            'driver_id': row['Abbreviation'].lower(),
            'code': row['Abbreviation'],
            'number': int(row['DriverNumber']),
            'first_name': row['FirstName'],
            'last_name': row['LastName'],
        })

        team = get_or_create_team(row['TeamName'])

        SprintResult.objects.update_or_create(
            session=session_obj,
            driver=driver,
            defaults={
                'team': team,
                'position': safe_value(row['Position']),
                'grid_position': safe_value(row.get('GridPosition')),
                'points': safe_value(row.get('Points', 0)),
                'laps_completed': safe_value(row.get('Laps', 0)),
                'status': safe_value(row.get('Status', 'Finished')),
            }
        )


def process_lap_times(session, session_obj: Session):
    """Process lap times for all drivers."""
    try:
        laps = session.laps

        for idx, lap in laps.iterrows():
            driver_code = lap['Driver']

            # Get driver
            try:
                driver = Driver.objects.get(code=driver_code)
            except Driver.DoesNotExist:
                continue

            # Get team
            team_name = lap.get('Team', '')
            team = get_or_create_team(team_name) if team_name else None

            if not team:
                continue

            LapTime.objects.update_or_create(
                session=session_obj,
                driver=driver,
                lap_number=lap['LapNumber'],
                defaults={
                    'team': team,
                    'lap_time': lap['LapTime'],
                    'sector1_time': lap.get('Sector1Time'),
                    'sector2_time': lap.get('Sector2Time'),
                    'sector3_time': lap.get('Sector3Time'),
                    'compound': lap.get('Compound', ''),
                    'tyre_life': lap.get('TyreLife'),
                    'is_personal_best': lap.get('IsPersonalBest', False),
                    'is_accurate': lap.get('IsAccurate', True),
                }
            )

        logger.info(f"Processed {len(laps)} lap times for {session_obj}")
    except Exception as e:
        logger.error(f"Error processing lap times: {e}")


def process_weather_data(session, session_obj: Session):
    """Process weather data."""
    try:
        weather = session.weather_data

        if weather is None or len(weather) == 0:
            logger.warning(f"No weather data available for {session_obj}")
            return

        for idx, row in weather.iterrows():
            WeatherData.objects.update_or_create(
                session=session_obj,
                timestamp=row['Time'],
                defaults={
                    'air_temp': safe_value(row.get('AirTemp', 0)),
                    'track_temp': safe_value(row.get('TrackTemp', 0)),
                    'humidity': safe_value(row.get('Humidity', 0)),
                    'pressure': safe_value(row.get('Pressure', 0)),
                    'rainfall': bool(safe_value(row.get('Rainfall', False))),
                    'wind_speed': safe_value(row.get('WindSpeed')),
                    'wind_direction': safe_value(row.get('WindDirection')),
                }
            )

        logger.info(f"Processed {len(weather)} weather records for {session_obj}")
    except Exception as e:
        logger.error(f"Error processing weather data: {e}")


def process_pit_stops(session, session_obj: Session):
    """Process pit stop data."""
    try:
        # Only race sessions have pit stops
        if session_obj.session_type != 'R':
            return

        laps = session.laps

        if laps is None or len(laps) == 0:
            logger.warning(f"No lap data available for pit stops in {session_obj}")
            return

        # Get pit stops from laps data
        # In FastF1, pit stops are identified by PitInTime and PitOutTime
        pit_data = laps[laps['PitInTime'].notna()].copy()

        if len(pit_data) == 0:
            logger.warning(f"No pit stops found in {session_obj}")
            return

        for idx, row in pit_data.iterrows():
            driver_code = row['Driver']

            # Get driver
            try:
                driver = Driver.objects.get(code=driver_code)
            except Driver.DoesNotExist:
                continue

            # Get team
            team_name = row.get('Team', '')
            team = get_or_create_team(team_name) if team_name else None

            if not team:
                continue

            # Calculate pit stop duration
            pit_duration = None
            if pd.notna(row.get('PitOutTime')) and pd.notna(row.get('PitInTime')):
                pit_duration = row['PitOutTime'] - row['PitInTime']

            # Count stops for this driver to get stop number
            stop_number = PitStop.objects.filter(
                session=session_obj,
                driver=driver
            ).count() + 1

            PitStop.objects.update_or_create(
                session=session_obj,
                driver=driver,
                lap=int(row['LapNumber']),
                defaults={
                    'team': team,
                    'stop_number': stop_number,
                    'duration': safe_value(pit_duration),
                }
            )

        logger.info(f"Processed {len(pit_data)} pit stops for {session_obj}")
    except Exception as e:
        logger.error(f"Error processing pit stops: {e}")


@shared_task
def collect_all_race_data():
    """Collect all race data from 2022 to current year."""
    current_year = datetime.now().year
    tasks = []

    for year in range(2022, current_year + 1):
        # Get race schedule
        schedule = fastf1.get_event_schedule(year)

        for round_num in range(1, len(schedule) + 1):
            task = collect_session_data.s(year, round_num, 'R')
            tasks.append(task)

    # Run tasks in parallel
    job = group(tasks)
    result = job.apply_async()

    logger.info(f"Started collecting race data for {len(tasks)} races")
    return f"Collecting race data for {len(tasks)} races"


@shared_task
def collect_all_qualifying_data():
    """Collect all qualifying data from 2022 to current year."""
    current_year = datetime.now().year
    tasks = []

    for year in range(2022, current_year + 1):
        schedule = fastf1.get_event_schedule(year)

        for round_num in range(1, len(schedule) + 1):
            task = collect_session_data.s(year, round_num, 'Q')
            tasks.append(task)

    job = group(tasks)
    result = job.apply_async()

    logger.info(f"Started collecting qualifying data for {len(tasks)} sessions")
    return f"Collecting qualifying data for {len(tasks)} sessions"


@shared_task
def collect_all_sprint_data():
    """Collect all sprint data from 2022 to current year."""
    current_year = datetime.now().year
    tasks = []

    for year in range(2022, current_year + 1):
        schedule = fastf1.get_event_schedule(year)

        # Check which events have sprints
        for round_num in range(1, len(schedule) + 1):
            try:
                # Try to get sprint session
                session = fastf1.get_session(year, round_num, 'S')
                task = collect_session_data.s(year, round_num, 'S')
                tasks.append(task)
            except:
                # No sprint for this event
                continue

    if tasks:
        job = group(tasks)
        result = job.apply_async()
        logger.info(f"Started collecting sprint data for {len(tasks)} sprints")

    return f"Collecting sprint data for {len(tasks)} sprints"


@shared_task
def collect_all_standings_data():
    """Calculate and save standings data from race results."""
    from collections import defaultdict

    current_year = datetime.now().year

    for year in range(2022, current_year + 1):
        logger.info(f"Calculating standings for {year}")

        try:
            season = Season.objects.get(year=year)
        except Season.DoesNotExist:
            continue

        # Get all events for this season, ordered by round
        events = Event.objects.filter(season=season).order_by('round_number')

        # Track cumulative points
        driver_points = defaultdict(lambda: {'points': 0, 'wins': 0})
        constructor_points = defaultdict(lambda: {'points': 0, 'wins': 0})

        for event in events:
            # Get race session for this event
            race_sessions = Session.objects.filter(
                event=event,
                session_type='R'
            )

            for race_session in race_sessions:
                # Get all race results for this session
                results = RaceResult.objects.filter(
                    session=race_session
                ).select_related('driver', 'team')

                # Add points from this race
                for result in results:
                    driver_key = result.driver.id
                    team_key = result.team.id

                    driver_points[driver_key]['points'] += safe_value(result.points) or 0
                    constructor_points[team_key]['points'] += safe_value(result.points) or 0

                    if safe_value(result.position) == 1:
                        driver_points[driver_key]['wins'] += 1
                        constructor_points[team_key]['wins'] += 1

                # Save driver standings after this event
                position = 1
                sorted_drivers = sorted(
                    driver_points.items(),
                    key=lambda x: (-x[1]['points'], -x[1]['wins'])
                )

                for driver_id, stats in sorted_drivers:
                    driver = Driver.objects.get(id=driver_id)
                    # Get driver's current team from latest result
                    latest_result = RaceResult.objects.filter(
                        driver=driver,
                        session__event__season=season
                    ).select_related('team').first()

                    if latest_result:
                        DriverStanding.objects.update_or_create(
                            season=season,
                            event=event,
                            driver=driver,
                            defaults={
                                'team': latest_result.team,
                                'position': position,
                                'points': stats['points'],
                                'wins': stats['wins'],
                            }
                        )
                        position += 1

                # Save constructor standings after this event
                position = 1
                sorted_constructors = sorted(
                    constructor_points.items(),
                    key=lambda x: (-x[1]['points'], -x[1]['wins'])
                )

                for team_id, stats in sorted_constructors:
                    team = Team.objects.get(id=team_id)
                    ConstructorStanding.objects.update_or_create(
                        season=season,
                        event=event,
                        team=team,
                        defaults={
                            'position': position,
                            'points': stats['points'],
                            'wins': stats['wins'],
                        }
                    )
                    position += 1

        logger.info(f"Finished calculating standings for {year}")

    return "Standings data collected successfully"


@shared_task
def collect_tyre_data():
    """Collect tyre data from 2025 onwards."""
    current_year = datetime.now().year
    tasks = []

    for year in range(2025, current_year + 1):
        schedule = fastf1.get_event_schedule(year)

        for round_num in range(1, len(schedule) + 1):
            # Collect race sessions for tyre strategies
            task = collect_session_data.s(year, round_num, 'R')
            tasks.append(task)

    if tasks:
        job = group(tasks)
        result = job.apply_async()
        logger.info(f"Started collecting tyre data for {len(tasks)} races")

    return f"Collecting tyre data for {len(tasks)} races"


@shared_task
def start_all_data_collection():
    """
    Start all data collection tasks in parallel (5 workers minimum).
    This is the main entry point for data collection.
    """
    logger.info("Starting all F1 data collection tasks")

    # Create task group for parallel execution
    job = group([
        collect_all_race_data.s(),
        collect_all_qualifying_data.s(),
        collect_all_sprint_data.s(),
        collect_all_standings_data.s(),
        collect_tyre_data.s(),
    ])

    result = job.apply_async()

    logger.info("All data collection tasks started")
    return "All data collection tasks started"
