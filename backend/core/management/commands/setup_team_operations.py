"""
Management command para configurar linhas de operação de equipes.
Analisa e agrupa equipes por linha sucessória/operação.
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import Team


class Command(BaseCommand):
    help = 'Configura linhas de operação e sucessão de equipes F1'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Executar em modo dry-run (não salvar alterações)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('CONFIGURAÇÃO DE LINHAS DE OPERAÇÃO DE EQUIPES F1'))
        self.stdout.write(self.style.SUCCESS('=' * 80))

        if dry_run:
            self.stdout.write(self.style.WARNING('\n⚠️  MODO DRY-RUN - Nenhuma alteração será salva\n'))

        # Definição completa de linhas de operação
        # Cada operação tem um ID único e lista de nomes históricos
        operation_lines = {
            # EQUIPES ATIVAS (2024-2025)

            1: {  # Red Bull Racing
                'current_name': 'Red Bull Racing',
                'names': [
                    'Red Bull Racing',
                    'Red Bull',
                    'Jaguar Racing',
                    'Jaguar',
                    'Stewart Grand Prix',
                    'Stewart',
                    'Stewart-Ford',
                ],
                'years': '1997-presente',
                'status': 'ACTIVE',
            },

            2: {  # Mercedes
                'current_name': 'Mercedes',
                'names': [
                    'Mercedes',
                    'Mercedes-AMG Petronas',
                    'Mercedes AMG Petronas',
                    'Mercedes GP',
                    'Mercedes-Benz',
                    'Brawn GP',
                    'Brawn',
                    'Honda Racing F1',
                    'Honda Racing',
                    'Honda',
                    'British American Racing',
                    'BAR',
                    'BAR-Honda',
                    'Lucky Strike BAR',
                    'Tyrrell Racing',
                    'Tyrrell',
                ],
                'years': '1970-presente',
                'status': 'ACTIVE',
            },

            3: {  # Ferrari
                'current_name': 'Ferrari',
                'names': [
                    'Ferrari',
                    'Scuderia Ferrari',
                    'Scuderia Ferrari HP',
                    'Scuderia Ferrari Mission Winnow',
                    'Ferrari Marlboro',
                ],
                'years': '1950-presente',
                'status': 'ACTIVE',
            },

            4: {  # McLaren
                'current_name': 'McLaren',
                'names': [
                    'McLaren',
                    'McLaren F1 Team',
                    'McLaren Racing',
                    'McLaren Mercedes',
                    'McLaren-Mercedes',
                    'Vodafone McLaren Mercedes',
                    'West McLaren Mercedes',
                    'Marlboro McLaren',
                    'McLaren-Ford',
                    'McLaren-BRM',
                    'McLaren-Serenissima',
                ],
                'years': '1966-presente',
                'status': 'ACTIVE',
            },

            5: {  # Alpine (Renault)
                'current_name': 'Alpine F1 Team',
                'names': [
                    'Alpine F1 Team',
                    'Alpine',
                    'Renault F1 Team',
                    'Renault',
                    'Renault F1',
                    'ING Renault F1',
                    'Mild Seven Renault F1',
                    'Lotus F1 Team',
                    'Lotus F1',
                    'Lotus',
                    'Benetton Formula',
                    'Benetton',
                    'Mild Seven Benetton',
                    'Toleman Group Motorsport',
                    'Toleman',
                ],
                'years': '1981-presente',
                'status': 'ACTIVE',
            },

            6: {  # Aston Martin
                'current_name': 'Aston Martin',
                'names': [
                    'Aston Martin',
                    'Aston Martin Aramco',
                    'Aston Martin Cognizant',
                    'Racing Point F1 Team',
                    'Racing Point',
                    'SportPesa Racing Point',
                    'BWT Racing Point',
                    'Force India',
                    'Sahara Force India',
                    'Kingfisher Force India',
                    'Spyker F1 Team',
                    'Spyker',
                    'Midland F1 Racing',
                    'Midland',
                    'Jordan Grand Prix',
                    'Jordan',
                    'Benson & Hedges Jordan',
                ],
                'years': '1991-presente',
                'status': 'ACTIVE',
            },

            7: {  # Williams
                'current_name': 'Williams',
                'names': [
                    'Williams',
                    'Williams F1',
                    'Williams Racing',
                    'Williams Grand Prix Engineering',
                    'AT&T Williams',
                    'Rothmans Williams',
                    'Canon Williams',
                ],
                'years': '1975-presente',
                'status': 'ACTIVE',
            },

            8: {  # Racing Bulls (ex-Toro Rosso, ex-Minardi)
                'current_name': 'Racing Bulls',
                'names': [
                    'Racing Bulls',
                    'RB F1 Team',
                    'RB',
                    'Scuderia AlphaTauri',
                    'AlphaTauri',
                    'Scuderia Toro Rosso',
                    'Toro Rosso',
                    'STR',
                    'Minardi F1',
                    'Minardi',
                    'European Minardi',
                ],
                'years': '1985-presente',
                'status': 'ACTIVE',
            },

            9: {  # Kick Sauber (ex-Alfa Romeo, ex-Sauber)
                'current_name': 'Kick Sauber',
                'names': [
                    'Kick Sauber',
                    'Stake F1 Team',
                    'Alfa Romeo Racing ORLEN',
                    'Alfa Romeo Racing',
                    'Alfa Romeo',
                    'Sauber F1 Team',
                    'Sauber',
                    'BMW Sauber F1 Team',
                    'BMW Sauber',
                    'Alfa Romeo Racing',  # Faltava este!
                ],
                'years': '1993-presente',
                'status': 'ACTIVE',
            },

            10: {  # Haas
                'current_name': 'Haas F1 Team',
                'names': [
                    'Haas F1 Team',
                    'Haas',
                    'MoneyGram Haas F1 Team',
                    'Uralkali Haas F1 Team',
                    'Rich Energy Haas F1 Team',
                ],
                'years': '2016-presente',
                'status': 'ACTIVE',
            },

            # EQUIPES HISTÓRICAS EXTINTAS

            20: {  # Brabham
                'current_name': 'Brabham',
                'names': [
                    'Brabham',
                    'Brabham Racing Organisation',
                    'Motor Racing Developments',
                    'MRD',
                    'Brabham-Repco',
                    'Brabham-Ford',
                    'Brabham-Alfa Romeo',
                    'Brabham-BMW',
                    'Brabham-Climax',
                ],
                'years': '1962-1992',
                'status': 'EXTINCT',
            },

            21: {  # Cooper
                'current_name': 'Cooper',
                'names': [
                    'Cooper',
                    'Cooper Car Company',
                    'Cooper-Climax',
                    'Cooper-Maserati',
                    'Cooper-BRM',
                ],
                'years': '1950-1969',
                'status': 'EXTINCT',
            },

            22: {  # Team Lotus (original)
                'current_name': 'Team Lotus',
                'names': [
                    'Team Lotus',
                    'Lotus-Climax',
                    'Lotus-Ford',
                    'Lotus-Renault',
                    'Team Lotus-Honda',
                    'Team Lotus-Judd',
                    'Team Lotus-Mugen',
                    'Lotus-BRM',
                    'Lotus-Borgward',
                ],
                'years': '1958-1994',
                'status': 'EXTINCT',
            },

            23: {  # BRM
                'current_name': 'BRM',
                'names': [
                    'BRM',
                    'British Racing Motors',
                    'Owen Racing Organisation',
                    'Stanley-BRM',
                ],
                'years': '1951-1977',
                'status': 'EXTINCT',
            },

            24: {  # Matra
                'current_name': 'Matra',
                'names': [
                    'Matra',
                    'Matra Sports',
                    'Matra International',
                    'Equipe Matra',
                ],
                'years': '1965-1972',
                'status': 'EXTINCT',
            },

            25: {  # March
                'current_name': 'March',
                'names': [
                    'March',
                    'March Engineering',
                    'March-Ford',
                    'March-Cosworth',
                ],
                'years': '1970-1992',
                'status': 'EXTINCT',
            },

            26: {  # Arrows
                'current_name': 'Arrows',
                'names': [
                    'Arrows',
                    'Arrows Grand Prix International',
                    'Arrows Racing',
                    'Footwork Arrows',
                    'Footwork',
                ],
                'years': '1978-2002',
                'status': 'EXTINCT',
            },

            27: {  # Ligier
                'current_name': 'Ligier',
                'names': [
                    'Ligier',
                    'Equipe Ligier',
                    'Ligier-Renault',
                    'Ligier-Mugen',
                ],
                'years': '1976-1996',
                'status': 'EXTINCT',
            },

            28: {  # Prost
                'current_name': 'Prost Grand Prix',
                'names': [
                    'Prost Grand Prix',
                    'Prost',
                    'Prost-Peugeot',
                    'Prost-Acer',
                ],
                'years': '1997-2001',
                'status': 'EXTINCT',
            },

            29: {  # Shadow
                'current_name': 'Shadow',
                'names': [
                    'Shadow',
                    'Shadow Racing Cars',
                    'UOP Shadow Racing Team',
                    'Shadow-Ford',
                    'Shadow-Matra',
                ],
                'years': '1973-1980',
                'status': 'EXTINCT',
            },

            # EQUIPES HISTÓRICAS FAMOSAS (EXTINTAS)

            30: {  # Maserati
                'current_name': 'Maserati',
                'names': [
                    'Maserati',
                    'Officine Alfieri Maserati',
                ],
                'years': '1950-1958',
                'status': 'EXTINCT',
            },

            31: {  # Surtees
                'current_name': 'Surtees',
                'names': [
                    'Surtees',
                    'Team Surtees',
                    'Surtees Racing Organisation',
                ],
                'years': '1970-1978',
                'status': 'EXTINCT',
            },

            32: {  # Lola
                'current_name': 'Lola',
                'names': [
                    'Lola',
                    'Lola Cars',
                    'Lola-Climax',
                    'Lola-BRM',
                    'Lola-Ford',
                ],
                'years': '1962-1997',
                'status': 'EXTINCT',
            },

            33: {  # Gordini
                'current_name': 'Gordini',
                'names': [
                    'Gordini',
                    'Equipe Gordini',
                ],
                'years': '1950-1956',
                'status': 'EXTINCT',
            },

            34: {  # Osella
                'current_name': 'Osella',
                'names': [
                    'Osella',
                    'Osella Squadra Corse',
                    'Osella-Alfa Romeo',
                ],
                'years': '1980-1990',
                'status': 'EXTINCT',
            },

            35: {  # ATS
                'current_name': 'ATS',
                'names': [
                    'ATS',
                    'Automobili Turismo e Sport',
                ],
                'years': '1977-1984',
                'status': 'EXTINCT',
            },

            36: {  # Hesketh
                'current_name': 'Hesketh',
                'names': [
                    'Hesketh',
                    'Hesketh Racing',
                ],
                'years': '1974-1978',
                'status': 'EXTINCT',
            },

            37: {  # Ensign
                'current_name': 'Ensign',
                'names': [
                    'Ensign',
                    'Ensign Racing',
                ],
                'years': '1973-1982',
                'status': 'EXTINCT',
            },

            38: {  # Talbot-Lago
                'current_name': 'Talbot-Lago',
                'names': [
                    'Talbot-Lago',
                    'Talbot',
                ],
                'years': '1950-1951',
                'status': 'EXTINCT',
            },

            39: {  # Vanwall
                'current_name': 'Vanwall',
                'names': [
                    'Vanwall',
                    'Vandervell Products',
                ],
                'years': '1954-1960',
                'status': 'EXTINCT',
            },

            40: {  # Connaught
                'current_name': 'Connaught',
                'names': [
                    'Connaught',
                    'Connaught Engineering',
                ],
                'years': '1952-1959',
                'status': 'EXTINCT',
            },

            41: {  # Kurtis Kraft
                'current_name': 'Kurtis Kraft',
                'names': [
                    'Kurtis Kraft',
                ],
                'years': '1950-1960',
                'status': 'EXTINCT',
            },

            42: {  # Wolf
                'current_name': 'Wolf',
                'names': [
                    'Wolf',
                    'Walter Wolf Racing',
                ],
                'years': '1977-1979',
                'status': 'EXTINCT',
            },

            43: {  # Larrousse
                'current_name': 'Larrousse',
                'names': [
                    'Larrousse',
                    'Larrousse F1',
                    'Équipe Larrousse',
                ],
                'years': '1987-1994',
                'status': 'EXTINCT',
            },

            44: {  # Leyton House (ex-March)
                'current_name': 'Leyton House',
                'names': [
                    'Leyton House',
                    'Leyton House Racing',
                ],
                'years': '1990-1991',
                'status': 'EXTINCT',
            },

            45: {  # Penske
                'current_name': 'Penske',
                'names': [
                    'Penske',
                    'Penske Racing',
                ],
                'years': '1974-1976',
                'status': 'EXTINCT',
            },

            46: {  # Eagle (Dan Gurney)
                'current_name': 'Eagle',
                'names': [
                    'Eagle',
                    'All American Racers',
                    'Eagle-Weslake',
                    'Eagle-Climax',
                ],
                'years': '1966-1969',
                'status': 'EXTINCT',
            },

            47: {  # Pacific
                'current_name': 'Pacific',
                'names': [
                    'Pacific',
                    'Pacific Grand Prix',
                ],
                'years': '1994-1995',
                'status': 'EXTINCT',
            },

            48: {  # Forti
                'current_name': 'Forti',
                'names': [
                    'Forti',
                    'Forti Corse',
                ],
                'years': '1995-1996',
                'status': 'EXTINCT',
            },

            49: {  # Zakspeed
                'current_name': 'Zakspeed',
                'names': [
                    'Zakspeed',
                ],
                'years': '1985-1989',
                'status': 'EXTINCT',
            },

            50: {  # Porsche
                'current_name': 'Porsche',
                'names': [
                    'Porsche',
                ],
                'years': '1961-1962',
                'status': 'EXTINCT',
            },
        }

        self.stdout.write(f'\n📊 Total de linhas de operação definidas: {len(operation_lines)}\n')

        # Estatísticas
        stats = {
            'processed': 0,
            'updated': 0,
            'not_found': 0,
            'active_operations': 0,
            'extinct_operations': 0,
        }

        with transaction.atomic():
            # Primeiro, resetar todos os campos para garantir estado limpo
            if not dry_run:
                Team.objects.all().update(
                    operation_line_id=None,
                    current_name='',
                    display_in_filters=True,
                    team_status='ACTIVE'
                )

            # Processar cada linha de operação
            for operation_id, operation_data in operation_lines.items():
                current_name = operation_data['current_name']
                names = operation_data['names']
                years = operation_data['years']
                status = operation_data['status']

                self.stdout.write(f'\n🔍 Processando operação {operation_id}: {current_name}')
                self.stdout.write(f'   Anos: {years}')
                self.stdout.write(f'   Status: {status}')
                self.stdout.write(f'   Nomes históricos: {len(names)}')

                # Contar operações por status
                if status == 'ACTIVE':
                    stats['active_operations'] += 1
                else:
                    stats['extinct_operations'] += 1

                # Encontrar todas as equipes que correspondem a esta operação
                teams_in_operation = Team.objects.filter(name__in=names)

                if not teams_in_operation.exists():
                    self.stdout.write(self.style.WARNING(f'   ⚠️  Nenhuma equipe encontrada para: {current_name}'))
                    stats['not_found'] += 1
                    continue

                self.stdout.write(f'   ✅ Encontradas {teams_in_operation.count()} equipes no banco')

                # Encontrar a equipe com MAIS DADOS para ser a visível
                # (não necessariamente o nome "atual", pois pode ser um registro vazio)
                from core.models import RaceResult, QualifyingResult

                teams_with_data = []
                for team in teams_in_operation:
                    race_count = RaceResult.objects.filter(team=team).count()
                    quali_count = QualifyingResult.objects.filter(team=team).count()
                    total_data = race_count + quali_count
                    teams_with_data.append((team, total_data))

                # Ordenar por quantidade de dados (mais dados primeiro)
                teams_with_data.sort(key=lambda x: x[1], reverse=True)

                # A equipe visível será a que tem mais dados
                # Se nenhuma tiver dados, usar a com o nome atual
                representative_team = None
                if teams_with_data and teams_with_data[0][1] > 0:
                    representative_team = teams_with_data[0][0]
                else:
                    # Fallback: usar equipe com nome atual
                    representative_team = teams_in_operation.filter(name=current_name).first()
                    if not representative_team:
                        representative_team = teams_in_operation.first()

                # Atualizar todas as equipes desta operação
                for team in teams_in_operation:
                    stats['processed'] += 1

                    # Determinar se deve aparecer no filtro
                    # Apenas a equipe representativa (com mais dados) deve aparecer
                    should_display = (team.id == representative_team.id) if representative_team else False

                    # Mostrar quantidade de dados para debug
                    team_data_count = next((count for t, count in teams_with_data if t.id == team.id), 0)

                    if not dry_run:
                        team.operation_line_id = operation_id
                        team.current_name = current_name
                        team.display_in_filters = should_display
                        team.team_status = status
                        team.years_active = years
                        team.save()
                        stats['updated'] += 1

                    display_marker = '👁️ ' if should_display else '  '
                    self.stdout.write(f'      {display_marker} {team.name:40s} (ID: {team.id:3d}) - {team_data_count:4d} resultados')

            if dry_run:
                self.stdout.write(self.style.WARNING('\n⚠️  DRY-RUN: Nenhuma alteração foi salva (transaction rollback)'))
                transaction.set_rollback(True)
            else:
                self.stdout.write(self.style.SUCCESS('\n✅ Alterações salvas com sucesso!'))

        # Relatório final
        self.stdout.write('\n' + '=' * 80)
        self.stdout.write(self.style.SUCCESS('RELATÓRIO FINAL'))
        self.stdout.write('=' * 80)
        self.stdout.write(f'Operações ativas: {stats["active_operations"]}')
        self.stdout.write(f'Operações extintas: {stats["extinct_operations"]}')
        self.stdout.write(f'Equipes processadas: {stats["processed"]}')
        self.stdout.write(f'Equipes atualizadas: {stats["updated"]}')
        self.stdout.write(f'Operações não encontradas: {stats["not_found"]}')

        if not dry_run:
            # Mostrar quantas equipes ficarão visíveis no filtro
            visible_teams = Team.objects.filter(display_in_filters=True).count()
            self.stdout.write(f'\n👁️  Equipes visíveis no filtro: {visible_teams}')
            self.stdout.write(f'🔒 Equipes ocultas (históricas): {Team.objects.filter(display_in_filters=False).count()}')

        self.stdout.write('\n' + '=' * 80)
        self.stdout.write(self.style.SUCCESS('✅ CONFIGURAÇÃO CONCLUÍDA!'))
        self.stdout.write('=' * 80)
