"""
Celery tasks for historical F1 data collection (pre-2018).
These tasks collect data from Jolpica F1 API (Ergast-compatible).
"""
import logging
from datetime import datetime
from celery import shared_task, group, chord
from django.db.models import Count

from core.models import Season, Event, RaceResult, DriverStanding, ConstructorStanding
from .historical_processor import HistoricalDataProcessor
from .jolpica_client import JolpicaF1Client

logger = logging.getLogger('data_collector')


@shared_task(bind=True, max_retries=3)
def collect_historical_race(self, year: int, round_num: int):
    """
    Collect historical race data for a specific race.

    Args:
        year: Season year
        round_num: Round number

    Returns:
        Status message
    """
    try:
        logger.info(f"Collecting historical race data for {year} Round {round_num}")

        processor = HistoricalDataProcessor()
        client = processor.client

        # Get race data
        races = client.get_races(year)

        # Find the specific round
        race_data = None
        for race in races:
            if int(race.get('round', 0)) == round_num:
                race_data = race
                break

        if not race_data:
            logger.warning(f"Race not found: {year} Round {round_num}")
            return f"Race not found: {year} Round {round_num}"

        # Process event and session
        event, session = processor.process_race_event(race_data, year)

        # Get and process race results
        results = client.get_race_results(year, round_num)
        if results:
            result_count = processor.process_race_results(session, results)
            logger.info(f"Processed {result_count} race results")

        # Try to get and process qualifying results
        try:
            qualifying_results = client.get_qualifying_results(year, round_num)
            if qualifying_results:
                qual_session = processor.process_qualifying_session(race_data, event)
                qual_count = processor.process_qualifying_results(qual_session, qualifying_results)
                logger.info(f"Processed {qual_count} qualifying results")
        except Exception as qual_error:
            logger.warning(f"Could not process qualifying for {year} R{round_num}: {qual_error}")

        # Try to get and process pit stops (only available from 2012+)
        if year >= 2012:
            try:
                pit_stops = client.get_pit_stops(year, round_num)
                if pit_stops:
                    pit_count = processor.process_pit_stops(session, pit_stops)
                    logger.info(f"Processed {pit_count} pit stops")
            except Exception as pit_error:
                logger.warning(f"Could not process pit stops for {year} R{round_num}: {pit_error}")

        logger.info(f"Successfully collected historical data for {year} Round {round_num}")
        return f"Collected {year} Round {round_num}"

    except Exception as exc:
        logger.error(f"Error collecting historical race data: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def collect_historical_standings(self, year: int, round_num: int):
    """
    Collect historical standings after a specific race.

    Args:
        year: Season year
        round_num: Round number

    Returns:
        Status message
    """
    try:
        logger.info(f"Collecting historical standings for {year} Round {round_num}")

        processor = HistoricalDataProcessor()
        client = processor.client

        # Get season and event
        try:
            season = Season.objects.get(year=year)
            event = Event.objects.get(season=season, round_number=round_num)
        except (Season.DoesNotExist, Event.DoesNotExist) as e:
            logger.error(f"Season or event not found: {e}")
            return f"Season or event not found for {year} Round {round_num}"

        # Get and process driver standings
        driver_standings = client.get_driver_standings(year, round_num)
        if driver_standings:
            driver_count = processor.process_driver_standings(season, event, driver_standings)
            logger.info(f"Processed {driver_count} driver standings")

        # Get and process constructor standings
        constructor_standings = client.get_constructor_standings(year, round_num)
        if constructor_standings:
            constructor_count = processor.process_constructor_standings(season, event, constructor_standings)
            logger.info(f"Processed {constructor_count} constructor standings")

        logger.info(f"Successfully collected standings for {year} Round {round_num}")
        return f"Collected standings for {year} Round {round_num}"

    except Exception as exc:
        logger.error(f"Error collecting historical standings: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=60)


@shared_task
def collect_historical_season(year: int):
    """
    Collect all historical data for a complete season.

    Args:
        year: Season year

    Returns:
        Status message
    """
    try:
        logger.info(f"Starting historical data collection for season {year}")

        client = JolpicaF1Client()

        # Get all races for this season
        races = client.get_races(year)

        if not races:
            logger.warning(f"No races found for {year}")
            return f"No races found for {year}"

        # Create tasks for each race and its standings
        race_tasks = []
        standings_tasks = []

        for race in races:
            round_num = int(race.get('round', 0))

            # Race data collection
            race_tasks.append(collect_historical_race.s(year, round_num))

            # Standings collection (after race)
            standings_tasks.append(collect_historical_standings.s(year, round_num))

        # Execute race tasks first, then standings
        logger.info(f"Scheduling {len(race_tasks)} race collection tasks for {year}")

        # Use chord to collect races first, then standings
        callback = summarize_season_collection.s(year)
        job = chord(race_tasks + standings_tasks)(callback)

        return f"Started collection for {year} with {len(races)} races"

    except Exception as e:
        logger.error(f"Error collecting historical season {year}: {e}", exc_info=True)
        return f"Error: {str(e)}"


@shared_task
def summarize_season_collection(results, year: int):
    """
    Summarize results of season collection.

    Args:
        results: List of task results
        year: Season year

    Returns:
        Summary message
    """
    logger.info(f"Season {year} collection complete. Results: {len(results)} tasks completed")
    return f"Season {year} collection complete"


@shared_task
def collect_all_historical_data(start_year: int = 1950, end_year: int = 2017):
    """
    Collect all historical F1 data from start_year to end_year.
    Default: 1950-2017 (pre-FastF1 era).

    Args:
        start_year: Starting year (inclusive)
        end_year: Ending year (inclusive)

    Returns:
        Status message
    """
    try:
        logger.info(f"Starting complete historical data collection: {start_year}-{end_year}")

        # Create season collection tasks
        season_tasks = []
        for year in range(start_year, end_year + 1):
            season_tasks.append(collect_historical_season.s(year))

        # Execute all season tasks
        job = group(season_tasks)
        result = job.apply_async()

        logger.info(f"Started historical collection for {len(season_tasks)} seasons")
        return f"Started historical collection: {start_year}-{end_year}"

    except Exception as e:
        logger.error(f"Error starting historical data collection: {e}", exc_info=True)
        return f"Error: {str(e)}"


@shared_task
def collect_historical_metadata():
    """
    Collect all historical metadata (drivers, teams, circuits).
    This should be run first before collecting race data.

    Returns:
        Status message
    """
    try:
        logger.info("Collecting historical metadata (drivers, teams, circuits)")

        processor = HistoricalDataProcessor()
        client = processor.client

        # Collect all drivers
        drivers = client.get_drivers()
        driver_count = 0
        for driver_data in drivers:
            processor.process_driver(driver_data)
            driver_count += 1

        logger.info(f"Processed {driver_count} drivers")

        # Collect all constructors
        constructors = client.get_constructors()
        team_count = 0
        for constructor_data in constructors:
            processor.process_team(constructor_data)
            team_count += 1

        logger.info(f"Processed {team_count} teams")

        # Collect all circuits
        circuits = client.get_circuits()
        circuit_count = 0
        for circuit_data in circuits:
            processor.process_circuit(circuit_data)
            circuit_count += 1

        logger.info(f"Processed {circuit_count} circuits")

        return f"Metadata collected: {driver_count} drivers, {team_count} teams, {circuit_count} circuits"

    except Exception as e:
        logger.error(f"Error collecting metadata: {e}", exc_info=True)
        return f"Error: {str(e)}"


@shared_task
def validate_historical_data():
    """
    Validate and report on historical data collection.

    Returns:
        Validation report
    """
    try:
        logger.info("Validating historical data...")

        report = {
            'seasons': {},
            'total_races': 0,
            'total_results': 0,
            'total_standings': 0,
            'issues': []
        }

        # Check each season
        seasons = Season.objects.filter(year__lt=2018).order_by('year')

        for season in seasons:
            year = season.year

            # Count events
            events = Event.objects.filter(season=season)
            event_count = events.count()

            # Count race results
            race_results = RaceResult.objects.filter(
                session__event__season=season
            )
            result_count = race_results.count()

            # Count standings
            driver_standings = DriverStanding.objects.filter(season=season).count()
            constructor_standings = ConstructorStanding.objects.filter(season=season).count()

            report['seasons'][year] = {
                'events': event_count,
                'race_results': result_count,
                'driver_standings': driver_standings,
                'constructor_standings': constructor_standings,
            }

            report['total_races'] += event_count
            report['total_results'] += result_count
            report['total_standings'] += driver_standings

            # Check for issues
            if event_count == 0:
                report['issues'].append(f"No events for {year}")
            if result_count == 0:
                report['issues'].append(f"No race results for {year}")

        logger.info(f"Validation complete: {report}")
        return report

    except Exception as e:
        logger.error(f"Error validating data: {e}", exc_info=True)
        return {'error': str(e)}


@shared_task
def incremental_historical_update(target_year: int = 2017):
    """
    Update historical data up to target year.
    Useful for adding missing years or updating incomplete data.

    Args:
        target_year: Year to collect up to (default 2017)

    Returns:
        Status message
    """
    try:
        logger.info(f"Running incremental historical update up to {target_year}")

        # Find gaps in data
        seasons_with_data = Season.objects.filter(
            year__lte=target_year
        ).values_list('year', flat=True)

        # Determine which years to collect
        all_years = set(range(1950, target_year + 1))
        existing_years = set(seasons_with_data)
        missing_years = sorted(all_years - existing_years)

        if missing_years:
            logger.info(f"Found {len(missing_years)} missing years: {missing_years}")

            # Collect missing seasons
            tasks = []
            for year in missing_years:
                tasks.append(collect_historical_season.s(year))

            job = group(tasks)
            job.apply_async()

            return f"Collecting {len(missing_years)} missing seasons: {missing_years}"
        else:
            logger.info(f"All seasons up to {target_year} already exist")
            return f"All seasons up to {target_year} already exist"

    except Exception as e:
        logger.error(f"Error in incremental update: {e}", exc_info=True)
        return f"Error: {str(e)}"


@shared_task
def start_complete_historical_ingestion():
    """
    Start complete historical data ingestion process.
    This is the main entry point for historical data collection.

    Steps:
    1. Collect metadata (drivers, teams, circuits)
    2. Collect all historical data (1950-2017)
    3. Validate collected data

    Returns:
        Status message
    """
    try:
        logger.info("Starting complete historical data ingestion")

        # Step 1: Collect metadata first
        logger.info("Step 1: Collecting metadata...")
        collect_historical_metadata.delay()

        # Step 2: Collect all historical data (1950-2017)
        # Use delay to ensure metadata is collected first
        logger.info("Step 2: Scheduling historical data collection...")
        collect_all_historical_data.apply_async(
            kwargs={'start_year': 1950, 'end_year': 2017},
            countdown=60  # Wait 60 seconds for metadata collection
        )

        # Step 3: Validate after collection
        logger.info("Step 3: Scheduling validation...")
        validate_historical_data.apply_async(
            countdown=3600  # Wait 1 hour for data collection
        )

        return "Complete historical ingestion started (1950-2017)"

    except Exception as e:
        logger.error(f"Error starting complete ingestion: {e}", exc_info=True)
        return f"Error: {str(e)}"
