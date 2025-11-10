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

# Load additional task modules
app.autodiscover_tasks(['data_collector'], related_name='historical_tasks')
app.autodiscover_tasks(['data_collector'], related_name='consolidation_tasks')
app.autodiscover_tasks(['data_auditor'])

# Celery Beat schedule for periodic tasks
app.conf.beat_schedule = {
    # Collect latest season data daily
    'collect-latest-season-daily': {
        'task': 'data_collector.tasks.collect_latest_season_data',
        'schedule': crontab(hour=0, minute=0),  # Diariamente à meia-noite
    },
    # Collect season metadata (calendar, circuits) daily
    'collect-metadata-daily': {
        'task': 'data_collector.tasks.collect_season_metadata',
        'schedule': crontab(hour=0, minute=5),  # Diariamente às 00:05
    },
    # Collect teams and drivers data daily
    'collect-teams-drivers-daily': {
        'task': 'data_collector.tasks.collect_team_and_driver_data',
        'schedule': crontab(hour=0, minute=10),  # Diariamente às 00:10
    },
    # Collect standings data daily
    'collect-standings-daily': {
        'task': 'data_collector.tasks.collect_all_standings_data',
        'schedule': crontab(hour=0, minute=15),  # Diariamente às 00:15
    },
    # Collect practice sessions daily
    'collect-practice-sessions-daily': {
        'task': 'data_collector.tasks.collect_practice_sessions',
        'schedule': crontab(hour=0, minute=20),  # Diariamente às 00:20
    },
    # Collect all race data daily
    'collect-race-data-daily': {
        'task': 'data_collector.tasks.collect_all_race_data',
        'schedule': crontab(hour=0, minute=25),  # Diariamente às 00:25
    },
    # Collect qualifying data daily
    'collect-qualifying-data-daily': {
        'task': 'data_collector.tasks.collect_all_qualifying_data',
        'schedule': crontab(hour=0, minute=30),  # Diariamente às 00:30
    },
    # Collect sprint data daily
    'collect-sprint-data-daily': {
        'task': 'data_collector.tasks.collect_all_sprint_data',
        'schedule': crontab(hour=0, minute=35),  # Diariamente às 00:35
    },
    # Collect tyre data daily
    'collect-tyre-data-daily': {
        'task': 'data_collector.tasks.collect_tyre_data',
        'schedule': crontab(hour=0, minute=40),  # Diariamente às 00:40
    },
    # Refresh cache every hour
    'refresh-cache-hourly': {
        'task': 'data_collector.tasks.refresh_cache_hourly',
        'schedule': crontab(minute=0),  # Executa a cada hora no minuto 0
    },
    # Train/update ML models every hour
    'train-ml-models-every-hour': {
        'task': 'data_collector.tasks.check_and_train_ml_models',
        'schedule': crontab(minute=0),  # Executa a cada hora
    },
    # Ingest historical data (pre-2018) every hour
    'ingest-historical-data-hourly': {
        'task': 'data_collector.historical_tasks.incremental_historical_update',
        'schedule': crontab(minute=15),  # Executa a cada hora no minuto 15
    },
    # Consolidate/aggregate team data every hour
    'consolidate-teams-hourly': {
        'task': 'data_collector.consolidation_tasks.consolidate_all_data',
        'schedule': crontab(minute=45),  # Executa a cada hora no minuto 45
        'kwargs': {'dry_run': False},  # Executar de verdade, não em modo dry_run
    },
    # Run data audit daily (identifies empty fields and suggests data from public sources)
    'run-data-audit-daily': {
        'task': 'data_auditor.run_daily_audit',
        'schedule': crontab(hour=1, minute=0),  # Diariamente às 01:00 (após coleta de dados)
    },
}

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing Celery."""
    print(f'Request: {self.request!r}')
