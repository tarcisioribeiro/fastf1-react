# -*- coding: utf-8 -*-
"""
Retreina apenas os modelos afetados pelos 5 fatores contextuais
(regulamento, atualizações de carro, clima, estratégia, forma atual):

1. Position Model V2  (posição final na corrida)
2. Pole Position Model (probabilidade de pole)
3. Pole Time Model     (tempo de pole)

Os modelos de lap_time e fastest_lap NÃO são afetados e podem continuar sendo
treinados pelo comando ``train_ml_models``.

Uso (rodar num container com RAM suficiente, ex.: um worker):

    docker compose exec celery-worker-2 python manage.py retrain_prediction_models
    docker compose exec celery-worker-2 python manage.py retrain_prediction_models --no-optimize
    docker compose exec celery-worker-2 python manage.py retrain_prediction_models --trials 20 --model position_v2
"""
import gc

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Retreina os modelos de previsão afetados pelos fatores contextuais'

    def add_arguments(self, parser):
        parser.add_argument('--year-start', type=int, default=None)
        parser.add_argument('--year-end', type=int, default=None)
        parser.add_argument(
            '--trials', type=int, default=25,
            help='Nº de trials do Optuna para o Position Model V2 (padrão: 25)',
        )
        parser.add_argument(
            '--no-optimize', action='store_true',
            help='Não otimizar hiperparâmetros do V2 (bem mais leve/rápido)',
        )
        parser.add_argument(
            '--model', choices=['all', 'position_v2', 'pole_position', 'pole_time'],
            default='all',
        )

    def handle(self, *args, **opts):
        year_start = opts['year_start']
        year_end = opts['year_end']
        trials = opts['trials']
        optimize = not opts['no_optimize']
        which = opts['model']

        self.stdout.write(self.style.SUCCESS('=' * 72))
        self.stdout.write(self.style.SUCCESS('Retreino dos modelos de previsão (fatores contextuais)'))
        self.stdout.write(self.style.SUCCESS('=' * 72))
        self.stdout.write(
            f'Período: {year_start or "todos"}-{year_end or "todos"} | '
            f'Optuna: {"sim (" + str(trials) + " trials)" if optimize else "não"} | '
            f'Modelo(s): {which}'
        )

        results = {}

        if which in ('all', 'position_v2'):
            self.stdout.write('\n--- Position Model V2 ---')
            try:
                from ml.position_model_v2 import train_position_model_v2
                m = train_position_model_v2(
                    year_start=year_start, year_end=year_end,
                    optimize=optimize, n_trials=trials,
                )
                results['position_v2'] = m
                self.stdout.write(self.style.SUCCESS(
                    f"  OK  MAE teste {m['test']['mae']:.3f} | R² {m['test']['r2']:.4f} | "
                    f"±2 pos {m['error_distribution']['within_2_pos']:.1f}%"
                ))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  FALHOU: {e}'))
            gc.collect()

        if which in ('all', 'pole_position'):
            self.stdout.write('\n--- Pole Position Model ---')
            try:
                from ml.trainer import F1PerformanceModel
                m = F1PerformanceModel(model_type='pole_position').train(
                    year_start=year_start, year_end=year_end, incremental=False,
                )
                results['pole_position'] = m
                self.stdout.write(self.style.SUCCESS(
                    f"  OK  Acc teste {m['test']['accuracy']:.3f} | AUC {m['test'].get('auc', 0):.3f}"
                ))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  FALHOU: {e}'))
            gc.collect()

        if which in ('all', 'pole_time'):
            self.stdout.write('\n--- Pole Time Model ---')
            try:
                from ml.trainer import F1PerformanceModel
                m = F1PerformanceModel(model_type='pole_time').train(
                    year_start=year_start, year_end=year_end, incremental=False,
                )
                results['pole_time'] = m
                self.stdout.write(self.style.SUCCESS(
                    f"  OK  MAE teste {m['test']['mae']:.3f}s | R² {m['test']['r2']:.4f}"
                ))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  FALHOU: {e}'))
            gc.collect()

        # Recarrega o predictor em memória (processos de longa duração)
        try:
            from ml.predictor import reload_predictor
            reload_predictor()
        except Exception:
            pass

        self.stdout.write('\n' + self.style.SUCCESS('=' * 72))
        self.stdout.write(self.style.SUCCESS(
            f'Concluído: {len(results)} modelo(s) treinado(s).'
        ))
        self.stdout.write(self.style.SUCCESS('=' * 72))
