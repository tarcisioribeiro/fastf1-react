"""
Coletor de dados históricos de F1 (1950-2024).
Usa Ergast API como fonte principal e Wikipedia como fallback.
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from django.db import transaction
from django.utils import timezone

from core.models import (
    Season, Event, Session, Driver, Team, Circuit,
    RaceResult, QualifyingResult, SprintResult,
    DriverStanding, ConstructorStanding, PitStop,
    HistoricalDataGap, HistoricalDataCollectionConfig
)

from .ergast_scraper import ergast_client, ergast_mapper

logger = logging.getLogger('data_collector')


class HistoricalDataCollector:
    """
    Coletor principal de dados históricos.
    Processa gaps identificados e coleta dados das fontes configuradas.
    """

    def __init__(self):
        self.config = HistoricalDataCollectionConfig.get_config()
        self.records_collected = 0

    def collect_gap(self, gap: HistoricalDataGap) -> bool:
        """
        Coletar dados para um gap específico.

        Args:
            gap: Gap a ser preenchido

        Returns:
            True se coletado com sucesso, False caso contrário
        """
        logger.info(f"Coletando gap: {gap}")

        try:
            # Marcar como coletando
            gap.status = 'collecting'
            gap.last_attempt_at = timezone.now()
            gap.attempt_count += 1
            gap.save()

            success = False

            # Rotear para método específico baseado no tipo de gap
            if gap.gap_type == 'season':
                success = self._collect_season(gap)
            elif gap.gap_type == 'event':
                success = self._collect_events_for_season(gap)
            elif gap.gap_type == 'session':
                success = self._collect_session(gap)
            elif gap.gap_type == 'result':
                success = self._collect_results(gap)
            elif gap.gap_type == 'standing':
                success = self._collect_standings(gap)
            elif gap.gap_type == 'driver':
                success = self._collect_driver_data(gap)
            elif gap.gap_type == 'team':
                success = self._collect_team_data(gap)
            elif gap.gap_type == 'circuit':
                success = self._collect_circuit_data(gap)

            if success:
                gap.status = 'completed'
                gap.collected_at = timezone.now()
                gap.error_message = ''
                logger.info(f"Gap coletado com sucesso: {gap}")
            else:
                if gap.attempt_count >= gap.max_attempts:
                    gap.status = 'failed'
                    logger.warning(f"Gap falhou após {gap.attempt_count} tentativas: {gap}")
                else:
                    gap.status = 'pending'

            gap.save()
            return success

        except Exception as e:
            logger.error(f"Erro ao coletar gap {gap}: {e}", exc_info=True)
            gap.status = 'pending' if gap.attempt_count < gap.max_attempts else 'failed'
            gap.error_message = str(e)
            gap.save()
            return False

    @transaction.atomic
    def _collect_season(self, gap: HistoricalDataGap) -> bool:
        """Coletar dados de uma temporada completa."""
        year = gap.year
        logger.info(f"Coletando temporada {year}")

        # Criar ou obter temporada
        season, created = Season.objects.get_or_create(year=year)

        if created:
            logger.info(f"Temporada {year} criada")

        # Buscar calendário na Ergast API
        if self.config.use_ergast_api:
            schedule = ergast_client.get_season_schedule(year)

            if schedule:
                # Processar eventos
                for race_data in schedule:
                    try:
                        self._process_race_from_ergast(season, race_data)
                        self.records_collected += 1
                    except Exception as e:
                        logger.error(f"Erro ao processar corrida {race_data.get('raceName')}: {e}")
                        continue

                return True

        return False

    @transaction.atomic
    def _collect_events_for_season(self, gap: HistoricalDataGap) -> bool:
        """Coletar eventos faltantes de uma temporada."""
        year = gap.year
        logger.info(f"Coletando eventos para temporada {year}")

        try:
            season = Season.objects.get(year=year)
        except Season.DoesNotExist:
            logger.error(f"Temporada {year} não encontrada")
            return False

        # Buscar calendário na Ergast API
        if self.config.use_ergast_api:
            schedule = ergast_client.get_season_schedule(year)

            if schedule:
                for race_data in schedule:
                    try:
                        self._process_race_from_ergast(season, race_data)
                        self.records_collected += 1
                    except Exception as e:
                        logger.error(f"Erro ao processar corrida: {e}")
                        continue

                return True

        return False

    @transaction.atomic
    def _collect_session(self, gap: HistoricalDataGap) -> bool:
        """Coletar dados de uma sessão específica."""
        year = gap.year
        round_number = gap.round_number
        session_type = gap.session_type

        logger.info(f"Coletando sessão {session_type} para {year} R{round_number}")

        try:
            season = Season.objects.get(year=year)
            event = Event.objects.get(season=season, round_number=round_number)
        except (Season.DoesNotExist, Event.DoesNotExist) as e:
            logger.error(f"Evento não encontrado: {year} R{round_number}")
            return False

        # Buscar dados na Ergast API
        if self.config.use_ergast_api:
            if session_type == 'R':
                # Coletar corrida
                race_data = ergast_client.get_race_results(year, round_number)
                if race_data:
                    return self._process_race_results(event, race_data)

            elif session_type == 'Q':
                # Coletar qualificação
                quali_data = ergast_client.get_qualifying_results(year, round_number)
                if quali_data:
                    return self._process_qualifying_results(event, quali_data)

            elif session_type == 'S':
                # Coletar sprint
                sprint_data = ergast_client.get_sprint_results(year, round_number)
                if sprint_data:
                    return self._process_sprint_results(event, sprint_data)

        return False

    @transaction.atomic
    def _collect_results(self, gap: HistoricalDataGap) -> bool:
        """Coletar resultados faltantes."""
        return self._collect_session(gap)

    @transaction.atomic
    def _collect_standings(self, gap: HistoricalDataGap) -> bool:
        """Coletar classificações faltantes."""
        year = gap.year
        round_number = gap.round_number

        logger.info(f"Coletando classificações para {year} R{round_number}")

        try:
            season = Season.objects.get(year=year)
            event = Event.objects.get(season=season, round_number=round_number)
        except (Season.DoesNotExist, Event.DoesNotExist) as e:
            logger.error(f"Evento não encontrado: {year} R{round_number}")
            return False

        if self.config.use_ergast_api:
            # Coletar classificação de pilotos
            driver_standings = ergast_client.get_driver_standings(year, round_number)
            if driver_standings:
                self._process_driver_standings(season, event, driver_standings)

            # Coletar classificação de construtores (apenas de 1958+)
            if year >= 1958:
                constructor_standings = ergast_client.get_constructor_standings(year, round_number)
                if constructor_standings:
                    self._process_constructor_standings(season, event, constructor_standings)

            return True

        return False

    def _collect_driver_data(self, gap: HistoricalDataGap) -> bool:
        """Coletar dados de pilotos."""
        # TODO: Implementar busca complementar na Wikipedia
        logger.info("Coleta de dados complementares de pilotos não implementada ainda")
        return False

    def _collect_team_data(self, gap: HistoricalDataGap) -> bool:
        """Coletar dados de equipes."""
        # TODO: Implementar busca complementar na Wikipedia
        logger.info("Coleta de dados complementares de equipes não implementada ainda")
        return False

    def _collect_circuit_data(self, gap: HistoricalDataGap) -> bool:
        """Coletar dados de circuitos."""
        # TODO: Implementar busca complementar na Wikipedia
        logger.info("Coleta de dados complementares de circuitos não implementada ainda")
        return False

    # ========================================================================
    # Métodos auxiliares para processar dados da Ergast API
    # ========================================================================

    def _process_race_from_ergast(self, season: Season, race_data: Dict):
        """Processar dados de corrida do calendário."""
        # Criar ou obter circuito
        circuit_data = ergast_mapper.map_circuit(race_data['Circuit'])
        circuit, _ = Circuit.objects.update_or_create(
            circuit_id=circuit_data['circuit_id'],
            defaults=circuit_data
        )

        # Criar ou obter evento
        event_id = f"{season.year}_{race_data['round']}"
        event_date = datetime.strptime(race_data['date'], '%Y-%m-%d').date()

        event, _ = Event.objects.update_or_create(
            event_id=event_id,
            defaults={
                'season': season,
                'round_number': int(race_data['round']),
                'circuit': circuit,
                'event_name': race_data['raceName'],
                'event_date': event_date,
                'event_type': 'race',
            }
        )

        logger.debug(f"Evento criado/atualizado: {event}")

    def _process_race_results(self, event: Event, race_data: Dict) -> bool:
        """Processar resultados de corrida."""
        if 'Results' not in race_data:
            logger.warning(f"Sem resultados para {event}")
            return False

        # Criar sessão
        session_id = f"{event.event_id}_R"
        race_datetime = datetime.combine(
            event.event_date,
            datetime.strptime(race_data.get('time', '14:00:00'), '%H:%M:%S').time()
        )
        race_datetime = timezone.make_aware(race_datetime)

        session, _ = Session.objects.get_or_create(
            session_id=session_id,
            defaults={
                'event': event,
                'session_type': 'R',
                'session_date': race_datetime,
                'is_complete': True,
                'data_collected': True,
                'collection_date': timezone.now(),
            }
        )

        # Processar resultados
        winner_time = None
        for result_data in race_data['Results']:
            try:
                # Criar/atualizar piloto
                driver_data = ergast_mapper.map_driver(result_data['Driver'])
                driver, _ = Driver.objects.update_or_create(
                    driver_id=driver_data['driver_id'],
                    defaults=driver_data
                )

                # Criar/atualizar equipe
                team_data = ergast_mapper.map_constructor(result_data['Constructor'])
                team, _ = Team.objects.update_or_create(
                    team_id=team_data['team_id'],
                    defaults=team_data
                )

                # Parsear tempos
                position = int(result_data['position'])

                # Tempo total
                total_race_time = None
                if 'Time' in result_data and 'millis' in result_data['Time']:
                    millis = int(result_data['Time']['millis'])
                    total_race_time = timedelta(milliseconds=millis)

                    if position == 1:
                        winner_time = total_race_time
                elif winner_time and 'Time' in result_data:
                    # Gap em relação ao vencedor
                    gap = ergast_mapper.parse_time(result_data['Time'].get('time', ''))
                    if gap:
                        total_race_time = winner_time + gap

                # Volta mais rápida
                fastest_lap_time = None
                fastest_lap_number = None
                if 'FastestLap' in result_data:
                    fastest_lap_data = result_data['FastestLap']
                    if 'Time' in fastest_lap_data:
                        fastest_lap_time = ergast_mapper.parse_time(fastest_lap_data['Time'].get('time', ''))
                    fastest_lap_number = int(fastest_lap_data.get('lap', 0))

                # Criar resultado
                RaceResult.objects.update_or_create(
                    session=session,
                    driver=driver,
                    defaults={
                        'team': team,
                        'position': position,
                        'grid_position': int(result_data.get('grid', 0)),
                        'points': float(result_data.get('points', 0)),
                        'laps_completed': int(result_data.get('laps', 0)),
                        'total_race_time': total_race_time,
                        'fastest_lap_time': fastest_lap_time,
                        'fastest_lap_number': fastest_lap_number,
                        'status': result_data.get('status', 'Finished'),
                        'dnf': result_data.get('status') != 'Finished',
                    }
                )

                self.records_collected += 1

            except Exception as e:
                logger.error(f"Erro ao processar resultado: {e}", exc_info=True)
                continue

        return True

    def _process_qualifying_results(self, event: Event, quali_data: Dict) -> bool:
        """Processar resultados de qualificação."""
        if 'QualifyingResults' not in quali_data:
            logger.warning(f"Sem resultados de qualificação para {event}")
            return False

        # Criar sessão
        session_id = f"{event.event_id}_Q"
        quali_datetime = datetime.combine(
            event.event_date,
            datetime.strptime('14:00:00', '%H:%M:%S').time()
        )
        quali_datetime = timezone.make_aware(quali_datetime) - timedelta(days=1)  # Dia anterior

        session, _ = Session.objects.get_or_create(
            session_id=session_id,
            defaults={
                'event': event,
                'session_type': 'Q',
                'session_date': quali_datetime,
                'is_complete': True,
                'data_collected': True,
                'collection_date': timezone.now(),
            }
        )

        # Processar resultados
        for result_data in quali_data['QualifyingResults']:
            try:
                # Criar/atualizar piloto
                driver_data = ergast_mapper.map_driver(result_data['Driver'])
                driver, _ = Driver.objects.update_or_create(
                    driver_id=driver_data['driver_id'],
                    defaults=driver_data
                )

                # Criar/atualizar equipe
                team_data = ergast_mapper.map_constructor(result_data['Constructor'])
                team, _ = Team.objects.update_or_create(
                    team_id=team_data['team_id'],
                    defaults=team_data
                )

                # Parsear tempos
                q1_time = ergast_mapper.parse_time(result_data.get('Q1', ''))
                q2_time = ergast_mapper.parse_time(result_data.get('Q2', ''))
                q3_time = ergast_mapper.parse_time(result_data.get('Q3', ''))

                # Criar resultado
                QualifyingResult.objects.update_or_create(
                    session=session,
                    driver=driver,
                    defaults={
                        'team': team,
                        'position': int(result_data['position']),
                        'q1_time': q1_time,
                        'q2_time': q2_time,
                        'q3_time': q3_time,
                    }
                )

                self.records_collected += 1

            except Exception as e:
                logger.error(f"Erro ao processar resultado de qualificação: {e}", exc_info=True)
                continue

        return True

    def _process_sprint_results(self, event: Event, sprint_data: Dict) -> bool:
        """Processar resultados de sprint."""
        if 'SprintResults' not in sprint_data:
            return False

        # Criar sessão
        session_id = f"{event.event_id}_S"
        sprint_datetime = datetime.combine(
            event.event_date,
            datetime.strptime('16:30:00', '%H:%M:%S').time()
        )
        sprint_datetime = timezone.make_aware(sprint_datetime) - timedelta(days=1)

        session, _ = Session.objects.get_or_create(
            session_id=session_id,
            defaults={
                'event': event,
                'session_type': 'S',
                'session_date': sprint_datetime,
                'is_complete': True,
                'data_collected': True,
                'collection_date': timezone.now(),
            }
        )

        # Processar resultados (similar à corrida)
        winner_time = None
        for result_data in sprint_data['SprintResults']:
            try:
                driver_data = ergast_mapper.map_driver(result_data['Driver'])
                driver, _ = Driver.objects.update_or_create(
                    driver_id=driver_data['driver_id'],
                    defaults=driver_data
                )

                team_data = ergast_mapper.map_constructor(result_data['Constructor'])
                team, _ = Team.objects.update_or_create(
                    team_id=team_data['team_id'],
                    defaults=team_data
                )

                position = int(result_data['position'])

                total_sprint_time = None
                if 'Time' in result_data and 'millis' in result_data['Time']:
                    millis = int(result_data['Time']['millis'])
                    total_sprint_time = timedelta(milliseconds=millis)

                    if position == 1:
                        winner_time = total_sprint_time
                elif winner_time and 'Time' in result_data:
                    gap = ergast_mapper.parse_time(result_data['Time'].get('time', ''))
                    if gap:
                        total_sprint_time = winner_time + gap

                fastest_lap_time = None
                if 'FastestLap' in result_data and 'Time' in result_data['FastestLap']:
                    fastest_lap_time = ergast_mapper.parse_time(result_data['FastestLap']['Time'].get('time', ''))

                SprintResult.objects.update_or_create(
                    session=session,
                    driver=driver,
                    defaults={
                        'team': team,
                        'position': position,
                        'grid_position': int(result_data.get('grid', 0)),
                        'points': float(result_data.get('points', 0)),
                        'laps_completed': int(result_data.get('laps', 0)),
                        'total_sprint_time': total_sprint_time,
                        'fastest_lap_time': fastest_lap_time,
                        'status': result_data.get('status', 'Finished'),
                    }
                )

                self.records_collected += 1

            except Exception as e:
                logger.error(f"Erro ao processar resultado de sprint: {e}", exc_info=True)
                continue

        return True

    def _process_driver_standings(self, season: Season, event: Event, standings_data: List[Dict]):
        """Processar classificação de pilotos."""
        for standing_data in standings_data:
            try:
                driver_data = ergast_mapper.map_driver(standing_data['Driver'])
                driver, _ = Driver.objects.update_or_create(
                    driver_id=driver_data['driver_id'],
                    defaults=driver_data
                )

                # Buscar última equipe do piloto neste evento
                # Procurar nos resultados da corrida
                latest_result = RaceResult.objects.filter(
                    session__event__season=season,
                    session__event__round_number__lte=event.round_number,
                    driver=driver
                ).select_related('team').order_by('-session__event__round_number').first()

                if latest_result:
                    team = latest_result.team
                else:
                    # Fallback: usar equipe do standing se disponível
                    if 'Constructors' in standing_data and standing_data['Constructors']:
                        team_data = ergast_mapper.map_constructor(standing_data['Constructors'][0])
                        team, _ = Team.objects.get_or_create(
                            team_id=team_data['team_id'],
                            defaults=team_data
                        )
                    else:
                        logger.warning(f"Sem equipe para {driver.full_name} em {event}")
                        continue

                DriverStanding.objects.update_or_create(
                    season=season,
                    event=event,
                    driver=driver,
                    defaults={
                        'team': team,
                        'position': int(standing_data['position']),
                        'points': float(standing_data['points']),
                        'wins': int(standing_data['wins']),
                        'podiums': 0,  # Não disponível na Ergast API - será calculado depois
                    }
                )

                self.records_collected += 1

            except Exception as e:
                logger.error(f"Erro ao processar classificação de piloto: {e}", exc_info=True)
                continue

    def _process_constructor_standings(self, season: Season, event: Event, standings_data: List[Dict]):
        """Processar classificação de construtores."""
        for standing_data in standings_data:
            try:
                team_data = ergast_mapper.map_constructor(standing_data['Constructor'])
                team, _ = Team.objects.update_or_create(
                    team_id=team_data['team_id'],
                    defaults=team_data
                )

                ConstructorStanding.objects.update_or_create(
                    season=season,
                    event=event,
                    team=team,
                    defaults={
                        'position': int(standing_data['position']),
                        'points': float(standing_data['points']),
                        'wins': int(standing_data['wins']),
                        'podiums': 0,  # Será calculado depois
                    }
                )

                self.records_collected += 1

            except Exception as e:
                logger.error(f"Erro ao processar classificação de construtor: {e}", exc_info=True)
                continue


def collect_historical_data(max_gaps: int = None) -> Dict:
    """
    Função principal para coleta de dados históricos.
    Processa gaps pendentes baseado na configuração.

    Args:
        max_gaps: Número máximo de gaps a processar (None = processar todos pendentes)

    Returns:
        Dict com estatísticas da coleta
    """
    config = HistoricalDataCollectionConfig.get_config()

    if not config.enabled:
        logger.info("Coleta de dados históricos está desativada")
        return {'status': 'disabled', 'gaps_processed': 0}

    logger.info("=" * 80)
    logger.info("Iniciando coleta de dados históricos")
    logger.info("=" * 80)

    collector = HistoricalDataCollector()

    # Buscar gaps pendentes (ordenados por prioridade)
    gaps = HistoricalDataGap.objects.filter(
        status='pending',
        attempt_count__lt=3  # Não tentar gaps que já falharam 3 vezes
    ).order_by('-priority', '-year')

    if max_gaps:
        gaps = gaps[:max_gaps]

    total_gaps = gaps.count()
    logger.info(f"Encontrados {total_gaps} gaps pendentes para processar")

    processed = 0
    successful = 0
    failed = 0

    for gap in gaps:
        success = collector.collect_gap(gap)

        processed += 1
        if success:
            successful += 1
        else:
            failed += 1

        # Log de progresso
        if processed % 10 == 0:
            logger.info(f"Progresso: {processed}/{total_gaps} gaps processados ({successful} sucesso, {failed} falha)")

    # Atualizar estatísticas na configuração
    config.total_records_collected += collector.records_collected
    config.save()

    logger.info("=" * 80)
    logger.info(f"Coleta concluída: {processed} gaps processados")
    logger.info(f"Sucesso: {successful}, Falha: {failed}")
    logger.info(f"Total de registros coletados: {collector.records_collected}")
    logger.info("=" * 80)

    return {
        'status': 'completed',
        'gaps_processed': processed,
        'gaps_successful': successful,
        'gaps_failed': failed,
        'records_collected': collector.records_collected,
    }
