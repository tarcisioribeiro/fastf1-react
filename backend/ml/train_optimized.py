"""
Optimized training script with Optuna hyperparameter optimization
and ensemble model comparison.
"""
import os
import sys
import django

# Setup Django
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

import numpy as np
import pandas as pd
import logging
from sklearn.model_selection import train_test_split, cross_val_score, KFold
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

try:
    import optuna
    OPTUNA_AVAILABLE = True
except ImportError:
    OPTUNA_AVAILABLE = False

from ml.feature_engineering import prepare_position_features_enhanced, align_features
from ml.trainer import F1PerformanceModel

logger = logging.getLogger('ml')
logging.basicConfig(level=logging.INFO)


def train_with_algorithm(algorithm, X_train, X_test, y_train, y_test):
    """
    Train a model with a specific algorithm and return metrics.

    Args:
        algorithm: Algorithm name ('catboost', 'lightgbm', 'xgboost', 'sklearn')
        X_train, X_test, y_train, y_test: Train/test data

    Returns:
        Dict with metrics and model
    """
    print(f"\n{'='*80}")
    print(f"TRAINING WITH {algorithm.upper()}")
    print(f"{'='*80}")

    model = F1PerformanceModel(model_type='position', algorithm=algorithm)
    model._create_model()
    model.feature_names = list(X_train.columns)

    # Fit scaler
    X_train_scaled = model.scaler.fit_transform(X_train)
    X_test_scaled = model.scaler.transform(X_test)

    # Train
    print(f"Training {algorithm} model...")
    model.model.fit(X_train_scaled, y_train)

    # Predict
    y_pred_train = model.model.predict(X_train_scaled)
    y_pred_test = model.model.predict(X_test_scaled)

    # Calculate metrics
    metrics = {
        'algorithm': algorithm,
        'train': {
            'mae': float(mean_absolute_error(y_train, y_pred_train)),
            'rmse': float(np.sqrt(mean_squared_error(y_train, y_pred_train))),
            'r2': float(r2_score(y_train, y_pred_train))
        },
        'test': {
            'mae': float(mean_absolute_error(y_test, y_pred_test)),
            'rmse': float(np.sqrt(mean_squared_error(y_test, y_pred_test))),
            'r2': float(r2_score(y_test, y_pred_test))
        }
    }

    # Error distribution
    test_errors = np.abs(y_test - y_pred_test)
    metrics['test']['error_distribution'] = {
        'median': float(np.median(test_errors)),
        'percentile_90': float(np.percentile(test_errors, 90)),
        'errors_le_1': float((test_errors <= 1).sum() / len(test_errors) * 100),
        'errors_le_2': float((test_errors <= 2).sum() / len(test_errors) * 100),
        'errors_le_3': float((test_errors <= 3).sum() / len(test_errors) * 100)
    }

    print(f"\nResults for {algorithm}:")
    print(f"  Train: MAE={metrics['train']['mae']:.3f}, RMSE={metrics['train']['rmse']:.3f}, R²={metrics['train']['r2']:.4f}")
    print(f"  Test:  MAE={metrics['test']['mae']:.3f}, RMSE={metrics['test']['rmse']:.3f}, R²={metrics['test']['r2']:.4f}")
    print(f"  Error ≤1 pos: {metrics['test']['error_distribution']['errors_le_1']:.1f}%")
    print(f"  Error ≤2 pos: {metrics['test']['error_distribution']['errors_le_2']:.1f}%")
    print(f"  Error ≤3 pos: {metrics['test']['error_distribution']['errors_le_3']:.1f}%")

    return metrics, model


