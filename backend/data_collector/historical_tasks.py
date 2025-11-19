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
    Task para calcular pódios faltantes nas classificações.
    A Ergast API não fornece pódios, então calculamos a partir dos resultados.

    Returns:
        Dict com estatísticas da atualização
    """
    logger.info("Calculando pódios faltantes nas classificações...")

    from core.models import DriverStanding, ConstructorStanding, RaceResult
    from django.db.models import Q

    updated_driver_standings = 0
    updated_constructor_standings = 0

    try:
        # Atualizar classificações de pilotos
        driver_standings = DriverStanding.objects.filter(podiums=0)

        for standing in driver_standings:
            # Contar pódios até este evento
            podiums = RaceResult.objects.filter(
                driver=standing.driver,
                session__event__season=standing.season,
                session__event__round_number__lte=standing.event.round_number,
                session__session_type='R',
                position__in=[1, 2, 3]
            ).count()

            if podiums > 0:
                standing.podiums = podiums
                standing.save()
                updated_driver_standings += 1

        # Atualizar classificações de construtores
        constructor_standings = ConstructorStanding.objects.filter(podiums=0)

        for standing in constructor_standings:
            # Contar pódios até este evento
            podiums = RaceResult.objects.filter(
                team=standing.team,
                session__event__season=standing.season,
                session__event__round_number__lte=standing.event.round_number,
                session__session_type='R',
                position__in=[1, 2, 3]
            ).count()

            if podiums > 0:
                standing.podiums = podiums
                standing.save()
                updated_constructor_standings += 1

        logger.info(f"Pódios calculados: {updated_driver_standings} pilotos, {updated_constructor_standings} construtores")

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
