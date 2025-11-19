"""
Django management command para recalcular pódios nas classificações.

Este comando força o recálculo de TODOS os pódios (posições 1, 2 e 3)
nas classificações de pilotos e construtores, corrigindo dados incorretos
ou inconsistentes.

Uso:
    python manage.py recalculate_podiums
"""
from django.core.management.base import BaseCommand
from django.db.models import Q
from core.models import DriverStanding, ConstructorStanding, RaceResult
import logging


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Recalcula TODOS os pódios nas classificações de pilotos e construtores'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Executa em modo dry-run (sem salvar alterações)',
        )
        parser.add_argument(
            '--year',
            type=int,
            help='Recalcula apenas para um ano específico',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Exibe detalhes de cada atualização',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        year = options.get('year')
        verbose = options['verbose']

        self.stdout.write(self.style.SUCCESS('=' * 80))
        if dry_run:
            self.stdout.write(self.style.WARNING('MODO DRY-RUN: Nenhuma alteração será salva'))
        self.stdout.write(self.style.SUCCESS('Recalculando TODOS os pódios nas classificações...'))
        self.stdout.write(self.style.SUCCESS('=' * 80))

        updated_driver_standings = 0
        updated_constructor_standings = 0
        total_driver_standings = 0
        total_constructor_standings = 0

        try:
            # ==================== PILOTOS ====================
            self.stdout.write(self.style.HTTP_INFO('\n[PILOTOS]'))

            # Filtrar por ano se especificado
            driver_standings = DriverStanding.objects.all().select_related('driver', 'season', 'event')
            if year:
                driver_standings = driver_standings.filter(season__year=year)

            total_driver_standings = driver_standings.count()
            self.stdout.write(f'Processando {total_driver_standings} classificações de pilotos...')

            for i, standing in enumerate(driver_standings, 1):
                # Contar pódios até este evento (posições 1, 2 ou 3 em corridas)
                podiums = RaceResult.objects.filter(
                    driver=standing.driver,
                    session__event__season=standing.season,
                    session__event__round_number__lte=standing.event.round_number,
                    session__session_type='R',
                    position__in=[1, 2, 3]
                ).count()

                # Atualizar se o valor for diferente
                if standing.podiums != podiums:
                    old_value = standing.podiums

                    if not dry_run:
                        standing.podiums = podiums
                        standing.save()

                    updated_driver_standings += 1

                    if verbose or updated_driver_standings <= 20:
                        status_text = f'  [{i}/{total_driver_standings}] {standing.driver} '
                        status_text += f'({standing.season.year} R{standing.event.round_number}): '
                        status_text += f'{old_value} -> {podiums} pódios'

                        if dry_run:
                            self.stdout.write(self.style.WARNING(status_text + ' [DRY-RUN]'))
                        else:
                            self.stdout.write(self.style.SUCCESS(status_text))

                # Log de progresso a cada 100 standings
                if i % 100 == 0:
                    self.stdout.write(
                        f'  Progresso: {i}/{total_driver_standings} '
                        f'({updated_driver_standings} atualizados)'
                    )

            self.stdout.write(
                self.style.SUCCESS(
                    f'\nPilotos: {total_driver_standings} processados, '
                    f'{updated_driver_standings} atualizados'
                )
            )

            # ==================== CONSTRUTORES ====================
            self.stdout.write(self.style.HTTP_INFO('\n[CONSTRUTORES]'))

            # Filtrar por ano se especificado
            constructor_standings = ConstructorStanding.objects.all().select_related('team', 'season', 'event')
            if year:
                constructor_standings = constructor_standings.filter(season__year=year)

            total_constructor_standings = constructor_standings.count()
            self.stdout.write(f'Processando {total_constructor_standings} classificações de construtores...')

            for i, standing in enumerate(constructor_standings, 1):
                # Contar pódios até este evento (posições 1, 2 ou 3 em corridas)
                podiums = RaceResult.objects.filter(
                    team=standing.team,
                    session__event__season=standing.season,
                    session__event__round_number__lte=standing.event.round_number,
                    session__session_type='R',
                    position__in=[1, 2, 3]
                ).count()

                # Atualizar se o valor for diferente
                if standing.podiums != podiums:
                    old_value = standing.podiums

                    if not dry_run:
                        standing.podiums = podiums
                        standing.save()

                    updated_constructor_standings += 1

                    if verbose or updated_constructor_standings <= 20:
                        status_text = f'  [{i}/{total_constructor_standings}] {standing.team.name} '
                        status_text += f'({standing.season.year} R{standing.event.round_number}): '
                        status_text += f'{old_value} -> {podiums} pódios'

                        if dry_run:
                            self.stdout.write(self.style.WARNING(status_text + ' [DRY-RUN]'))
                        else:
                            self.stdout.write(self.style.SUCCESS(status_text))

                # Log de progresso a cada 100 standings
                if i % 100 == 0:
                    self.stdout.write(
                        f'  Progresso: {i}/{total_constructor_standings} '
                        f'({updated_constructor_standings} atualizados)'
                    )

            self.stdout.write(
                self.style.SUCCESS(
                    f'\nConstrutores: {total_constructor_standings} processados, '
                    f'{updated_constructor_standings} atualizados'
                )
            )

            # ==================== RESUMO ====================
            self.stdout.write(self.style.SUCCESS('\n' + '=' * 80))
            if dry_run:
                self.stdout.write(self.style.WARNING('RECÁLCULO CONCLUÍDO (DRY-RUN)!'))
            else:
                self.stdout.write(self.style.SUCCESS('RECÁLCULO CONCLUÍDO!'))
            self.stdout.write(
                self.style.SUCCESS(
                    f'Total processado: {total_driver_standings + total_constructor_standings}'
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f'Total atualizado: {updated_driver_standings + updated_constructor_standings}'
                )
            )
            self.stdout.write(self.style.SUCCESS('=' * 80))

            if dry_run:
                self.stdout.write(
                    self.style.WARNING(
                        '\nNenhuma alteração foi salva (modo dry-run). '
                        'Execute sem --dry-run para aplicar as mudanças.'
                    )
                )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\nErro ao recalcular pódios: {e}'))
            logger.error(f'Erro ao recalcular pódios: {e}', exc_info=True)
            raise
