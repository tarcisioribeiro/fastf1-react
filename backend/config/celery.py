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
# Otimizado para alta paralelização e coleta mais frequente
app.conf.beat_schedule = {
    # ========================================================================
    # TAREFAS DE SCRAPING HISTÓRICO (Alta Prioridade - A cada 2 minutos)
    # ========================================================================
    'scraping-historical-incremental': {
        'task': 'data_collector.historical_tasks.incremental_historical_update',
        'schedule': crontab(minute='*/2'),  # A cada 2 minutos (muito frequente!)
        'options': {'queue': 'historical', 'priority': 9}
    },
    'scraping-historical-parallel': {
        'task': 'data_collector.historical_tasks.collect_historical_data_parallel',
        'schedule': crontab(minute='*/3'),  # A cada 3 minutos
        'options': {'queue': 'historical', 'priority': 9}
    },
    'scraping-gaps-scan': {
        'task': 'data_collector.historical_tasks.scan_historical_data_gaps',
        'schedule': crontab(minute='*/10'),  # A cada 10 minutos
        'options': {'queue': 'historical', 'priority': 8}
    },

    # ========================================================================
    # TAREFAS FASTF1 - DADOS ATUAIS (Alta Frequência - A cada 5-10 min)
    # ========================================================================
    'fastf1-latest-season': {
        'task': 'data_collector.tasks.collect_latest_season_data',
        'schedule': crontab(minute='*/5'),  # A cada 5 minutos
        'options': {'queue': 'fastf1', 'priority': 8}
    },
    'fastf1-refresh-cache': {
        'task': 'data_collector.tasks.refresh_cache_hourly',
        'schedule': crontab(minute='*/10'),  # A cada 10 minutos
        'options': {'queue': 'fastf1', 'priority': 7}
    },
    'fastf1-practice-sessions': {
        'task': 'data_collector.tasks.collect_practice_sessions',
        'schedule': crontab(minute='*/15'),  # A cada 15 minutos
        'options': {'queue': 'fastf1', 'priority': 6}
    },

    # ========================================================================
    # COLETA DE DADOS COMPLETOS (Paralelo - A cada 15-20 min)
    # ========================================================================
    'collect-race-data-frequent': {
        'task': 'data_collector.tasks.collect_all_race_data',
        'schedule': crontab(minute='*/15'),  # A cada 15 minutos (era 1h!)
        'options': {'queue': 'fastf1', 'priority': 6}
    },
    'collect-qualifying-data-frequent': {
        'task': 'data_collector.tasks.collect_all_qualifying_data',
        'schedule': crontab(minute='*/15'),  # A cada 15 minutos (era 1h!)
        'options': {'queue': 'fastf1', 'priority': 6}
    },
    'collect-sprint-data-frequent': {
        'task': 'data_collector.tasks.collect_all_sprint_data',
        'schedule': crontab(minute='*/20'),  # A cada 20 minutos (era 1h!)
        'options': {'queue': 'fastf1', 'priority': 5}
    },
    'collect-tyre-data-frequent': {
        'task': 'data_collector.tasks.collect_tyre_data',
        'schedule': crontab(minute='*/20'),  # A cada 20 minutos (era 1h!)
        'options': {'queue': 'fastf1', 'priority': 5}
    },

    # ========================================================================
    # CLASSIFICAÇÕES E METADADOS (A cada 10-15 minutos)
    # ========================================================================
    'collect-standings-frequent': {
        'task': 'data_collector.tasks.collect_all_standings_data',
        'schedule': crontab(minute='*/10'),  # A cada 10 minutos (era 1h!)
        'options': {'priority': 7}
    },
    'collect-metadata-frequent': {
        'task': 'data_collector.tasks.collect_season_metadata',
        'schedule': crontab(minute='*/15'),  # A cada 15 minutos (era 1h!)
        'options': {'priority': 6}
    },
    'collect-teams-drivers-frequent': {
        'task': 'data_collector.tasks.collect_team_and_driver_data',
        'schedule': crontab(minute='*/15'),  # A cada 15 minutos (era 1h!)
        'options': {'priority': 6}
    },

    # ========================================================================
    # CONSOLIDAÇÃO E MACHINE LEARNING (A cada 30 min - 1h)
    # ========================================================================
    'consolidate-teams-frequent': {
        'task': 'data_collector.consolidation_tasks.consolidate_all_data',
        'schedule': crontab(minute='*/30'),  # A cada 30 minutos (era 1h!)
        'kwargs': {'dry_run': False},
        'options': {'priority': 5}
    },
    'train-ml-models-frequent': {
        'task': 'data_collector.tasks.check_and_train_ml_models',
        'schedule': crontab(minute='*/30'),  # A cada 30 minutos (era 1h!)
        'options': {'priority': 4}
    },

    # ========================================================================
    # AUDITORIA E MANUTENÇÃO (Diária/Semanal)
    # ========================================================================
    'run-data-audit-daily': {
        'task': 'data_auditor.run_daily_audit',
        'schedule': crontab(hour=1, minute=0),  # Diariamente às 01:00
        'options': {'priority': 3}
    },
    'calculate-missing-podiums-daily': {
        'task': 'data_collector.historical_tasks.calculate_missing_podiums',
        'schedule': crontab(hour=2, minute=0),  # Diariamente às 02:00
        'options': {'priority': 3}
    },
}

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing Celery."""
    print(f'Request: {self.request!r}')