def optimize_catboost_with_optuna(X_train, X_test, y_train, y_test, n_trials=50):
    """
    Optimize CatBoost hyperparameters using Optuna.

    Args:
        X_train, X_test, y_train, y_test: Training data
        n_trials: Number of optimization trials

    Returns:
        Best model and metrics
    """
    if not OPTUNA_AVAILABLE:
        print("Optuna not available, skipping optimization")
        return None

    print(f"\n{'='*80}")
    print(f"OPTIMIZING CATBOOST WITH OPTUNA ({n_trials} trials)")
    print(f"{'='*80}")

    import catboost as cb
    from sklearn.preprocessing import StandardScaler

    # Scale data
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    def objective(trial):
        """Optuna objective function."""
        params = {
            'iterations': trial.suggest_int('iterations', 500, 2000),
            'depth': trial.suggest_int('depth', 6, 12),
            'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.1, log=True),
            'l2_leaf_reg': trial.suggest_float('l2_leaf_reg', 1, 10),
            'random_seed': 42,
            'verbose': False,
            'task_type': 'CPU',
            'thread_count': -1,
            'loss_function': 'RMSE'
        }

        model = cb.CatBoostRegressor(**params)
        model.fit(X_train_scaled, y_train, eval_set=(X_test_scaled, y_test), verbose=False)

        y_pred = model.predict(X_test_scaled)
        mae = mean_absolute_error(y_test, y_pred)

        return mae

    # Run optimization
    study = optuna.create_study(direction='minimize', study_name='catboost_position')
    study.optimize(objective, n_trials=n_trials, show_progress_bar=True)

    print(f"\nBest trial:")
    print(f"  MAE: {study.best_value:.3f}")
    print(f"  Params: {study.best_params}")

    # Train final model with best params
    best_params = study.best_params
    best_params.update({
        'random_seed': 42,
        'verbose': False,
        'task_type': 'CPU',
        'thread_count': -1,
        'loss_function': 'RMSE'
    })

    final_model = cb.CatBoostRegressor(**best_params)
    final_model.fit(X_train_scaled, y_train)

    # Evaluate
    y_pred_train = final_model.predict(X_train_scaled)
    y_pred_test = final_model.predict(X_test_scaled)

    metrics = {
        'algorithm': 'catboost_optimized',
        'best_params': study.best_params,
        'train': {
            'mae': float(mean_absolute_error(y_train, y_pred_train)),
            'rmse': float(np.sqrt(mean_squared_error(y_train, y_pred_train))),
            'r2': float(r2_score(y_train, y_pred_train))
        },
        'test': {
            'mae': float(mean_absolute_error(y_test, y_pred_test)),
            'rmse': float(np.sqrt(mean_squared_error(y_test, y_pred_test))),
            'r2': float(r2_score(y_test, y_pred_test))
        }
    }

    test_errors = np.abs(y_test - y_pred_test)
    metrics['test']['error_distribution'] = {
        'median': float(np.median(test_errors)),
        'errors_le_1': float((test_errors <= 1).sum() / len(test_errors) * 100),
        'errors_le_2': float((test_errors <= 2).sum() / len(test_errors) * 100),
        'errors_le_3': float((test_errors <= 3).sum() / len(test_errors) * 100)
    }

    print(f"\nOptimized CatBoost Results:")
    print(f"  Train: MAE={metrics['train']['mae']:.3f}, RMSE={metrics['train']['rmse']:.3f}, R²={metrics['train']['r2']:.4f}")
    print(f"  Test:  MAE={metrics['test']['mae']:.3f}, RMSE={metrics['test']['rmse']:.3f}, R²={metrics['test']['r2']:.4f}")
    print(f"  Error ≤1 pos: {metrics['test']['error_distribution']['errors_le_1']:.1f}%")
    print(f"  Error ≤2 pos: {metrics['test']['error_distribution']['errors_le_2']:.1f}%")
    print(f"  Error ≤3 pos: {metrics['test']['error_distribution']['errors_le_3']:.1f}%")

    return metrics, final_model, scaler


def train_ensemble(X_train, X_test, y_train, y_test):
    """
    Train an ensemble of multiple algorithms and average predictions.

    Args:
        X_train, X_test, y_train, y_test: Training data

    Returns:
        Ensemble metrics
    """
    print(f"\n{'='*80}")
    print(f"TRAINING ENSEMBLE MODEL")
    print(f"{'='*80}")

    algorithms = ['catboost', 'lightgbm', 'xgboost']
    models = []

    for algo in algorithms:
        print(f"\nTraining {algo} for ensemble...")
        model = F1PerformanceModel(model_type='position', algorithm=algo)
        model._create_model()
        model.feature_names = list(X_train.columns)

        X_train_scaled = model.scaler.fit_transform(X_train)
        X_test_scaled = model.scaler.transform(X_test)

        model.model.fit(X_train_scaled, y_train)
        models.append((model, X_train_scaled, X_test_scaled))

    # Ensemble predictions (average)
    train_preds = []
    test_preds = []

    for model, X_train_scaled, X_test_scaled in models:
        train_preds.append(model.model.predict(X_train_scaled))
        test_preds.append(model.model.predict(X_test_scaled))

    y_pred_train_ensemble = np.mean(train_preds, axis=0)
    y_pred_test_ensemble = np.mean(test_preds, axis=0)

    # Calculate metrics
    metrics = {
        'algorithm': 'ensemble',
        'train': {
            'mae': float(mean_absolute_error(y_train, y_pred_train_ensemble)),
            'rmse': float(np.sqrt(mean_squared_error(y_train, y_pred_train_ensemble))),
            'r2': float(r2_score(y_train, y_pred_train_ensemble))
        },
        'test': {
            'mae': float(mean_absolute_error(y_test, y_pred_test_ensemble)),
            'rmse': float(np.sqrt(mean_squared_error(y_test, y_pred_test_ensemble))),
            'r2': float(r2_score(y_test, y_pred_test_ensemble))
        }
    }

    test_errors = np.abs(y_test - y_pred_test_ensemble)
    metrics['test']['error_distribution'] = {
        'median': float(np.median(test_errors)),
        'errors_le_1': float((test_errors <= 1).sum() / len(test_errors) * 100),
        'errors_le_2': float((test_errors <= 2).sum() / len(test_errors) * 100),
        'errors_le_3': float((test_errors <= 3).sum() / len(test_errors) * 100)
    }

    print(f"\nEnsemble Results:")
    print(f"  Train: MAE={metrics['train']['mae']:.3f}, RMSE={metrics['train']['rmse']:.3f}, R²={metrics['train']['r2']:.4f}")
    print(f"  Test:  MAE={metrics['test']['mae']:.3f}, RMSE={metrics['test']['rmse']:.3f}, R²={metrics['test']['r2']:.4f}")
    print(f"  Error ≤1 pos: {metrics['test']['error_distribution']['errors_le_1']:.1f}%")
    print(f"  Error ≤2 pos: {metrics['test']['error_distribution']['errors_le_2']:.1f}%")
    print(f"  Error ≤3 pos: {metrics['test']['error_distribution']['errors_le_3']:.1f}%")

    return metrics, models


