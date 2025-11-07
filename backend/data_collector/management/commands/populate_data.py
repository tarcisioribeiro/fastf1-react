"""
Management command to populate F1 data.
This command will trigger the Celery tasks to collect data.
"""
from django.core.management.base import BaseCommand
from data_collector.tasks import start_all_data_collection
import logging

logger = logging.getLogger('data_collector')


class Command(BaseCommand):
    help = 'Populate F1 data from FastF1 API using Celery tasks'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting F1 data collection...'))

        try:
            # Trigger the main collection task
            result = start_all_data_collection.delay()

            self.stdout.write(
                self.style.SUCCESS(
                    f'Data collection task started successfully!'
                    f'\nTask ID: {result.id}'
                    f'\nYou can monitor progress in the Celery worker logs.'
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error starting data collection: {e}')
            )
