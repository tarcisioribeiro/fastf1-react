"""
Despacho adaptativo das tarefas de coleta do FastF1 com base na memória livre da máquina.

Em vez de enfileirar centenas de subtarefas de uma só vez (padrão `group()`), este
módulo libera o trabalho em uma janela deslizante cujo tamanho é recalculado a cada
ciclo a partir da RAM disponível. Assim garantimos:

- uma margem de segurança fixa de RAM sempre livre na máquina (``SAFETY_MARGIN_MB``);
- um teto de paralelismo (``MAX_PARALLEL``) para não saturar a API do FastF1;
- degradação graciosa: sob pressão de memória o lote encolhe até 1 por vez, em vez
  de derrubar a máquina (que não tem swap);
- teto *global*: várias cadeias simultâneas (corridas + qualifying + sprints…)
  cooperam via inspeção do cluster e nunca somam além de ``compute_slots()``.

Parâmetros ajustáveis por variável de ambiente:

- ``COLLECTION_EST_MB_PER_TASK``      (padrão 350) custo de RAM de pico por subtarefa
- ``COLLECTION_SAFETY_MARGIN_MB``     (padrão 2048) RAM que nunca deve ser consumida
- ``COLLECTION_MAX_PARALLEL``         (padrão 6)   teto de subtarefas simultâneas
- ``COLLECTION_DISPATCH_INTERVAL_SEC``(padrão 20)  intervalo de reavaliação da janela
"""
import logging
import os

import psutil
from celery import shared_task, current_app

logger = logging.getLogger('data_collector')

# Nome da subtarefa de coleta contada para o teto global de paralelismo.
_COLLECT_TASK_NAME = 'data_collector.tasks.collect_session_data'

def _env_int(name: str, default: int) -> int:
    """Lê um inteiro do ambiente, tolerando variável ausente ou vazia."""
    try:
        return int(os.getenv(name) or default)
    except (TypeError, ValueError):
        logger.warning("%s inválido no ambiente; usando padrão %d", name, default)
        return default


EST_MB_PER_TASK = _env_int('COLLECTION_EST_MB_PER_TASK', 350)
SAFETY_MARGIN_MB = _env_int('COLLECTION_SAFETY_MARGIN_MB', 2048)
MAX_PARALLEL = _env_int('COLLECTION_MAX_PARALLEL', 6)
MIN_PARALLEL = 1
DISPATCH_INTERVAL_SEC = _env_int('COLLECTION_DISPATCH_INTERVAL_SEC', 20)

# Salvaguarda contra loop infinito do dispatcher (ex.: subtarefa presa).
_MAX_ITERATIONS = 5000