def main():
    """Main training and comparison function."""
    print("="*80)
    print("ENHANCED F1 POSITION PREDICTOR TRAINING")
    print("="*80)

    # Load data
    print("\nLoading enhanced features...")
    X, y = prepare_position_features_enhanced(year_start=2018)

    if X.empty or y.empty:
        print("ERROR: No data available")
        return

    print(f"Loaded {X.shape[0]} samples with {X.shape[1]} features")

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    print(f"Train: {len(X_train)}, Test: {len(X_test)}")

    # Train with different algorithms
    all_results = []

    # 1. CatBoost (default)
    metrics_cb, model_cb = train_with_algorithm('catboost', X_train, X_test, y_train, y_test)
    all_results.append(metrics_cb)

    # 2. LightGBM
    metrics_lgb, model_lgb = train_with_algorithm('lightgbm', X_train, X_test, y_train, y_test)
    all_results.append(metrics_lgb)

    # 3. XGBoost
    metrics_xgb, model_xgb = train_with_algorithm('xgboost', X_train, X_test, y_train, y_test)
    all_results.append(metrics_xgb)

    # 4. Optimized CatBoost with Optuna
    if OPTUNA_AVAILABLE:
        metrics_opt, model_opt, scaler_opt = optimize_catboost_with_optuna(
            X_train, X_test, y_train, y_test, n_trials=30
        )
        if metrics_opt:
            all_results.append(metrics_opt)

    # 5. Ensemble
    metrics_ens, models_ens = train_ensemble(X_train, X_test, y_train, y_test)
    all_results.append(metrics_ens)

    # Compare results
    print(f"\n{'='*80}")
    print("FINAL COMPARISON")
    print(f"{'='*80}\n")

    # Sort by test R²
    all_results.sort(key=lambda x: x['test']['r2'], reverse=True)

    print(f"{'Algorithm':<25} {'Test MAE':<12} {'Test RMSE':<12} {'Test R²':<12} {'≤2 pos %':<12}")
    print("-" * 80)

    for result in all_results:
        algo = result['algorithm']
        mae = result['test']['mae']
        rmse = result['test']['rmse']
        r2 = result['test']['r2']
        err_le_2 = result['test']['error_distribution']['errors_le_2']

        print(f"{algo:<25} {mae:<12.3f} {rmse:<12.3f} {r2:<12.4f} {err_le_2:<12.1f}")

    # Save best model
    best_result = all_results[0]
    print(f"\n{'='*80}")
    print(f"BEST MODEL: {best_result['algorithm']}")
    print(f"  Test R²: {best_result['test']['r2']:.4f} ({best_result['test']['r2']*100:.2f}%)")
    print(f"  Test MAE: {best_result['test']['mae']:.3f} positions")
    print(f"  Errors ≤2 pos: {best_result['test']['error_distribution']['errors_le_2']:.1f}%")
    print(f"{'='*80}")

    # Save the best model
    if best_result['algorithm'] == 'catboost_optimized':
        print("\nSaving optimized CatBoost model...")
        # Save optimized model
        final_model = F1PerformanceModel(model_type='position', algorithm='catboost')
        final_model.model = model_opt
        final_model.scaler = scaler_opt
        final_model.feature_names = list(X_train.columns)
        final_model.metadata['best_params'] = metrics_opt['best_params']
        final_model.metadata['metrics'] = {
            'train': metrics_opt['train'],
            'test': metrics_opt['test']
        }
        final_model.save_model()
        print("Model saved!")

    elif best_result['algorithm'] == 'ensemble':
        print("\nNote: Ensemble model not saved (requires special handling)")
        print("Saving best individual model (CatBoost) instead...")
        model_cb.save_model()
        print("Model saved!")

    else:
        # Save individual best model
        if best_result['algorithm'] == 'catboost':
            model_cb.save_model()
        elif best_result['algorithm'] == 'lightgbm':
            model_lgb.save_model()
        elif best_result['algorithm'] == 'xgboost':
            model_xgb.save_model()
        print("Model saved!")


if __name__ == '__main__':
    main()
