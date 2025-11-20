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

# Configurações adicionais para otimização de memória
app.conf.update(
    # Limita o número de tarefas que um worker pode executar antes de reiniciar
    worker_max_tasks_per_child=50,
    # Limita o prefetch para evitar acúmulo de tarefas em memória
    worker_prefetch_multiplier=1,
    # Serialização mais eficiente
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    # Timeout de tarefas
    task_time_limit=3600,  # 1 hora
    task_soft_time_limit=3300,  # 55 minutos
    # Otimizações de memória
    worker_disable_rate_limits=True,
    task_acks_late=True,  # ACK após conclusão para evitar perda de tarefas
    task_reject_on_worker_lost=True,
)

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Load additional task modules
app.autodiscover_tasks(['data_collector'], related_name='historical_tasks')
app.autodiscover_tasks(['data_collector'], related_name='consolidation_tasks')
app.autodiscover_tasks(['data_auditor'])

# Celery Beat schedule for periodic tasks
# Agendamento iniciando às 07:15 com intervalos de 5 minutos entre tarefas
# Cada tarefa se repete a cada hora no mesmo minuto
app.conf.beat_schedule = {
    # ========================================================================
    # COLETA DE DADOS ATUAIS - FastF1 (Horário: 07:15-07:55, a cada hora)
    # ========================================================================
    '07:15-collect-latest-season': {
        'task': 'data_collector.tasks.collect_latest_season_data',
        'schedule': crontab(minute=15),  # XX:15 de cada hora
        'options': {'priority': 9}
    },
    '07:20-refresh-cache': {
        'task': 'data_collector.tasks.refresh_cache_hourly',
        'schedule': crontab(minute=20),  # XX:20 de cada hora
        'options': {'priority': 8}
    },
    '07:25-collect-all-race-data': {
        'task': 'data_collector.tasks.collect_all_race_data',
        'schedule': crontab(minute=25),  # XX:25 de cada hora
        'options': {'priority': 8}
    },
    '07:30-collect-all-qualifying-data': {
        'task': 'data_collector.tasks.collect_all_qualifying_data',
        'schedule': crontab(minute=30),  # XX:30 de cada hora
        'options': {'priority': 8}
    },
    '07:35-collect-all-sprint-data': {
        'task': 'data_collector.tasks.collect_all_sprint_data',
        'schedule': crontab(minute=35),  # XX:35 de cada hora
        'options': {'priority': 7}
    },
    '07:40-collect-tyre-data': {
        'task': 'data_collector.tasks.collect_tyre_data',
        'schedule': crontab(minute=40),  # XX:40 de cada hora
        'options': {'priority': 7}
    },
    '07:45-collect-standings': {
        'task': 'data_collector.tasks.collect_all_standings_data',
        'schedule': crontab(minute=45),  # XX:45 de cada hora
        'options': {'priority': 7}
    },
    '07:50-collect-metadata': {
        'task': 'data_collector.tasks.collect_season_metadata',
        'schedule': crontab(minute=50),  # XX:50 de cada hora
        'options': {'priority': 6}
    },
    '07:55-collect-teams-drivers': {
        'task': 'data_collector.tasks.collect_team_and_driver_data',
        'schedule': crontab(minute=55),  # XX:55 de cada hora
        'options': {'priority': 6}
    },

    # ========================================================================
    # COLETA DE DADOS HISTÓRICOS (Horário: 08:00-08:30, a cada 2 horas)
    # ========================================================================
    '08:00-scan-historical-gaps': {
        'task': 'data_collector.historical_tasks.scan_historical_data_gaps',
        'schedule': crontab(minute=0, hour='*/2'),  # 00:00, 02:00, 04:00, 06:00, 08:00, etc.
        'options': {'priority': 8}
    },
    '08:05-collect-historical-parallel': {
        'task': 'data_collector.historical_tasks.collect_historical_data_parallel',
        'schedule': crontab(minute=5, hour='*/2'),  # 00:05, 02:05, 04:05, 06:05, 08:05, etc.
        'options': {'priority': 8}
    },
    '08:10-incremental-historical-update': {
        'task': 'data_collector.historical_tasks.incremental_historical_update',
        'schedule': crontab(minute=10, hour='*/2'),  # 00:10, 02:10, 04:10, 06:10, 08:10, etc.
        'options': {'priority': 8}
    },

    # ========================================================================
    # SESSÕES DE TREINO (Horário: 09:00, a cada 2 horas)
    # ========================================================================
    '09:00-collect-practice-sessions': {
        'task': 'data_collector.tasks.collect_practice_sessions',
        'schedule': crontab(minute=0, hour='*/2'),  # 01:00, 03:00, 05:00, 07:00, 09:00, etc.
        'options': {'priority': 5}
    },

    # ========================================================================
    # CONSOLIDAÇÃO E ML (Horário: 10:00-10:15, a cada 4 horas)
    # ========================================================================
    '10:00-consolidate-data': {
        'task': 'data_collector.consolidation_tasks.consolidate_all_data',
        'schedule': crontab(minute=0, hour='*/4'),  # 00:00, 04:00, 08:00, 12:00, 16:00, 20:00
        'kwargs': {'dry_run': False},
        'options': {'priority': 5}
    },
    '10:15-train-ml-models': {
        'task': 'data_collector.tasks.check_and_train_ml_models',
        'schedule': crontab(minute=15, hour='*/4'),  # 00:15, 04:15, 08:15, 12:15, 16:15, 20:15
        'options': {'priority': 4}
    },

    # ========================================================================
    # MANUTENÇÃO E AUDITORIA (Diária)
    # ========================================================================
    '01:00-daily-audit': {
        'task': 'data_auditor.run_daily_audit',
        'schedule': crontab(hour=1, minute=0),  # Diariamente às 01:00
        'options': {'priority': 3}
    },
    '02:00-calculate-podiums': {
        'task': 'data_collector.historical_tasks.calculate_missing_podiums',
        'schedule': crontab(hour=2, minute=0),  # Diariamente às 02:00
        'options': {'priority': 3}
    },
    '02:30-fix-duplicate-drivers': {
        'task': 'data_collector.historical_tasks.fix_duplicate_driver_records',
        'schedule': crontab(hour=2, minute=30),  # Diariamente às 02:30
        'options': {'priority': 3}
    },
    '02:45-generate-constructor-standings': {
        'task': 'data_collector.historical_tasks.generate_constructor_standings_from_results',
        'schedule': crontab(hour=2, minute=45),  # Diariamente às 02:45
        'options': {'priority': 3}
    },
    '03:00-weekly-maintenance': {
        'task': 'data_collector.tasks.weekly_database_maintenance',
        'schedule': crontab(hour=3, minute=0, day_of_week=0),  # Semanalmente aos domingos às 03:00
        'options': {'priority': 2}
    },
}

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing Celery."""
    print(f'Request: {self.request!r}')
