"""
Celery tasks para auditoria de dados.
"""
import logging
from celery import shared_task
from .auditor import run_audit

logger = logging.getLogger(__name__)


@shared_task(name='data_auditor.run_daily_audit')
def run_daily_audit():
    """
    Task Celery para executar auditoria diária de dados.
    Identifica campos vazios e busca sugestões em fontes públicas.
    """
    logger.info("Iniciando auditoria diária de dados...")

    try:
        report = run_audit()

        logger.info(f"Auditoria concluída com sucesso!")
        logger.info(f"  - Tabelas escaneadas: {report.total_tables_scanned}")
        logger.info(f"  - Campos vazios encontrados: {report.total_empty_fields_found}")
        logger.info(f"  - Sugestões encontradas: {report.total_suggestions_found}")
        logger.info(f"  - Tempo de execução: {report.execution_time_seconds:.2f}s")

        return {
            'status': 'success',
            'report_id': report.id,
            'summary': {
                'tables_scanned': report.total_tables_scanned,
                'empty_fields': report.total_empty_fields_found,
                'suggestions': report.total_suggestions_found,
                'execution_time': report.execution_time_seconds,
            }
        }

    except Exception as e:
        logger.error(f"Erro durante auditoria diária: {e}", exc_info=True)
        return {
            'status': 'error',
            'error': str(e)
        }


@shared_task(name='data_auditor.run_manual_audit')
def run_manual_audit():
    """
    Task para executar auditoria manual (pode ser chamada via API).
    """
    return run_daily_audit()
