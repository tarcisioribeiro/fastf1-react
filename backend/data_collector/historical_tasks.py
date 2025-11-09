"""
Celery tasks for historical F1 data collection (pre-2018).
These tasks collect data from Jolpica F1 API (Ergast-compatible).

Features:
- Colored logging for better visibility
- Database logging of errors and warnings
- Sleep delays for better log readability
- Strict filtering to collect ONLY data before 2018
"""
import logging
import time
import traceback as tb
from datetime import datetime
from celery import shared_task, group, chord
from django.db.models import Count

from core.models import (
    Season, Event, RaceResult, DriverStanding,
    ConstructorStanding, DataCollectionLog
)
from .historical_processor import HistoricalDataProcessor
from .jolpica_client import JolpicaF1Client

logger = logging.getLogger('data_collector')

# ANSI Color Codes for terminal output
class Colors:
    """ANSI color codes for colored logging."""
    RESET = '\033[0m'
    BOLD = '\033[1m'

    # Levels
    DEBUG = '\033[36m'      # Cyan
    INFO = '\033[32m'       # Green
    WARNING = '\033[33m'    # Yellow
    ERROR = '\033[31m'      # Red
    CRITICAL = '\033[35m'   # Magenta

    # Status
    SUCCESS = '\033[92m'    # Bright Green
    SKIPPED = '\033[90m'    # Gray

    # Context
    YEAR = '\033[94m'       # Blue
    ROUND = '\033[96m'      # Cyan


def colored_log(level, message, color=None):
    """Log a message with color and save errors/warnings to database."""
    if color is None:
        color_map = {
            'DEBUG': Colors.DEBUG,
            'INFO': Colors.INFO,
            'WARNING': Colors.WARNING,
            'ERROR': Colors.ERROR,
            'CRITICAL': Colors.CRITICAL,
            'SUCCESS': Colors.SUCCESS,
        }
        color = color_map.get(level.upper(), Colors.RESET)

    colored_message = f"{color}{message}{Colors.RESET}"

    # Log to console with color
    if level.upper() == 'WARNING':
        logger.warning(colored_message)
    elif level.upper() in ['ERROR', 'CRITICAL']:
        logger.error(colored_message)
    elif level.upper() == 'DEBUG':
        logger.debug(colored_message)
    else:
        logger.info(colored_message)


def validate_year(year: int) -> bool:
    """
    Valida se o ano está dentro do range permitido (< 2018).

    IMPORTANTE: Dados de 2018+ devem vir do FastF1, NÃO da Jolpica!
    """
    if year >= 2018:
        msg = f"❌ Ano {year} está fora do range! Jolpica API deve ser usada APENAS para anos < 2018"
        colored_log('ERROR', msg)
        DataCollectionLog.log_error(
            source='JOLPICA',
            task_name='validate_year',
            message=msg,
            year=year
        )
        return False

    if year < 1950:
        msg = f"⚠️  Ano {year} é anterior a 1950 (primeira temporada de F1)"
        colored_log('WARNING', msg)
        DataCollectionLog.log_warning(
            source='JOLPICA',
            task_name='validate_year',
            message=msg,
            year=year
        )
        return False

    return True


