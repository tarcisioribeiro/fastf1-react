"""
Celery configuration for F1 Data Platform.
"""
import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('f1_data_platform')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery Beat schedule for periodic tasks
app.conf.beat_schedule = {
    # Collect race data every Monday at 2 AM
    'collect-race-data-weekly': {
        'task': 'data_collector.tasks.collect_all_race_data',
        'schedule': crontab(hour=2, minute=0, day_of_week=1),
    },
    # Collect qualifying data every Sunday at 3 AM
    'collect-qualifying-data-weekly': {
        'task': 'data_collector.tasks.collect_all_qualifying_data',
        'schedule': crontab(hour=3, minute=0, day_of_week=0),
    },
    # Collect sprint data when available (Fridays at 4 AM)
    'collect-sprint-data-weekly': {
        'task': 'data_collector.tasks.collect_all_sprint_data',
        'schedule': crontab(hour=4, minute=0, day_of_week=5),
    },
    # Collect standings data daily at 5 AM
    'collect-standings-daily': {
        'task': 'data_collector.tasks.collect_all_standings_data',
        'schedule': crontab(hour=5, minute=0),
    },
    # Collect tyre data for 2025 season every Monday at 6 AM
    'collect-tyre-data-weekly': {
        'task': 'data_collector.tasks.collect_tyre_data',
        'schedule': crontab(hour=6, minute=0, day_of_week=1),
    },
}

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing Celery."""
    print(f'Request: {self.request!r}')
