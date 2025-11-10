"""
Celery tasks for consolidating duplicate drivers and teams.
This merges historical data (Jolpica API 1950-2017) with modern data (FastF1 2018+).
"""
import logging
from celery import shared_task
from django.db import transaction
from django.db.models import Count, Max, Q
from core.models import (
    Driver, Team, RaceResult, QualifyingResult, SprintResult,
    DriverStanding, ConstructorStanding, LapTime, TyreStrategy, PitStop
)

logger = logging.getLogger('data_collector')


@shared_task(bind=True, name='data_collector.consolidate_duplicate_drivers')
def consolidate_duplicate_drivers(self, dry_run=True):
    """
    Consolidate duplicate driver records.

    Strategy:
    1. Find all duplicate driver codes
    2. For each duplicate set:
       - Choose the "primary" driver (most recent data, usually FastF1)
       - Move all historical data to primary driver
       - Delete old duplicate records

    Args:
        dry_run: If True, only report what would be done without making changes

    Returns:
        dict: Summary of consolidation actions
    """
    logger.info(f"Starting driver consolidation (dry_run={dry_run})")

    # Find duplicate driver codes
    duplicates = Driver.objects.values('code').annotate(
        count=Count('id'),
        max_id=Max('id')
    ).filter(count__gt=1).order_by('-count')

    total_duplicates = duplicates.count()
    logger.info(f"Found {total_duplicates} driver codes with duplicates")

    consolidated = []
    errors = []

    for dup in duplicates:
        code = dup['code']
        drivers = Driver.objects.filter(code=code).order_by('-id')

        try:
            # Choose primary driver (most recent ID = FastF1 data)
            primary = drivers.first()
            duplicates_to_merge = drivers.exclude(id=primary.id)

            logger.info(f"\nProcessing code {code}:")
            logger.info(f"  Primary: ID {primary.id} - {primary.full_name}")

            if dry_run:
                # Just report what would be done
                for old_driver in duplicates_to_merge:
                    race_results = RaceResult.objects.filter(driver=old_driver).count()
                    quali_results = QualifyingResult.objects.filter(driver=old_driver).count()
                    sprint_results = SprintResult.objects.filter(driver=old_driver).count()
                    standings = DriverStanding.objects.filter(driver=old_driver).count()
                    lap_times = LapTime.objects.filter(driver=old_driver).count()

                    logger.info(f"  Would merge ID {old_driver.id} ({old_driver.full_name}):")
                    logger.info(f"    - {race_results} race results")
                    logger.info(f"    - {quali_results} qualifying results")
                    logger.info(f"    - {sprint_results} sprint results")
                    logger.info(f"    - {standings} driver standings")
                    logger.info(f"    - {lap_times} lap times")

                consolidated.append({
                    'code': code,
                    'primary_id': primary.id,
                    'merged_count': duplicates_to_merge.count(),
                    'action': 'would_consolidate'
                })
            else:
                # Actually consolidate
                with transaction.atomic():
                    total_moved = 0

                    for old_driver in duplicates_to_merge:
                        # Move all related records to primary driver
                        race_moved = RaceResult.objects.filter(driver=old_driver).update(driver=primary)
                        quali_moved = QualifyingResult.objects.filter(driver=old_driver).update(driver=primary)
                        sprint_moved = SprintResult.objects.filter(driver=old_driver).update(driver=primary)
                        standings_moved = DriverStanding.objects.filter(driver=old_driver).update(driver=primary)
                        lap_times_moved = LapTime.objects.filter(driver=old_driver).update(driver=primary)

                        moved = race_moved + quali_moved + sprint_moved + standings_moved + lap_times_moved
                        total_moved += moved

                        logger.info(f"  Merged ID {old_driver.id}: {moved} records moved")

                        # Delete old driver record
                        old_driver.delete()
                        logger.info(f"  Deleted duplicate driver ID {old_driver.id}")

                    consolidated.append({
                        'code': code,
                        'primary_id': primary.id,
                        'merged_count': duplicates_to_merge.count(),
                        'records_moved': total_moved,
                        'action': 'consolidated'
                    })

                    logger.info(f"  ✓ Consolidated {code}: {total_moved} records moved")

        except Exception as e:
            logger.error(f"Error consolidating driver {code}: {e}")
            errors.append({
                'code': code,
                'error': str(e)
            })

    result = {
        'status': 'success' if not errors else 'partial',
        'dry_run': dry_run,
        'total_duplicate_codes': total_duplicates,
        'consolidated': len(consolidated),
        'errors': len(errors),
        'details': consolidated,
        'error_details': errors
    }

    logger.info(f"Driver consolidation completed: {result['consolidated']} codes processed")
    return result


