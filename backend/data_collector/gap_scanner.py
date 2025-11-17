"""
Script de varredura para identificar dados históricos faltantes.
Identifica gaps (lacunas) de dados de 1950 até o ano atual.
"""
import logging
from typing import List, Dict
from django.db import transaction
from django.utils import timezone

from core.models import (
    Season, Event, Session, RaceResult, QualifyingResult, SprintResult,
    DriverStanding, ConstructorStanding, Driver, Team, Circuit,
    HistoricalDataGap, HistoricalDataCollectionConfig
)

logger = logging.getLogger('data_collector')


class HistoricalDataGapScanner:
    """
    Scanner para identificar gaps (lacunas) de dados históricos.
    Varre o banco de dados e registra dados faltantes no modelo HistoricalDataGap.
    """

    def __init__(self):
        self.config = HistoricalDataCollectionConfig.get_config()
        self.gaps_found = []

    def scan_all(self) -> Dict[str, int]:
        """
        Executa varredura completa de gaps.

        Returns:
            Dict com estatísticas de gaps encontrados
        """
        logger.info("=" * 80)
        logger.info("Iniciando varredura de dados históricos faltantes")
        logger.info(f"Período: {self.config.end_year} - {self.config.start_year}")
        logger.info("=" * 80)

        stats = {
            'seasons': 0,
            'events': 0,
            'sessions': 0,
            'results': 0,
            'standings': 0,
            'drivers': 0,
            'teams': 0,
            'circuits': 0,
            'total': 0
        }

        # 1. Verificar temporadas faltantes
        if self.config.collect_races or self.config.collect_qualifying or self.config.collect_sprints:
            stats['seasons'] = self._scan_missing_seasons()

        # 2. Verificar eventos faltantes em temporadas existentes
        if self.config.collect_races or self.config.collect_qualifying or self.config.collect_sprints:
            stats['events'] = self._scan_missing_events()

        # 3. Verificar sessões faltantes em eventos existentes
        stats['sessions'] = self._scan_missing_sessions()

        # 4. Verificar resultados faltantes
        stats['results'] = self._scan_missing_results()

        # 5. Verificar classificações faltantes
        if self.config.collect_standings:
            stats['standings'] = self._scan_missing_standings()

        # 6. Verificar pilotos sem dados completos
        if self.config.collect_drivers:
            stats['drivers'] = self._scan_incomplete_drivers()

        # 7. Verificar equipes sem dados completos
        if self.config.collect_teams:
            stats['teams'] = self._scan_incomplete_teams()

        # 8. Verificar circuitos sem dados completos
        if self.config.collect_circuits:
            stats['circuits'] = self._scan_incomplete_circuits()

        stats['total'] = sum(stats.values())

        # Salvar gaps no banco de dados
        self._save_gaps()

        # Atualizar configuração
        self.config.last_scan_at = timezone.now()
        self.config.save()

        logger.info("=" * 80)
        logger.info("Varredura concluída")
        logger.info(f"Total de gaps encontrados: {stats['total']}")
        for key, value in stats.items():
            if key != 'total' and value > 0:
                logger.info(f"  - {key}: {value}")
        logger.info("=" * 80)

        return stats

    def _scan_missing_seasons(self) -> int:
        """Verificar temporadas completamente faltantes."""
        logger.info("Verificando temporadas faltantes...")

        count = 0
        for year in range(self.config.start_year, self.config.end_year - 1, -1):
            # Verificar se a temporada existe
            if not Season.objects.filter(year=year).exists():
                self.gaps_found.append({
                    'gap_type': 'season',
                    'status': 'pending',
                    'year': year,
                    'description': f'Temporada {year} completamente faltante',
                    'priority': 500 + (year - 1950),  # Anos mais recentes têm maior prioridade
                })
                count += 1

        logger.info(f"Encontradas {count} temporadas faltantes")
        return count

    def _scan_missing_events(self) -> int:
        """Verificar eventos faltantes em temporadas existentes."""
        logger.info("Verificando eventos faltantes...")

        count = 0
        seasons = Season.objects.filter(
            year__gte=self.config.end_year,
            year__lte=self.config.start_year
        )

        for season in seasons:
            # Para cada temporada, verificar se há número esperado de eventos
            # Temporadas F1 geralmente têm entre 7 (anos 50) e 24 (anos recentes) corridas

            events_count = Event.objects.filter(season=season).count()

            # Definir número esperado de eventos baseado no ano
            year = season.year
            if year >= 2020:
                expected_min = 15  # Anos recentes: mínimo 15 GPs
            elif year >= 2000:
                expected_min = 12
            elif year >= 1980:
                expected_min = 10
            elif year >= 1960:
                expected_min = 7
            else:
                expected_min = 5

            if events_count < expected_min:
                self.gaps_found.append({
                    'gap_type': 'event',
                    'status': 'pending',
                    'year': year,
                    'description': f'Temporada {year} tem apenas {events_count} eventos (esperado: >{expected_min})',
                    'priority': 400 + (year - 1950),
                })
                count += 1

        logger.info(f"Encontrados {count} eventos faltantes")
        return count

    def _scan_missing_sessions(self) -> int:
        """Verificar sessões faltantes em eventos existentes."""
        logger.info("Verificando sessões faltantes...")

        count = 0
        events = Event.objects.filter(
            season__year__gte=self.config.end_year,
            season__year__lte=self.config.start_year
        ).select_related('season')

        for event in events:
            year = event.season.year

            # Verificar sessão de corrida (obrigatória)
            if self.config.collect_races:
                if not Session.objects.filter(event=event, session_type='R').exists():
                    self.gaps_found.append({
                        'gap_type': 'session',
                        'status': 'pending',
                        'year': year,
                        'round_number': event.round_number,
                        'session_type': 'R',
                        'description': f'Corrida faltante: {year} R{event.round_number} - {event.event_name}',
                        'priority': 450 + (year - 1950),
                    })
                    count += 1

            # Verificar sessão de qualificação (obrigatória para anos recentes)
            if self.config.collect_qualifying and year >= 1950:
                if not Session.objects.filter(event=event, session_type='Q').exists():
                    self.gaps_found.append({
                        'gap_type': 'session',
                        'status': 'pending',
                        'year': year,
                        'round_number': event.round_number,
                        'session_type': 'Q',
                        'description': f'Qualificação faltante: {year} R{event.round_number} - {event.event_name}',
                        'priority': 400 + (year - 1950),
                    })
                    count += 1

            # Verificar sprint (apenas para anos com sprint: 2021+)
            if self.config.collect_sprints and year >= 2021:
                # Nem todos os GPs têm sprint, então não é erro se não existir
                # Mas registramos como gap de baixa prioridade para verificação
                pass

        logger.info(f"Encontradas {count} sessões faltantes")
        return count

    def _scan_missing_results(self) -> int:
        """Verificar resultados faltantes em sessões existentes."""
        logger.info("Verificando resultados faltantes...")

        count = 0
        sessions = Session.objects.filter(
            event__season__year__gte=self.config.end_year,
            event__season__year__lte=self.config.start_year
        ).select_related('event', 'event__season')

        for session in sessions:
            year = session.event.season.year

            # Verificar se há resultados para esta sessão
            if session.session_type == 'R':
                results_count = RaceResult.objects.filter(session=session).count()
                if results_count == 0:
                    self.gaps_found.append({
                        'gap_type': 'result',
                        'status': 'pending',
                        'year': year,
                        'round_number': session.event.round_number,
                        'session_type': 'R',
                        'description': f'Resultados de corrida faltantes: {year} R{session.event.round_number} - {session.event.event_name}',
                        'priority': 400 + (year - 1950),
                    })
                    count += 1
                elif results_count < 10:  # Menos de 10 pilotos é suspeito
                    self.gaps_found.append({
                        'gap_type': 'result',
                        'status': 'pending',
                        'year': year,
                        'round_number': session.event.round_number,
                        'session_type': 'R',
                        'description': f'Resultados incompletos: {year} R{session.event.round_number} - apenas {results_count} pilotos',
                        'priority': 350 + (year - 1950),
                    })
                    count += 1

            elif session.session_type == 'Q':
                results_count = QualifyingResult.objects.filter(session=session).count()
                if results_count == 0:
                    self.gaps_found.append({
                        'gap_type': 'result',
                        'status': 'pending',
                        'year': year,
                        'round_number': session.event.round_number,
                        'session_type': 'Q',
                        'description': f'Resultados de qualificação faltantes: {year} R{session.event.round_number} - {session.event.event_name}',
                        'priority': 350 + (year - 1950),
                    })
                    count += 1

            elif session.session_type == 'S':
                results_count = SprintResult.objects.filter(session=session).count()
                if results_count == 0:
                    self.gaps_found.append({
                        'gap_type': 'result',
                        'status': 'pending',
                        'year': year,
                        'round_number': session.event.round_number,
                        'session_type': 'S',
                        'description': f'Resultados de sprint faltantes: {year} R{session.event.round_number} - {session.event.event_name}',
                        'priority': 350 + (year - 1950),
                    })
                    count += 1

        logger.info(f"Encontrados {count} resultados faltantes")
        return count

    def _scan_missing_standings(self) -> int:
        """Verificar classificações faltantes."""
        logger.info("Verificando classificações faltantes...")

        count = 0
        events = Event.objects.filter(
            season__year__gte=self.config.end_year,
            season__year__lte=self.config.start_year
        ).select_related('season')

        for event in events:
            year = event.season.year

            # Verificar classificação de pilotos
            driver_standings = DriverStanding.objects.filter(
                season=event.season,
                event=event
            ).count()

            if driver_standings == 0:
                self.gaps_found.append({
                    'gap_type': 'standing',
                    'status': 'pending',
                    'year': year,
                    'round_number': event.round_number,
                    'description': f'Classificação de pilotos faltante: {year} R{event.round_number}',
                    'priority': 300 + (year - 1950),
                })
                count += 1

            # Verificar classificação de construtores (apenas a partir de 1958)
            if year >= 1958:
                constructor_standings = ConstructorStanding.objects.filter(
                    season=event.season,
                    event=event
                ).count()

                if constructor_standings == 0:
                    self.gaps_found.append({
                        'gap_type': 'standing',
                        'status': 'pending',
                        'year': year,
                        'round_number': event.round_number,
                        'description': f'Classificação de construtores faltante: {year} R{event.round_number}',
                        'priority': 300 + (year - 1950),
                    })
                    count += 1

        logger.info(f"Encontradas {count} classificações faltantes")
        return count

    def _scan_incomplete_drivers(self) -> int:
        """Verificar pilotos com dados incompletos."""
        logger.info("Verificando pilotos com dados incompletos...")

        count = 0
        drivers = Driver.objects.all()

        for driver in drivers:
            # Verificar se falta data de nascimento
            if not driver.date_of_birth:
                self.gaps_found.append({
                    'gap_type': 'driver',
                    'status': 'pending',
                    'year': 2024,  # Ano padrão para dados atemporais
                    'description': f'Piloto sem data de nascimento: {driver.full_name}',
                    'priority': 100,
                })
                count += 1

            # Verificar se falta nacionalidade
            if not driver.nationality:
                self.gaps_found.append({
                    'gap_type': 'driver',
                    'status': 'pending',
                    'year': 2024,
                    'description': f'Piloto sem nacionalidade: {driver.full_name}',
                    'priority': 150,
                })
                count += 1

        logger.info(f"Encontrados {count} pilotos com dados incompletos")
        return count

    def _scan_incomplete_teams(self) -> int:
        """Verificar equipes com dados incompletos."""
        logger.info("Verificando equipes com dados incompletos...")

        count = 0
        teams = Team.objects.all()

        for team in teams:
            # Verificar se falta cor
            if not team.color or team.color == '#FFFFFF':
                self.gaps_found.append({
                    'gap_type': 'team',
                    'status': 'pending',
                    'year': 2024,
                    'description': f'Equipe sem cor definida: {team.name}',
                    'priority': 50,
                })
                count += 1

        logger.info(f"Encontradas {count} equipes com dados incompletos")
        return count

    def _scan_incomplete_circuits(self) -> int:
        """Verificar circuitos com dados incompletos."""
        logger.info("Verificando circuitos com dados incompletos...")

        count = 0
        circuits = Circuit.objects.all()

        for circuit in circuits:
            # Verificar se falta coordenadas
            if not circuit.latitude or not circuit.longitude:
                self.gaps_found.append({
                    'gap_type': 'circuit',
                    'status': 'pending',
                    'year': 2024,
                    'description': f'Circuito sem coordenadas: {circuit.name}',
                    'priority': 50,
                })
                count += 1

            # Verificar se falta comprimento
            if not circuit.length_km:
                self.gaps_found.append({
                    'gap_type': 'circuit',
                    'status': 'pending',
                    'year': 2024,
                    'description': f'Circuito sem comprimento: {circuit.name}',
                    'priority': 30,
                })
                count += 1

        logger.info(f"Encontrados {count} circuitos com dados incompletos")
        return count

    @transaction.atomic
    def _save_gaps(self):
        """Salvar gaps encontrados no banco de dados."""
        logger.info(f"Salvando {len(self.gaps_found)} gaps no banco de dados...")

        created_count = 0
        updated_count = 0

        for gap_data in self.gaps_found:
            # Verificar se já existe um gap similar (mesmo tipo, ano, round)
            existing_gap = HistoricalDataGap.objects.filter(
                gap_type=gap_data['gap_type'],
                year=gap_data['year'],
                round_number=gap_data.get('round_number'),
                session_type=gap_data.get('session_type', '')
            ).first()

            if existing_gap:
                # Se já existe e está concluído, não sobrescrever
                if existing_gap.status == 'completed':
                    continue

                # Atualizar gap existente
                for key, value in gap_data.items():
                    setattr(existing_gap, key, value)
                existing_gap.save()
                updated_count += 1
            else:
                # Criar novo gap
                HistoricalDataGap.objects.create(**gap_data)
                created_count += 1

        logger.info(f"Gaps salvos: {created_count} criados, {updated_count} atualizados")


def run_gap_scan() -> Dict[str, int]:
    """
    Função auxiliar para executar varredura de gaps.
    Pode ser chamada por tasks Celery ou management commands.
    """
    scanner = HistoricalDataGapScanner()
    return scanner.scan_all()