@shared_task(bind=True, max_retries=3)
def collect_historical_race(self, year: int, round_num: int):
    """
    Collect historical race data for a specific race.

    Args:
        year: Season year (MUST be < 2018)
        round_num: Round number

    Returns:
        Status message
    """
    task_context = {
        'task_id': self.request.id,
        'year': year,
        'round_number': round_num
    }

    try:
        # Validação crítica: apenas anos < 2018
        if not validate_year(year):
            return f"Skipped: {year} is >= 2018 (use FastF1 instead)"

        colored_log('INFO', f"📥 Collecting historical race data for {Colors.YEAR}{year}{Colors.RESET} Round {Colors.ROUND}{round_num}{Colors.RESET}")
        time.sleep(0.3)  # Small delay for log readability

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
            msg = f"Race not found: {year} Round {round_num}"
            colored_log('WARNING', msg)
            DataCollectionLog.log_warning(
                source='JOLPICA',
                task_name='collect_historical_race',
                message=msg,
                **task_context
            )
            return msg

        # Process event and session
        event, session = processor.process_race_event(race_data, year)
        colored_log('SUCCESS', f"  ✓ Event and session created")
        time.sleep(0.2)

        # Get and process race results
        results = client.get_race_results(year, round_num)
        if results:
            result_count = processor.process_race_results(session, results)
            colored_log('SUCCESS', f"  ✓ Processed {result_count} race results")
            time.sleep(0.2)

        # Try to get and process qualifying results
        try:
            qualifying_results = client.get_qualifying_results(year, round_num)
            if qualifying_results:
                qual_session = processor.process_qualifying_session(race_data, event)
                qual_count = processor.process_qualifying_results(qual_session, qualifying_results)
                colored_log('SUCCESS', f"  ✓ Processed {qual_count} qualifying results")
                time.sleep(0.2)
        except Exception as qual_error:
            msg = f"Could not process qualifying for {year} R{round_num}: {qual_error}"
            colored_log('WARNING', msg)
            DataCollectionLog.log_warning(
                source='JOLPICA',
                task_name='collect_historical_race',
                message=msg,
                exception_type=qual_error.__class__.__name__,
                **task_context
            )

        # Try to get and process pit stops (only available from 2012+)
        if year >= 2012:
            try:
                pit_stops = client.get_pit_stops(year, round_num)
                if pit_stops:
                    pit_count = processor.process_pit_stops(session, pit_stops)
                    colored_log('SUCCESS', f"  ✓ Processed {pit_count} pit stops")
                    time.sleep(0.2)
            except Exception as pit_error:
                msg = f"Could not process pit stops for {year} R{round_num}: {pit_error}"
                colored_log('WARNING', msg)
                DataCollectionLog.log_warning(
                    source='JOLPICA',
                    task_name='collect_historical_race',
                    message=msg,
                    exception_type=pit_error.__class__.__name__,
                    **task_context
                )

        colored_log('SUCCESS', f"✅ Successfully collected historical data for {year} Round {round_num}")

        # Log success to database
        DataCollectionLog.log_info(
            source='JOLPICA',
            task_name='collect_historical_race',
            message=f"Successfully collected data for {year} R{round_num}",
            **task_context
        )

        return f"Collected {year} Round {round_num}"

    except Exception as exc:
        msg = f"Error collecting historical race data for {year} R{round_num}: {exc}"
        colored_log('ERROR', msg)

        # Save error to database
        DataCollectionLog.log_error(
            source='JOLPICA',
            task_name='collect_historical_race',
            message=msg,
            exc=exc,
            traceback=tb.format_exc(),
            **task_context
        )

        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def collect_historical_standings(self, year: int, round_num: int):
    """
    Collect historical standings after a specific race.

    Args:
        year: Season year (MUST be < 2018)
        round_num: Round number

    Returns:
        Status message
    """
    task_context = {
        'task_id': self.request.id,
        'year': year,
        'round_number': round_num
    }

    try:
        # Validação crítica: apenas anos < 2018
        if not validate_year(year):
            return f"Skipped: {year} is >= 2018 (use FastF1 instead)"

        colored_log('INFO', f"📊 Collecting historical standings for {Colors.YEAR}{year}{Colors.RESET} Round {Colors.ROUND}{round_num}{Colors.RESET}")
        time.sleep(0.3)

        processor = HistoricalDataProcessor()
        client = processor.client

        # Get season and event
        try:
            season = Season.objects.get(year=year)
            event = Event.objects.get(season=season, round_number=round_num)
        except (Season.DoesNotExist, Event.DoesNotExist) as e:
            msg = f"Season or event not found for {year} Round {round_num}"
            colored_log('ERROR', msg)
            DataCollectionLog.log_error(
                source='JOLPICA',
                task_name='collect_historical_standings',
                message=msg,
                exc=e,
                **task_context
            )
            return msg

        # Get and process driver standings
        driver_standings = client.get_driver_standings(year, round_num)
        if driver_standings:
            driver_count = processor.process_driver_standings(season, event, driver_standings)
            colored_log('SUCCESS', f"  ✓ Processed {driver_count} driver standings")
            time.sleep(0.2)

        # Get and process constructor standings
        constructor_standings = client.get_constructor_standings(year, round_num)
        if constructor_standings:
            constructor_count = processor.process_constructor_standings(season, event, constructor_standings)
            colored_log('SUCCESS', f"  ✓ Processed {constructor_count} constructor standings")
            time.sleep(0.2)

        colored_log('SUCCESS', f"✅ Successfully collected standings for {year} Round {round_num}")

        # Log success to database
        DataCollectionLog.log_info(
            source='JOLPICA',
            task_name='collect_historical_standings',
            message=f"Successfully collected standings for {year} R{round_num}",
            **task_context
        )

        return f"Collected standings for {year} Round {round_num}"

    except Exception as exc:
        msg = f"Error collecting historical standings for {year} R{round_num}: {exc}"
        colored_log('ERROR', msg)

        DataCollectionLog.log_error(
            source='JOLPICA',
            task_name='collect_historical_standings',
            message=msg,
            exc=exc,
            traceback=tb.format_exc(),
            **task_context
        )

        raise self.retry(exc=exc, countdown=60)


