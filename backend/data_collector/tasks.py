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
        # Make session.date timezone-aware for comparison
        from django.utils import timezone as django_tz
        session_date_aware = django_tz.make_aware(session.date, django_tz.get_current_timezone()) if pd.notna(session.date) and session.date.tzinfo is None else session.date
        is_complete = session_date_aware < timezone.now()

        session_obj, created = Session.objects.get_or_create(
            session_id=session_id,
            defaults={
                'event': event,
                'session_type': session_type,
                'session_date': session_date_aware,
                'is_complete': is_complete,
                'data_collected': True,
                'collection_date': timezone.now(),
            }
        )

        # Update is_complete for existing sessions
        if not created:
            session_obj.is_complete = is_complete
            session_obj.session_date = session_date_aware
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

    # Get the winner's time (first position) to calculate total times for other drivers
    winner_time = None
    for idx, row in results.iterrows():
        if safe_value(row.get('Position')) == 1:
            winner_time = safe_value(row.get('Time'))
            break

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
        # In FastF1, the 'Time' column for the winner is the total race time
        # For other drivers, it's the gap to the winner (time difference)
        # We need to calculate the total time by adding the gap to the winner's time
        time_value = safe_value(row.get('Time'))
        position = safe_value(row.get('Position'))

        total_race_time = None
        if time_value is not None:
            if position == 1:
                # Winner: use the time directly
                total_race_time = time_value
            elif winner_time is not None:
                # Other drivers: add the gap to the winner's time
                total_race_time = winner_time + time_value
            else:
                # Fallback: use the value as is
                total_race_time = time_value

        fastest_lap_time = safe_value(row.get('FastestLapTime'))
        fastest_lap_number = safe_value(row.get('FastestLap'))

        RaceResult.objects.update_or_create(
            session=session_obj,
            driver=driver,
            defaults={
                'team': team,
                'position': position,
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
        # Access weather data from the session
        weather = session.weather_data

        if weather is None or len(weather) == 0:
            logger.warning(f"No weather data available for {session_obj}")
            return

        logger.info(f"Found {len(weather)} weather records for {session_obj}")
        logger.debug(f"Weather data columns: {weather.columns.tolist()}")

        processed_count = 0
        for idx, row in weather.iterrows():
            try:
                # Get timestamp - FastF1 uses 'Time' column which is session time (timedelta)
                timestamp = row.get('Time')

                # Convert session time to absolute datetime
                # session.date is the session start datetime
                if pd.notna(timestamp) and hasattr(session, 'date') and pd.notna(session.date):
                    absolute_time = session.date + timestamp

                    # Make timezone-aware if needed
                    from django.utils import timezone as django_tz
                    if absolute_time.tzinfo is None:
                        absolute_time = django_tz.make_aware(absolute_time, django_tz.get_current_timezone())
                else:
                    logger.warning(f"Skipping weather record with invalid timestamp: {timestamp}")
                    continue

                # Create or update weather record
                WeatherData.objects.update_or_create(
                    session=session_obj,
                    timestamp=absolute_time,
                    defaults={
                        'air_temp': safe_value(row.get('AirTemp', 0)) or 0,
                        'track_temp': safe_value(row.get('TrackTemp', 0)) or 0,
                        'humidity': safe_value(row.get('Humidity', 0)) or 0,
                        'pressure': safe_value(row.get('Pressure', 0)) or 0,
                        'rainfall': bool(safe_value(row.get('Rainfall', False))),
                        'wind_speed': safe_value(row.get('WindSpeed')),
                        'wind_direction': safe_value(row.get('WindDirection')),
                    }
                )
                processed_count += 1
            except Exception as row_error:
                logger.error(f"Error processing weather row: {row_error}")
                continue

        logger.info(f"Successfully processed {processed_count} weather records for {session_obj}")
    except Exception as e:
        logger.error(f"Error processing weather data for {session_obj}: {e}", exc_info=True)


def process_pit_stops(session, session_obj: Session):
    """Process pit stop data from race sessions."""
    try:
        # Only race and sprint sessions have pit stops
        if session_obj.session_type not in ['R', 'S']:
            return

        laps = session.laps

        if laps is None or len(laps) == 0:
            logger.warning(f"No lap data available for pit stops in {session_obj}")
            return

        logger.info(f"Processing pit stops for {session_obj}")
        logger.debug(f"Total laps available: {len(laps)}")

        # Get pit stops from laps data
        # In FastF1, pit stops are identified by PitInTime being not null (inlap)
        pit_data = laps[laps['PitInTime'].notna()].copy()

        if len(pit_data) == 0:
            logger.info(f"No pit stops found in {session_obj} (this is normal for some sessions)")
            return

        logger.info(f"Found {len(pit_data)} potential pit stops")

        processed_count = 0
        # Track stops per driver to assign stop numbers correctly
        driver_stop_counts = {}

        for idx, row in pit_data.iterrows():
            try:
                driver_code = row.get('Driver')

                if not driver_code:
                    logger.warning(f"Skipping pit stop with no driver code")
                    continue

                # Get driver
                try:
                    driver = Driver.objects.get(code=driver_code)
                except Driver.DoesNotExist:
                    logger.warning(f"Driver {driver_code} not found in database")
                    continue

                # Get team
                team_name = row.get('Team', '')
                team = get_or_create_team(team_name) if team_name else None

                if not team:
                    logger.warning(f"No team found for driver {driver_code}")
                    continue

                # Calculate pit stop duration
                pit_duration = None
                if pd.notna(row.get('PitOutTime')) and pd.notna(row.get('PitInTime')):
                    # Duration is a timedelta
                    pit_duration = row['PitOutTime'] - row['PitInTime']

                    # Validate duration (pit stops should be between 2 and 60 seconds typically)
                    if pd.notna(pit_duration):
                        duration_seconds = pit_duration.total_seconds()
                        if duration_seconds < 0 or duration_seconds > 300:  # 5 minutes max
                            logger.warning(f"Invalid pit stop duration: {duration_seconds}s for {driver_code}")
                            pit_duration = None

                # Get or increment stop number for this driver
                if driver.id not in driver_stop_counts:
                    driver_stop_counts[driver.id] = 1
                else:
                    driver_stop_counts[driver.id] += 1

                stop_number = driver_stop_counts[driver.id]
                lap_number = int(row.get('LapNumber', 0))

                if lap_number <= 0:
                    logger.warning(f"Invalid lap number for pit stop: {lap_number}")
                    continue

                # Create or update pit stop record
                PitStop.objects.update_or_create(
                    session=session_obj,
                    driver=driver,
                    lap=lap_number,
                    defaults={
                        'team': team,
                        'stop_number': stop_number,
                        'duration': safe_value(pit_duration),
                    }
                )
                processed_count += 1

            except Exception as row_error:
                logger.error(f"Error processing pit stop row: {row_error}")
                continue

        logger.info(f"Successfully processed {processed_count} pit stops for {session_obj}")
    except Exception as e:
        logger.error(f"Error processing pit stops for {session_obj}: {e}", exc_info=True)


@shared_task
def collect_all_race_data():
    """Collect all race data from 2018 to current year."""
    current_year = datetime.now().year
    tasks = []

    for year in range(2018, current_year + 1):
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
    """Collect all qualifying data from 2018 to current year."""
    current_year = datetime.now().year
    tasks = []

    for year in range(2018, current_year + 1):
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
    """Collect all sprint data from 2021 to current year."""
    current_year = datetime.now().year
    tasks = []

    for year in range(2021, current_year + 1):
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
    """Calculate and save standings data from race and sprint results."""
    from collections import defaultdict

    current_year = datetime.now().year

    for year in range(2018, current_year + 1):
        logger.info(f"Calculating standings for {year}")

        try:
            season = Season.objects.get(year=year)
        except Season.DoesNotExist:
            continue

        # Get all events for this season, ordered by round
        events = Event.objects.filter(season=season).order_by('round_number')

        # Track cumulative statistics
        driver_stats = defaultdict(lambda: {'points': 0, 'wins': 0, 'podiums': 0})
        constructor_stats = defaultdict(lambda: {'points': 0, 'wins': 0, 'podiums': 0})

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

                    driver_stats[driver_key]['points'] += safe_value(result.points) or 0
                    constructor_stats[team_key]['points'] += safe_value(result.points) or 0

                    # Count wins (only from races, not sprints)
                    if safe_value(result.position) == 1:
                        driver_stats[driver_key]['wins'] += 1
                        constructor_stats[team_key]['wins'] += 1

                    # Count podiums (only from races, not sprints) - positions 1, 2, 3
                    if safe_value(result.position) in [1, 2, 3]:
                        driver_stats[driver_key]['podiums'] += 1
                        constructor_stats[team_key]['podiums'] += 1

            # Get sprint session for this event (if exists)
            sprint_sessions = Session.objects.filter(
                event=event,
                session_type='S'
            )

            for sprint_session in sprint_sessions:
                # Get all sprint results for this session
                sprint_results = SprintResult.objects.filter(
                    session=sprint_session
                ).select_related('driver', 'team')

                # Add points from sprint (but NOT wins or podiums)
                for result in sprint_results:
                    driver_key = result.driver.id
                    team_key = result.team.id

                    driver_stats[driver_key]['points'] += safe_value(result.points) or 0
                    constructor_stats[team_key]['points'] += safe_value(result.points) or 0

            # Save driver standings after this event
            position = 1
            sorted_drivers = sorted(
                driver_stats.items(),
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
                            'podiums': stats['podiums'],
                        }
                    )
                    position += 1

            # Save constructor standings after this event
            position = 1
            sorted_constructors = sorted(
                constructor_stats.items(),
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
                        'podiums': stats['podiums'],
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
def collect_latest_season_data():
    """
    Collect data for the latest/current season only.
    Focuses on current year to keep data fresh.
    """
    current_year = datetime.now().year
    logger.info(f"Collecting latest season data for {current_year}")

    try:
        # Ensure season exists
        season = get_or_create_season(current_year)

        # Get event schedule for current year
        schedule = fastf1.get_event_schedule(current_year)

        # Find the latest completed event
        latest_round = None
        for round_num in range(len(schedule), 0, -1):
            try:
                # Try to load the race session
                session = fastf1.get_session(current_year, round_num, 'R')
                session.load()
                latest_round = round_num
                break
            except:
                continue

        if latest_round:
            logger.info(f"Latest round found: {latest_round}")

            # Collect data for this round
            tasks = []

            # Race
            tasks.append(collect_session_data.s(current_year, latest_round, 'R'))

            # Qualifying
            try:
                q_session = fastf1.get_session(current_year, latest_round, 'Q')
                tasks.append(collect_session_data.s(current_year, latest_round, 'Q'))
            except:
                pass

            # Sprint (if exists)
            try:
                s_session = fastf1.get_session(current_year, latest_round, 'S')
                tasks.append(collect_session_data.s(current_year, latest_round, 'S'))
            except:
                pass

            # Execute tasks
            if tasks:
                job = group(tasks)
                job.apply_async()

            # Update standings
            collect_all_standings_data.delay()

            logger.info(f"Started collecting data for round {latest_round}")
            return f"Collecting data for {current_year} Round {latest_round}"
        else:
            logger.warning(f"No completed rounds found for {current_year}")
            return f"No data available for {current_year} yet"

    except Exception as e:
        logger.error(f"Error collecting latest season data: {e}")
        return f"Error: {str(e)}"


@shared_task
def collect_season_metadata():
    """
    Collect and update seasons, events, and circuits metadata.
    This task ensures we have up-to-date calendar and circuit information.
    """
    current_year = datetime.now().year
    logger.info("Collecting season metadata (seasons, events, circuits)")

    updated_count = 0

    # Collect data for last 3 years to keep recent history fresh
    for year in range(current_year - 2, current_year + 1):
        try:
            logger.info(f"Processing season {year}")

            # Create or get season
            season = get_or_create_season(year)

            # Get event schedule
            schedule = fastf1.get_event_schedule(year)

            for idx, event_row in schedule.iterrows():
                try:
                    round_num = event_row['RoundNumber']
                    event_id = f"{year}_{round_num}"

                    # Create or update circuit
                    circuit_info = {
                        'circuit_id': event_row.get('Location', '').lower().replace(' ', '_'),
                        'name': event_row.get('Location', 'Unknown'),
                        'location': event_row.get('Location', 'Unknown'),
                        'country': event_row.get('Country', 'Unknown'),
                    }
                    circuit = get_or_create_circuit(circuit_info)

                    # Create or update event
                    event, created = Event.objects.update_or_create(
                        event_id=event_id,
                        defaults={
                            'season': season,
                            'round_number': round_num,
                            'event_name': event_row['EventName'],
                            'event_date': event_row['EventDate'],
                            'circuit': circuit,
                            'event_type': event_row.get('EventFormat', 'conventional'),
                        }
                    )

                    if created:
                        updated_count += 1
                        logger.info(f"Created event: {event.event_name}")

                except Exception as event_error:
                    logger.error(f"Error processing event: {event_error}")
                    continue

        except Exception as year_error:
            logger.error(f"Error processing year {year}: {year_error}")
            continue

    logger.info(f"Season metadata collection complete. Updated {updated_count} events.")
    return f"Updated {updated_count} events across recent seasons"


@shared_task
def collect_team_and_driver_data():
    """
    Collect and update teams and drivers information.
    Scans recent race results to find all active teams and drivers.
    """
    logger.info("Collecting teams and drivers data")

    current_year = datetime.now().year
    teams_updated = 0
    drivers_updated = 0

    # Get recent sessions (last 2 years) to collect team/driver info
    for year in range(current_year - 1, current_year + 1):
        try:
            schedule = fastf1.get_event_schedule(year)

            # Sample a few races to get team/driver roster
            for round_num in [1, len(schedule) // 2, len(schedule)]:
                try:
                    session = fastf1.get_session(year, round_num, 'R')
                    session.load()

                    results = session.results

                    for idx, row in results.iterrows():
                        # Update driver
                        driver, created = Driver.objects.update_or_create(
                            driver_id=row['Abbreviation'].lower(),
                            defaults={
                                'code': row['Abbreviation'],
                                'number': int(row['DriverNumber']),
                                'first_name': row['FirstName'],
                                'last_name': row['LastName'],
                            }
                        )
                        if created:
                            drivers_updated += 1

                        # Update team
                        team = get_or_create_team(row['TeamName'])
                        if team:
                            teams_updated += 1

                except Exception as session_error:
                    logger.debug(f"Could not load session {year} R{round_num}: {session_error}")
                    continue

        except Exception as year_error:
            logger.error(f"Error processing year {year}: {year_error}")
            continue

    logger.info(f"Teams/Drivers collection complete. Teams: {teams_updated}, Drivers: {drivers_updated}")
    return f"Updated {teams_updated} teams and {drivers_updated} drivers"


@shared_task
def collect_practice_sessions():
    """
    Collect Free Practice session data (FP1, FP2, FP3).
    Useful for analysis and weather data.
    """
    current_year = datetime.now().year
    logger.info(f"Collecting practice sessions for {current_year}")

    tasks = []

    try:
        schedule = fastf1.get_event_schedule(current_year)

        # Only collect practice for latest 3 rounds
        for round_num in range(max(1, len(schedule) - 2), len(schedule) + 1):
            for session_type in ['FP1', 'FP2', 'FP3']:
                try:
                    # Check if session exists
                    session = fastf1.get_session(current_year, round_num, session_type)
                    task = collect_session_data.s(current_year, round_num, session_type)
                    tasks.append(task)
                except:
                    continue

        if tasks:
            job = group(tasks)
            job.apply_async()
            logger.info(f"Started collecting {len(tasks)} practice sessions")
            return f"Collecting {len(tasks)} practice sessions"
        else:
            return "No practice sessions to collect"

    except Exception as e:
        logger.error(f"Error collecting practice sessions: {e}")
        return f"Error: {str(e)}"


@shared_task
def start_all_data_collection():
    """
    Start all data collection tasks in parallel (5 workers minimum).
    This is the main entry point for data collection.
    """
    logger.info("Starting all F1 data collection tasks")

    # Create task group for parallel execution
    job = group([
        collect_latest_season_data.s(),
        collect_season_metadata.s(),
        collect_team_and_driver_data.s(),
        collect_all_standings_data.s(),
    ])

    result = job.apply_async()

    logger.info("All data collection tasks started")
    return "All data collection tasks started"
