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
    # Refresh cache every hour (minuto 0)
    'refresh-cache-hourly': {
        'task': 'data_collector.tasks.refresh_cache_hourly',
        'schedule': crontab(minute=0),  # Executa a cada hora no minuto 0
    },
    # Train/update ML models every hour (minuto 0)
    'train-ml-models-every-hour': {
        'task': 'data_collector.tasks.check_and_train_ml_models',
        'schedule': crontab(minute=0),  # Executa a cada hora
    },
    # Collect season metadata (calendar, circuits) every hour (minuto 5)
    'collect-metadata-hourly': {
        'task': 'data_collector.tasks.collect_season_metadata',
        'schedule': crontab(minute=5),  # Executa a cada hora no minuto 5
    },
    # Collect teams and drivers data every hour (minuto 10)
    'collect-teams-drivers-hourly': {
        'task': 'data_collector.tasks.collect_team_and_driver_data',
        'schedule': crontab(minute=10),  # Executa a cada hora no minuto 10
    },
    # Ingest historical data (pre-2018) every hour (minuto 15)
    'ingest-historical-data-hourly': {
        'task': 'data_collector.historical_tasks.incremental_historical_update',
        'schedule': crontab(minute=15),  # Executa a cada hora no minuto 15
    },
    # Collect practice sessions every hour (minuto 20)
    'collect-practice-sessions-hourly': {
        'task': 'data_collector.tasks.collect_practice_sessions',
        'schedule': crontab(minute=20),  # Executa a cada hora no minuto 20
    },
    # Collect all race data every hour (minuto 25)
    'collect-race-data-hourly': {
        'task': 'data_collector.tasks.collect_all_race_data',
        'schedule': crontab(minute=25),  # Executa a cada hora no minuto 25
    },
    # Collect qualifying data every hour (minuto 30)
    'collect-qualifying-data-hourly': {
        'task': 'data_collector.tasks.collect_all_qualifying_data',
        'schedule': crontab(minute=30),  # Executa a cada hora no minuto 30
    },
    # Collect sprint data every hour (minuto 35)
    'collect-sprint-data-hourly': {
        'task': 'data_collector.tasks.collect_all_sprint_data',
        'schedule': crontab(minute=35),  # Executa a cada hora no minuto 35
    },
    # Collect tyre data every hour (minuto 40)
    'collect-tyre-data-hourly': {
        'task': 'data_collector.tasks.collect_tyre_data',
        'schedule': crontab(minute=40),  # Executa a cada hora no minuto 40
    },
    # Consolidate/aggregate team data every hour (minuto 45)
    'consolidate-teams-hourly': {
        'task': 'data_collector.consolidation_tasks.consolidate_all_data',
        'schedule': crontab(minute=45),  # Executa a cada hora no minuto 45
        'kwargs': {'dry_run': False},  # Executar de verdade, não em modo dry_run
    },
    # Collect latest season data every hour (minuto 50)
    'collect-latest-season-hourly': {
        'task': 'data_collector.tasks.collect_latest_season_data',
        'schedule': crontab(minute=50),  # Executa a cada hora no minuto 50
    },
    # Collect standings data every hour (minuto 55)
    'collect-standings-hourly': {
        'task': 'data_collector.tasks.collect_all_standings_data',
        'schedule': crontab(minute=55),  # Executa a cada hora no minuto 55
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
