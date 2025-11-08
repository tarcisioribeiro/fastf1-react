"""
Django management command for ingesting historical F1 data.
Usage:
    python manage.py ingest_historical_data [options]
"""
from django.core.management.base import BaseCommand, CommandError
from data_collector.historical_tasks import (
    collect_historical_metadata,
    collect_historical_season,
    collect_all_historical_data,
    validate_historical_data,
    incremental_historical_update,
    start_complete_historical_ingestion
)


class Command(BaseCommand):
    help = 'Ingest historical F1 data from Jolpica API (1950-2017)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--mode',
            type=str,
            default='complete',
            choices=['complete', 'metadata', 'season', 'year-range', 'incremental', 'validate'],
            help='Collection mode'
        )
        parser.add_argument(
            '--year',
            type=int,
            help='Specific year to collect (for season mode)'
        )
        parser.add_argument(
            '--start-year',
            type=int,
            default=1950,
            help='Start year (for year-range mode)'
        )
        parser.add_argument(
            '--end-year',
            type=int,
            default=2017,
            help='End year (for year-range mode)'
        )
        parser.add_argument(
            '--target-year',
            type=int,
            default=2017,
            help='Target year for incremental update'
        )

    def handle(self, *args, **options):
        mode = options['mode']

        self.stdout.write(self.style.SUCCESS(f'\n=== Historical F1 Data Ingestion ==='))
        self.stdout.write(self.style.SUCCESS(f'Mode: {mode}\n'))

        try:
            if mode == 'complete':
                self._run_complete_ingestion()

            elif mode == 'metadata':
                self._run_metadata_collection()

            elif mode == 'season':
                year = options.get('year')
                if not year:
                    raise CommandError('--year is required for season mode')
                self._run_season_collection(year)

            elif mode == 'year-range':
                start_year = options['start_year']
                end_year = options['end_year']
                self._run_year_range_collection(start_year, end_year)

            elif mode == 'incremental':
                target_year = options['target_year']
                self._run_incremental_update(target_year)

            elif mode == 'validate':
                self._run_validation()

        except Exception as e:
            raise CommandError(f'Error during ingestion: {str(e)}')

    def _run_complete_ingestion(self):
        """Run complete historical data ingestion (1950-2017)."""
        self.stdout.write(self.style.WARNING(
            'Starting COMPLETE historical data ingestion (1950-2017)...'
        ))
        self.stdout.write(
            'This will collect all metadata, race data, and standings.\n'
            'This process may take several hours.\n'
        )

        # Start the complete ingestion
        result = start_complete_historical_ingestion.delay()

        self.stdout.write(self.style.SUCCESS(
            f'\n✓ Complete ingestion task started!'
        ))
        self.stdout.write(
            f'Task ID: {result.id}\n'
            f'\nThis will run in the background via Celery.\n'
            f'Monitor progress in Celery logs.\n'
        )

    def _run_metadata_collection(self):
        """Collect metadata only (drivers, teams, circuits)."""
        self.stdout.write(
            'Collecting metadata (drivers, teams, circuits)...\n'
        )

        result = collect_historical_metadata.delay()

        self.stdout.write(self.style.SUCCESS(
            f'\n✓ Metadata collection task started!'
        ))
        self.stdout.write(f'Task ID: {result.id}\n')

    def _run_season_collection(self, year: int):
        """Collect data for a specific season."""
        self.stdout.write(
            f'Collecting data for season {year}...\n'
        )

        if year >= 2018:
            self.stdout.write(self.style.WARNING(
                f'Warning: Year {year} should use FastF1 collection instead of historical collection.\n'
            ))

        result = collect_historical_season.delay(year)

        self.stdout.write(self.style.SUCCESS(
            f'\n✓ Season {year} collection task started!'
        ))
        self.stdout.write(f'Task ID: {result.id}\n')

    def _run_year_range_collection(self, start_year: int, end_year: int):
        """Collect data for a range of years."""
        self.stdout.write(
            f'Collecting data for years {start_year}-{end_year}...\n'
        )

        if end_year >= 2018:
            self.stdout.write(self.style.WARNING(
                f'Warning: Years >= 2018 should use FastF1 collection.\n'
                f'Recommended end_year: 2017\n'
            ))

        result = collect_all_historical_data.delay(start_year, end_year)

        self.stdout.write(self.style.SUCCESS(
            f'\n✓ Year range {start_year}-{end_year} collection task started!'
        ))
        self.stdout.write(f'Task ID: {result.id}\n')

    def _run_incremental_update(self, target_year: int):
        """Run incremental update to fill gaps."""
        self.stdout.write(
            f'Running incremental update up to {target_year}...\n'
            f'This will find and collect missing seasons.\n'
        )

        result = incremental_historical_update.delay(target_year)

        self.stdout.write(self.style.SUCCESS(
            f'\n✓ Incremental update task started!'
        ))
        self.stdout.write(f'Task ID: {result.id}\n')

    def _run_validation(self):
        """Validate collected historical data."""
        self.stdout.write('Validating historical data...\n')

        # Run validation synchronously to show results
        result = validate_historical_data()

        if 'error' in result:
            self.stdout.write(self.style.ERROR(
                f'\n✗ Validation error: {result["error"]}\n'
            ))
            return

        self.stdout.write(self.style.SUCCESS('\n✓ Validation complete!\n'))

        # Display summary
        self.stdout.write(self.style.SUCCESS('=== Summary ==='))
        self.stdout.write(f'Total Races: {result["total_races"]}')
        self.stdout.write(f'Total Results: {result["total_results"]}')
        self.stdout.write(f'Total Standings: {result["total_standings"]}\n')

        # Display per-season data
        self.stdout.write(self.style.SUCCESS('=== Per Season ==='))
        for year, data in sorted(result['seasons'].items()):
            self.stdout.write(
                f'{year}: {data["events"]} events, '
                f'{data["race_results"]} results, '
                f'{data["driver_standings"]} driver standings'
            )

        # Display issues
        if result['issues']:
            self.stdout.write(self.style.WARNING('\n=== Issues Found ==='))
            for issue in result['issues']:
                self.stdout.write(self.style.WARNING(f'• {issue}'))
        else:
            self.stdout.write(self.style.SUCCESS('\n✓ No issues found!'))

        self.stdout.write('')
