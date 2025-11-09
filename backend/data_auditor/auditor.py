"""
Módulo principal de auditoria de dados.
Escaneia o banco de dados, identifica campos vazios e busca sugestões em fontes públicas.
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from django.db import models
from django.apps import apps
from core.models import (
    Driver, Circuit, Team, DataAuditReport, DataAuditSuggestion
)
from .web_sources import DataSourceAggregator

logger = logging.getLogger(__name__)


class DatabaseAuditor:
    """Auditor de banco de dados - identifica campos vazios e busca sugestões."""

    # Configuração de campos a serem auditados por modelo
    AUDIT_CONFIG = {
        'Driver': {
            'fields': ['date_of_birth', 'nationality'],
            'identifier_field': 'full_name',
            'search_methods': {
                'date_of_birth': 'find_driver_date_of_birth',
                'nationality': 'find_driver_nationality',
            }
        },
        'Circuit': {
            'fields': ['latitude', 'longitude', 'length_km'],
            'identifier_field': 'name',
            'search_methods': {
                'latitude': 'find_circuit_coordinates',
                'longitude': 'find_circuit_coordinates',
            }
        },
        # Pode expandir para outros modelos no futuro
    }

    def __init__(self):
        self.data_source = DataSourceAggregator()
        self.audit_results = {
            'tables': {},
            'summary': {
                'total_tables_scanned': 0,
                'total_fields_scanned': 0,
                'total_empty_fields_found': 0,
                'total_suggestions_found': 0,
            }
        }

    def audit_database(self) -> DataAuditReport:
        """
        Executa auditoria completa do banco de dados.
        Retorna um DataAuditReport com os resultados.
        """
        start_time = datetime.now()
        report = DataAuditReport.objects.create(status='pending')

        try:
            # Auditar cada modelo configurado
            for model_name, config in self.AUDIT_CONFIG.items():
                logger.info(f"Auditando modelo: {model_name}")
                self._audit_model(model_name, config, report)

            # Atualizar estatísticas finais
            report.total_tables_scanned = self.audit_results['summary']['total_tables_scanned']
            report.total_fields_scanned = self.audit_results['summary']['total_fields_scanned']
            report.total_empty_fields_found = self.audit_results['summary']['total_empty_fields_found']
            report.total_suggestions_found = self.audit_results['summary']['total_suggestions_found']
            report.audit_results = self.audit_results
            report.status = 'completed'

            # Calcular tempo de execução
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            report.execution_time_seconds = execution_time

            report.save()

            logger.info(f"Auditoria concluída em {execution_time:.2f}s")
            logger.info(f"Total de campos vazios: {report.total_empty_fields_found}")
            logger.info(f"Total de sugestões: {report.total_suggestions_found}")

            return report

        except Exception as e:
            logger.error(f"Erro durante auditoria: {e}", exc_info=True)
            report.status = 'failed'
            report.error_message = str(e)
            report.save()
            raise

    def _audit_model(self, model_name: str, config: Dict, report: DataAuditReport):
        """Audita um modelo específico."""
        try:
            # Obter modelo
            model = apps.get_model('core', model_name)
        except LookupError:
            logger.warning(f"Modelo {model_name} não encontrado")
            return

        self.audit_results['summary']['total_tables_scanned'] += 1
        table_results = {
            'fields': {},
            'empty_count': 0,
            'suggestion_count': 0,
        }

        # Obter todos os registros
        queryset = model.objects.all()
        total_records = queryset.count()

        logger.info(f"  Total de registros em {model_name}: {total_records}")

        # Auditar cada campo configurado
        for field_name in config['fields']:
            self.audit_results['summary']['total_fields_scanned'] += 1

            field_results = self._audit_field(
                model=model,
                queryset=queryset,
                field_name=field_name,
                config=config,
                report=report
            )

            table_results['fields'][field_name] = field_results
            table_results['empty_count'] += field_results['empty_count']
            table_results['suggestion_count'] += field_results['suggestion_count']

        self.audit_results['tables'][model_name] = table_results
        self.audit_results['summary']['total_empty_fields_found'] += table_results['empty_count']
        self.audit_results['summary']['total_suggestions_found'] += table_results['suggestion_count']

    def _audit_field(
        self,
        model,
        queryset,
        field_name: str,
        config: Dict,
        report: DataAuditReport
    ) -> Dict:
        """Audita um campo específico de um modelo."""
        field_results = {
            'empty_count': 0,
            'suggestion_count': 0,
            'examples': []
        }

        # Encontrar registros com campo vazio/nulo
        empty_filter = {f"{field_name}__isnull": True}

        # Também verificar strings vazias se for CharField
        model_field = model._meta.get_field(field_name)
        if isinstance(model_field, (models.CharField, models.TextField)):
            empty_records = queryset.filter(
                models.Q(**empty_filter) | models.Q(**{f"{field_name}": ""})
            )
        elif isinstance(model_field, (models.FloatField, models.IntegerField)):
            # Para coordenadas, considerar 0 como vazio também
            if field_name in ['latitude', 'longitude']:
                empty_records = queryset.filter(
                    models.Q(**empty_filter) | models.Q(**{f"{field_name}": 0})
                )
            else:
                empty_records = queryset.filter(**empty_filter)
        else:
            empty_records = queryset.filter(**empty_filter)

        empty_count = empty_records.count()
        field_results['empty_count'] = empty_count

        if empty_count > 0:
            logger.info(f"    Campo '{field_name}': {empty_count} registros vazios")

            # Limitar a busca de sugestões aos primeiros 10 registros para evitar sobrecarga
            max_suggestions = min(10, empty_count)

            for record in empty_records[:max_suggestions]:
                suggestion = self._find_suggestion(
                    model=model,
                    record=record,
                    field_name=field_name,
                    config=config,
                    report=report
                )

                if suggestion:
                    field_results['suggestion_count'] += 1
                    field_results['examples'].append({
                        'record_id': record.id,
                        'identifier': self._get_record_identifier(record, config),
                        'suggested_value': suggestion.suggested_value[:100],  # Primeiros 100 chars
                    })

        return field_results

    def _find_suggestion(
        self,
        model,
        record,
        field_name: str,
        config: Dict,
        report: DataAuditReport
    ) -> Optional[DataAuditSuggestion]:
        """Busca sugestão para um campo vazio específico."""
        search_method_name = config['search_methods'].get(field_name)
        if not search_method_name:
            return None

        # Obter método de busca
        search_method = getattr(self.data_source, search_method_name, None)
        if not search_method:
            logger.warning(f"Método de busca '{search_method_name}' não encontrado")
            return None

        # Preparar argumentos para busca
        identifier = self._get_record_identifier(record, config)

        # Para Driver
        if model.__name__ == 'Driver':
            result = search_method(
                driver_name=identifier,
                driver_id=getattr(record, 'driver_id', None)
            )
        # Para Circuit
        elif model.__name__ == 'Circuit':
            result = search_method(
                circuit_name=identifier,
                circuit_id=getattr(record, 'circuit_id', None)
            )
        else:
            return None

        if not result:
            return None

        # Extrair valor sugerido
        suggested_value = result.get(field_name)
        if not suggested_value:
            # Para coordenadas, pode vir como 'latitude' ou 'longitude'
            if field_name in result:
                suggested_value = result[field_name]
            else:
                return None

        # Obter valor atual
        current_value = getattr(record, field_name)

        # Criar sugestão
        try:
            suggestion = DataAuditSuggestion.objects.create(
                report=report,
                table_name=model.__name__,
                field_name=field_name,
                record_id=record.id,
                record_identifier=identifier,
                current_value=str(current_value) if current_value else None,
                suggested_value=str(suggested_value),
                confidence_score=result.get('confidence', 0.5),
                source_name=result.get('source', 'Unknown'),
                source_url=result.get('url', ''),
            )

            logger.info(f"      Sugestão criada: {identifier} -> {field_name} = {suggested_value}")
            return suggestion

        except Exception as e:
            logger.error(f"Erro ao criar sugestão: {e}")
            return None

    def _get_record_identifier(self, record, config: Dict) -> str:
        """Obtém identificador legível de um registro."""
        identifier_field = config.get('identifier_field', 'id')

        if identifier_field == 'full_name' and hasattr(record, 'full_name'):
            return record.full_name
        elif hasattr(record, identifier_field):
            value = getattr(record, identifier_field)
            if callable(value):
                return str(value())
            return str(value)
        else:
            return f"ID {record.id}"


def run_audit() -> DataAuditReport:
    """
    Função helper para executar auditoria.
    Pode ser chamada manualmente ou via Celery task.
    """
    auditor = DatabaseAuditor()
    return auditor.audit_database()
