"""
Django management command to consolidate duplicate driver records.
Finds drivers with the same driver_id and merges them into a single record.
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count
from core.models import (
    Driver, RaceResult, QualifyingResult, SprintResult,
    DriverStanding, LapTime, PitStop, TyreStrategy
)


class Command(BaseCommand):
    help = 'Consolidate duplicate driver records (same driver_id)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually doing it',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('Running in DRY RUN mode - no data will be changed\n'))

        # Find duplicate driver_ids
        duplicates = (
            Driver.objects.values('driver_id')
            .annotate(count=Count('id'))
            .filter(count__gt=1)
            .order_by('-count')
        )

        if not duplicates.exists():
            self.stdout.write(self.style.SUCCESS('No duplicate drivers found!'))
            return

        self.stdout.write(f'Found {duplicates.count()} drivers with duplicates\n')

        total_merged = 0
        total_deleted = 0

        for dup in duplicates:
            driver_id = dup['driver_id']
            count = dup['count']

            # Get all duplicate records for this driver_id
            drivers = Driver.objects.filter(driver_id=driver_id).order_by('id')

            # Keep the first (oldest) record
            keeper = drivers.first()
            duplicates_to_merge = drivers.exclude(id=keeper.id)

            self.stdout.write(
                f'\n{self.style.WARNING(f"Driver: {keeper.full_name} ({driver_id})")}'
            )
            self.stdout.write(f'  Keeping: ID {keeper.id} (code={keeper.code}, number={keeper.number})')

            for duplicate in duplicates_to_merge:
                self.stdout.write(
                    f'  Merging: ID {duplicate.id} (code={duplicate.code}, number={duplicate.number})'
                )

            if not dry_run:
                merged, deleted = self._merge_drivers(keeper, duplicates_to_merge)
                total_merged += merged
                total_deleted += deleted
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  ✓ Merged {merged} records, deleted {deleted} duplicate driver(s)'
                    )
                )
            else:
                # Count what would be merged
                count_to_merge = sum([
                    duplicate.race_results.count() +
                    duplicate.qualifying_results.count() +
                    duplicate.sprint_results.count() +
                    duplicate.standings.count() +
                    duplicate.lap_times.count() +
                    duplicate.pit_stops.count() +
                    duplicate.tyre_strategies.count()
                    for duplicate in duplicates_to_merge
                ])
                self.stdout.write(f'  Would merge {count_to_merge} related records')

        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✓ Consolidation complete! Merged {total_merged} records, '
                    f'deleted {total_deleted} duplicate drivers'
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    '\nThis was a DRY RUN - no actual data was changed'
                )
            )

    @transaction.atomic
    def _merge_drivers(self, keeper, duplicates):
        """
        Merge duplicate driver records into the keeper record.
        Updates all foreign key references to point to the keeper.
        """
        merged_count = 0

        for duplicate in duplicates:
            # Update all related records to point to the keeper

            # Race results
            race_results = duplicate.race_results.all()
            for result in race_results:
                # Check if keeper already has a result for this session
                existing = RaceResult.objects.filter(
                    session=result.session,
                    driver=keeper
                ).first()

                if not existing:
                    result.driver = keeper
                    result.save()
                    merged_count += 1
                else:
                    # Delete duplicate result
                    result.delete()

            # Qualifying results
            qual_results = duplicate.qualifying_results.all()
            for result in qual_results:
                existing = QualifyingResult.objects.filter(
                    session=result.session,
                    driver=keeper
                ).first()

                if not existing:
                    result.driver = keeper
                    result.save()
                    merged_count += 1
                else:
                    result.delete()

            # Sprint results
            sprint_results = duplicate.sprint_results.all()
            for result in sprint_results:
                existing = SprintResult.objects.filter(
                    session=result.session,
                    driver=keeper
                ).first()

                if not existing:
                    result.driver = keeper
                    result.save()
                    merged_count += 1
                else:
                    result.delete()

            # Driver standings
            standings = duplicate.standings.all()
            for standing in standings:
                existing = DriverStanding.objects.filter(
                    season=standing.season,
                    event=standing.event,
                    driver=keeper
                ).first()

                if not existing:
                    standing.driver = keeper
                    standing.save()
                    merged_count += 1
                else:
                    standing.delete()

            # Lap times
            lap_times = duplicate.lap_times.all()
            for lap_time in lap_times:
                existing = LapTime.objects.filter(
                    session=lap_time.session,
                    driver=keeper,
                    lap_number=lap_time.lap_number
                ).first()

                if not existing:
                    lap_time.driver = keeper
                    lap_time.save()
                    merged_count += 1
                else:
                    lap_time.delete()

            # Pit stops
            pit_stops = duplicate.pit_stops.all()
            for pit_stop in pit_stops:
                existing = PitStop.objects.filter(
                    session=pit_stop.session,
                    driver=keeper,
                    stop_number=pit_stop.stop_number
                ).first()

                if not existing:
                    pit_stop.driver = keeper
                    pit_stop.save()
                    merged_count += 1
                else:
                    pit_stop.delete()

            # Tyre strategies
            tyre_strategies = duplicate.tyre_strategies.all()
            for strategy in tyre_strategies:
                existing = TyreStrategy.objects.filter(
                    session=strategy.session,
                    driver=keeper,
                    stint_number=strategy.stint_number
                ).first()

                if not existing:
                    strategy.driver = keeper
                    strategy.save()
                    merged_count += 1
                else:
                    strategy.delete()

        # Delete the duplicate driver records
        deleted_count = duplicates.count()
        duplicates.delete()

        return merged_count, deleted_count
