"""
Celery tasks para coleta de dados históricos de F1.
Executa varredura e coleta de dados de 1950-2024.
"""
import gc
import logging
from datetime import timedelta
from celery import shared_task, group, chord
from django.utils import timezone
from typing import Dict

from core.models import HistoricalDataCollectionConfig, HistoricalDataGap
from .gap_scanner import run_gap_scan
from .historical_collector import collect_historical_data

logger = logging.getLogger('data_collector')


@shared_task(bind=True, max_retries=3)
def scan_historical_data_gaps(self) -> Dict:
    """
    Task para varredura de gaps de dados históricos.
    Identifica dados faltantes e cria registros de HistoricalDataGap.

    Returns:
        Dict com estatísticas de gaps encontrados
    """
    try:
        logger.info("=" * 80)
        logger.info("Task: Varredura de gaps de dados históricos")
        logger.info("=" * 80)

        config = HistoricalDataCollectionConfig.get_config()

        if not config.enabled:
            logger.info("Coleta histórica desativada. Pulando varredura.")
            return {'status': 'disabled'}

        # Executar varredura
        stats = run_gap_scan()

        logger.info(f"Varredura concluída: {stats['total']} gaps encontrados")

        # Liberar memória
        gc.collect()

        return {
            'status': 'completed',
            'stats': stats,
            'timestamp': timezone.now().isoformat()
        }

    except Exception as exc:
        logger.error(f"Erro na varredura de gaps: {exc}", exc_info=True)
        gc.collect()  # Liberar memória mesmo em caso de erro
        raise self.retry(exc=exc, countdown=300)  # Retry após 5 minutos