def compute_slots() -> int:
    """Quantas subtarefas podem rodar em paralelo agora sem faltar memória."""
    vm = psutil.virtual_memory()
    available_mb = vm.available / (1024 * 1024)
    usable_mb = max(0.0, available_mb - SAFETY_MARGIN_MB)
    slots = int(usable_mb // EST_MB_PER_TASK)
    slots = max(MIN_PARALLEL, min(MAX_PARALLEL, slots))
    logger.info(
        "compute_slots: RAM livre=%.0fMB utilizável=%.0fMB custo/task=%dMB -> %d slots",
        available_mb, usable_mb, EST_MB_PER_TASK, slots,
    )
    return slots


def _broker_queue_depth() -> int:
    """Nº de mensagens ainda paradas na fila padrão do broker (Redis)."""
    try:
        queue = current_app.conf.task_default_queue or 'celery'
        with current_app.connection_or_acquire() as conn:
            return int(conn.default_channel.client.llen(queue))
    except Exception as exc:  # pragma: no cover - defensivo
        logger.warning("não foi possível medir a fila do broker (%s)", exc)
        return 0


def global_pending_collects():
    """
    Nº de coletas já "no ar" no cluster inteiro: ``collect_session_data`` em
    execução ou reservada (via inspeção) + mensagens aguardando na fila do broker.

    É o teto de paralelismo *global* — assim várias cadeias de ``throttled_collect``
    simultâneas (corridas + qualifying + sprints…) cooperam e nunca somam além de
    ``compute_slots()``, seja executando, seja acumulando fila no Redis.

    Retorna ``None`` se a inspeção falhar (o dispatcher pula o ciclo então —
    postura conservadora para não estourar a memória).
    """
    try:
        insp = current_app.control.inspect(timeout=1.0)
        buckets = []
        for getter in (insp.active, insp.reserved):
            data = getter() or {}
            buckets.extend(data.values())
        running = sum(
            1
            for tasks in buckets
            for t in tasks
            if t.get('name') == _COLLECT_TASK_NAME
        )
    except Exception as exc:  # pragma: no cover - defensivo
        logger.warning("inspeção do cluster falhou (%s); ciclo será pulado", exc)
        return None

    return running + _broker_queue_depth()


@shared_task(
    bind=True,
    name='data_collector.adaptive_dispatch.throttled_collect',
    description="Despacha coletas de sessão em janela deslizante dimensionada pela RAM livre",
)
def throttled_collect(self, job_spec, cursor=0, iteration=0):
    """
    Despacha ``job_spec`` respeitando um teto *global* de coletas simultâneas.

    A cada ciclo: (1) mede a RAM livre -> ``compute_slots()``; (2) mede quantas
    coletas já estão no ar no cluster inteiro (executando + reservadas + na fila);
    (3) despacha só a diferença; (4) re-agenda a si mesma. Os workers drenam no
    ritmo do pool e a memória fica limitada por ``compute_slots()``.

    Args:
        job_spec: lista de ``[year, round_num, session_type]``
        cursor: índice da próxima sessão a despachar (uso interno)
        iteration: contador de ciclos (uso interno, salvaguarda anti-loop)
    """
    from data_collector.tasks import collect_session_data

    total = len(job_spec)

    if cursor >= total:
        logger.info("throttled_collect: concluído (%d sessões despachadas)", total)
        return f"Concluído: {total} sessões despachadas"

    if iteration >= _MAX_ITERATIONS:
        logger.error(
            "throttled_collect: limite de %d ciclos atingido em cursor=%d/%d — abortando",
            _MAX_ITERATIONS, cursor, total,
        )
        return f"Abortado por limite de ciclos: cursor={cursor}/{total}"

    slots = compute_slots()
    pending = global_pending_collects()
    if pending is None:
        free_slots = 0  # inspeção falhou: não despacha nada neste ciclo
    else:
        free_slots = max(0, slots - pending)

    # Nota: o teto global age *entre* ciclos (a cada DISPATCH_INTERVAL_SEC). Várias
    # cadeias curtas disparadas no mesmo instante podem, no 1º ciclo, enfileirar
    # até (nº de cadeias * slots) mensagens antes de "se enxergarem". Isso é
    # inofensivo: o pool de workers (soma dos --concurrency) é o teto real de
    # memória — o excedente apenas aguarda como mensagem leve no Redis.

    dispatched = 0
    while dispatched < free_slots and cursor < total:
        year, round_num, session_type = job_spec[cursor]
        collect_session_data.apply_async(args=[year, round_num, session_type])
        cursor += 1
        dispatched += 1

    if cursor < total:
        # Re-agenda para reavaliar a janela. A mensagem vai ao broker com ETA,
        # então sobrevive a reinício de worker.
        throttled_collect.apply_async(
            args=[job_spec, cursor, iteration + 1],
            countdown=DISPATCH_INTERVAL_SEC,
        )
    else:
        logger.info("throttled_collect: concluído (%d sessões despachadas)", total)

    logger.info(
        "throttled_collect: cursor=%d/%d slots=%d no_ar=%s (despachadas +%d)",
        cursor, total, slots, pending, dispatched,
    )
    return f"cursor={cursor}/{total} slots={slots} no_ar={pending}"


@shared_task(
    name='data_collector.adaptive_dispatch.report_resource_usage',
    description="Registra uso de memória/CPU da máquina para observabilidade do despacho adaptativo",
)
def report_resource_usage():
    """Loga o estado de recursos da máquina (acompanhamento do throttle)."""
    vm = psutil.virtual_memory()
    cpu = psutil.cpu_percent(interval=1.0)
    slots = compute_slots()
    pending = global_pending_collects()
    logger.info(
        "recursos: RAM usada %.0f/%.0fMB (%.0f%%) livre %.0fMB | CPU %.0f%% | slots=%d coletas_no_ar=%s",
        (vm.total - vm.available) / 1024 / 1024,
        vm.total / 1024 / 1024,
        vm.percent,
        vm.available / 1024 / 1024,
        cpu,
        slots,
        pending,
    )
    return {
        'ram_percent': vm.percent,
        'ram_available_mb': round(vm.available / 1024 / 1024),
        'cpu_percent': cpu,
        'slots': slots,
        'pending_collects': pending,
    }