@shared_task
def collect_historical_season(year: int):
    """
    Collect all historical data for a complete season.

    Args:
        year: Season year (MUST be < 2018)

    Returns:
        Status message
    """
    try:
        # Validação crítica: apenas anos < 2018
        if not validate_year(year):
            colored_log('SKIPPED', f"⏭️  Skipping year {year} (>= 2018, use FastF1 instead)", Colors.SKIPPED)
            return f"Skipped: {year} is >= 2018"

        colored_log('INFO', f"\n{'='*80}\n🏁 Starting historical data collection for season {Colors.YEAR}{Colors.BOLD}{year}{Colors.RESET}\n{'='*80}")
        time.sleep(0.5)

        client = JolpicaF1Client()

        # Get all races for this season
        races = client.get_races(year)

        if not races:
            msg = f"No races found for {year}"
            colored_log('WARNING', msg)
            DataCollectionLog.log_warning(
                source='JOLPICA',
                task_name='collect_historical_season',
                message=msg,
                year=year
            )
            return msg

        colored_log('INFO', f"📋 Found {len(races)} races for {year}")
        time.sleep(0.3)

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
        colored_log('INFO', f"📅 Scheduling {len(race_tasks)} race collection tasks for {year}")
        time.sleep(0.3)

        # Use chord to collect races first, then standings
        callback = summarize_season_collection.s(year)
        job = chord(race_tasks + standings_tasks)(callback)

        # Log to database
        DataCollectionLog.log_info(
            source='JOLPICA',
            task_name='collect_historical_season',
            message=f"Started collection for {year} with {len(races)} races",
            year=year
        )

        return f"Started collection for {year} with {len(races)} races"

    except Exception as e:
        msg = f"Error collecting historical season {year}: {e}"
        colored_log('ERROR', msg)

        DataCollectionLog.log_error(
            source='JOLPICA',
            task_name='collect_historical_season',
            message=msg,
            exc=e,
            traceback=tb.format_exc(),
            year=year
        )

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
    colored_log('SUCCESS', f"🎉 Season {Colors.YEAR}{Colors.BOLD}{year}{Colors.RESET}{Colors.SUCCESS} collection complete. Results: {len(results)} tasks completed{Colors.RESET}")

    DataCollectionLog.log_info(
        source='JOLPICA',
        task_name='summarize_season_collection',
        message=f"Season {year} collection complete with {len(results)} tasks",
        year=year
    )

    return f"Season {year} collection complete"