@shared_task(bind=True, max_retries=3)
def collect_historical_data_batch(self, batch_size: int = None) -> Dict:
    """
    Task para coleta de um lote de dados históricos.

    Args:
        batch_size: Número de gaps a processar neste lote (None = usar tasks_per_batch da config)

    Returns:
        Dict com estatísticas da coleta
    """
    try:
        logger.info("=" * 80)
        logger.info("Task: Coleta de dados históricos (lote)")
        logger.info("=" * 80)

        config = HistoricalDataCollectionConfig.get_config()

        if not config.enabled:
            logger.info("Coleta histórica desativada.")
            return {'status': 'disabled'}

        if batch_size is None:
            batch_size = config.tasks_per_batch

        # Executar coleta
        result = collect_historical_data(max_gaps=batch_size)

        logger.info(f"Lote concluído: {result['gaps_processed']} gaps processados")

        return result

    except Exception as exc:
        logger.error(f"Erro na coleta de dados históricos: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=300)


@shared_task
def collect_single_gap(gap_id: int) -> Dict:
    """
    Task para coletar um gap específico.
    Usado para processamento paralelo em massa.

    Args:
        gap_id: ID do HistoricalDataGap a processar

    Returns:
        Dict com resultado da coleta
    """
    try:
        gap = HistoricalDataGap.objects.get(id=gap_id)

        from .historical_collector import HistoricalDataCollector
        collector = HistoricalDataCollector()

        success = collector.collect_gap(gap)

        return {
            'gap_id': gap_id,
            'status': 'success' if success else 'failed',
            'records_collected': collector.records_collected
        }

    except HistoricalDataGap.DoesNotExist:
        logger.error(f"Gap {gap_id} não encontrado")
        return {'gap_id': gap_id, 'status': 'error', 'error': 'Gap não encontrado'}

    except Exception as e:
        logger.error(f"Erro ao coletar gap {gap_id}: {e}", exc_info=True)
        return {'gap_id': gap_id, 'status': 'error', 'error': str(e)}


@shared_task
def collect_historical_data_parallel() -> Dict:
    """
    Task para coleta paralela de dados históricos.
    Processa múltiplos gaps em paralelo usando workers.

    IMPORTANTE: Esta task não pode usar .get() pois roda dentro de um worker.
    Em vez disso, dispara as tasks e retorna imediatamente.

    Returns:
        Dict com estatísticas da coleta
    """
    logger.info("=" * 80)
    logger.info("Task: Coleta paralela de dados históricos")
    logger.info("=" * 80)

    config = HistoricalDataCollectionConfig.get_config()

    if not config.enabled:
        logger.info("Coleta histórica desativada.")
        return {'status': 'disabled'}

    # Buscar gaps pendentes (alta prioridade)
    gaps = HistoricalDataGap.objects.filter(
        status='pending',
        attempt_count__lt=3
    ).order_by('-priority', '-year')[:config.tasks_per_batch]

    if not gaps.exists():
        logger.info("Nenhum gap pendente para processar")
        return {'status': 'no_gaps', 'gaps_processed': 0}

    gap_ids = list(gaps.values_list('id', flat=True))
    logger.info(f"Disparando {len(gap_ids)} tasks de coleta em paralelo")

    # Disparar tasks paralelas sem aguardar (evita deadlock)
    for gap_id in gap_ids:
        collect_single_gap.apply_async(args=[gap_id])

    logger.info(f"✓ {len(gap_ids)} tasks disparadas com sucesso")

    return {
        'status': 'dispatched',
        'gaps_dispatched': len(gap_ids),
        'message': 'Tasks disparadas para processamento assíncrono'
    }


@shared_task
def incremental_historical_update() -> Dict:
    """
    Task principal para atualização incremental de dados históricos.
    Executa:
    1. Varredura de gaps (se necessário)
    2. Coleta de dados em paralelo

    Esta task é executada periodicamente (configurável via Django Admin).

    Returns:
        Dict com estatísticas completas
    """
    logger.info("=" * 80)
    logger.info("Task: Atualização incremental de dados históricos")
    logger.info("=" * 80)

    config = HistoricalDataCollectionConfig.get_config()

    if not config.enabled:
        logger.info("Coleta histórica desativada.")
        return {'status': 'disabled'}

    result = {
        'status': 'completed',
        'scan': None,
        'collection': None
    }

    # 1. Verificar se precisa fazer varredura
    should_scan = False
    if not config.last_scan_at:
        should_scan = True
        logger.info("Primeira varredura - nunca executada antes")
    else:
        # Verificar se já passou o intervalo de varredura
        time_since_scan = timezone.now() - config.last_scan_at
        scan_interval = timedelta(minutes=config.scan_interval_minutes)

        if time_since_scan >= scan_interval:
            should_scan = True
            logger.info(f"Tempo desde última varredura: {time_since_scan.total_seconds()/60:.1f} minutos")

    if should_scan:
        logger.info("Executando varredura de gaps...")
        scan_result = scan_historical_data_gaps.delay()
        result['scan'] = 'scheduled'
    else:
        logger.info("Varredura não necessária neste momento")
        result['scan'] = 'skipped'

    # 2. Executar coleta paralela
    logger.info("Executando coleta paralela de dados...")
    collection_result = collect_historical_data_parallel()
    result['collection'] = collection_result

    logger.info("=" * 80)
    logger.info("Atualização incremental concluída")
    logger.info("=" * 80)

    return result


@shared_task
def collect_year_data(year: int) -> Dict:
    """
    Task para coletar dados completos de um ano específico.
    Apenas para dados históricos (1950-2017, pois FastF1 API cobre 2018+).

    Args:
        year: Ano a coletar (1950-2017)

    Returns:
        Dict com estatísticas da coleta
    """
    if year < 1950 or year > 2017:
        logger.error(f"Ano {year} fora do intervalo permitido (1950-2017)")
        return {
            'status': 'error',
            'year': year,
            'error': 'Ano fora do intervalo permitido. Use 1950-2017 para dados históricos. 2018+ são coletados via FastF1 API.'
        }

    logger.info(f"Coletando dados completos para o ano {year}")

    from .historical_collector import HistoricalDataCollector
    from core.models import Season

    try:
        # Verificar se a temporada existe
        season, created = Season.objects.get_or_create(year=year)

        if created:
            logger.info(f"Temporada {year} criada")

        # Criar gap para o ano
        gap, _ = HistoricalDataGap.objects.get_or_create(
            gap_type='season',
            year=year,
            defaults={
                'status': 'pending',
                'description': f'Coleta forçada da temporada {year}',
                'priority': 1000,  # Alta prioridade
            }
        )

        # Coletar dados
        collector = HistoricalDataCollector()
        success = collector.collect_gap(gap)

        return {
            'status': 'success' if success else 'failed',
            'year': year,
            'records_collected': collector.records_collected
        }

    except Exception as e:
        logger.error(f"Erro ao coletar ano {year}: {e}", exc_info=True)
        return {'status': 'error', 'year': year, 'error': str(e)}


@shared_task
def calculate_missing_podiums() -> Dict:
    """
    Task para calcular pódios e vitórias faltantes nas classificações.
    A Ergast API não fornece pódios, então calculamos a partir dos resultados.

    Returns:
        Dict com estatísticas da atualização
    """
    logger.info("=" * 80)
    logger.info("Calculando pódios e vitórias faltantes nas classificações...")
    logger.info("=" * 80)

    from core.models import DriverStanding, ConstructorStanding, RaceResult
    from django.db.models import Q

    updated_driver_standings = 0
    updated_constructor_standings = 0

    try:
        # Atualizar classificações de pilotos (onde podiums=0 OU wins pode estar errado)
        driver_standings = DriverStanding.objects.filter(
            Q(podiums=0) | Q(wins=0)
        ).select_related('driver', 'season', 'event')

        logger.info(f"Processando {driver_standings.count()} classificações de pilotos...")

        for standing in driver_standings:
            # Contar pódios até este evento
            podiums = RaceResult.objects.filter(
                driver=standing.driver,
                session__event__season=standing.season,
                session__event__round_number__lte=standing.event.round_number,
                session__session_type='R',
                position__in=[1, 2, 3]
            ).count()

            # Contar vitórias até este evento
            wins = RaceResult.objects.filter(
                driver=standing.driver,
                session__event__season=standing.season,
                session__event__round_number__lte=standing.event.round_number,
                session__session_type='R',
                position=1
            ).count()

            updated = False
            if podiums > 0 and standing.podiums != podiums:
                standing.podiums = podiums
                updated = True
            if wins > 0 and standing.wins != wins:
                standing.wins = wins
                updated = True

            if updated:
                standing.save()
                updated_driver_standings += 1

        # Atualizar classificações de construtores
        constructor_standings = ConstructorStanding.objects.filter(
            Q(podiums=0) | Q(wins=0)
        ).select_related('team', 'season', 'event')

        logger.info(f"Processando {constructor_standings.count()} classificações de construtores...")

        for standing in constructor_standings:
            # Contar pódios até este evento (soma de todos os pilotos da equipe)
            podiums = RaceResult.objects.filter(
                team=standing.team,
                session__event__season=standing.season,
                session__event__round_number__lte=standing.event.round_number,
                session__session_type='R',
                position__in=[1, 2, 3]
            ).count()

            # Contar vitórias até este evento
            wins = RaceResult.objects.filter(
                team=standing.team,
                session__event__season=standing.season,
                session__event__round_number__lte=standing.event.round_number,
                session__session_type='R',
                position=1
            ).count()

            updated = False
            if podiums > 0 and standing.podiums != podiums:
                standing.podiums = podiums
                updated = True
            if wins > 0 and standing.wins != wins:
                standing.wins = wins
                updated = True

            if updated:
                standing.save()
                updated_constructor_standings += 1

        logger.info("=" * 80)
        logger.info(f"Pódios/Vitórias calculados: {updated_driver_standings} pilotos, {updated_constructor_standings} construtores")
        logger.info("=" * 80)

        return {
            'status': 'completed',
            'updated_driver_standings': updated_driver_standings,
            'updated_constructor_standings': updated_constructor_standings
        }

    except Exception as e:
        logger.error(f"Erro ao calcular pódios: {e}", exc_info=True)
        return {'status': 'error', 'error': str(e)}


@shared_task
def recalculate_all_podiums(force: bool = False) -> Dict:
    """
    Task para recalcular TODOS os pódios nas classificações, não apenas os faltantes.
    Útil para corrigir dados incorretos ou inconsistentes.

    Args:
        force: Se True, recalcula mesmo que já exista valor de pódios

    Returns:
        Dict com estatísticas da atualização
    """
    logger.info("=" * 80)
    logger.info("Recalculando TODOS os pódios nas classificações...")
    logger.info("=" * 80)

    from core.models import DriverStanding, ConstructorStanding, RaceResult
    from django.db.models import Q

    updated_driver_standings = 0
    updated_constructor_standings = 0
    total_driver_standings = 0
    total_constructor_standings = 0

    try:
        # Atualizar TODAS as classificações de pilotos
        driver_standings = DriverStanding.objects.all().select_related('driver', 'season', 'event')
        total_driver_standings = driver_standings.count()

        logger.info(f"Processando {total_driver_standings} classificações de pilotos...")

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
                standing.podiums = podiums
                standing.save()
                updated_driver_standings += 1

                if updated_driver_standings <= 10:  # Log dos primeiros 10 para debug
                    logger.info(f"  Piloto {standing.driver} ({standing.season.year} R{standing.event.round_number}): {old_value} -> {podiums} pódios")

            # Log de progresso a cada 100 standings
            if i % 100 == 0:
                logger.info(f"  Progresso pilotos: {i}/{total_driver_standings} ({updated_driver_standings} atualizados)")

        logger.info(f"Pilotos processados: {total_driver_standings}, atualizados: {updated_driver_standings}")
        logger.info("-" * 80)

        # Atualizar TODAS as classificações de construtores
        constructor_standings = ConstructorStanding.objects.all().select_related('team', 'season', 'event')
        total_constructor_standings = constructor_standings.count()

        logger.info(f"Processando {total_constructor_standings} classificações de construtores...")

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
                standing.podiums = podiums
                standing.save()
                updated_constructor_standings += 1

                if updated_constructor_standings <= 10:  # Log dos primeiros 10 para debug
                    logger.info(f"  Equipe {standing.team.name} ({standing.season.year} R{standing.event.round_number}): {old_value} -> {podiums} pódios")

            # Log de progresso a cada 100 standings
            if i % 100 == 0:
                logger.info(f"  Progresso construtores: {i}/{total_constructor_standings} ({updated_constructor_standings} atualizados)")

        logger.info(f"Construtores processados: {total_constructor_standings}, atualizados: {updated_constructor_standings}")
        logger.info("=" * 80)
        logger.info(f"RECÁLCULO CONCLUÍDO!")
        logger.info(f"Total processado: {total_driver_standings + total_constructor_standings}")
        logger.info(f"Total atualizado: {updated_driver_standings + updated_constructor_standings}")
        logger.info("=" * 80)

        return {
            'status': 'completed',
            'total_driver_standings': total_driver_standings,
            'updated_driver_standings': updated_driver_standings,
            'total_constructor_standings': total_constructor_standings,
            'updated_constructor_standings': updated_constructor_standings
        }

    except Exception as e:
        logger.error(f"Erro ao recalcular pódios: {e}", exc_info=True)
        return {'status': 'error', 'error': str(e)}


@shared_task
def initialize_historical_collection() -> Dict:
    """
    Task para inicializar coleta de dados históricos.
    Cria configuração inicial e executa primeira varredura.

    Returns:
        Dict com resultado da inicialização
    """
    logger.info("=" * 80)
    logger.info("Inicializando sistema de coleta histórica")
    logger.info("=" * 80)

    try:
        # Criar ou obter configuração
        config = HistoricalDataCollectionConfig.get_config()

        logger.info(f"Configuração carregada: {config}")
        logger.info(f"Workers: {config.max_workers}, Tasks/batch: {config.tasks_per_batch}")
        logger.info(f"Período: {config.end_year} - {config.start_year}")

        # Executar primeira varredura
        logger.info("Executando varredura inicial...")
        scan_result = scan_historical_data_gaps.delay()

        # Aguardar varredura concluir
        import time
        time.sleep(5)

        # Executar primeira coleta
        logger.info("Iniciando primeira coleta...")
        collection_result = collect_historical_data_parallel()

        logger.info("=" * 80)
        logger.info("Inicialização concluída")
        logger.info("=" * 80)

        return {
            'status': 'initialized',
            'config': {
                'enabled': config.enabled,
                'max_workers': config.max_workers,
                'tasks_per_batch': config.tasks_per_batch,
                'start_year': config.start_year,
                'end_year': config.end_year,
            },
            'collection': collection_result
        }

    except Exception as e:
        logger.error(f"Erro ao inicializar: {e}", exc_info=True)
        return {'status': 'error', 'error': str(e)}


@shared_task(bind=True, max_retries=2)
def fix_duplicate_driver_records(self) -> Dict:
    """
    Task para corrigir registros de pilotos duplicados.
    Separa pilotos históricos de pilotos atuais que compartilham o mesmo código.

    Exemplos:
    - Jos Verstappen vs Max Verstappen (VER)
    - Michael Schumacher vs Mick Schumacher (MSC)

    Deve rodar diariamente para garantir que novos dados importados
    sejam corretamente separados.

    Returns:
        Dict com estatísticas das correções
    """
    from core.models import Driver, RaceResult, QualifyingResult, DriverStanding
    from django.db import transaction

    try:
        logger.info("=" * 80)
        logger.info("Task: Correção de pilotos duplicados")
        logger.info("=" * 80)

        corrections = []

        # Definir mapeamento de pilotos que precisam ser separados
        # Formato: (driver_id_atual, ano_limite, driver_id_novo, codigo_novo, nome, sobrenome)
        driver_splits = [
            # Verstappen: Jos (até 2003) vs Max (2015+)
            {
                'current_driver_id': 'verstappen',
                'year_cutoff': 2003,
                'new_driver_id': 'jos_verstappen',
                'new_code': 'JVE',
                'new_number': 100,
                'new_first_name': 'Jos',
                'new_last_name': 'Verstappen',
                'new_nationality': 'Dutch',
                'current_first_name': 'Max',
            },
            # Schumacher: Michael (até 2012) vs Mick (2021+)
            {
                'current_driver_id': 'michael_schumacher',
                'year_cutoff': 2012,
                'new_driver_id': 'michael_schumacher_sr',
                'new_code': 'MS1',
                'new_number': 101,
                'new_first_name': 'Michael',
                'new_last_name': 'Schumacher',
                'new_nationality': 'German',
                'move_old_to_new': True,  # Michael é o antigo, mover resultados antigos para ele
            },
        ]

        for split in driver_splits:
            try:
                current_driver = Driver.objects.filter(driver_id=split['current_driver_id']).first()
                if not current_driver:
                    continue

                # Verificar se há resultados misturados
                year_cutoff = split['year_cutoff']
                old_results = RaceResult.objects.filter(
                    driver=current_driver,
                    session__event__season__year__lte=year_cutoff
                ).count()
                new_results = RaceResult.objects.filter(
                    driver=current_driver,
                    session__event__season__year__gt=year_cutoff
                ).count()

                # Se não há mistura, pular
                if old_results == 0 or new_results == 0:
                    continue

                logger.info(f"Separando {split['current_driver_id']}: {old_results} antigos, {new_results} novos")

                # Verificar se o novo driver já existe
                new_driver = Driver.objects.filter(driver_id=split['new_driver_id']).first()

                if not new_driver:
                    # Criar novo driver
                    new_driver = Driver.objects.create(
                        driver_id=split['new_driver_id'],
                        code=split['new_code'],
                        number=split['new_number'],
                        first_name=split['new_first_name'],
                        last_name=split['new_last_name'],
                        nationality=split['new_nationality']
                    )
                    logger.info(f"Criado: {new_driver.full_name} ({new_driver.code})")

                # Mover resultados
                with transaction.atomic():
                    if split.get('move_old_to_new', False):
                        # Mover resultados antigos para o novo driver
                        moved_race = RaceResult.objects.filter(
                            driver=current_driver,
                            session__event__season__year__lte=year_cutoff
                        ).update(driver=new_driver)

                        moved_quali = QualifyingResult.objects.filter(
                            driver=current_driver,
                            session__event__season__year__lte=year_cutoff
                        ).update(driver=new_driver)

                        moved_stand = DriverStanding.objects.filter(
                            driver=current_driver,
                            season__year__lte=year_cutoff
                        ).update(driver=new_driver)
                    else:
                        # Mover resultados antigos para o novo driver
                        moved_race = RaceResult.objects.filter(
                            driver=current_driver,
                            session__event__season__year__lte=year_cutoff
                        ).update(driver=new_driver)

                        moved_quali = QualifyingResult.objects.filter(
                            driver=current_driver,
                            session__event__season__year__lte=year_cutoff
                        ).update(driver=new_driver)

                        moved_stand = DriverStanding.objects.filter(
                            driver=current_driver,
                            season__year__lte=year_cutoff
                        ).update(driver=new_driver)

                        # Atualizar nome do driver atual
                        if 'current_first_name' in split:
                            current_driver.first_name = split['current_first_name']
                            current_driver.save()

                corrections.append({
                    'driver': split['current_driver_id'],
                    'moved_race': moved_race,
                    'moved_quali': moved_quali,
                    'moved_stand': moved_stand
                })

                logger.info(f"Movidos: {moved_race} corridas, {moved_quali} qualis, {moved_stand} standings")

            except Exception as e:
                logger.error(f"Erro ao separar {split.get('current_driver_id', 'unknown')}: {e}")
                continue

        logger.info("=" * 80)
        logger.info(f"Correção concluída: {len(corrections)} pilotos corrigidos")
        logger.info("=" * 80)

        return {
            'status': 'completed',
            'corrections': corrections,
            'timestamp': timezone.now().isoformat()
        }

    except Exception as exc:
        logger.error(f"Erro na correção de pilotos duplicados: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=300)


@shared_task(bind=True, max_retries=2)
def generate_constructor_standings_from_results(self) -> Dict:
    """
    Task para gerar ConstructorStandings a partir dos RaceResults existentes.
    Útil para dados históricos onde os standings não foram coletados diretamente.

    Calcula pontos, vitórias e pódios acumulados para cada equipe em cada evento.

    Returns:
        Dict com estatísticas da geração
    """
    from core.models import (
        Season, Event, Team, RaceResult, ConstructorStanding
    )
    from django.db import transaction
    from django.db.models import Sum, Count, Q

    try:
        logger.info("=" * 80)
        logger.info("Gerando ConstructorStandings a partir dos resultados")
        logger.info("=" * 80)

        created_standings = 0
        updated_standings = 0

        # Buscar todas as temporadas que têm resultados mas não têm standings
        seasons_with_results = Season.objects.filter(
            events__sessions__race_results__isnull=False
        ).distinct()

        for season in seasons_with_results:
            # Verificar se já tem standings para esta temporada
            existing_standings = ConstructorStanding.objects.filter(season=season).count()

            # Buscar eventos com resultados nesta temporada
            events = Event.objects.filter(
                season=season,
                sessions__race_results__isnull=False
            ).distinct().order_by('round_number')

            if not events.exists():
                continue

            logger.info(f"Processando temporada {season.year} ({events.count()} eventos)")

            # Buscar todas as equipes que participaram nesta temporada
            teams = Team.objects.filter(
                race_results__session__event__season=season
            ).distinct()

            for event in events:
                for team in teams:
                    # Calcular pontos acumulados até este evento
                    points = RaceResult.objects.filter(
                        team=team,
                        session__event__season=season,
                        session__event__round_number__lte=event.round_number,
                        session__session_type='R'
                    ).aggregate(total=Sum('points'))['total'] or 0

                    # Se a equipe não tem pontos até este evento, pode não ter participado
                    results_count = RaceResult.objects.filter(
                        team=team,
                        session__event__season=season,
                        session__event__round_number__lte=event.round_number,
                        session__session_type='R'
                    ).count()

                    if results_count == 0:
                        continue

                    # Calcular vitórias e pódios acumulados
                    wins = RaceResult.objects.filter(
                        team=team,
                        session__event__season=season,
                        session__event__round_number__lte=event.round_number,
                        session__session_type='R',
                        position=1
                    ).count()

                    podiums = RaceResult.objects.filter(
                        team=team,
                        session__event__season=season,
                        session__event__round_number__lte=event.round_number,
                        session__session_type='R',
                        position__in=[1, 2, 3]
                    ).count()

                    # Criar ou atualizar standing
                    standing, created = ConstructorStanding.objects.update_or_create(
                        season=season,
                        event=event,
                        team=team,
                        defaults={
                            'points': points,
                            'wins': wins,
                            'podiums': podiums,
                            'position': 0  # Será calculado depois
                        }
                    )

                    if created:
                        created_standings += 1
                    else:
                        updated_standings += 1

                # Calcular posições para este evento
                event_standings = ConstructorStanding.objects.filter(
                    season=season,
                    event=event
                ).order_by('-points', '-wins', '-podiums')

                for pos, standing in enumerate(event_standings, 1):
                    if standing.position != pos:
                        standing.position = pos
                        standing.save()

        logger.info("=" * 80)
        logger.info(f"Standings gerados: {created_standings} criados, {updated_standings} atualizados")
        logger.info("=" * 80)

        return {
            'status': 'completed',
            'created_standings': created_standings,
            'updated_standings': updated_standings,
            'timestamp': timezone.now().isoformat()
        }

    except Exception as exc:
        logger.error(f"Erro ao gerar standings: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=300)
