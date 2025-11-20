"""
Model training module for F1 ML predictions.
Handles incremental training and model persistence.

Enhanced with XGBoost and LightGBM for improved accuracy.
"""
import logging
import os
import joblib
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd

# Traditional ML
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from sklearn.model_selection import train_test_split

# Advanced ML
try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    xgb = None

try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False
    lgb = None

try:
    import catboost as cb
    CATBOOST_AVAILABLE = True
except ImportError:
    CATBOOST_AVAILABLE = False
    cb = None

try:
    import optuna
    OPTUNA_AVAILABLE = True
except ImportError:
    OPTUNA_AVAILABLE = False
    optuna = None

from django.conf import settings
from ml.feature_engineering import (
    prepare_lap_time_features,
    prepare_position_features,
    prepare_position_features_enhanced,
    prepare_pole_position_features,
    prepare_fastest_lap_features,
    prepare_pole_time_features,
    get_feature_names,
    align_features
)

logger = logging.getLogger('ml')


class F1PerformanceModel:
    """
    F1 Performance prediction model with incremental learning support.

    Supports multiple prediction types:
    - lap_time: Predict lap times based on session conditions (REGRESSION)
    - position: Predict final race positions (REGRESSION)
    - pole_position: Predict probability of pole position (CLASSIFICATION)
    - fastest_lap: Predict probability of fastest lap (CLASSIFICATION)
    """

    def __init__(self, model_type: str = 'lap_time', model_dir: str = None, algorithm: str = 'auto'):
        """
        Initialize the model.

        Args:
            model_type: Type of prediction ('lap_time', 'position', 'pole_position', 'fastest_lap')
            model_dir: Directory to save/load models (default: settings.BASE_DIR/models)
            algorithm: Algorithm to use ('auto', 'xgboost', 'lightgbm', 'catboost', 'sklearn', 'ensemble')
        """
        self.model_type = model_type
        self.algorithm = algorithm
        self.model = None
        self.scaler = None
        self.feature_names = None
        self.is_classifier = model_type in ['pole_position', 'fastest_lap']

        # Determine which algorithm to use
        if algorithm == 'auto':
            # Prefer CatBoost > LightGBM > XGBoost > sklearn
            if CATBOOST_AVAILABLE:
                self.algorithm = 'catboost'
            elif LIGHTGBM_AVAILABLE:
                self.algorithm = 'lightgbm'
            elif XGBOOST_AVAILABLE:
                self.algorithm = 'xgboost'
            else:
                self.algorithm = 'sklearn'

        self.metadata = {
            'model_type': model_type,
            'is_classifier': self.is_classifier,
            'algorithm': self.algorithm,
            'created_at': None,
            'last_trained': None,
            'training_samples': 0,
            'metrics': {}
        }

        # Set model directory
        if model_dir is None:
            self.model_dir = Path(settings.BASE_DIR) / 'models'
        else:
            self.model_dir = Path(model_dir)

        self.model_dir.mkdir(parents=True, exist_ok=True)

        # Model file paths
        self.model_path = self.model_dir / f'{model_type}_predictor.pkl'
        self.scaler_path = self.model_dir / f'{model_type}_scaler.pkl'
        self.metadata_path = self.model_dir / f'{model_type}_metadata.json'
        self.features_path = self.model_dir / f'{model_type}_features.json'

    def _create_model(self):
        """Create a new model instance based on selected algorithm."""
        logger.info(f"Creating {self.algorithm} model for {self.model_type}")

        if self.algorithm == 'catboost':
            # CatBoost - Best for tabular data with categorical features
            if self.is_classifier:
                self.model = cb.CatBoostClassifier(
                    iterations=1000,
                    depth=8,
                    learning_rate=0.03,
                    l2_leaf_reg=3,
                    random_seed=42,
                    verbose=False,
                    task_type='CPU',
                    thread_count=-1
                )
            else:
                if self.model_type == 'position':
                    # Optimized for position prediction
                    self.model = cb.CatBoostRegressor(
                        iterations=1500,
                        depth=10,
                        learning_rate=0.02,
                        l2_leaf_reg=3,
                        random_seed=42,
                        verbose=False,
                        task_type='CPU',
                        thread_count=-1,
                        loss_function='RMSE'
                    )
                else:
                    self.model = cb.CatBoostRegressor(
                        iterations=1000,
                        depth=8,
                        learning_rate=0.03,
                        l2_leaf_reg=3,
                        random_seed=42,
                        verbose=False,
                        task_type='CPU',
                        thread_count=-1
                    )

        elif self.algorithm == 'lightgbm':
            # LightGBM - Fast and efficient
            if self.is_classifier:
                self.model = lgb.LGBMClassifier(
                    n_estimators=1000,
                    max_depth=8,
                    learning_rate=0.03,
                    num_leaves=31,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    random_state=42,
                    n_jobs=-1,
                    verbose=-1
                )
            else:
                if self.model_type == 'position':
                    self.model = lgb.LGBMRegressor(
                        n_estimators=1500,
                        max_depth=10,
                        learning_rate=0.02,
                        num_leaves=63,
                        subsample=0.8,
                        colsample_bytree=0.8,
                        reg_alpha=0.1,
                        reg_lambda=1.0,
                        random_state=42,
                        n_jobs=-1,
                        verbose=-1
                    )
                else:
                    self.model = lgb.LGBMRegressor(
                        n_estimators=1000,
                        max_depth=8,
                        learning_rate=0.03,
                        num_leaves=31,
                        subsample=0.8,
                        colsample_bytree=0.8,
                        random_state=42,
                        n_jobs=-1,
                        verbose=-1
                    )

        elif self.algorithm == 'xgboost':
            # XGBoost - Balanced performance
            if self.is_classifier:
                self.model = xgb.XGBClassifier(
                    n_estimators=1000,
                    max_depth=8,
                    learning_rate=0.03,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    objective='binary:logistic',
                    eval_metric='logloss',
                    random_state=42,
                    n_jobs=-1
                )
            else:
                if self.model_type == 'position':
                    self.model = xgb.XGBRegressor(
                        n_estimators=1500,
                        max_depth=10,
                        learning_rate=0.02,
                        subsample=0.8,
                        colsample_bytree=0.8,
                        objective='reg:squarederror',
                        reg_alpha=0.1,
                        reg_lambda=1.0,
                        random_state=42,
                        n_jobs=-1
                    )
                else:
                    self.model = xgb.XGBRegressor(
                        n_estimators=1000,
                        max_depth=8,
                        learning_rate=0.03,
                        subsample=0.8,
                        colsample_bytree=0.8,
                        objective='reg:squarederror',
                        random_state=42,
                        n_jobs=-1
                    )

        else:  # sklearn
            logger.warning(f"Using sklearn (fallback) for {self.model_type}")
            if self.is_classifier:
                self.model = RandomForestClassifier(
                    n_estimators=500,
                    max_depth=10,
                    random_state=42,
                    n_jobs=-1
                )
            else:
                if self.model_type == 'position':
                    self.model = RandomForestRegressor(
                        n_estimators=500,
                        max_depth=12,
                        random_state=42,
                        n_jobs=-1,
                        min_samples_split=5
                    )
                else:
                    self.model = GradientBoostingRegressor(
                        n_estimators=300,
                        learning_rate=0.05,
                        max_depth=8,
                        random_state=42,
                        subsample=0.8
                    )

        # Create scaler for feature normalization
        self.scaler = StandardScaler()

        logger.info(f"Created new {self.model_type} model using {self.algorithm}")

    def load_model(self) -> bool:
        """
        Load existing model from disk.

        Returns:
            True if model loaded successfully, False otherwise
        """
        try:
            if not self.model_path.exists():
                logger.info(f"No existing model found at {self.model_path}")
                return False

            # Load model, scaler, and metadata
            self.model = joblib.load(self.model_path)
            self.scaler = joblib.load(self.scaler_path)

            # Load metadata
            if self.metadata_path.exists():
                with open(self.metadata_path, 'r') as f:
                    self.metadata = json.load(f)

            # Load feature names
            if self.features_path.exists():
                with open(self.features_path, 'r') as f:
                    self.feature_names = json.load(f)

            logger.info(f"Loaded {self.model_type} model from {self.model_path}")
            logger.info(f"Model trained on {self.metadata.get('training_samples', 'unknown')} samples")
            logger.info(f"Last trained: {self.metadata.get('last_trained', 'unknown')}")

            return True

        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False

    def save_model(self):
        """Save model, scaler, metadata, and feature names to disk."""
        try:
            # Save model and scaler
            joblib.dump(self.model, self.model_path)
            joblib.dump(self.scaler, self.scaler_path)

            # Save metadata
            self.metadata['last_saved'] = datetime.now().isoformat()
            with open(self.metadata_path, 'w') as f:
                json.dump(self.metadata, f, indent=2)

            # Save feature names
            if self.feature_names:
                with open(self.features_path, 'w') as f:
                    json.dump(self.feature_names, f, indent=2)

            logger.info(f"Saved {self.model_type} model to {self.model_path}")

        except Exception as e:
            logger.error(f"Error saving model: {e}")
            raise

    def train(
        self,
        year_start: Optional[int] = None,
        year_end: Optional[int] = None,
        incremental: bool = False
    ) -> Dict:
        """
        Train or update the model.

        Args:
            year_start: Starting year for training data (default: None = all years)
            year_end: Ending year for training data (default: None = all years)
            incremental: If True and model exists, perform incremental training

        Returns:
            Dictionary with training metrics
        """
        year_msg = "all available years"
        if year_start is not None and year_end is not None:
            year_msg = f"{year_start} to {year_end}"
        elif year_start is not None:
            year_msg = f"{year_start} onwards"
        elif year_end is not None:
            year_msg = f"up to {year_end}"

        logger.info(f"Starting training for {self.model_type} model")
        logger.info(f"Year range: {year_msg}")
        logger.info(f"Incremental: {incremental}")

        # Load existing model if incremental training
        if incremental:
            loaded = self.load_model()
            if not loaded:
                logger.warning("Incremental training requested but no existing model found. Training from scratch.")
                incremental = False

        # Prepare features based on model type
        if self.model_type == 'lap_time':
            X, y = prepare_lap_time_features(year_start, year_end)
        elif self.model_type == 'position':
            # Use ENHANCED features for position prediction
            X, y = prepare_position_features_enhanced(year_start, year_end)
        elif self.model_type == 'pole_position':
            X, y = prepare_pole_position_features(year_start, year_end)
        elif self.model_type == 'fastest_lap':
            X, y = prepare_fastest_lap_features(year_start, year_end)
        elif self.model_type == 'pole_time':
            X, y = prepare_pole_time_features(year_start, year_end)
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")

        if X.empty or y.empty:
            raise ValueError("No training data available")

        logger.info(f"Training data: {X.shape[0]} samples, {X.shape[1]} features")

        # Store or align feature names
        if not incremental or self.feature_names is None:
            self.feature_names = get_feature_names(X)
            logger.info(f"Stored {len(self.feature_names)} feature names")
        else:
            # Align features to match existing model
            X = align_features(X, self.feature_names)
            logger.info(f"Aligned features to match existing model")

        # Split data for evaluation
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        # Create model and scaler if needed
        if not incremental or self.model is None:
            self._create_model()
            logger.info("Created new model and scaler")

        # Scale features
        if not incremental or self.scaler is None:
            # Fit new scaler
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            logger.info("Fitted new scaler")
        else:
            # Use existing scaler (partial_fit for incremental)
            try:
                self.scaler.partial_fit(X_train)
                X_train_scaled = self.scaler.transform(X_train)
                X_test_scaled = self.scaler.transform(X_test)
                logger.info("Updated existing scaler")
            except AttributeError:
                # StandardScaler doesn't have partial_fit, refit
                X_train_scaled = self.scaler.fit_transform(X_train)
                X_test_scaled = self.scaler.transform(X_test)
                logger.info("Refitted scaler (no partial_fit available)")

        # For models with warm_start, we can continue training
        if hasattr(self.model, 'warm_start'):
            self.model.fit(X_train_scaled, y_train)
        else:
            # For models without warm_start, we need to retrain
            self.model.fit(X_train_scaled, y_train)

        # Evaluate model
        y_pred_train = self.model.predict(X_train_scaled)
        y_pred_test = self.model.predict(X_test_scaled)

        # Calculate metrics based on model type (regression vs classification)
        if self.is_classifier:
            # Classification metrics
            # Get probability predictions for AUC
            if hasattr(self.model, 'predict_proba'):
                y_prob_train = self.model.predict_proba(X_train_scaled)[:, 1]
                y_prob_test = self.model.predict_proba(X_test_scaled)[:, 1]
            else:
                y_prob_train = y_pred_train
                y_prob_test = y_pred_test

            metrics = {
                'train': {
                    'accuracy': float(accuracy_score(y_train, y_pred_train)),
                    'precision': float(precision_score(y_train, y_pred_train, zero_division=0)),
                    'recall': float(recall_score(y_train, y_pred_train, zero_division=0)),
                    'f1': float(f1_score(y_train, y_pred_train, zero_division=0)),
                    'auc': float(roc_auc_score(y_train, y_prob_train)) if len(np.unique(y_train)) > 1 else 0.0
                },
                'test': {
                    'accuracy': float(accuracy_score(y_test, y_pred_test)),
                    'precision': float(precision_score(y_test, y_pred_test, zero_division=0)),
                    'recall': float(recall_score(y_test, y_pred_test, zero_division=0)),
                    'f1': float(f1_score(y_test, y_pred_test, zero_division=0)),
                    'auc': float(roc_auc_score(y_test, y_prob_test)) if len(np.unique(y_test)) > 1 else 0.0
                },
                'samples': {
                    'train': len(X_train),
                    'test': len(X_test),
                    'total': len(X),
                    'positive_train': int(y_train.sum()),
                    'positive_test': int(y_test.sum())
                }
            }

            logger.info("Training completed successfully")
            logger.info(f"Train Accuracy: {metrics['train']['accuracy']:.3f}, F1: {metrics['train']['f1']:.3f}, AUC: {metrics['train']['auc']:.3f}")
            logger.info(f"Test Accuracy: {metrics['test']['accuracy']:.3f}, F1: {metrics['test']['f1']:.3f}, AUC: {metrics['test']['auc']:.3f}")
            logger.info(f"Positive samples - Train: {metrics['samples']['positive_train']}, Test: {metrics['samples']['positive_test']}")

        else:
            # Regression metrics
            metrics = {
                'train': {
                    'mae': float(mean_absolute_error(y_train, y_pred_train)),
                    'rmse': float(np.sqrt(mean_squared_error(y_train, y_pred_train))),
                    'r2': float(r2_score(y_train, y_pred_train))
                },
                'test': {
                    'mae': float(mean_absolute_error(y_test, y_pred_test)),
                    'rmse': float(np.sqrt(mean_squared_error(y_test, y_pred_test))),
                    'r2': float(r2_score(y_test, y_pred_test))
                },
                'samples': {
                    'train': len(X_train),
                    'test': len(X_test),
                    'total': len(X)
                }
            }

            logger.info("Training completed successfully")
            logger.info(f"Train MAE: {metrics['train']['mae']:.2f}, RMSE: {metrics['train']['rmse']:.2f}, R²: {metrics['train']['r2']:.3f}")
            logger.info(f"Test MAE: {metrics['test']['mae']:.2f}, RMSE: {metrics['test']['rmse']:.2f}, R²: {metrics['test']['r2']:.3f}")

        # Update metadata
        if self.metadata.get('created_at') is None:
            self.metadata['created_at'] = datetime.now().isoformat()

        self.metadata['last_trained'] = datetime.now().isoformat()
        self.metadata['training_samples'] = len(X)
        self.metadata['metrics'] = metrics

        # Set year range for metadata
        if year_start is not None or year_end is not None:
            year_range_start = year_start if year_start is not None else "all"
            year_range_end = year_end if year_end is not None else "all"
            self.metadata['year_range'] = f"{year_range_start}-{year_range_end}"
        else:
            self.metadata['year_range'] = "all years"

        # Save model
        self.save_model()

        return metrics

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Make predictions using the trained model.

        Args:
            X: DataFrame with features

        Returns:
            Array of predictions
        """
        if self.model is None:
            raise ValueError("Model not trained or loaded")

        # Align features
        if self.feature_names:
            X = align_features(X, self.feature_names)

        # Scale features
        X_scaled = self.scaler.transform(X)

        # Predict
        predictions = self.model.predict(X_scaled)

        return predictions

    def get_metadata(self) -> Dict:
        """Get model metadata."""
        return self.metadata.copy()


def train_all_models(
    year_start: Optional[int] = None,
    year_end: Optional[int] = None,
    incremental: bool = True
) -> Dict:
    """
    Train all F1 prediction models.

    Args:
        year_start: Starting year for training data (default: None = all years)
        year_end: Ending year for training data (default: None = all years)
        incremental: If True, perform incremental training on existing models

    Returns:
        Dictionary with training results for all models
    """
    logger.info("=" * 80)
    logger.info("Starting training for all F1 models")
    logger.info("=" * 80)

    results = {}

    # Train lap time model
    try:
        logger.info("\n" + "=" * 80)
        logger.info("Training LAP TIME model")
        logger.info("=" * 80)
        lap_time_model = F1PerformanceModel(model_type='lap_time')
        lap_metrics = lap_time_model.train(
            year_start=year_start,
            year_end=year_end,
            incremental=incremental
        )
        results['lap_time'] = {
            'status': 'success',
            'metrics': lap_metrics
        }
    except Exception as e:
        logger.error(f"Error training lap_time model: {e}", exc_info=True)
        results['lap_time'] = {
            'status': 'error',
            'error': str(e)
        }

    # Train position model (ENHANCED with XGBoost)
    try:
        logger.info("\n" + "=" * 80)
        logger.info("Training POSITION model (ENHANCED)")
        logger.info("=" * 80)
        position_model = F1PerformanceModel(model_type='position', use_xgboost=True)
        position_metrics = position_model.train(
            year_start=year_start,
            year_end=year_end,
            incremental=incremental
        )
        results['position'] = {
            'status': 'success',
            'metrics': position_metrics
        }
    except Exception as e:
        logger.error(f"Error training position model: {e}", exc_info=True)
        results['position'] = {
            'status': 'error',
            'error': str(e)
        }

    # Train pole position model
    try:
        logger.info("\n" + "=" * 80)
        logger.info("Training POLE POSITION model")
        logger.info("=" * 80)
        pole_model = F1PerformanceModel(model_type='pole_position', use_xgboost=True)
        pole_metrics = pole_model.train(
            year_start=year_start,
            year_end=year_end,
            incremental=incremental
        )
        results['pole_position'] = {
            'status': 'success',
            'metrics': pole_metrics
        }
    except Exception as e:
        logger.error(f"Error training pole_position model: {e}", exc_info=True)
        results['pole_position'] = {
            'status': 'error',
            'error': str(e)
        }

    # Train fastest lap model
    try:
        logger.info("\n" + "=" * 80)
        logger.info("Training FASTEST LAP model")
        logger.info("=" * 80)
        fastest_lap_model = F1PerformanceModel(model_type='fastest_lap')
        fastest_lap_metrics = fastest_lap_model.train(
            year_start=year_start,
            year_end=year_end,
            incremental=incremental
        )
        results['fastest_lap'] = {
            'status': 'success',
            'metrics': fastest_lap_metrics
        }
    except Exception as e:
        logger.error(f"Error training fastest_lap model: {e}", exc_info=True)
        results['fastest_lap'] = {
            'status': 'error',
            'error': str(e)
        }

    # Train pole time model (NEW)
    try:
        logger.info("\n" + "=" * 80)
        logger.info("Training POLE TIME model")
        logger.info("=" * 80)
        pole_time_model = F1PerformanceModel(model_type='pole_time')
        pole_time_metrics = pole_time_model.train(
            year_start=year_start,
            year_end=year_end,
            incremental=incremental
        )
        results['pole_time'] = {
            'status': 'success',
            'metrics': pole_time_metrics
        }
    except Exception as e:
        logger.error(f"Error training pole_time model: {e}", exc_info=True)
        results['pole_time'] = {
            'status': 'error',
            'error': str(e)
        }

    logger.info("\n" + "=" * 80)
    logger.info("Training complete for all models")
    logger.info("=" * 80)
    logger.info(f"Summary: {sum(1 for r in results.values() if r['status'] == 'success')}/{len(results)} models trained successfully")

    return results