@shared_task
def collect_all_historical_data(start_year: int = 1950, end_year: int = 2017):
    """
    Collect all historical F1 data from start_year to end_year.

    IMPORTANTE: end_year DEVE ser < 2018! Dados de 2018+ vêm do FastF1.

    Args:
        start_year: Starting year (inclusive, default 1950)
        end_year: Ending year (inclusive, MUST be < 2018, default 2017)

    Returns:
        Status message
    """
    try:
        # Validação crítica: end_year DEVE ser < 2018
        if end_year >= 2018:
            msg = f"❌ ERRO CRÍTICO: end_year ({end_year}) deve ser < 2018! Dados de 2018+ devem vir do FastF1."
            colored_log('CRITICAL', msg)
            DataCollectionLog.log_error(
                source='JOLPICA',
                task_name='collect_all_historical_data',
                message=msg,
                year=end_year
            )
            # Forçar end_year para 2017
            end_year = 2017
            colored_log('WARNING', f"⚠️  end_year ajustado automaticamente para 2017")

        colored_log('INFO', f"\n{'='*80}\n🚀 Starting complete historical data collection: {Colors.YEAR}{start_year}{Colors.RESET} to {Colors.YEAR}{end_year}{Colors.RESET}\n{'='*80}")
        time.sleep(0.5)

        # Create season collection tasks (filtrando apenas < 2018)
        season_tasks = []
        for year in range(start_year, end_year + 1):
            if year < 2018:  # Garantia adicional
                season_tasks.append(collect_historical_season.s(year))
            else:
                colored_log('SKIPPED', f"⏭️  Skipping {year} (>= 2018)", Colors.SKIPPED)

        # Execute all season tasks
        job = group(season_tasks)
        result = job.apply_async()

        colored_log('INFO', f"✅ Started historical collection for {len(season_tasks)} seasons (all < 2018)")

        DataCollectionLog.log_info(
            source='JOLPICA',
            task_name='collect_all_historical_data',
            message=f"Started historical collection: {start_year}-{end_year} ({len(season_tasks)} seasons)"
        )

        return f"Started historical collection: {start_year}-{end_year}"

    except Exception as e:
        msg = f"Error starting historical data collection: {e}"
        colored_log('ERROR', msg)

        DataCollectionLog.log_error(
            source='JOLPICA',
            task_name='collect_all_historical_data',
            message=msg,
            exc=e,
            traceback=tb.format_exc()
        )

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
        colored_log('INFO', "🔧 Collecting historical metadata (drivers, teams, circuits)")
        time.sleep(0.3)

        processor = HistoricalDataProcessor()
        client = processor.client

        # Collect all drivers
        drivers = client.get_drivers()
        driver_count = 0
        for driver_data in drivers:
            processor.process_driver(driver_data)
            driver_count += 1

        colored_log('SUCCESS', f"  ✓ Processed {driver_count} drivers")
        time.sleep(0.2)

        # Collect all constructors
        constructors = client.get_constructors()
        team_count = 0
        for constructor_data in constructors:
            processor.process_team(constructor_data)
            team_count += 1

        colored_log('SUCCESS', f"  ✓ Processed {team_count} teams")
        time.sleep(0.2)

        # Collect all circuits
        circuits = client.get_circuits()
        circuit_count = 0
        for circuit_data in circuits:
            processor.process_circuit(circuit_data)
            circuit_count += 1

        colored_log('SUCCESS', f"  ✓ Processed {circuit_count} circuits")
        time.sleep(0.2)

        msg = f"Metadata collected: {driver_count} drivers, {team_count} teams, {circuit_count} circuits"
        colored_log('SUCCESS', f"✅ {msg}")

        DataCollectionLog.log_info(
            source='JOLPICA',
            task_name='collect_historical_metadata',
            message=msg
        )

        return msg

    except Exception as e:
        msg = f"Error collecting metadata: {e}"
        colored_log('ERROR', msg)

        DataCollectionLog.log_error(
            source='JOLPICA',
            task_name='collect_historical_metadata',
            message=msg,
            exc=e,
            traceback=tb.format_exc()
        )

        return f"Error: {str(e)}"


@shared_task
def validate_historical_data():
    """
    Validate and report on historical data collection.

    Returns:
        Validation report
    """
    try:
        colored_log('INFO', "🔍 Validating historical data...")
        time.sleep(0.3)

        report = {
            'seasons': {},
            'total_races': 0,
            'total_results': 0,
            'total_standings': 0,
            'issues': []
        }

        # Check each season (APENAS < 2018)
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
                issue = f"No events for {year}"
                report['issues'].append(issue)
                colored_log('WARNING', f"  ⚠️  {issue}")
            if result_count == 0:
                issue = f"No race results for {year}"
                report['issues'].append(issue)
                colored_log('WARNING', f"  ⚠️  {issue}")

        colored_log('SUCCESS', f"✅ Validation complete: {len(seasons)} seasons checked")
        colored_log('INFO', f"📊 Total races: {report['total_races']}, Total results: {report['total_results']}")

        if report['issues']:
            colored_log('WARNING', f"⚠️  Found {len(report['issues'])} issues")
            for issue in report['issues']:
                DataCollectionLog.log_warning(
                    source='JOLPICA',
                    task_name='validate_historical_data',
                    message=issue
                )

        DataCollectionLog.log_info(
            source='JOLPICA',
            task_name='validate_historical_data',
            message=f"Validation complete: {len(seasons)} seasons, {len(report['issues'])} issues"
        )

        return report

    except Exception as e:
        msg = f"Error validating data: {e}"
        colored_log('ERROR', msg)

        DataCollectionLog.log_error(
            source='JOLPICA',
            task_name='validate_historical_data',
            message=msg,
            exc=e,
            traceback=tb.format_exc()
        )

        return {'error': str(e)}


