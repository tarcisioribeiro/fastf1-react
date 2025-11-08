"""
Model training module for F1 ML predictions.
Handles incremental training and model persistence.
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
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import SGDRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

from django.conf import settings
from ml.feature_engineering import (
    prepare_lap_time_features,
    prepare_position_features,
    get_feature_names,
    align_features
)

logger = logging.getLogger('ml')


class F1PerformanceModel:
    """
    F1 Performance prediction model with incremental learning support.

    Supports two prediction types:
    - lap_time: Predict lap times based on session conditions
    - position: Predict final race positions
    """

    def __init__(self, model_type: str = 'lap_time', model_dir: str = None):
        """
        Initialize the model.

        Args:
            model_type: Type of prediction ('lap_time' or 'position')
            model_dir: Directory to save/load models (default: settings.BASE_DIR/models)
        """
        self.model_type = model_type
        self.model = None
        self.scaler = None
        self.feature_names = None
        self.metadata = {
            'model_type': model_type,
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
        """Create a new model instance."""
        if self.model_type == 'lap_time':
            # Use GradientBoosting for lap time prediction (better for regression)
            self.model = GradientBoostingRegressor(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=5,
                random_state=42,
                subsample=0.8,
                warm_start=True  # Allow incremental training
            )
        elif self.model_type == 'position':
            # Use RandomForest for position prediction
            self.model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                warm_start=True,  # Allow incremental training
                n_jobs=-1
            )
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")

        # Create scaler for feature normalization
        self.scaler = StandardScaler()

        logger.info(f"Created new {self.model_type} model")

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
        year_start: int = 2018,
        year_end: Optional[int] = None,
        incremental: bool = False
    ) -> Dict:
        """
        Train or update the model.

        Args:
            year_start: Starting year for training data
            year_end: Ending year for training data (default: current year)
            incremental: If True and model exists, perform incremental training

        Returns:
            Dictionary with training metrics
        """
        logger.info(f"Starting training for {self.model_type} model")
        logger.info(f"Year range: {year_start} to {year_end or 'current'}")
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
            X, y = prepare_position_features(year_start, year_end)
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

        # Update metadata
        if self.metadata.get('created_at') is None:
            self.metadata['created_at'] = datetime.now().isoformat()

        self.metadata['last_trained'] = datetime.now().isoformat()
        self.metadata['training_samples'] = len(X)
        self.metadata['metrics'] = metrics
        self.metadata['year_range'] = f"{year_start}-{year_end or datetime.now().year}"

        # Save model
        self.save_model()

        # Log metrics
        logger.info("Training completed successfully")
        logger.info(f"Train MAE: {metrics['train']['mae']:.2f}, RMSE: {metrics['train']['rmse']:.2f}, R²: {metrics['train']['r2']:.3f}")
        logger.info(f"Test MAE: {metrics['test']['mae']:.2f}, RMSE: {metrics['test']['rmse']:.2f}, R²: {metrics['test']['r2']:.3f}")

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
    year_start: int = 2018,
    year_end: Optional[int] = None,
    incremental: bool = True
) -> Dict:
    """
    Train all F1 prediction models.

    Args:
        year_start: Starting year for training data
        year_end: Ending year for training data
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

    # Train position model
    try:
        logger.info("\n" + "=" * 80)
        logger.info("Training POSITION model")
        logger.info("=" * 80)
        position_model = F1PerformanceModel(model_type='position')
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

    logger.info("\n" + "=" * 80)
    logger.info("Training complete for all models")
    logger.info("=" * 80)

    return results
