"""
Management command para sincronizar descrições de tarefas Celery.

Este comando atualiza as descrições das tarefas periódicas no banco de dados
do django-celery-beat com as descrições definidas nos decorators @shared_task.
"""
from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask
from celery import current_app


# Mapeamento de tarefas para descrições
TASK_DESCRIPTIONS = {
    'data_collector.tasks.collect_session_data': 'Coleta dados de uma sessão específica (corrida, qualifying, sprint ou treino livre)',
    'data_collector.tasks.collect_all_race_data': 'Coleta dados de todas as corridas desde 2018 até o ano atual',
    'data_collector.tasks.collect_all_qualifying_data': 'Coleta dados de todos os qualifyings desde 2018 até o ano atual',
    'data_collector.tasks.collect_all_sprint_data': 'Coleta dados de todas as corridas sprint desde 2021 até o ano atual',
    'data_collector.tasks.collect_all_standings_data': 'Calcula e salva as classificações de pilotos e construtores baseado nos resultados de corridas e sprints',
    'data_collector.tasks.collect_tyre_data': 'Coleta dados de estratégias de pneus desde 2025',
    'data_collector.tasks.collect_latest_season_data': 'Coleta dados da última corrida da temporada atual para manter os dados atualizados',
    'data_collector.tasks.collect_season_metadata': 'Coleta e atualiza metadados de temporadas, eventos e circuitos (calendário da F1)',
    'data_collector.tasks.collect_team_and_driver_data': 'Coleta e atualiza informações de equipes e pilotos ativos',
    'data_collector.tasks.collect_practice_sessions': 'Coleta dados das sessões de treinos livres (FP1, FP2, FP3) dos últimos eventos',
    'data_collector.tasks.start_all_data_collection': 'Inicia todas as tarefas de coleta de dados em paralelo (ponto de entrada principal)',
    'data_collector.tasks.refresh_cache_hourly': 'Atualiza o cache com dados mais recentes da temporada atual (corridas, qualifyings, sprints e classificações)',
    'data_collector.tasks.train_ml_models': 'Treina ou atualiza modelos de Machine Learning para previsões de tempo de volta e posições',
    'data_collector.tasks.train_ml_models_from_scratch': 'Treina modelos de Machine Learning do zero (treinamento completo, não incremental)',
    'data_collector.tasks.update_ml_models': 'Atualiza modelos de Machine Learning incrementalmente com novos dados',
    'data_collector.tasks.check_and_train_ml_models': 'Verifica se os modelos de ML existem e os treina se necessário',
    'data_collector.tasks.clean_database_duplicates': 'Detecta e remove registros duplicados do banco de dados',
    'data_collector.tasks.weekly_database_maintenance': 'Executa manutenção semanal do banco de dados (limpeza de duplicatas, otimização e relatório)',

    # Tarefas de consolidação
    'data_collector.consolidation_tasks.consolidate_all_data': 'Consolida dados de equipes e pilotos, unificando registros duplicados',

    # Tarefas de auditoria
    'data_auditor.run_daily_audit': 'Executa auditoria diária dos dados para identificar campos vazios e sugerir preenchimentos',
}


class Command(BaseCommand):
    help = 'Sincroniza descrições das tarefas Celery com o banco de dados do django-celery-beat'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Apenas mostra o que seria atualizado sem fazer alterações',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('Modo dry-run: nenhuma alteração será feita'))
            self.stdout.write('')

        updated_count = 0
        not_found_count = 0

        # Atualizar descrições de tarefas periódicas existentes
        for task_name, description in TASK_DESCRIPTIONS.items():
            try:
                # Buscar tarefas que correspondem ao nome da task
                tasks = PeriodicTask.objects.filter(task=task_name)

                if not tasks.exists():
                    self.stdout.write(
                        self.style.WARNING(f'⚠ Tarefa não encontrada no DB: {task_name}')
                    )
                    not_found_count += 1
                    continue

                for task in tasks:
                    old_description = task.description or '(vazio)'

                    if task.description != description:
                        if not dry_run:
                            task.description = description
                            task.save(update_fields=['description'])

                        self.stdout.write(
                            self.style.SUCCESS(f'✓ Atualizada: {task.name}')
                        )
                        self.stdout.write(f'  Task: {task_name}')
                        self.stdout.write(f'  Descrição antiga: {old_description}')
                        self.stdout.write(f'  Descrição nova: {description}')
                        self.stdout.write('')
                        updated_count += 1
                    else:
                        self.stdout.write(
                            self.style.SUCCESS(f'✓ Já atualizada: {task.name}')
                        )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Erro ao atualizar {task_name}: {str(e)}')
                )

        # Resumo
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('RESUMO'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(f'Tarefas atualizadas: {updated_count}')
        self.stdout.write(f'Tarefas não encontradas no DB: {not_found_count}')

        if dry_run:
            self.stdout.write('')
            self.stdout.write(
                self.style.WARNING('Execute sem --dry-run para aplicar as alterações')
            )
        else:
            self.stdout.write('')
            self.stdout.write(
                self.style.SUCCESS('✓ Descrições sincronizadas com sucesso!')
            )
