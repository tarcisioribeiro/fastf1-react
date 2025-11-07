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
    # Collect latest season data every 5 minutes
    'collect-latest-season-every-5min': {
        'task': 'data_collector.tasks.collect_latest_season_data',
        'schedule': crontab(minute='*/5'),
    },
    # Collect season metadata (calendar, circuits) every 5 minutes
    'collect-metadata-every-5min': {
        'task': 'data_collector.tasks.collect_season_metadata',
        'schedule': crontab(minute='*/5'),
    },
    # Collect teams and drivers data every 5 minutes
    'collect-teams-drivers-every-5min': {
        'task': 'data_collector.tasks.collect_team_and_driver_data',
        'schedule': crontab(minute='*/5'),
    },
    # Collect standings data every 5 minutes
    'collect-standings-every-5min': {
        'task': 'data_collector.tasks.collect_all_standings_data',
        'schedule': crontab(minute='*/5'),
    },
    # Collect practice sessions every 5 minutes
    'collect-practice-sessions-every-5min': {
        'task': 'data_collector.tasks.collect_practice_sessions',
        'schedule': crontab(minute='*/5'),
    },
    # Collect all race data (historical) every 5 minutes
    'collect-race-data-every-5min': {
        'task': 'data_collector.tasks.collect_all_race_data',
        'schedule': crontab(minute='*/5'),
    },
    # Collect qualifying data every 5 minutes
    'collect-qualifying-data-every-5min': {
        'task': 'data_collector.tasks.collect_all_qualifying_data',
        'schedule': crontab(minute='*/5'),
    },
    # Collect sprint data every 5 minutes
    'collect-sprint-data-every-5min': {
        'task': 'data_collector.tasks.collect_all_sprint_data',
        'schedule': crontab(minute='*/5'),
    },
    # Collect tyre data every 5 minutes
    'collect-tyre-data-every-5min': {
        'task': 'data_collector.tasks.collect_tyre_data',
        'schedule': crontab(minute='*/5'),
    },
}

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing Celery."""
    print(f'Request: {self.request!r}')
