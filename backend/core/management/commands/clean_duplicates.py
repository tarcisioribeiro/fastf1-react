# -*- coding: utf-8 -*-
"""
Management command para detectar e remover duplicatas no banco de dados.

Este comando varre todas as tabelas principais do banco de dados procurando por
registros duplicados baseados nas constraints unique_together definidas nos modelos.

Uso:
    python manage.py clean_duplicates --dry-run  # Apenas reporta, nao remove
    python manage.py clean_duplicates --fix      # Remove duplicatas
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count

from core.models import (
    Team, Driver, Circuit, Season, Event, Session,
    RaceResult, QualifyingResult, SprintResult,
    DriverStanding, ConstructorStanding,
    LapTime, TyreStrategy, PitStop
)


class Command(BaseCommand):
    help = 'Detecta e remove registros duplicados no banco de dados'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Apenas reporta duplicatas sem remover',
        )
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Remove duplicatas do banco de dados',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Exibe informacoes detalhadas',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        fix = options['fix']
        verbose = options['verbose']

        if not dry_run and not fix:
            self.stdout.write(
                self.style.WARNING(
                    'Use --dry-run para reportar ou --fix para corrigir duplicatas'
                )
            )
            return

        self.stdout.write(self.style.SUCCESS('=== Iniciando varredura de duplicatas ===\n'))

        total_duplicates = 0
        total_removed = 0

        models_config = [
            {'model': Team, 'name': 'Team', 'unique_fields': ['team_id'], 'display_field': 'name'},
            {'model': Driver, 'name': 'Driver', 'unique_fields': ['driver_id'], 'display_field': 'full_name'},
            {'model': Circuit, 'name': 'Circuit', 'unique_fields': ['circuit_id'], 'display_field': 'name'},
            {'model': Season, 'name': 'Season', 'unique_fields': ['year'], 'display_field': 'year'},
            {'model': Event, 'name': 'Event', 'unique_fields': ['season', 'round_number'], 'display_field': 'event_name', 'also_check': ['event_id']},
            {'model': Session, 'name': 'Session', 'unique_fields': ['event', 'session_type'], 'display_field': '__str__', 'also_check': ['session_id']},
            {'model': RaceResult, 'name': 'RaceResult', 'unique_fields': ['session', 'driver'], 'display_field': '__str__'},
            {'model': QualifyingResult, 'name': 'QualifyingResult', 'unique_fields': ['session', 'driver'], 'display_field': '__str__'},
            {'model': SprintResult, 'name': 'SprintResult', 'unique_fields': ['session', 'driver'], 'display_field': '__str__'},
            {'model': DriverStanding, 'name': 'DriverStanding', 'unique_fields': ['season', 'event', 'driver'], 'display_field': '__str__'},
            {'model': ConstructorStanding, 'name': 'ConstructorStanding', 'unique_fields': ['season', 'event', 'team'], 'display_field': '__str__'},
            {'model': LapTime, 'name': 'LapTime', 'unique_fields': ['session', 'driver', 'lap_number'], 'display_field': '__str__'},
            {'model': TyreStrategy, 'name': 'TyreStrategy', 'unique_fields': ['session', 'driver', 'stint_number'], 'display_field': '__str__'},
            {'model': PitStop, 'name': 'PitStop', 'unique_fields': ['session', 'driver', 'stop_number'], 'display_field': '__str__'},
        ]

        for config in models_config:
            model = config['model']
            name = config['name']
            unique_fields = config['unique_fields']
            display_field = config.get('display_field', '__str__')
            also_check = config.get('also_check', [])

            self.stdout.write(f'\n--- Verificando {name} ---')

            duplicates_found, removed = self._check_and_fix_duplicates(
                model, unique_fields, display_field, fix, verbose
            )
            total_duplicates += duplicates_found
            total_removed += removed

            for field in also_check:
                dup_found, rem = self._check_unique_field(
                    model, field, display_field, fix, verbose
                )
                total_duplicates += dup_found
                total_removed += rem

        self.stdout.write(self.style.SUCCESS(f'\n=== Resumo da Varredura ==='))
        self.stdout.write(f'Total de duplicatas encontradas: {total_duplicates}')

        if fix:
            self.stdout.write(self.style.SUCCESS(f'Total de registros removidos: {total_removed}'))
            self.stdout.write(self.style.SUCCESS('\nBanco de dados limpo!'))
        else:
            self.stdout.write(
                self.style.WARNING(
                    f'\nModo dry-run: nenhum registro foi removido.'
                    f'\nUse --fix para aplicar as correcoes.'
                )
            )

    def _check_and_fix_duplicates(self, model, unique_fields, display_field, fix, verbose):
        duplicates_found = 0
        removed = 0

        duplicates = (
            model.objects
            .values(*unique_fields)
            .annotate(count=Count('id'))
            .filter(count__gt=1)
        )

        if not duplicates.exists():
            self.stdout.write(self.style.SUCCESS(f'  OK - Nenhuma duplicata encontrada'))
            return 0, 0

        for dup in duplicates:
            filter_kwargs = {field: dup[field] for field in unique_fields}
            duplicate_records = model.objects.filter(**filter_kwargs).order_by('-created_at', '-id')

            count = duplicate_records.count()
            duplicates_found += count - 1

            if count > 1:
                self.stdout.write(
                    self.style.WARNING(
                        f'  AVISO: Encontradas {count} instancias duplicadas'
                    )
                )

                if verbose:
                    for idx, record in enumerate(duplicate_records):
                        status = "MANTER" if idx == 0 else "REMOVER"
                        display = self._get_display_value(record, display_field)
                        self.stdout.write(
                            f'    [{status}] ID: {record.id} - {display} '
                            f'(criado em: {record.created_at})'
                        )

                if fix:
                    records_to_delete = duplicate_records[1:]
                    with transaction.atomic():
                        count_deleted = records_to_delete.delete()[0]
                        removed += count_deleted
                        self.stdout.write(
                            self.style.SUCCESS(f'    OK - Removidos {count_deleted} registros duplicados')
                        )

        return duplicates_found, removed

    def _check_unique_field(self, model, field, display_field, fix, verbose):
        duplicates_found = 0
        removed = 0

        duplicates = (
            model.objects
            .values(field)
            .annotate(count=Count('id'))
            .filter(count__gt=1)
            .exclude(**{f'{field}__isnull': True})
            .exclude(**{f'{field}__exact': ''})
        )

        if not duplicates.exists():
            return 0, 0

        self.stdout.write(
            self.style.WARNING(
                f'  AVISO: Campo unico "{field}" tem duplicatas'
            )
        )

        for dup in duplicates:
            field_value = dup[field]
            duplicate_records = model.objects.filter(**{field: field_value}).order_by('-created_at', '-id')

            count = duplicate_records.count()
            duplicates_found += count - 1

            if verbose:
                self.stdout.write(f'    Valor duplicado: {field_value} ({count} vezes)')
                for idx, record in enumerate(duplicate_records):
                    status = "MANTER" if idx == 0 else "REMOVER"
                    display = self._get_display_value(record, display_field)
                    self.stdout.write(
                        f'      [{status}] ID: {record.id} - {display}'
                    )

            if fix:
                records_to_delete = duplicate_records[1:]
                with transaction.atomic():
                    count_deleted = records_to_delete.delete()[0]
                    removed += count_deleted
                    self.stdout.write(
                        self.style.SUCCESS(f'    OK - Removidos {count_deleted} registros')
                    )

        return duplicates_found, removed

    def _get_display_value(self, record, display_field):
        if display_field == '__str__':
            return str(record)
        elif hasattr(record, display_field):
            attr = getattr(record, display_field)
            return attr() if callable(attr) else attr
        else:
            return f'ID: {record.id}'
