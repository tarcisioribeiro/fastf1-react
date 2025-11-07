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
    # Collect race data every 15 minutes
    'collect-race-data-every-15min': {
        'task': 'data_collector.tasks.collect_all_race_data',
        'schedule': crontab(minute='*/15'),
    },
    # Collect qualifying data every 15 minutes
    'collect-qualifying-data-every-15min': {
        'task': 'data_collector.tasks.collect_all_qualifying_data',
        'schedule': crontab(minute='*/15'),
    },
    # Collect sprint data every 15 minutes
    'collect-sprint-data-every-15min': {
        'task': 'data_collector.tasks.collect_all_sprint_data',
        'schedule': crontab(minute='*/15'),
    },
    # Collect standings data every 15 minutes
    'collect-standings-every-15min': {
        'task': 'data_collector.tasks.collect_all_standings_data',
        'schedule': crontab(minute='*/15'),
    },
    # Collect tyre data every 15 minutes
    'collect-tyre-data-every-15min': {
        'task': 'data_collector.tasks.collect_tyre_data',
        'schedule': crontab(minute='*/15'),
    },
}

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing Celery."""
    print(f'Request: {self.request!r}')
