# -*- coding: utf-8 -*-
"""
Management command para consolidar nomes de equipes históricas.

Este comando:
1. Atualiza o campo canonical_name de todas as equipes usando o TEAM_CONSOLIDATION_MAP
2. Garante que equipes com sucessões históricas sejam consolidadas sob o mesmo nome canônico

Exemplos de consolidação:
- Jaguar, Stewart → Red Bull Racing
- Brawn GP, Honda, BAR, Tyrrell → Mercedes
- Benetton, Toleman → Alpine

Uso:
    python manage.py consolidate_teams --dry-run  # Apenas reporta, não atualiza
    python manage.py consolidate_teams --apply    # Aplica as consolidações
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q

from core.models import Team, RaceResult, QualifyingResult, SprintResult


class Command(BaseCommand):
    help = 'Consolida nomes históricos de equipes usando o TEAM_CONSOLIDATION_MAP'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Apenas reporta consolidações sem aplicar',
        )
        parser.add_argument(
            '--apply',
            action='store_true',
            help='Aplica as consolidações no banco de dados',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Exibe informações detalhadas',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        apply = options['apply']
        verbose = options['verbose']

        if not dry_run and not apply:
            self.stdout.write(
                self.style.WARNING(
                    'Use --dry-run para reportar ou --apply para aplicar consolidações'
                )
            )
            return

        self.stdout.write(self.style.SUCCESS('=== Consolidação de Equipes Históricas ===\n'))
        self.stdout.write('Mapeamento de consolidação:')
        for canonical, aliases in Team.TEAM_CONSOLIDATION_MAP.items():
            self.stdout.write(f'  {canonical}:')
            for alias in aliases:
                self.stdout.write(f'    - {alias}')
        self.stdout.write('')

        # Estatísticas
        teams_updated = 0
        teams_already_consolidated = 0
        teams_no_consolidation = 0

        # Buscar todas as equipes
        all_teams = Team.objects.all().order_by('name')
        total_teams = all_teams.count()

        self.stdout.write(f'\nAnalisando {total_teams} equipes...\n')

        for team in all_teams:
            canonical = Team.get_canonical_name(team.name)

            # Verificar se precisa atualizar
            if team.canonical_name == canonical:
                teams_already_consolidated += 1
                if verbose:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  ✓ {team.name} já consolidado como {canonical}'
                        )
                    )
                continue

            # Verificar se há consolidação para esta equipe
            if canonical == team.name and canonical not in Team.TEAM_CONSOLIDATION_MAP:
                # Nenhuma consolidação definida para esta equipe
                teams_no_consolidation += 1
                if verbose:
                    self.stdout.write(
                        f'  - {team.name} (sem consolidação definida)'
                    )
                continue

            # Equipe precisa ser consolidada
            teams_updated += 1
            self.stdout.write(
                self.style.WARNING(
                    f'  → {team.name} será consolidado como {canonical}'
                )
            )

            if apply:
                team.canonical_name = canonical
                team.save(update_fields=['canonical_name'])
                self.stdout.write(
                    self.style.SUCCESS(
                        f'    ✓ Atualizado no banco de dados'
                    )
                )

        # Resumo
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('\n=== Resumo da Consolidação ==='))
        self.stdout.write(f'Total de equipes: {total_teams}')
        self.stdout.write(
            self.style.SUCCESS(f'Já consolidadas: {teams_already_consolidated}')
        )
        self.stdout.write(f'Sem consolidação definida: {teams_no_consolidation}')

        if teams_updated > 0:
            self.stdout.write(
                self.style.WARNING(f'Precisam ser consolidadas: {teams_updated}')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Precisam ser consolidadas: {teams_updated}')
            )

        if apply:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✓ Consolidação aplicada com sucesso! '
                    f'{teams_updated} equipes atualizadas.'
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    f'\nModo dry-run: nenhuma alteração foi feita.'
                    f'\nUse --apply para aplicar as consolidações.'
                )
            )

        # Análise de dados históricos
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('\n=== Análise de Impacto nos Dados Históricos ==='))

        self._analyze_historical_impact(verbose)

    def _analyze_historical_impact(self, verbose):
        """Analisa quantos registros históricos serão afetados pela consolidação."""

        # Contar resultados por equipe
        teams_with_data = {}

        for canonical, aliases in Team.TEAM_CONSOLIDATION_MAP.items():
            # Buscar equipes que fazem parte desta linhagem
            all_names = [canonical] + aliases
            teams = Team.objects.filter(name__in=all_names)

            if not teams.exists():
                continue

            # Contar resultados
            race_count = RaceResult.objects.filter(team__in=teams).count()
            quali_count = QualifyingResult.objects.filter(team__in=teams).count()
            sprint_count = SprintResult.objects.filter(team__in=teams).count()
            total = race_count + quali_count + sprint_count

            if total > 0:
                teams_with_data[canonical] = {
                    'teams': [t.name for t in teams],
                    'race_results': race_count,
                    'quali_results': quali_count,
                    'sprint_results': sprint_count,
                    'total': total,
                }

        if not teams_with_data:
            self.stdout.write(
                self.style.WARNING(
                    'Nenhum dado histórico encontrado para as equipes mapeadas.'
                )
            )
            return

        # Exibir por equipe consolidada
        for canonical, data in sorted(teams_with_data.items(), key=lambda x: x[1]['total'], reverse=True):
            self.stdout.write(f'\n{canonical}:')
            self.stdout.write(f'  Equipes na linhagem: {", ".join(data["teams"])}')
            self.stdout.write(f'  Resultados de corrida: {data["race_results"]}')
            self.stdout.write(f'  Resultados de qualifying: {data["quali_results"]}')
            self.stdout.write(f'  Resultados de sprint: {data["sprint_results"]}')
            self.stdout.write(
                self.style.SUCCESS(f'  Total de registros: {data["total"]}')
            )

        # Total geral
        total_consolidated = sum(d['total'] for d in teams_with_data.values())
        self.stdout.write('\n' + '-' * 60)
        self.stdout.write(
            self.style.SUCCESS(
                f'Total de registros históricos consolidados: {total_consolidated:,}'
            )
        )
