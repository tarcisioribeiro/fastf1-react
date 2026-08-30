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
from ml.factors import (
    compute_all_factors, factor_feature_vector, merge_factor_features,
)

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
        self.position_model_v2 = None  # New V2 model
        self.pole_position_model = None
        self.pole_time_model = None
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

        try:
            self.pole_time_model = F1PerformanceModel(model_type='pole_time')
            if self.pole_time_model.load_model():
                logger.info("Pole time model loaded successfully")
            else:
                logger.warning("No pole time model found")
                self.pole_time_model = None
        except Exception as e:
            logger.error(f"Error loading pole time model: {e}")
            self.pole_time_model = None

        # Load Position Model V2 (enhanced)
        try:
            from ml.position_model_v2 import PositionModelV2
            self.position_model_v2 = PositionModelV2()
            if self.position_model_v2.load_model():
                logger.info("Position model V2 loaded successfully")
            else:
                logger.warning("No position model V2 found")
                self.position_model_v2 = None
        except Exception as e:
            logger.error(f"Error loading position model V2: {e}")
            self.position_model_v2 = None

    def reload_models(self):
        """Reload models from disk (useful after training)."""
        logger.info("Reloading models")
        self._load_models()

    def _resolve_reference_date(self, circuit, year):
        """Data de referência para o cálculo dos fatores.

        Usa a data do evento nesse circuito/ano se existir; senão, agora.
        """
        from django.utils import timezone as _tz
        try:
            if circuit is not None:
                ev = Event.objects.filter(
                    season__year=year, circuit=circuit
                ).order_by('round_number').first()
                if ev and ev.event_date:
                    from datetime import datetime as _dt, time as _time
                    return _tz.make_aware(
                        _dt.combine(ev.event_date, _time(12, 0)),
                        _tz.get_current_timezone(),
                    )
        except Exception:
            pass
        return _tz.now()

    def compute_prediction_factors(self, driver=None, team=None, circuit=None,
                                   year=None):
        """Calcula os 5 fatores (regulamento, carro, clima, estratégia, forma).

        Retorna ``(factor_features, factors)`` onde ``factor_features`` é o
        vetor numérico para o ML e ``factors`` é o dict de ``FactorResult``.
        """
        if year is None:
            year = datetime.now().year
        ref_date = self._resolve_reference_date(circuit, year)
        try:
            factors = compute_all_factors(
                driver=driver, team=team, circuit=circuit, year=year,
                reference_date=ref_date,
            )
            merged = {}
            for fr in factors.values():
                merged.update(fr.features)
            return merge_factor_features(merged), factors
        except Exception as e:
            logger.warning(f"Erro ao calcular fatores de previsão: {e}")
            return merge_factor_features({}), {}

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

            # Align features to match training data
            if self.lap_time_model.feature_names:
                X = align_features(X, self.lap_time_model.feature_names)

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
        use_v2: bool = True,
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
            use_v2: Use the enhanced V2 model if available (default: True)
            **kwargs: Additional parameters

        Returns:
            Predicted position (float), or None if prediction fails
        """
        # Prefer V2 model if available and requested
        if use_v2 and self.position_model_v2 is not None:
            return self._predict_position_v2(
                driver_code, team_name, circuit_name, grid_position,
                quali_position, air_temp, track_temp, humidity, rainfall, **kwargs
            )

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
                'laps_completed': kwargs.get('laps_completed', 50),
                'pit_stops': kwargs.get('pit_stops', 2),
                'dnf': 0.0,
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

            # Align features to match training data
            if self.position_model.feature_names:
                X = align_features(X, self.position_model.feature_names)

            # Make prediction
            prediction = self.position_model.predict(X)

            return float(prediction[0])

        except Exception as e:
            logger.error(f"Error predicting position: {e}", exc_info=True)
            return None

    def _predict_position_v2(
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
        Predict position using enhanced V2 model.
        """
        try:
            if quali_position is None:
                quali_position = grid_position

            year = kwargs.get('year', datetime.now().year)

            # Build enhanced feature dict for V2 model
            features = {
                # Basic features
                'grid_position': grid_position,
                'quali_position': quali_position,
                'driver_code': driver_code,
                'team_name': team_name,
                'circuit_name': circuit_name,
                'year': year,
                'laps_completed': kwargs.get('laps_completed', 50),
                'pit_stops': kwargs.get('pit_stops', 2),

                # Weather
                'air_temp': air_temp,
                'track_temp': track_temp,
                'humidity': humidity,
                'rainfall': 1.0 if rainfall else 0.0,

                # Default values for enhanced features
                # These will be overwritten if kwargs provides them
                'driver_avg_position_recent': kwargs.get('driver_avg_position_recent', 10.0),
                'driver_avg_points_recent': kwargs.get('driver_avg_points_recent', 5.0),
                'driver_wins_recent': kwargs.get('driver_wins_recent', 0),
                'driver_podiums_recent': kwargs.get('driver_podiums_recent', 0),
                'driver_momentum_score': kwargs.get('driver_momentum_score', 0.5),

                'team_avg_position_recent': kwargs.get('team_avg_position_recent', 10.0),
                'team_avg_points_recent': kwargs.get('team_avg_points_recent', 10.0),
                'team_momentum': kwargs.get('team_momentum', 0.5),

                'avg_position_at_circuit': kwargs.get('avg_position_at_circuit', 10.0),
                'wins_at_circuit': kwargs.get('wins_at_circuit', 0),
                'podiums_at_circuit': kwargs.get('podiums_at_circuit', 0),
                'circuit_familiarity': kwargs.get('circuit_familiarity', 0.3),

                'quali_race_gap': abs(quali_position - grid_position),
                'overtaking_difficulty': kwargs.get('overtaking_difficulty', 0.5),

                'teammate_quali_gap': kwargs.get('teammate_quali_gap', 0.0),
                'teammate_race_gap': kwargs.get('teammate_race_gap', 0.0),
                'teammate_head_to_head': kwargs.get('teammate_head_to_head', 0.5),

                'position_trend': kwargs.get('position_trend', 0.0),
                'points_trend': kwargs.get('points_trend', 0.0),
                'form_improving': kwargs.get('form_improving', 0.0),

                # V2 specific features
                'driver_dnf_rate': kwargs.get('driver_dnf_rate', 0.1),
                'team_dnf_rate': kwargs.get('team_dnf_rate', 0.1),
                'circuit_dnf_rate': kwargs.get('circuit_dnf_rate', 0.1),
                'combined_dnf_probability': kwargs.get('combined_dnf_probability', 0.1),

                'driver_championship_position': kwargs.get('driver_championship_position', 10),
                'driver_championship_points': kwargs.get('driver_championship_points', 50),
                'team_championship_position': kwargs.get('team_championship_position', 5),
                'team_championship_points': kwargs.get('team_championship_points', 100),

                'car_tier': kwargs.get('car_tier', 2),
                'avg_team_finish_position': kwargs.get('avg_team_finish_position', 10.0),

                'safety_car_probability': kwargs.get('safety_car_probability', 0.5),

                'avg_start_gain': kwargs.get('avg_start_gain', 0.0),
                'start_consistency': kwargs.get('start_consistency', 0.5),

                # Interactions
                'grid_x_momentum': grid_position * kwargs.get('driver_momentum_score', 0.5),
                'quali_x_circuit_history': quali_position * kwargs.get('avg_position_at_circuit', 10.0),
                'team_momentum_x_overtaking': kwargs.get('team_momentum', 0.5) * kwargs.get('overtaking_difficulty', 0.5),
                'grid_x_overtaking': grid_position * kwargs.get('overtaking_difficulty', 0.5),
                'recent_form_x_circuit': kwargs.get('driver_avg_position_recent', 10.0) * kwargs.get('circuit_familiarity', 0.3),
                'champ_pos_x_grid': kwargs.get('driver_championship_position', 10) * grid_position / 20,
                'car_tier_x_grid': kwargs.get('car_tier', 2) * grid_position / 20,
                'dnf_x_circuit': kwargs.get('combined_dnf_probability', 0.1) * kwargs.get('circuit_dnf_rate', 0.1),
                'start_gain_x_grid': kwargs.get('avg_start_gain', 0.0) * grid_position / 20,
            }

            # Injeta as features dos 5 fatores (regulamento, carro, clima,
            # estratégia, forma) que ainda não estejam no dicionário.
            for _k, _v in kwargs.items():
                if _k in features:
                    continue
                if isinstance(_v, (int, float)) and not isinstance(_v, bool):
                    features[_k] = _v

            # Convert to DataFrame
            X = pd.DataFrame([features])

            # Encode categorical variables
            X = encode_categorical(X, 'driver_code', 'driver')
            X = encode_categorical(X, 'team_name', 'team')
            X = encode_categorical(X, 'circuit_name', 'circuit')

            # Make prediction
            prediction = self.position_model_v2.predict(X)

            return float(prediction[0])

        except Exception as e:
            logger.error(f"Error predicting position V2: {e}", exc_info=True)
            # Fallback to legacy model
            if self.position_model is not None:
                logger.info("Falling back to legacy position model")
                return self.predict_position(
                    driver_code, team_name, circuit_name, grid_position,
                    quali_position, air_temp, track_temp, humidity, rainfall,
                    use_v2=False, **kwargs
                )
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

            # Injeta features dos 5 fatores passadas via kwargs
            for _k, _v in kwargs.items():
                if _k in features:
                    continue
                if isinstance(_v, (int, float)) and not isinstance(_v, bool):
                    features[_k] = _v

            # Convert to DataFrame
            X = pd.DataFrame([features])

            # Encode categorical variables
            X = encode_categorical(X, 'driver_code', 'driver')
            X = encode_categorical(X, 'team_name', 'team')
            X = encode_categorical(X, 'circuit_name', 'circuit')

            # Align features to match training data
            if self.pole_position_model.feature_names:
                X = align_features(X, self.pole_position_model.feature_names)

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

    def predict_pole_time(
        self,
        circuit_id: int,
        year: int,
        air_temp: float = 20.0,
        track_temp: float = 30.0,
        humidity: float = 50.0,
        rainfall: bool = False,
        **kwargs
    ) -> Optional[Dict]:
        """
        Predict pole position lap time for a circuit.

        Args:
            circuit_id: Circuit database ID
            year: Year for prediction
            air_temp: Air temperature in Celsius
            track_temp: Track temperature in Celsius
            humidity: Humidity percentage
            rainfall: Whether it's raining
            **kwargs: Additional parameters

        Returns:
            Dictionary with predicted time and confidence, or None if prediction fails
        """
        if self.pole_time_model is None:
            logger.warning("Pole time model not available")
            return None

        try:
            # Get circuit
            circuit = Circuit.objects.get(id=circuit_id)

            # Get historical pole times at this circuit
            from core.models import QualifyingResult
            from ml.feature_engineering import safe_timedelta_to_seconds

            historical_poles = QualifyingResult.objects.filter(
                session__event__circuit=circuit,
                session__session_type='Q',
                position=1,
                q3_time__isnull=False
            ).order_by('-session__session_date')[:10]

            historical_times = []
            historical_years = []
            for h in historical_poles:
                h_time = safe_timedelta_to_seconds(h.q3_time)
                if h_time and h_time > 0:
                    historical_times.append(h_time)
                    historical_years.append(h.session.event.season.year)

            # Calculate historical statistics
            if historical_times:
                avg_pole_time = np.mean(historical_times)
                min_pole_time = np.min(historical_times)
                max_pole_time = np.max(historical_times)
                std_pole_time = np.std(historical_times) if len(historical_times) > 1 else 0.0
            else:
                # No historical data - use circuit length as estimate
                circuit_length = circuit.length_km if circuit.length_km else 5.0
                avg_pole_time = circuit_length * 18  # ~18s per km rough estimate
                min_pole_time = avg_pole_time
                max_pole_time = avg_pole_time
                std_pole_time = 0.0

            # Calculate time trend
            time_trend = 0.0
            if len(historical_times) >= 2 and len(historical_years) >= 2:
                x = np.array(historical_years)
                y_hist = np.array(historical_times)
                if len(set(x)) > 1:
                    slope = np.polyfit(x, y_hist, 1)[0]
                    time_trend = slope

            # Era indicator
            era = 4 if year >= 2022 else 3 if year >= 2017 else 2 if year >= 2014 else 1

            # Circuit characteristics
            circuit_length = circuit.length_km if circuit.length_km else 5.0
            num_corners = circuit.number_of_corners if circuit.number_of_corners else 15

            # Circuit type score
            circuit_type_score = 0.5
            if circuit.circuit_type:
                if 'street' in circuit.circuit_type.lower():
                    circuit_type_score = 1.0
                elif 'permanent' in circuit.circuit_type.lower():
                    circuit_type_score = 0.0

            # Direction
            is_clockwise = 1.0 if hasattr(circuit, 'direction') and circuit.direction == 'clockwise' else 0.0

            # Altitude effect
            altitude_effect = abs(circuit.latitude) / 90.0 if circuit.latitude else 0.0

            # Season progression (assume mid-season)
            season_progression = kwargs.get('round_number', 12) / 24.0

            # Build feature dict
            features = {
                'circuit_length_km': circuit_length,
                'number_of_corners': num_corners,
                'circuit_type_score': circuit_type_score,
                'is_clockwise': is_clockwise,
                'altitude_effect': altitude_effect,
                'year': year,
                'era': era,
                'season_progression': season_progression,
                'avg_pole_time_historical': avg_pole_time,
                'min_pole_time_historical': min_pole_time,
                'max_pole_time_historical': max_pole_time,
                'std_pole_time_historical': std_pole_time,
                'time_trend': time_trend,
                'num_historical_poles': len(historical_times),
                'air_temp': air_temp,
                'track_temp': track_temp,
                'humidity': humidity,
                'rainfall': 1.0 if rainfall else 0.0,
                'corners_per_km': num_corners / circuit_length if circuit_length > 0 else 3.0,
                'expected_time_per_km': avg_pole_time / circuit_length if circuit_length > 0 else 20.0,
                'year_normalized': (year - 2018) / 12.0,
                'length_x_corners': circuit_length * num_corners,
                'era_x_length': era * circuit_length,
                'temp_x_humidity': track_temp * humidity / 100.0,
                'circuit_name': circuit.name
            }

            # Create DataFrame
            X = pd.DataFrame([features])

            # Encode categorical
            from ml.feature_engineering import encode_categorical
            X = encode_categorical(X, 'circuit_name', 'circuit')

            # Align features
            if self.pole_time_model.feature_names:
                X = align_features(X, self.pole_time_model.feature_names)

            # Predict
            X_scaled = self.pole_time_model.scaler.transform(X)
            predicted_time = float(self.pole_time_model.model.predict(X_scaled)[0])

            # Calculate confidence based on historical data
            if len(historical_times) >= 3:
                confidence = 'high'
            elif len(historical_times) >= 1:
                confidence = 'medium'
            else:
                confidence = 'low'

            # Format time as mm:ss.sss
            minutes = int(predicted_time // 60)
            seconds = predicted_time % 60
            formatted_time = f"{minutes}:{seconds:06.3f}"

            return {
                'predicted_time_seconds': round(predicted_time, 3),
                'predicted_time_formatted': formatted_time,
                'confidence': confidence,
                'historical_avg': round(avg_pole_time, 3) if historical_times else None,
                'historical_min': round(min_pole_time, 3) if historical_times else None,
                'historical_max': round(max_pole_time, 3) if historical_times else None,
                'num_historical_samples': len(historical_times),
                'circuit': {
                    'id': circuit.id,
                    'name': circuit.name,
                    'length_km': circuit_length,
                    'corners': num_corners
                }
            }

        except Circuit.DoesNotExist:
            logger.error(f"Circuit with id {circuit_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error predicting pole time: {e}", exc_info=True)
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
        team_name = kwargs.pop('team_name', None)
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

        # Calcula os 5 fatores (regulamento, carro, clima, estratégia, forma)
        # e injeta as features reais no lugar dos defaults fixos.
        team_obj = kwargs.pop('team_obj', None) or Team.objects.filter(name=team_name).first()
        factor_features, factors = self.compute_prediction_factors(
            driver=driver, team=team_obj, circuit=circuit, year=year,
        )
        for _k, _v in factor_features.items():
            kwargs.setdefault(_k, _v)

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
            },
            'factors': {k: fr.as_applied() for k, fr in factors.items()},
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

        # Fatores no nível da equipe (regulamento, carro, clima do circuito,
        # estratégia) — sem piloto específico
        team_factor_features, team_factors = self.compute_prediction_factors(
            driver=None, team=team, circuit=circuit, year=year,
        )

        # Predict for each driver
        driver_predictions = []
        for driver in drivers:
            pred = self.predict_driver_performance(
                driver=driver,
                circuit=circuit,
                year=year,
                team_name=team.name,
                team_obj=team,
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
            },
            'factors': {k: fr.as_applied() for k, fr in team_factors.items()},
        }

    def is_ready(self) -> bool:
        """Check if predictor has models loaded and ready."""
        return self.lap_time_model is not None or self.position_model is not None

    def get_model_info(self) -> Dict:
        """Get information about loaded models."""
        return {
            'lap_time': self.lap_time_model.get_metadata() if self.lap_time_model else None,
            'position': self.position_model.get_metadata() if self.position_model else None,
            'position_v2': self.position_model_v2.get_metadata() if self.position_model_v2 else None,
            'pole_position': self.pole_position_model.get_metadata() if self.pole_position_model else None,
            'pole_time': self.pole_time_model.get_metadata() if self.pole_time_model else None,
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
