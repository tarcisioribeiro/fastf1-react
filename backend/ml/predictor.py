"""
Prediction module for F1 ML models.
Provides easy-to-use prediction functions for API endpoints.
"""
import logging
from typing import Dict, Optional, List
from datetime import datetime

import pandas as pd
import numpy as np

from core.models import Driver, Team, Circuit, Session, Event, Season
from ml.trainer import F1PerformanceModel
from ml.feature_engineering import encode_categorical, align_features

logger = logging.getLogger('ml')


class F1Predictor:
    """
    High-level predictor for F1 performance predictions.
    Handles model loading and feature preparation for predictions.
    """

    def __init__(self):
        """Initialize predictor and load models."""
        self.lap_time_model = None
        self.position_model = None
        self.pole_position_model = None
        self._load_models()

    def _load_models(self):
        """Load all available models."""
        try:
            self.lap_time_model = F1PerformanceModel(model_type='lap_time')
            if self.lap_time_model.load_model():
                logger.info("Lap time model loaded successfully")
            else:
                logger.warning("No lap time model found")
                self.lap_time_model = None
        except Exception as e:
            logger.error(f"Error loading lap time model: {e}")
            self.lap_time_model = None

        try:
            self.position_model = F1PerformanceModel(model_type='position')
            if self.position_model.load_model():
                logger.info("Position model loaded successfully")
            else:
                logger.warning("No position model found")
                self.position_model = None
        except Exception as e:
            logger.error(f"Error loading position model: {e}")
            self.position_model = None

        try:
            self.pole_position_model = F1PerformanceModel(model_type='pole_position')
            if self.pole_position_model.load_model():
                logger.info("Pole position model loaded successfully")
            else:
                logger.warning("No pole position model found")
                self.pole_position_model = None
        except Exception as e:
            logger.error(f"Error loading pole position model: {e}")
            self.pole_position_model = None

    def reload_models(self):
        """Reload models from disk (useful after training)."""
        logger.info("Reloading models")
        self._load_models()

    def predict_lap_time(
        self,
        driver_code: str,
        team_name: str,
        circuit_name: str,
        session_type: str = 'R',
        lap_number: int = 1,
        compound: str = 'SOFT',
        tyre_life: int = 0,
        air_temp: float = 20.0,
        track_temp: float = 30.0,
        humidity: float = 50.0,
        rainfall: bool = False,
        **kwargs
    ) -> Optional[float]:
        """
        Predict lap time for given conditions.

        Args:
            driver_code: Driver 3-letter code (e.g., 'VER')
            team_name: Team name (e.g., 'Red Bull Racing')
            circuit_name: Circuit name (e.g., 'Monaco')
            session_type: Session type ('R', 'Q', etc.)
            lap_number: Lap number
            compound: Tyre compound
            tyre_life: Tyre age in laps
            air_temp: Air temperature in Celsius
            track_temp: Track temperature in Celsius
            humidity: Humidity percentage
            rainfall: Whether it's raining
            **kwargs: Additional parameters

        Returns:
            Predicted lap time in seconds, or None if prediction fails
        """
        if self.lap_time_model is None:
            logger.warning("Lap time model not available")
            return None

        try:
            # Build feature dict
            # Note: sector times are not available for prediction, so we skip them
            # The model should be trained to handle missing sector times or we provide estimates
            features = {
                'lap_number': lap_number,
                'sector1_time': kwargs.get('sector1_time', 25.0),  # Default estimate
                'sector2_time': kwargs.get('sector2_time', 25.0),
                'sector3_time': kwargs.get('sector3_time', 25.0),
                'compound': compound,
                'tyre_life': tyre_life,
                'session_type': session_type,
                'year': kwargs.get('year', datetime.now().year),
                'driver_code': driver_code,
                'team_name': team_name,
                'circuit_name': circuit_name,
                'air_temp': air_temp,
                'track_temp': track_temp,
                'humidity': humidity,
                'rainfall': 1.0 if rainfall else 0.0,
                'wind_speed': kwargs.get('wind_speed', 0.0)
            }

            # Convert to DataFrame
            X = pd.DataFrame([features])

            # Encode categorical variables (matching training)
            X = encode_categorical(X, 'compound', 'compound')
            X = encode_categorical(X, 'session_type', 'session')
            X = encode_categorical(X, 'driver_code', 'driver')
            X = encode_categorical(X, 'team_name', 'team')
            X = encode_categorical(X, 'circuit_name', 'circuit')

            # Make prediction
            prediction = self.lap_time_model.predict(X)

            return float(prediction[0])

        except Exception as e:
            logger.error(f"Error predicting lap time: {e}", exc_info=True)
            return None

    def predict_position(
        self,
        driver_code: str,
        team_name: str,
        circuit_name: str,
        grid_position: int = 10,
        quali_position: Optional[int] = None,
        air_temp: float = 20.0,
        track_temp: float = 30.0,
        humidity: float = 50.0,
        rainfall: bool = False,
        **kwargs
    ) -> Optional[float]:
        """
        Predict race finishing position.

        Args:
            driver_code: Driver 3-letter code
            team_name: Team name
            circuit_name: Circuit name
            grid_position: Starting grid position
            quali_position: Qualifying position (defaults to grid_position)
            air_temp: Air temperature in Celsius
            track_temp: Track temperature in Celsius
            humidity: Humidity percentage
            rainfall: Whether it's raining
            **kwargs: Additional parameters

        Returns:
            Predicted position (float), or None if prediction fails
        """
        if self.position_model is None:
            logger.warning("Position model not available")
            return None

        try:
            if quali_position is None:
                quali_position = grid_position

            # Build feature dict
            features = {
                'grid_position': grid_position,
                'quali_position': quali_position,
                'driver_code': driver_code,
                'team_name': team_name,
                'circuit_name': circuit_name,
                'year': kwargs.get('year', datetime.now().year),
                'laps_completed': kwargs.get('laps_completed', 50),  # Default estimate
                'pit_stops': kwargs.get('pit_stops', 2),  # Default estimate
                'dnf': 0.0,  # Assume finish
                'air_temp': air_temp,
                'track_temp': track_temp,
                'humidity': humidity,
                'rainfall': 1.0 if rainfall else 0.0
            }

            # Convert to DataFrame
            X = pd.DataFrame([features])

            # Encode categorical variables
            X = encode_categorical(X, 'driver_code', 'driver')
            X = encode_categorical(X, 'team_name', 'team')
            X = encode_categorical(X, 'circuit_name', 'circuit')

            # Make prediction
            prediction = self.position_model.predict(X)

            return float(prediction[0])

        except Exception as e:
            logger.error(f"Error predicting position: {e}", exc_info=True)
            return None

    def predict_pole_position(
        self,
        driver_code: str,
        team_name: str,
        circuit_name: str,
        air_temp: float = 20.0,
        track_temp: float = 30.0,
        humidity: float = 50.0,
        rainfall: bool = False,
        **kwargs
    ) -> Optional[Dict]:
        """
        Predict probability of pole position for a driver.

        Args:
            driver_code: Driver 3-letter code
            team_name: Team name
            circuit_name: Circuit name
            air_temp: Air temperature in Celsius
            track_temp: Track temperature in Celsius
            humidity: Humidity percentage
            rainfall: Whether it's raining
            **kwargs: Additional parameters

        Returns:
            Dictionary with pole prediction probability and confidence
        """
        if self.pole_position_model is None:
            logger.warning("Pole position model not available")
            return None

        try:
            # Get historical qualifying data for momentum features
            from core.models import QualifyingResult
            from ml.feature_engineering import calculate_driver_momentum

            # Build feature dict with defaults for features the model expects
            features = {
                'driver_code': driver_code,
                'team_name': team_name,
                'circuit_name': circuit_name,
                'year': kwargs.get('year', datetime.now().year),

                # Recent quali performance (defaults if no history)
                'avg_quali_position_recent': kwargs.get('avg_quali_position_recent', 10.0),
                'poles_recent': kwargs.get('poles_recent', 0),
                'front_row_recent': kwargs.get('front_row_recent', 0),

                # Circuit-specific quali
                'avg_quali_position_at_circuit': kwargs.get('avg_quali_position_at_circuit', 10.0),
                'poles_at_circuit': kwargs.get('poles_at_circuit', 0),

                # Team quali performance
                'team_avg_quali_position': kwargs.get('team_avg_quali_position', 10.0),

                # Weather
                'air_temp': air_temp,
                'track_temp': track_temp,
                'humidity': humidity,
                'rainfall': 1.0 if rainfall else 0.0
            }

            # Convert to DataFrame
            X = pd.DataFrame([features])

            # Encode categorical variables
            X = encode_categorical(X, 'driver_code', 'driver')
            X = encode_categorical(X, 'team_name', 'team')
            X = encode_categorical(X, 'circuit_name', 'circuit')

            # Get probability prediction
            if hasattr(self.pole_position_model.model, 'predict_proba'):
                proba = self.pole_position_model.model.predict_proba(
                    self.pole_position_model.scaler.transform(X)
                )
                pole_probability = float(proba[0][1])  # Probability of class 1 (pole)
            else:
                # Fallback to binary prediction
                prediction = self.pole_position_model.predict(X)
                pole_probability = float(prediction[0])

            return {
                'probability': pole_probability,
                'confidence': 'high' if pole_probability > 0.7 else 'medium' if pole_probability > 0.3 else 'low',
                'percentage': round(pole_probability * 100, 2)
            }

        except Exception as e:
            logger.error(f"Error predicting pole position: {e}", exc_info=True)
            return None

    def predict_driver_performance(
        self,
        driver: Driver,
        circuit: Circuit,
        year: Optional[int] = None,
        **kwargs
    ) -> Dict:
        """
        Predict comprehensive driver performance at a circuit.

        Args:
            driver: Driver object
            circuit: Circuit object
            year: Year for prediction (default: current year)
            **kwargs: Additional parameters (team, weather, etc.)

        Returns:
            Dictionary with predictions
        """
        if year is None:
            year = datetime.now().year

        # Get driver's current team (or from kwargs)
        team_name = kwargs.get('team_name')
        if team_name is None:
            # Try to get from latest race result
            from core.models import RaceResult
            latest_result = RaceResult.objects.filter(
                driver=driver
            ).select_related('team').order_by('-session__session_date').first()

            if latest_result:
                team_name = latest_result.team.name
            else:
                team_name = 'Unknown'

        # Predict average lap time
        avg_lap_time = self.predict_lap_time(
            driver_code=driver.code,
            team_name=team_name,
            circuit_name=circuit.name,
            session_type='R',
            lap_number=25,  # Mid-race
            **kwargs
        )

        # Predict qualifying lap time
        quali_lap_time = self.predict_lap_time(
            driver_code=driver.code,
            team_name=team_name,
            circuit_name=circuit.name,
            session_type='Q',
            lap_number=1,
            compound='SOFT',
            **kwargs
        )

        # Predict race position (estimate grid position from quali)
        estimated_grid = kwargs.get('grid_position', 10)
        predicted_position = self.predict_position(
            driver_code=driver.code,
            team_name=team_name,
            circuit_name=circuit.name,
            grid_position=estimated_grid,
            **kwargs
        )

        return {
            'driver': {
                'code': driver.code,
                'name': driver.full_name
            },
            'team': team_name,
            'circuit': {
                'name': circuit.name,
                'location': circuit.location
            },
            'predictions': {
                'race_lap_time': avg_lap_time,
                'qualifying_lap_time': quali_lap_time,
                'predicted_position': predicted_position,
                'position_range': {
                    'min': max(1, int(predicted_position) - 2) if predicted_position else None,
                    'max': min(20, int(predicted_position) + 2) if predicted_position else None
                }
            },
            'model_info': {
                'lap_time_model': self.lap_time_model.get_metadata() if self.lap_time_model else None,
                'position_model': self.position_model.get_metadata() if self.position_model else None
            }
        }

    def predict_constructor_performance(
        self,
        team: Team,
        circuit: Circuit,
        year: Optional[int] = None,
        **kwargs
    ) -> Dict:
        """
        Predict comprehensive constructor performance at a circuit.

        Args:
            team: Team object
            circuit: Circuit object
            year: Year for prediction (default: current year)
            **kwargs: Additional parameters

        Returns:
            Dictionary with predictions
        """
        if year is None:
            year = datetime.now().year

        # Get team's drivers for this year
        from core.models import RaceResult
        drivers = Driver.objects.filter(
            race_results__team=team,
            race_results__session__event__season__year=year
        ).distinct()[:2]  # Get top 2 drivers

        if not drivers:
            # Fallback to any drivers from recent years
            drivers = Driver.objects.filter(
                race_results__team=team
            ).distinct().order_by('-race_results__session__session_date')[:2]

        # Predict for each driver
        driver_predictions = []
        for driver in drivers:
            pred = self.predict_driver_performance(
                driver=driver,
                circuit=circuit,
                year=year,
                team_name=team.name,
                **kwargs
            )
            driver_predictions.append(pred)

        # Aggregate team predictions
        avg_position = None
        if driver_predictions and all(p['predictions']['predicted_position'] for p in driver_predictions):
            positions = [p['predictions']['predicted_position'] for p in driver_predictions]
            avg_position = sum(positions) / len(positions)

        return {
            'team': {
                'name': team.name,
                'color': team.color
            },
            'circuit': {
                'name': circuit.name,
                'location': circuit.location
            },
            'predictions': {
                'average_position': avg_position,
                'drivers': driver_predictions
            },
            'model_info': {
                'lap_time_model': self.lap_time_model.get_metadata() if self.lap_time_model else None,
                'position_model': self.position_model.get_metadata() if self.position_model else None
            }
        }

    def is_ready(self) -> bool:
        """Check if predictor has models loaded and ready."""
        return self.lap_time_model is not None or self.position_model is not None

    def get_model_info(self) -> Dict:
        """Get information about loaded models."""
        return {
            'lap_time': self.lap_time_model.get_metadata() if self.lap_time_model else None,
            'position': self.position_model.get_metadata() if self.position_model else None,
            'pole_position': self.pole_position_model.get_metadata() if self.pole_position_model else None,
            'ready': self.is_ready()
        }


# Global predictor instance (singleton)
_predictor_instance = None


def get_predictor() -> F1Predictor:
    """Get or create global predictor instance."""
    global _predictor_instance
    if _predictor_instance is None:
        _predictor_instance = F1Predictor()
    return _predictor_instance


def reload_predictor():
    """Reload predictor models (call after training)."""
    global _predictor_instance
    if _predictor_instance is not None:
        _predictor_instance.reload_models()
    else:
        _predictor_instance = F1Predictor()