@shared_task(bind=True, name='data_collector.consolidate_duplicate_teams')
def consolidate_duplicate_teams(self, dry_run=True):
    """
    Consolidate duplicate team records using the TEAM_CONSOLIDATION_MAP.

    Strategy:
    1. Use Team.TEAM_CONSOLIDATION_MAP to identify which teams should be merged
    2. For each consolidation group:
       - Find or create the canonical team
       - Move all historical data to canonical team
       - Delete old team records

    Args:
        dry_run: If True, only report what would be done without making changes

    Returns:
        dict: Summary of consolidation actions
    """
    logger.info(f"Starting team consolidation (dry_run={dry_run})")

    consolidated = []
    errors = []

    # Get consolidation map from model
    consolidation_map = Team.TEAM_CONSOLIDATION_MAP

    logger.info(f"Processing {len(consolidation_map)} consolidation groups")

    for canonical_name, aliases in consolidation_map.items():
        try:
            logger.info(f"\nProcessing group: {canonical_name}")

            # Find all teams that match canonical name or aliases
            all_names = [canonical_name] + aliases
            teams = Team.objects.filter(
                Q(name__in=all_names) |
                Q(canonical_name=canonical_name)
            ).order_by('-id')

            if teams.count() <= 1:
                logger.info(f"  Only one team found, no consolidation needed")
                continue

            # Choose or create primary team
            # Prefer team with canonical_name set, otherwise most recent
            primary = teams.filter(canonical_name=canonical_name).first()
            if not primary:
                primary = teams.first()
                if not dry_run:
                    primary.canonical_name = canonical_name
                    primary.save()

            teams_to_merge = teams.exclude(id=primary.id)

            logger.info(f"  Primary: ID {primary.id} - {primary.name}")

            if dry_run:
                # Just report what would be done
                for old_team in teams_to_merge:
                    race_results = RaceResult.objects.filter(team=old_team).count()
                    quali_results = QualifyingResult.objects.filter(team=old_team).count()
                    sprint_results = SprintResult.objects.filter(team=old_team).count()
                    standings = ConstructorStanding.objects.filter(team=old_team).count()

                    logger.info(f"  Would merge ID {old_team.id} ({old_team.name}):")
                    logger.info(f"    - {race_results} race results")
                    logger.info(f"    - {quali_results} qualifying results")
                    logger.info(f"    - {sprint_results} sprint results")
                    logger.info(f"    - {standings} constructor standings")

                consolidated.append({
                    'canonical_name': canonical_name,
                    'primary_id': primary.id,
                    'merged_count': teams_to_merge.count(),
                    'action': 'would_consolidate'
                })
            else:
                # Actually consolidate
                with transaction.atomic():
                    total_moved = 0

                    # Set canonical_name on primary if not set
                    if not primary.canonical_name:
                        primary.canonical_name = canonical_name
                        primary.save()
                        logger.info(f"  Set canonical_name on primary team")

                    for old_team in teams_to_merge:
                        # Move all related records to primary team
                        race_moved = RaceResult.objects.filter(team=old_team).update(team=primary)
                        quali_moved = QualifyingResult.objects.filter(team=old_team).update(team=primary)
                        sprint_moved = SprintResult.objects.filter(team=old_team).update(team=primary)
                        standings_moved = ConstructorStanding.objects.filter(team=old_team).update(team=primary)
                        tyre_moved = TyreStrategy.objects.filter(team=old_team).update(team=primary)

                        moved = race_moved + quali_moved + sprint_moved + standings_moved + tyre_moved
                        total_moved += moved

                        logger.info(f"  Merged ID {old_team.id} ({old_team.name}): {moved} records moved")

                        # Delete old team record
                        old_team.delete()
                        logger.info(f"  Deleted duplicate team ID {old_team.id}")

                    consolidated.append({
                        'canonical_name': canonical_name,
                        'primary_id': primary.id,
                        'merged_count': teams_to_merge.count(),
                        'records_moved': total_moved,
                        'action': 'consolidated'
                    })

                    logger.info(f"  ✓ Consolidated {canonical_name}: {total_moved} records moved")

        except Exception as e:
            logger.error(f"Error consolidating team {canonical_name}: {e}")
            errors.append({
                'canonical_name': canonical_name,
                'error': str(e)
            })

    result = {
        'status': 'success' if not errors else 'partial',
        'dry_run': dry_run,
        'total_consolidation_groups': len(consolidation_map),
        'consolidated': len(consolidated),
        'errors': len(errors),
        'details': consolidated,
        'error_details': errors
    }

    logger.info(f"Team consolidation completed: {result['consolidated']} groups processed")
    return result


@shared_task(bind=True, name='data_collector.consolidate_all_data')
def consolidate_all_data(self, dry_run=True):
    """
    Consolidate all duplicate data (drivers and teams).

    This is the main task that should be run to unify historical and modern data.

    Args:
        dry_run: If True, only report what would be done without making changes

    Returns:
        dict: Summary of all consolidation actions
    """
    logger.info(f"Starting full data consolidation (dry_run={dry_run})")

    results = {
        'status': 'started',
        'dry_run': dry_run,
        'timestamp': str(timezone.now())
    }

    # Step 1: Consolidate drivers
    try:
        logger.info("=" * 80)
        logger.info("STEP 1: CONSOLIDATING DRIVERS")
        logger.info("=" * 80)
        driver_result = consolidate_duplicate_drivers(dry_run=dry_run)
        results['drivers'] = driver_result
    except Exception as e:
        logger.error(f"Error consolidating drivers: {e}")
        results['drivers'] = {'status': 'error', 'error': str(e)}

    # Step 2: Consolidate teams
    try:
        logger.info("\n" + "=" * 80)
        logger.info("STEP 2: CONSOLIDATING TEAMS")
        logger.info("=" * 80)
        team_result = consolidate_duplicate_teams(dry_run=dry_run)
        results['teams'] = team_result
    except Exception as e:
        logger.error(f"Error consolidating teams: {e}")
        results['teams'] = {'status': 'error', 'error': str(e)}

    # Final summary
    results['status'] = 'completed'

    logger.info("\n" + "=" * 80)
    logger.info("CONSOLIDATION SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Drivers consolidated: {results.get('drivers', {}).get('consolidated', 0)}")
    logger.info(f"Teams consolidated: {results.get('teams', {}).get('consolidated', 0)}")
    logger.info(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")

    if not dry_run:
        logger.info("\n✓ Data consolidation completed successfully!")
        logger.info("Historical data is now unified with modern FastF1 data.")
    else:
        logger.info("\nℹ This was a dry run. No changes were made.")
        logger.info("Run with dry_run=False to apply changes.")

    return results


# Import timezone at the end to avoid circular imports
from django.utils import timezone