@shared_task
def incremental_historical_update(target_year: int = 2017):
    """
    Update historical data up to target year.
    Useful for adding missing years or updating incomplete data.

    IMPORTANTE: target_year DEVE ser < 2018!

    Args:
        target_year: Year to collect up to (MUST be < 2018, default 2017)

    Returns:
        Status message
    """
    try:
        # Validação crítica: target_year DEVE ser < 2018
        if target_year >= 2018:
            msg = f"❌ ERRO: target_year ({target_year}) deve ser < 2018! Ajustando para 2017."
            colored_log('ERROR', msg)
            DataCollectionLog.log_error(
                source='JOLPICA',
                task_name='incremental_historical_update',
                message=msg,
                year=target_year
            )
            target_year = 2017

        colored_log('INFO', f"🔄 Running incremental historical update up to {Colors.YEAR}{target_year}{Colors.RESET}")
        time.sleep(0.3)

        # Find gaps in data (APENAS < 2018)
        seasons_with_data = Season.objects.filter(
            year__lt=2018,
            year__lte=target_year
        ).values_list('year', flat=True)

        # Determine which years to collect (APENAS < 2018)
        all_years = set(range(1950, min(target_year + 1, 2018)))  # Garante que não passa de 2017
        existing_years = set(seasons_with_data)
        missing_years = sorted(all_years - existing_years)

        if missing_years:
            colored_log('INFO', f"📝 Found {len(missing_years)} missing years: {missing_years}")
            time.sleep(0.3)

            # Collect missing seasons
            tasks = []
            for year in missing_years:
                if year < 2018:  # Garantia adicional
                    tasks.append(collect_historical_season.s(year))
                else:
                    colored_log('SKIPPED', f"⏭️  Skipping {year} (>= 2018)", Colors.SKIPPED)

            job = group(tasks)
            job.apply_async()

            msg = f"Collecting {len(tasks)} missing seasons: {[y for y in missing_years if y < 2018]}"
            colored_log('SUCCESS', f"✅ {msg}")

            DataCollectionLog.log_info(
                source='JOLPICA',
                task_name='incremental_historical_update',
                message=msg
            )

            return msg
        else:
            msg = f"All seasons up to {target_year} already exist"
            colored_log('INFO', f"ℹ️  {msg}")

            DataCollectionLog.log_info(
                source='JOLPICA',
                task_name='incremental_historical_update',
                message=msg
            )

            return msg

    except Exception as e:
        msg = f"Error in incremental update: {e}"
        colored_log('ERROR', msg)

        DataCollectionLog.log_error(
            source='JOLPICA',
            task_name='incremental_historical_update',
            message=msg,
            exc=e,
            traceback=tb.format_exc()
        )

        return f"Error: {str(e)}"


@shared_task
def start_complete_historical_ingestion():
    """
    Start complete historical data ingestion process.
    This is the main entry point for historical data collection.

    Coleta APENAS dados pré-2018 (1950-2017).

    Steps:
    1. Collect metadata (drivers, teams, circuits)
    2. Collect all historical data (1950-2017)
    3. Validate collected data

    Returns:
        Status message
    """
    try:
        colored_log('INFO', f"\n{'='*80}\n🏁 Starting COMPLETE historical data ingestion (1950-2017 ONLY)\n{'='*80}")
        time.sleep(0.5)

        # Step 1: Collect metadata first
        colored_log('INFO', "📝 Step 1: Collecting metadata...")
        time.sleep(0.3)
        collect_historical_metadata.delay()

        # Step 2: Collect all historical data (1950-2017 ONLY)
        colored_log('INFO', "📥 Step 2: Scheduling historical data collection (1950-2017)...")
        time.sleep(0.3)
        collect_all_historical_data.apply_async(
            kwargs={'start_year': 1950, 'end_year': 2017},  # Explicitamente 2017
            countdown=60  # Wait 60 seconds for metadata collection
        )

        # Step 3: Validate after collection
        colored_log('INFO', "🔍 Step 3: Scheduling validation...")
        time.sleep(0.3)
        validate_historical_data.apply_async(
            countdown=3600  # Wait 1 hour for data collection
        )

        msg = "Complete historical ingestion started (1950-2017 ONLY)"
        colored_log('SUCCESS', f"✅ {msg}")

        DataCollectionLog.log_info(
            source='JOLPICA',
            task_name='start_complete_historical_ingestion',
            message=msg
        )

        return msg

    except Exception as e:
        msg = f"Error starting complete ingestion: {e}"
        colored_log('ERROR', msg)

        DataCollectionLog.log_error(
            source='JOLPICA',
            task_name='start_complete_historical_ingestion',
            message=msg,
            exc=e,
            traceback=tb.format_exc()
        )

        return f"Error: {str(e)}"
