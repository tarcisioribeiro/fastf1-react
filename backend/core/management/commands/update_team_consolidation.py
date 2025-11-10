"""
Comando Django para atualizar campos de consolidação de equipes de F1.
Preenche: operation_line_id, current_name, display_in_filters, etc.
"""
from django.core.management.base import BaseCommand
from core.models import Team


class Command(BaseCommand):
    help = 'Atualiza campos de consolidação de equipes (operation_line_id, current_name, etc.)'

    # Mapeamento: operation_line_id -> (current_name, [team_ids], [display_ids])
    CONSOLIDATION_MAP = {
        # Equipes Atuais (2025)
        1: ('Ferrari', [1], [1]),
        2: ('Mercedes', [2, 127, 49, 113, 62], [2]),
        3: ('Red Bull Racing', [3, 139, 136, 117], [3]),
        4: ('McLaren', [9], [9]),
        5: ('Alpine F1 Team', [15, 4, 159, 142, 52, 133], [15]),
        6: ('Aston Martin', [12, 11, 5, 119], [12]),
        7: ('Williams', [10], [10]),
        8: ('Haas F1 Team', [109, 6], [6]),  # Manter id: 6
        9: ('Kick Sauber', [13, 16, 19, 20, 8, 54], [13]),
        10: ('Racing Bulls', [18, 14, 17, 7, 131], [18]),
    }

    # Variações de motor
    ENGINE_VARIANTS = [
        'brabham-alfa_romeo', 'brabham-brm', 'brabham-climax',
        'brabham-ford', 'brabham-repco',
        'cooper-alfa_romeo', 'cooper-ats', 'cooper-borgward',
        'cooper-brm', 'cooper-castellotti', 'cooper-climax',
        'cooper-ferrari', 'cooper-ford', 'cooper-maserati', 'cooper-osca',
        'lotus-brm', 'lotus-climax',
        'eagle-climax', 'eagle-weslake',
        'brm-ford',
        'mclaren-ford',
    ]

    # Anos ativos
    YEARS_ACTIVE = {
        1: '1950-present',
        127: '1970-1998', 49: '1999-2005', 113: '2006-2008', 62: '2009', 2: '2010-present',
        136: '1997-1999', 117: '2000-2004', 139: '2005-present', 3: '2005-present',
        9: '1966-present',
        133: '1981-1985', 52: '1986-2001', 4: '2002-2011, 2016-2020', 159: '2012-2015', 142: '2012-2015', 15: '2021-present',
        119: '1991-2005', 5: '2008-2018', 11: '2019-2020', 12: '2021-present',
        10: '1977-present',
        109: '2016-2022', 6: '2016-present',
        8: '1993-2005, 2010-2017', 54: '2006-2009', 16: '2019-2023', 19: '2018-2023', 20: '2018-2023', 13: '2024-present',
        131: '1985-2005', 7: '2006-2019', 17: '2020-2023', 14: '2024', 18: '2025-present',
    }

    # Status
    TEAM_STATUS = {
        1: 'ACTIVE', 2: 'ACTIVE', 3: 'ACTIVE', 9: 'ACTIVE', 15: 'ACTIVE',
        12: 'ACTIVE', 10: 'ACTIVE', 6: 'ACTIVE', 13: 'ACTIVE', 18: 'ACTIVE',
        127: 'RENAMED', 49: 'RENAMED', 113: 'RENAMED', 62: 'RENAMED',
        136: 'RENAMED', 117: 'RENAMED', 139: 'RENAMED',
        133: 'RENAMED', 52: 'RENAMED', 4: 'RENAMED', 159: 'RENAMED', 142: 'RENAMED',
        119: 'RENAMED', 5: 'RENAMED', 11: 'RENAMED',
        109: 'RENAMED',
        8: 'RENAMED', 54: 'RENAMED', 16: 'RENAMED', 19: 'RENAMED', 20: 'RENAMED',
        131: 'RENAMED', 7: 'RENAMED', 17: 'RENAMED', 14: 'RENAMED',
    }

    # Predecessores
    PREDECESSORS = {
        49: 127, 113: 49, 62: 113, 2: 62,
        117: 136, 3: 117,
        52: 133, 4: 52, 15: 4,
        5: 119, 11: 5, 12: 11,
        54: 8, 19: 54, 13: 19,
        7: 131, 17: 7, 14: 17, 18: 14,
    }

    def handle(self, *args, **options):
        self.stdout.write("=" * 80)
        self.stdout.write("ATUALIZANDO CAMPOS DE CONSOLIDAÇÃO")
        self.stdout.write("=" * 80)

        # Fase 1: Consolidar equipes atuais
        self.stdout.write("\n📋 FASE 1: Atualizando equipes atuais")
        self.stdout.write("-" * 80)

        total_updated = 0
        for operation_id, (current_name, team_ids, display_ids) in self.CONSOLIDATION_MAP.items():
            self.stdout.write(f"\n🔹 Operação {operation_id}: {current_name}")

            for team_id in team_ids:
                try:
                    team = Team.objects.get(id=team_id)
                    team.operation_line_id = operation_id
                    team.current_name = current_name
                    team.display_in_filters = (team.id in display_ids)
                    team.years_active = self.YEARS_ACTIVE.get(team.id, '')
                    team.team_status = self.TEAM_STATUS.get(team.id, 'ACTIVE')
                    team.save()
                    total_updated += 1

                    status = "✅ EXIBIR" if team.display_in_filters else "🔇 OCULTAR"
                    self.stdout.write(f"   {status} - {team.name} (id: {team.id})")

                except Team.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f"   ⚠️  Team id {team_id} não encontrada"))

        # Fase 2: Marcar variações de motor
        self.stdout.write("\n\n📋 FASE 2: Marcando variações de motor")
        self.stdout.write("-" * 80)

        engine_count = 0
        for team_id in self.ENGINE_VARIANTS:
            teams = Team.objects.filter(team_id=team_id)
            if teams.exists():
                teams.update(is_engine_variant=True, display_in_filters=False, team_status='RENAMED')
                for team in teams:
                    self.stdout.write(f"   🔧 {team.name} (id: {team.id})")
                    engine_count += 1

        # Fase 3: Configurar predecessores
        self.stdout.write("\n\n📋 FASE 3: Configurando predecessores")
        self.stdout.write("-" * 80)

        predecessor_count = 0
        for team_id, predecessor_id in self.PREDECESSORS.items():
            try:
                team = Team.objects.get(id=team_id)
                predecessor = Team.objects.get(id=predecessor_id)
                team.predecessor = predecessor
                team.save()
                predecessor_count += 1
                self.stdout.write(f"   ➡️  {predecessor.name} → {team.name}")
            except Team.DoesNotExist:
                pass

        # Estatísticas
        self.stdout.write("\n\n" + "=" * 80)
        self.stdout.write("📊 RESUMO")
        self.stdout.write("=" * 80)

        visible_teams = Team.objects.filter(display_in_filters=True).count()
        self.stdout.write(f"\n✅ Equipes consolidadas: {total_updated}")
        self.stdout.write(f"✅ Variações de motor: {engine_count}")
        self.stdout.write(f"✅ Predecessores configurados: {predecessor_count}")
        self.stdout.write(f"👁️  Equipes visíveis nos filtros: {visible_teams}")

        # Listar equipes visíveis
        self.stdout.write("\n\n📋 EQUIPES NOS FILTROS:")
        self.stdout.write("-" * 80)

        for idx, team in enumerate(Team.objects.filter(display_in_filters=True).order_by('current_name'), 1):
            operation_count = Team.objects.filter(operation_line_id=team.operation_line_id).count()
            self.stdout.write(f"{idx:2d}. {team.current_name:25s} (variações: {operation_count})")

        self.stdout.write("\n" + "=" * 80)
        self.stdout.write(self.style.SUCCESS("✅ ATUALIZAÇÃO CONCLUÍDA!"))
        self.stdout.write("=" * 80 + "\n")
