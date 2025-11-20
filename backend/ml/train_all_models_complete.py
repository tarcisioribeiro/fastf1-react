"""
Train ALL ML models with ALL available data.

This script trains:
1. Position Model V2 (enhanced with new features)
2. Pole Position Model (classification)
3. Pole Time Model (regression)
4. Lap Time Model
5. Fastest Lap Model

All models are trained with data from ALL years available in the database,
not just 2018+.
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
from ml.position_model_v2 import PositionModelV2, train_position_model_v2

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ml')


def train_all_models_complete():
    """Train all models with complete historical data."""

    print("=" * 80)
    print("TRAINING ALL ML MODELS WITH COMPLETE DATA")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    results = {}

    # 1. POSITION MODEL V2 (Enhanced)
    print("\n" + "=" * 80)
    print("1. TRAINING POSITION MODEL V2 (ENHANCED)")
    print("=" * 80)

    try:
        # Train with ALL data (year_start=None means all data)
        position_metrics = train_position_model_v2(
            year_start=None,  # ALL DATA
            year_end=None,
            optimize=True,  # Use Optuna optimization
            n_trials=30     # Reduced trials for faster training
        )

        results['position_v2'] = {
            'status': 'success',
            'metrics': position_metrics
        }

        print(f"\nPosition V2 - Test MAE: {position_metrics['test']['mae']:.3f}")
        print(f"Position V2 - Test R²: {position_metrics['test']['r2']:.4f}")
        print(f"Position V2 - Within 2 pos: {position_metrics['error_distribution']['within_2_pos']:.1f}%")

    except Exception as e:
        logger.error(f"Error training Position V2: {e}", exc_info=True)
        results['position_v2'] = {'status': 'error', 'error': str(e)}

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

    # 6. Also train legacy position model for comparison
    print("\n" + "=" * 80)
    print("6. TRAINING LEGACY POSITION MODEL (for comparison)")
    print("=" * 80)

    try:
        position_model = F1PerformanceModel(model_type='position')
        position_metrics = position_model.train(
            year_start=None,  # ALL DATA
            year_end=None,
            incremental=False
        )

        results['position_legacy'] = {
            'status': 'success',
            'metrics': position_metrics
        }

        print(f"\nPosition Legacy - Test MAE: {position_metrics['test']['mae']:.3f}")
        print(f"Position Legacy - Test R²: {position_metrics['test']['r2']:.4f}")

    except Exception as e:
        logger.error(f"Error training Position Legacy: {e}", exc_info=True)
        results['position_legacy'] = {'status': 'error', 'error': str(e)}

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

    # Compare Position models
    if results.get('position_v2', {}).get('status') == 'success' and \
       results.get('position_legacy', {}).get('status') == 'success':

        v2_mae = results['position_v2']['metrics']['test']['mae']
        legacy_mae = results['position_legacy']['metrics']['test']['mae']

        improvement = (legacy_mae - v2_mae) / legacy_mae * 100

        print(f"\nPosition Model V2 vs Legacy:")
        print(f"  V2 MAE: {v2_mae:.3f}")
        print(f"  Legacy MAE: {legacy_mae:.3f}")
        print(f"  Improvement: {improvement:.1f}%")

    print("\n" + "=" * 80)

    return results


if __name__ == '__main__':
    train_all_models_complete()
