# -*- coding: utf-8 -*-
"""
Management command para treinar ou retreinar os modelos de Machine Learning.

Este comando treina dois modelos:
1. Lap Time Predictor - Prevê tempos de volta
2. Position Predictor - Prevê posições finais

Uso:
    python manage.py train_ml_models --year-start 2018 --year-end 2025
    python manage.py train_ml_models --incremental  # Treinamento incremental
    python manage.py train_ml_models --full         # Treinamento completo desde 2018
"""
from django.core.management.base import BaseCommand
from datetime import datetime

from ml.trainer import train_all_models, F1PerformanceModel


class Command(BaseCommand):
    help = 'Treina ou retreina os modelos de ML para previsões F1'

    def add_arguments(self, parser):
        parser.add_argument(
            '--year-start',
            type=int,
            default=2018,
            help='Ano inicial para dados de treinamento (padrão: 2018)',
        )
        parser.add_argument(
            '--year-end',
            type=int,
            default=None,
            help='Ano final para dados de treinamento (padrão: ano atual)',
        )
        parser.add_argument(
            '--incremental',
            action='store_true',
            help='Treinamento incremental (atualiza modelos existentes)',
        )
        parser.add_argument(
            '--full',
            action='store_true',
            help='Treinamento completo do zero (ignora modelos existentes)',
        )
        parser.add_argument(
            '--model',
            type=str,
            choices=['lap_time', 'position', 'all'],
            default='all',
            help='Modelo a treinar (lap_time, position, ou all)',
        )

    def handle(self, *args, **options):
        year_start = options['year_start']
        year_end = options['year_end'] or datetime.now().year
        incremental = options['incremental']
        full = options['full']
        model_type = options['model']

        # Validações
        if incremental and full:
            self.stdout.write(
                self.style.ERROR(
                    'Erro: Não é possível usar --incremental e --full ao mesmo tempo'
                )
            )
            return

        if not incremental and not full:
            # Por padrão, usar incremental se modelos existem
            incremental = True
            self.stdout.write(
                self.style.WARNING(
                    'Modo não especificado. Usando treinamento incremental por padrão.'
                )
            )

        if full:
            incremental = False

        # Cabeçalho
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('=== Treinamento de Modelos ML para F1 ==='))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write('')
        self.stdout.write(f'Período de dados: {year_start} - {year_end}')
        self.stdout.write(f'Modo: {"Incremental" if incremental else "Completo (do zero)"}')
        self.stdout.write(f'Modelo(s): {model_type}')
        self.stdout.write('')

        # Treinar modelos
        try:
            if model_type == 'all':
                results = train_all_models(
                    year_start=year_start,
                    year_end=year_end,
                    incremental=incremental
                )

                # Exibir resultados
                self.stdout.write('')
                self.stdout.write(self.style.SUCCESS('=' * 80))
                self.stdout.write(self.style.SUCCESS('=== Resultados do Treinamento ==='))
                self.stdout.write(self.style.SUCCESS('=' * 80))

                for name, result in results.items():
                    self.stdout.write('')
                    self.stdout.write(self.style.WARNING(f'--- {name.upper()} MODEL ---'))

                    if result['status'] == 'success':
                        metrics = result['metrics']

                        self.stdout.write(self.style.SUCCESS('✓ Treinamento bem-sucedido!'))
                        self.stdout.write('')
                        self.stdout.write('Amostras:')
                        self.stdout.write(f"  Treino: {metrics['samples']['train']:,}")
                        self.stdout.write(f"  Teste: {metrics['samples']['test']:,}")
                        self.stdout.write(f"  Total: {metrics['samples']['total']:,}")
                        self.stdout.write('')
                        self.stdout.write('Métricas de Treino:')
                        self.stdout.write(f"  MAE:  {metrics['train']['mae']:.4f}")
                        self.stdout.write(f"  RMSE: {metrics['train']['rmse']:.4f}")
                        self.stdout.write(f"  R²:   {metrics['train']['r2']:.4f}")
                        self.stdout.write('')
                        self.stdout.write('Métricas de Teste:')
                        self.stdout.write(f"  MAE:  {metrics['test']['mae']:.4f}")
                        self.stdout.write(f"  RMSE: {metrics['test']['rmse']:.4f}")
                        self.stdout.write(f"  R²:   {metrics['test']['r2']:.4f}")

                    else:
                        self.stdout.write(
                            self.style.ERROR(f"✗ Erro: {result['error']}")
                        )

            else:
                # Treinar modelo individual
                self.stdout.write(f'Treinando modelo {model_type}...')
                model = F1PerformanceModel(model_type=model_type)
                metrics = model.train(
                    year_start=year_start,
                    year_end=year_end,
                    incremental=incremental
                )

                # Exibir resultados
                self.stdout.write('')
                self.stdout.write(self.style.SUCCESS('=' * 80))
                self.stdout.write(self.style.SUCCESS('✓ Treinamento bem-sucedido!'))
                self.stdout.write(self.style.SUCCESS('=' * 80))
                self.stdout.write('')
                self.stdout.write('Amostras:')
                self.stdout.write(f"  Treino: {metrics['samples']['train']:,}")
                self.stdout.write(f"  Teste: {metrics['samples']['test']:,}")
                self.stdout.write(f"  Total: {metrics['samples']['total']:,}")
                self.stdout.write('')
                self.stdout.write('Métricas de Treino:')
                self.stdout.write(f"  MAE:  {metrics['train']['mae']:.4f}")
                self.stdout.write(f"  RMSE: {metrics['train']['rmse']:.4f}")
                self.stdout.write(f"  R²:   {metrics['train']['r2']:.4f}")
                self.stdout.write('')
                self.stdout.write('Métricas de Teste:')
                self.stdout.write(f"  MAE:  {metrics['test']['mae']:.4f}")
                self.stdout.write(f"  RMSE: {metrics['test']['rmse']:.4f}")
                self.stdout.write(f"  R²:   {metrics['test']['r2']:.4f}")

            # Sucesso geral
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('=' * 80))
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Treinamento concluído com sucesso!'
                )
            )
            self.stdout.write(self.style.SUCCESS('=' * 80))

        except Exception as e:
            self.stdout.write('')
            self.stdout.write(self.style.ERROR('=' * 80))
            self.stdout.write(self.style.ERROR(f'✗ Erro durante o treinamento: {str(e)}'))
            self.stdout.write(self.style.ERROR('=' * 80))
            raise
