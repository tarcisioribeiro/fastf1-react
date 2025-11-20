"""
Optimized training script for all ML models.
Uses batch processing for better performance.
Trains with ALL available data.
"""
import os
import sys
import django
import logging
from datetime import datetime

# Setup Django
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

import numpy as np
from ml.trainer import F1PerformanceModel

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ml')


def train_all_optimized():
    """Train all models with complete historical data (optimized version)."""

    print("=" * 80)
    print("TRAINING ALL ML MODELS WITH COMPLETE DATA (OPTIMIZED)")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    results = {}

    # 1. POSITION MODEL (Enhanced features from feature_engineering.py)
    print("\n" + "=" * 80)
    print("1. TRAINING POSITION MODEL (ENHANCED)")
    print("=" * 80)

    try:
        position_model = F1PerformanceModel(model_type='position')
        position_metrics = position_model.train(
            year_start=None,  # ALL DATA
            year_end=None,
            incremental=False
        )

        results['position'] = {
            'status': 'success',
            'metrics': position_metrics
        }

        print(f"\nPosition - Test MAE: {position_metrics['test']['mae']:.3f}")
        print(f"Position - Test R²: {position_metrics['test']['r2']:.4f}")

    except Exception as e:
        logger.error(f"Error training Position: {e}", exc_info=True)
        results['position'] = {'status': 'error', 'error': str(e)}

    # 2. POLE POSITION MODEL
    print("\n" + "=" * 80)
    print("2. TRAINING POLE POSITION MODEL")
    print("=" * 80)

    try:
        pole_model = F1PerformanceModel(model_type='pole_position')
        pole_metrics = pole_model.train(
            year_start=None,  # ALL DATA
            year_end=None,
            incremental=False
        )

        results['pole_position'] = {
            'status': 'success',
            'metrics': pole_metrics
        }

        print(f"\nPole Position - Test Accuracy: {pole_metrics['test']['accuracy']:.3f}")
        print(f"Pole Position - Test AUC: {pole_metrics['test']['auc']:.3f}")
        print(f"Pole Position - Test F1: {pole_metrics['test']['f1']:.3f}")

    except Exception as e:
        logger.error(f"Error training Pole Position: {e}", exc_info=True)
        results['pole_position'] = {'status': 'error', 'error': str(e)}

    # 3. POLE TIME MODEL
    print("\n" + "=" * 80)
    print("3. TRAINING POLE TIME MODEL")
    print("=" * 80)

    try:
        pole_time_model = F1PerformanceModel(model_type='pole_time')
        pole_time_metrics = pole_time_model.train(
            year_start=None,  # ALL DATA
            year_end=None,
            incremental=False
        )

        results['pole_time'] = {
            'status': 'success',
            'metrics': pole_time_metrics
        }

        print(f"\nPole Time - Test MAE: {pole_time_metrics['test']['mae']:.3f}s")
        print(f"Pole Time - Test R²: {pole_time_metrics['test']['r2']:.4f}")

    except Exception as e:
        logger.error(f"Error training Pole Time: {e}", exc_info=True)
        results['pole_time'] = {'status': 'error', 'error': str(e)}

    # 4. LAP TIME MODEL
    print("\n" + "=" * 80)
    print("4. TRAINING LAP TIME MODEL")
    print("=" * 80)

    try:
        lap_time_model = F1PerformanceModel(model_type='lap_time')
        lap_time_metrics = lap_time_model.train(
            year_start=None,  # ALL DATA
            year_end=None,
            incremental=False
        )

        results['lap_time'] = {
            'status': 'success',
            'metrics': lap_time_metrics
        }

        print(f"\nLap Time - Test MAE: {lap_time_metrics['test']['mae']:.3f}s")
        print(f"Lap Time - Test R²: {lap_time_metrics['test']['r2']:.4f}")

    except Exception as e:
        logger.error(f"Error training Lap Time: {e}", exc_info=True)
        results['lap_time'] = {'status': 'error', 'error': str(e)}

    # 5. FASTEST LAP MODEL
    print("\n" + "=" * 80)
    print("5. TRAINING FASTEST LAP MODEL")
    print("=" * 80)

    try:
        fastest_lap_model = F1PerformanceModel(model_type='fastest_lap')
        fastest_lap_metrics = fastest_lap_model.train(
            year_start=None,  # ALL DATA
            year_end=None,
            incremental=False
        )

        results['fastest_lap'] = {
            'status': 'success',
            'metrics': fastest_lap_metrics
        }

        print(f"\nFastest Lap - Test Accuracy: {fastest_lap_metrics['test']['accuracy']:.3f}")
        print(f"Fastest Lap - Test AUC: {fastest_lap_metrics['test']['auc']:.3f}")

    except Exception as e:
        logger.error(f"Error training Fastest Lap: {e}", exc_info=True)
        results['fastest_lap'] = {'status': 'error', 'error': str(e)}

    # SUMMARY
    print("\n" + "=" * 80)
    print("TRAINING SUMMARY")
    print("=" * 80)

    successful = sum(1 for r in results.values() if r['status'] == 'success')
    total = len(results)

    print(f"\nModels trained: {successful}/{total}")
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    for model_name, result in results.items():
        status = "✓" if result['status'] == 'success' else "✗"
        if result['status'] == 'success':
            metrics = result['metrics']
            if 'test' in metrics:
                if 'mae' in metrics['test']:
                    print(f"  {status} {model_name}: MAE={metrics['test']['mae']:.3f}, R²={metrics['test']['r2']:.4f}")
                elif 'accuracy' in metrics['test']:
                    print(f"  {status} {model_name}: Acc={metrics['test']['accuracy']:.3f}, AUC={metrics['test']['auc']:.3f}")
        else:
            print(f"  {status} {model_name}: {result.get('error', 'Unknown error')}")

    print("\n" + "=" * 80)

    return results


if __name__ == '__main__':
    train_all_optimized()
