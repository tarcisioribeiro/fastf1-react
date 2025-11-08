"""
Django management command to remove duplicate records from database.
"""
from django.core.management.base import BaseCommand
from django.db.models import Count
from core.models import (
    Driver, Team, Circuit, Season, Event, Session,
    RaceResult, QualifyingResult, SprintResult,
    DriverStanding, ConstructorStanding,
    LapTime, PitStop, TyreStrategy, WeatherData
)


class Command(BaseCommand):
    help = 'Remove duplicate records from all database tables'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('Running in DRY RUN mode - no data will be deleted\n'))

        total_deleted = 0

        # 1. Drivers - unique by code
        self.stdout.write('Checking Drivers...')
        deleted = self.remove_duplicates_by_field(Driver, ['code'], dry_run)
        total_deleted += deleted

        # 2. Teams - unique by team_id
        self.stdout.write('Checking Teams...')
        deleted = self.remove_duplicates_by_field(Team, ['team_id'], dry_run)
        total_deleted += deleted

        # 3. Circuits - unique by circuit_id
        self.stdout.write('Checking Circuits...')
        deleted = self.remove_duplicates_by_field(Circuit, ['circuit_id'], dry_run)
        total_deleted += deleted

        # 4. Seasons - unique by year
        self.stdout.write('Checking Seasons...')
        deleted = self.remove_duplicates_by_field(Season, ['year'], dry_run)
        total_deleted += deleted

        # 5. Events - unique together [season, round_number]
        self.stdout.write('Checking Events...')
        deleted = self.remove_duplicates_by_fields(Event, ['season', 'round_number'], dry_run)
        total_deleted += deleted

        # 6. Sessions - unique together [event, session_type]
        self.stdout.write('Checking Sessions...')
        deleted = self.remove_duplicates_by_fields(Session, ['event', 'session_type'], dry_run)
        total_deleted += deleted

        # 7. RaceResults - unique together [session, driver]
        self.stdout.write('Checking Race Results...')
        deleted = self.remove_duplicates_by_fields(RaceResult, ['session', 'driver'], dry_run)
        total_deleted += deleted

        # 8. QualifyingResults - unique together [session, driver]
        self.stdout.write('Checking Qualifying Results...')
        deleted = self.remove_duplicates_by_fields(QualifyingResult, ['session', 'driver'], dry_run)
        total_deleted += deleted

        # 9. SprintResults - unique together [session, driver]
        self.stdout.write('Checking Sprint Results...')
        deleted = self.remove_duplicates_by_fields(SprintResult, ['session', 'driver'], dry_run)
        total_deleted += deleted

        # 10. DriverStandings - unique together [season, event, driver]
        self.stdout.write('Checking Driver Standings...')
        deleted = self.remove_duplicates_by_fields(DriverStanding, ['season', 'event', 'driver'], dry_run)
        total_deleted += deleted

        # 11. ConstructorStandings - unique together [season, event, team]
        self.stdout.write('Checking Constructor Standings...')
        deleted = self.remove_duplicates_by_fields(ConstructorStanding, ['season', 'event', 'team'], dry_run)
        total_deleted += deleted

        # 12. LapTimes - unique together [session, driver, lap_number]
        self.stdout.write('Checking Lap Times...')
        deleted = self.remove_duplicates_by_fields(LapTime, ['session', 'driver', 'lap_number'], dry_run)
        total_deleted += deleted

        # 13. PitStops - unique together [session, driver, stop_number]
        self.stdout.write('Checking Pit Stops...')
        deleted = self.remove_duplicates_by_fields(PitStop, ['session', 'driver', 'stop_number'], dry_run)
        total_deleted += deleted

        # 14. TyreStrategy - unique together [session, driver, stint_number]
        self.stdout.write('Checking Tyre Strategies...')
        deleted = self.remove_duplicates_by_fields(TyreStrategy, ['session', 'driver', 'stint_number'], dry_run)
        total_deleted += deleted

        # 15. WeatherData - by session and timestamp (keep most recent)
        self.stdout.write('Checking Weather Data...')
        deleted = self.remove_weather_duplicates(dry_run)
        total_deleted += deleted

        self.stdout.write(self.style.SUCCESS(f'\nTotal records deleted: {total_deleted}'))
        if dry_run:
            self.stdout.write(self.style.WARNING('This was a DRY RUN - no actual data was deleted'))

    def remove_duplicates_by_field(self, model, fields, dry_run=False):
        """Remove duplicates based on single field."""
        field = fields[0]
        duplicates = (
            model.objects.values(field)
            .annotate(count=Count('id'))
            .filter(count__gt=1)
        )

        deleted_count = 0
        for dup in duplicates:
            field_value = dup[field]
            # Keep the oldest record, delete the rest
            records = model.objects.filter(**{field: field_value}).order_by('id')
            to_delete = records[1:]  # Skip first (oldest)

            count = to_delete.count()
            if count > 0:
                self.stdout.write(f'  Found {count} duplicates for {field}={field_value}')
                if not dry_run:
                    to_delete.delete()
                deleted_count += count

        return deleted_count

    def remove_duplicates_by_fields(self, model, fields, dry_run=False):
        """Remove duplicates based on multiple fields."""
        # Get all combinations that have duplicates
        duplicates = (
            model.objects.values(*fields)
            .annotate(count=Count('id'))
            .filter(count__gt=1)
        )

        deleted_count = 0
        for dup in duplicates:
            # Build filter kwargs
            filter_kwargs = {field: dup[field] for field in fields}

            # Keep the oldest record, delete the rest
            records = model.objects.filter(**filter_kwargs).order_by('id')
            to_delete = records[1:]  # Skip first (oldest)

            count = to_delete.count()
            if count > 0:
                self.stdout.write(f'  Found {count} duplicates for {filter_kwargs}')
                if not dry_run:
                    to_delete.delete()
                deleted_count += count

        return deleted_count

    def remove_weather_duplicates(self, dry_run=False):
        """Remove weather data duplicates, keeping most recent."""
        duplicates = (
            WeatherData.objects.values('session', 'timestamp')
            .annotate(count=Count('id'))
            .filter(count__gt=1)
        )

        deleted_count = 0
        for dup in duplicates:
            # Keep the most recent (by id), delete older ones
            records = WeatherData.objects.filter(
                session=dup['session'],
                timestamp=dup['timestamp']
            ).order_by('-id')  # Most recent first

            to_delete = records[1:]  # Skip first (most recent)
            count = to_delete.count()
            if count > 0:
                self.stdout.write(f'  Found {count} weather duplicates')
                if not dry_run:
                    to_delete.delete()
                deleted_count += count

        return deleted_count
