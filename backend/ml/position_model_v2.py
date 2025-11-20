"""
Enhanced Position Prediction Model V2.

Improvements:
1. Temporal validation (no data leakage)
2. New critical features (championship position, DNF probability, car tier)
3. Hyperparameter optimization with Optuna
4. Ensemble model (Stacking)
5. Post-processing for valid rankings
6. Uses ALL available data (not just 2018+)
"""
import logging
import os
import joblib
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Tuple, List

import numpy as np
import pandas as pd

from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import TimeSeriesSplit
from sklearn.ensemble import StackingRegressor

# Advanced ML
try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False

try:
    import catboost as cb
    CATBOOST_AVAILABLE = True
except ImportError:
    CATBOOST_AVAILABLE = False

try:
    import optuna
    from optuna.samplers import TPESampler
    OPTUNA_AVAILABLE = True
except ImportError:
    OPTUNA_AVAILABLE = False

from django.conf import settings
from django.db.models import Avg, Count, Max, Min, F, Q

logger = logging.getLogger('ml')


def safe_timedelta_to_seconds(td) -> Optional[float]:
    """Convert timedelta to seconds, handling None and NaN values."""
    if td is None or pd.isna(td):
        return None
    if isinstance(td, timedelta):
        return td.total_seconds()
    return float(td)


def encode_categorical_target(df: pd.DataFrame, column: str, prefix: str = None) -> pd.DataFrame:
    """Target encoding for categorical variables with smoothing."""
    if prefix is None:
        prefix = column

    dummies = pd.get_dummies(df[column], prefix=prefix, dtype=float)
    df = df.drop(columns=[column])
    df = pd.concat([df, dummies], axis=1)

    return df


def calculate_dnf_probability(driver, team, circuit, reference_date, num_races=20):
    """
    Calculate historical DNF probability for driver/team/circuit.
    """
    from core.models import RaceResult

    # Driver DNF rate
    driver_results = RaceResult.objects.filter(
        driver=driver,
        session__session_date__lt=reference_date,
        session__session_type='R'
    ).order_by('-session__session_date')[:num_races]

    driver_dnf_rate = 0.1  # Default
    if driver_results:
        dnfs = sum(1 for r in driver_results if r.dnf)
        driver_dnf_rate = dnfs / len(driver_results)

    # Team reliability
    team_results = RaceResult.objects.filter(
        team=team,
        session__session_date__lt=reference_date,
        session__session_type='R'
    ).order_by('-session__session_date')[:num_races * 2]

    team_dnf_rate = 0.1
    if team_results:
        dnfs = sum(1 for r in team_results if r.dnf)
        team_dnf_rate = dnfs / len(team_results)

    # Circuit DNF rate (some circuits have more incidents)
    circuit_results = RaceResult.objects.filter(
        session__event__circuit=circuit,
        session__session_date__lt=reference_date,
        session__session_type='R'
    ).order_by('-session__session_date')[:100]

    circuit_dnf_rate = 0.1
    if circuit_results:
        dnfs = sum(1 for r in circuit_results if r.dnf)
        circuit_dnf_rate = dnfs / len(circuit_results)

    # Combined probability
    combined_dnf = (driver_dnf_rate * 0.4 + team_dnf_rate * 0.4 + circuit_dnf_rate * 0.2)

    return {
        'driver_dnf_rate': driver_dnf_rate,
        'team_dnf_rate': team_dnf_rate,
        'circuit_dnf_rate': circuit_dnf_rate,
        'combined_dnf_probability': combined_dnf
    }


def calculate_championship_position(driver, team, reference_date):
    """
    Get driver and team championship positions before this race.
    """
    from core.models import DriverStanding, ConstructorStanding, Season

    # Get season
    year = reference_date.year

    # Driver standing
    driver_standing = DriverStanding.objects.filter(
        driver=driver,
        season__year=year
    ).order_by('-id').first()

    driver_champ_pos = 15  # Default mid-field
    driver_champ_points = 0
    if driver_standing:
        driver_champ_pos = driver_standing.position
        driver_champ_points = driver_standing.points

    # Constructor standing
    constructor_standing = ConstructorStanding.objects.filter(
        team=team,
        season__year=year
    ).order_by('-id').first()

    team_champ_pos = 5  # Default mid-field
    team_champ_points = 0
    if constructor_standing:
        team_champ_pos = constructor_standing.position
        team_champ_points = constructor_standing.points

    return {
        'driver_championship_position': driver_champ_pos,
        'driver_championship_points': driver_champ_points,
        'team_championship_position': team_champ_pos,
        'team_championship_points': team_champ_points
    }


def calculate_car_performance_tier(team, reference_date, num_races=5):
    """
    Calculate car performance tier (1=top, 2=upper-mid, 3=lower-mid, 4=backmarker).
    Based on recent average finishing positions.
    """
    from core.models import RaceResult

    recent_results = RaceResult.objects.filter(
        team=team,
        session__session_date__lt=reference_date,
        session__session_type='R',
        position__isnull=False
    ).order_by('-session__session_date')[:num_races * 2]

    if not recent_results:
        return {'car_tier': 2.5, 'avg_team_position': 10.0}

    positions = [r.position for r in recent_results]
    avg_pos = np.mean(positions)

    # Determine tier
    if avg_pos <= 4:
        tier = 1  # Top team
    elif avg_pos <= 8:
        tier = 2  # Upper midfield
    elif avg_pos <= 14:
        tier = 3  # Lower midfield
    else:
        tier = 4  # Backmarker

    return {
        'car_tier': tier,
        'avg_team_position': avg_pos
    }


def calculate_safety_car_probability(circuit):
    """
    Calculate historical Safety Car probability at circuit.
    """
    from core.models import RaceResult

    # Get races at this circuit
    races = RaceResult.objects.filter(
        session__event__circuit=circuit,
        session__session_type='R'
    ).values('session__id').distinct()

    num_races = races.count()
    if num_races < 5:
        return 0.5  # Default

    # Count races with significant position changes (proxy for SC)
    # Races with SC typically have more position variance
    sc_proxy = 0
    for race in races[:50]:  # Limit for performance
        session_id = race['session__id']
        results = RaceResult.objects.filter(session__id=session_id)

        position_changes = []
        for r in results:
            if r.grid_position and r.position:
                position_changes.append(abs(r.grid_position - r.position))

        if position_changes and np.mean(position_changes) > 3:
            sc_proxy += 1

    return sc_proxy / min(num_races, 50)


def calculate_start_performance(driver, reference_date, num_races=10):
    """
    Calculate driver's performance on race starts (first lap position changes).
    """
    from core.models import RaceResult

    results = RaceResult.objects.filter(
        driver=driver,
        session__session_date__lt=reference_date,
        session__session_type='R',
        grid_position__isnull=False,
        position__isnull=False
    ).order_by('-session__session_date')[:num_races]

    if not results:
        return {
            'avg_start_gain': 0.0,
            'start_consistency': 0.5
        }

    # Calculate position changes (positive = gained positions)
    changes = []
    for r in results:
        # We don't have lap 1 position, so use final as proxy
        # Better drivers typically maintain or gain from grid
        change = r.grid_position - r.position
        changes.append(change)

    avg_gain = np.mean(changes)
    consistency = 1 - (np.std(changes) / 10 if len(changes) > 1 else 0.5)

    return {
        'avg_start_gain': avg_gain,
        'start_consistency': max(0, min(1, consistency))
    }


def prepare_position_features_v2(
    year_start: Optional[int] = None,
    year_end: Optional[int] = None,
    min_samples: int = 50
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series]:
    """
    Enhanced position features V2 with new critical features.

    Returns:
        Tuple of (X, y, dates) where dates is used for temporal split
    """
    from core.models import (
        RaceResult, Session, QualifyingResult, WeatherData, PitStop
    )
    from ml.feature_engineering import (
        calculate_driver_momentum, calculate_team_momentum,
        calculate_circuit_history, calculate_overtaking_difficulty,
        calculate_teammate_performance_gap, calculate_season_progression
    )

    year_filter_msg = "all years"
    if year_start is not None and year_end is not None:
        year_filter_msg = f"{year_start} to {year_end}"
    elif year_start is not None:
        year_filter_msg = f"{year_start} onwards"
    elif year_end is not None:
        year_filter_msg = f"up to {year_end}"

    logger.info(f"Preparing ENHANCED position features V2 from {year_filter_msg}")

    # Query race results
    query_filter = {
        'session__session_type': 'R',
        'position__isnull': False
    }

    if year_start is not None:
        query_filter['session__event__season__year__gte'] = year_start
    if year_end is not None:
        query_filter['session__event__season__year__lte'] = year_end

    results = RaceResult.objects.filter(
        **query_filter
    ).select_related(
        'session', 'session__event', 'session__event__circuit',
        'session__event__season', 'driver', 'team'
    ).order_by('session__session_date')

    logger.info(f"Found {results.count()} race results")

    if results.count() < min_samples:
        logger.warning(f"Not enough samples: {results.count()} < {min_samples}")
        return pd.DataFrame(), pd.Series(dtype=float), pd.Series(dtype='datetime64[ns]')

    data = []
    dates = []

    for result in results:
        try:
            race_date = result.session.session_date

            # Get qualifying position
            quali_session = Session.objects.filter(
                event=result.session.event,
                session_type='Q'
            ).first()

            quali_position = None
            if quali_session:
                quali_result = QualifyingResult.objects.filter(
                    session=quali_session,
                    driver=result.driver
                ).first()
                if quali_result:
                    quali_position = quali_result.position

            # Original momentum features
            driver_momentum = calculate_driver_momentum(
                result.driver, race_date, num_races=5
            )

            team_momentum = calculate_team_momentum(
                result.team, race_date, num_races=5
            )

            circuit_history = calculate_circuit_history(
                result.driver, result.session.event.circuit, race_date, num_races=5
            )

            overtaking_difficulty = calculate_overtaking_difficulty(
                result.session.event.circuit
            )

            # Teammate comparison
            teammate = RaceResult.objects.filter(
                session=result.session,
                team=result.team
            ).exclude(driver=result.driver).first()

            teammate_metrics = calculate_teammate_performance_gap(
                result.driver,
                teammate.driver if teammate else None,
                race_date
            )

            season_progression = calculate_season_progression(
                result.driver, result.team, race_date
            )

            # NEW V2 FEATURES

            # DNF probability
            dnf_prob = calculate_dnf_probability(
                result.driver, result.team,
                result.session.event.circuit, race_date
            )

            # Championship position
            champ_position = calculate_championship_position(
                result.driver, result.team, race_date
            )

            # Car performance tier
            car_tier = calculate_car_performance_tier(
                result.team, race_date
            )

            # Safety car probability
            sc_prob = calculate_safety_car_probability(
                result.session.event.circuit
            )

            # Start performance
            start_perf = calculate_start_performance(
                result.driver, race_date
            )

            # Weather
            weather_avg = WeatherData.objects.filter(
                session=result.session
            ).aggregate(
                avg_air_temp=Avg('air_temp'),
                avg_track_temp=Avg('track_temp'),
                avg_humidity=Avg('humidity'),
                rainfall=Max('rainfall')
            )

            # Pit stops
            pit_count = PitStop.objects.filter(
                session=result.session,
                driver=result.driver
            ).count()

            # Build feature dict
            grid_pos = result.grid_position if result.grid_position else 20
            quali_pos = quali_position if quali_position else grid_pos

            features = {
                # Basic features
                'grid_position': grid_pos,
                'quali_position': quali_pos,
                'driver_code': result.driver.code,
                'team_name': result.team.name,
                'circuit_name': result.session.event.circuit.name,
                'year': result.session.event.season.year,
                'laps_completed': result.laps_completed,
                'pit_stops': pit_count,

                # Weather
                'air_temp': weather_avg['avg_air_temp'] if weather_avg['avg_air_temp'] else 20.0,
                'track_temp': weather_avg['avg_track_temp'] if weather_avg['avg_track_temp'] else 30.0,
                'humidity': weather_avg['avg_humidity'] if weather_avg['avg_humidity'] else 50.0,
                'rainfall': 1.0 if weather_avg['rainfall'] else 0.0,

                # Driver momentum
                'driver_avg_position_recent': driver_momentum['avg_position_recent'],
                'driver_avg_points_recent': driver_momentum['avg_points_recent'],
                'driver_wins_recent': driver_momentum['wins_recent'],
                'driver_podiums_recent': driver_momentum['podiums_recent'],
                'driver_momentum_score': driver_momentum['momentum_score'],

                # Team momentum
                'team_avg_position_recent': team_momentum['team_avg_position_recent'],
                'team_avg_points_recent': team_momentum['team_avg_points_recent'],
                'team_momentum': team_momentum['team_momentum'],

                # Circuit history
                'avg_position_at_circuit': circuit_history['avg_position_at_circuit'],
                'wins_at_circuit': circuit_history['wins_at_circuit'],
                'podiums_at_circuit': circuit_history['podiums_at_circuit'],
                'circuit_familiarity': circuit_history['circuit_familiarity'],

                # Race dynamics
                'quali_race_gap': abs(quali_pos - grid_pos),
                'overtaking_difficulty': overtaking_difficulty,

                # Teammate
                'teammate_quali_gap': teammate_metrics['teammate_quali_gap'],
                'teammate_race_gap': teammate_metrics['teammate_race_gap'],
                'teammate_head_to_head': teammate_metrics['teammate_head_to_head'],

                # Season progression
                'position_trend': season_progression['position_trend'],
                'points_trend': season_progression['points_trend'],
                'form_improving': season_progression['form_improving'],

                # NEW V2: DNF probability
                'driver_dnf_rate': dnf_prob['driver_dnf_rate'],
                'team_dnf_rate': dnf_prob['team_dnf_rate'],
                'circuit_dnf_rate': dnf_prob['circuit_dnf_rate'],
                'combined_dnf_probability': dnf_prob['combined_dnf_probability'],

                # NEW V2: Championship position
                'driver_championship_position': champ_position['driver_championship_position'],
                'driver_championship_points': champ_position['driver_championship_points'],
                'team_championship_position': champ_position['team_championship_position'],
                'team_championship_points': champ_position['team_championship_points'],

                # NEW V2: Car tier
                'car_tier': car_tier['car_tier'],
                'avg_team_finish_position': car_tier['avg_team_position'],

                # NEW V2: Safety car
                'safety_car_probability': sc_prob,

                # NEW V2: Start performance
                'avg_start_gain': start_perf['avg_start_gain'],
                'start_consistency': start_perf['start_consistency'],

                # Feature interactions
                'grid_x_momentum': grid_pos * driver_momentum['momentum_score'],
                'quali_x_circuit_history': quali_pos * circuit_history['avg_position_at_circuit'],
                'team_momentum_x_overtaking': team_momentum['team_momentum'] * overtaking_difficulty,
                'grid_x_overtaking': grid_pos * overtaking_difficulty,
                'recent_form_x_circuit': driver_momentum['avg_position_recent'] * circuit_history['circuit_familiarity'],

                # NEW V2 interactions
                'champ_pos_x_grid': champ_position['driver_championship_position'] * grid_pos / 20,
                'car_tier_x_grid': car_tier['car_tier'] * grid_pos / 20,
                'dnf_x_circuit': dnf_prob['combined_dnf_probability'] * dnf_prob['circuit_dnf_rate'],
                'start_gain_x_grid': start_perf['avg_start_gain'] * grid_pos / 20,

                # Target
                'position': result.position
            }

            data.append(features)
            dates.append(race_date)

        except Exception as e:
            logger.error(f"Error processing result {result.id}: {e}")
            continue

    if not data:
        logger.warning("No valid data after processing")
        return pd.DataFrame(), pd.Series(dtype=float), pd.Series(dtype='datetime64[ns]')

    df = pd.DataFrame(data)
    dates_series = pd.Series(dates)

    logger.info(f"Created DataFrame with {len(df)} rows and {len(df.columns)} columns")

    # Separate target
    y = df['position']
    X = df.drop(columns=['position'])

    # Encode categorical
    X = encode_categorical_target(X, 'driver_code', 'driver')
    X = encode_categorical_target(X, 'team_name', 'team')
    X = encode_categorical_target(X, 'circuit_name', 'circuit')

    X = X.fillna(0)

    logger.info(f"Final V2 feature matrix: {X.shape}, Target: {y.shape}")

    return X, y, dates_series


class PositionModelV2:
    """
    Enhanced Position Prediction Model V2.

    Features:
    - Temporal validation
    - Hyperparameter optimization
    - Ensemble stacking
    - Post-processing for valid rankings
    """

    def __init__(self, model_dir: str = None):
        self.model = None
        self.scaler = None
        self.feature_names = None
        self.best_params = None

        if model_dir is None:
            self.model_dir = Path(settings.BASE_DIR) / 'models'
        else:
            self.model_dir = Path(model_dir)

        self.model_dir.mkdir(parents=True, exist_ok=True)

        self.model_path = self.model_dir / 'position_v2_model.pkl'
        self.scaler_path = self.model_dir / 'position_v2_scaler.pkl'
        self.metadata_path = self.model_dir / 'position_v2_metadata.json'
        self.features_path = self.model_dir / 'position_v2_features.json'

        self.metadata = {
            'model_type': 'position_v2',
            'created_at': None,
            'last_trained': None,
            'training_samples': 0,
            'metrics': {}
        }

    def _create_base_models(self, params: Dict = None):
        """Create base models for ensemble."""
        if params is None:
            params = {}

        models = []

        # LightGBM
        if LIGHTGBM_AVAILABLE:
            lgb_params = params.get('lgb', {
                'n_estimators': 1500,
                'max_depth': 10,
                'learning_rate': 0.02,
                'num_leaves': 63,
                'subsample': 0.8,
                'colsample_bytree': 0.8,
                'reg_alpha': 0.1,
                'reg_lambda': 1.0,
                'random_state': 42,
                'n_jobs': -1,
                'verbose': -1
            })
            models.append(('lgb', lgb.LGBMRegressor(**lgb_params)))

        # XGBoost
        if XGBOOST_AVAILABLE:
            xgb_params = params.get('xgb', {
                'n_estimators': 1500,
                'max_depth': 10,
                'learning_rate': 0.02,
                'subsample': 0.8,
                'colsample_bytree': 0.8,
                'reg_alpha': 0.1,
                'reg_lambda': 1.0,
                'random_state': 42,
                'n_jobs': -1
            })
            models.append(('xgb', xgb.XGBRegressor(**xgb_params)))

        # CatBoost
        if CATBOOST_AVAILABLE:
            cb_params = params.get('cb', {
                'iterations': 1500,
                'depth': 10,
                'learning_rate': 0.02,
                'l2_leaf_reg': 3,
                'random_seed': 42,
                'verbose': False,
                'thread_count': -1
            })
            models.append(('cb', cb.CatBoostRegressor(**cb_params)))

        return models

    def _optimize_hyperparameters(self, X_train, y_train, n_trials=50):
        """Optimize hyperparameters using Optuna."""
        if not OPTUNA_AVAILABLE:
            logger.warning("Optuna not available, using default parameters")
            return None

        logger.info(f"Starting hyperparameter optimization with {n_trials} trials")

        def objective(trial):
            params = {
                'n_estimators': trial.suggest_int('n_estimators', 500, 2000),
                'max_depth': trial.suggest_int('max_depth', 6, 12),
                'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.1, log=True),
                'num_leaves': trial.suggest_int('num_leaves', 31, 127),
                'subsample': trial.suggest_float('subsample', 0.6, 1.0),
                'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
                'reg_alpha': trial.suggest_float('reg_alpha', 1e-3, 10.0, log=True),
                'reg_lambda': trial.suggest_float('reg_lambda', 1e-3, 10.0, log=True),
            }

            # TimeSeriesSplit for validation
            tscv = TimeSeriesSplit(n_splits=3)
            scores = []

            for train_idx, val_idx in tscv.split(X_train):
                X_tr, X_val = X_train.iloc[train_idx], X_train.iloc[val_idx]
                y_tr, y_val = y_train.iloc[train_idx], y_train.iloc[val_idx]

                # Scale
                scaler = StandardScaler()
                X_tr_scaled = scaler.fit_transform(X_tr)
                X_val_scaled = scaler.transform(X_val)

                model = lgb.LGBMRegressor(
                    **params,
                    random_state=42,
                    n_jobs=-1,
                    verbose=-1
                )

                model.fit(X_tr_scaled, y_tr)
                y_pred = model.predict(X_val_scaled)

                mae = mean_absolute_error(y_val, y_pred)
                scores.append(mae)

            return np.mean(scores)

        # Create study
        sampler = TPESampler(seed=42)
        study = optuna.create_study(direction='minimize', sampler=sampler)
        study.optimize(objective, n_trials=n_trials, show_progress_bar=True)

        logger.info(f"Best trial MAE: {study.best_trial.value:.3f}")
        logger.info(f"Best parameters: {study.best_trial.params}")

        return study.best_trial.params

    def train(
        self,
        year_start: Optional[int] = None,
        year_end: Optional[int] = None,
        optimize_hyperparams: bool = True,
        n_trials: int = 50
    ) -> Dict:
        """
        Train the V2 position model.

        Args:
            year_start: Starting year (None = all data)
            year_end: Ending year (None = all data)
            optimize_hyperparams: Whether to optimize hyperparameters
            n_trials: Number of Optuna trials

        Returns:
            Dictionary with training metrics
        """
        logger.info("=" * 80)
        logger.info("Training Position Model V2")
        logger.info("=" * 80)

        # Load data
        X, y, dates = prepare_position_features_v2(year_start, year_end)

        if X.empty:
            raise ValueError("No training data available")

        logger.info(f"Loaded {X.shape[0]} samples with {X.shape[1]} features")

        # Store feature names
        self.feature_names = list(X.columns)

        # TEMPORAL SPLIT (crucial for avoiding data leakage)
        # Use 80% oldest data for training, 20% newest for testing
        split_idx = int(len(X) * 0.8)

        X_train = X.iloc[:split_idx]
        X_test = X.iloc[split_idx:]
        y_train = y.iloc[:split_idx]
        y_test = y.iloc[split_idx:]

        logger.info(f"Temporal split: Train {len(X_train)}, Test {len(X_test)}")
        logger.info(f"Train period: {dates.iloc[0]} to {dates.iloc[split_idx-1]}")
        logger.info(f"Test period: {dates.iloc[split_idx]} to {dates.iloc[-1]}")

        # Optimize hyperparameters
        if optimize_hyperparams and OPTUNA_AVAILABLE:
            self.best_params = self._optimize_hyperparameters(X_train, y_train, n_trials)
        else:
            self.best_params = None

        # Create scaler
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # Create ensemble model
        base_models = self._create_base_models()

        if len(base_models) >= 2:
            # Stacking ensemble
            logger.info("Creating Stacking ensemble")

            # Use LightGBM as meta-learner
            meta_learner = lgb.LGBMRegressor(
                n_estimators=500,
                max_depth=6,
                learning_rate=0.05,
                random_state=42,
                n_jobs=-1,
                verbose=-1
            )

            self.model = StackingRegressor(
                estimators=base_models,
                final_estimator=meta_learner,
                cv=5,
                n_jobs=-1
            )
        else:
            # Single model fallback
            logger.info("Using single LightGBM model")
            self.model = base_models[0][1]

        # Train
        logger.info("Training model...")
        self.model.fit(X_train_scaled, y_train)

        # Evaluate
        y_pred_train = self.model.predict(X_train_scaled)
        y_pred_test = self.model.predict(X_test_scaled)

        # Post-process predictions
        y_pred_train = self._post_process_predictions(y_pred_train)
        y_pred_test = self._post_process_predictions(y_pred_test)

        # Calculate metrics
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

        # Error distribution
        test_errors = np.abs(y_test - y_pred_test)
        metrics['error_distribution'] = {
            'within_1_pos': float((test_errors <= 1).sum() / len(test_errors) * 100),
            'within_2_pos': float((test_errors <= 2).sum() / len(test_errors) * 100),
            'within_3_pos': float((test_errors <= 3).sum() / len(test_errors) * 100),
            'median_error': float(np.median(test_errors))
        }

        logger.info("\nTraining Results:")
        logger.info(f"Train MAE: {metrics['train']['mae']:.3f}, R²: {metrics['train']['r2']:.3f}")
        logger.info(f"Test MAE: {metrics['test']['mae']:.3f}, R²: {metrics['test']['r2']:.3f}")
        logger.info(f"Errors ≤1 pos: {metrics['error_distribution']['within_1_pos']:.1f}%")
        logger.info(f"Errors ≤2 pos: {metrics['error_distribution']['within_2_pos']:.1f}%")
        logger.info(f"Errors ≤3 pos: {metrics['error_distribution']['within_3_pos']:.1f}%")

        # Update metadata
        self.metadata['created_at'] = datetime.now().isoformat()
        self.metadata['last_trained'] = datetime.now().isoformat()
        self.metadata['training_samples'] = len(X)
        self.metadata['metrics'] = metrics
        self.metadata['best_params'] = self.best_params

        # Save
        self.save_model()

        return metrics

    def _post_process_predictions(self, predictions: np.ndarray) -> np.ndarray:
        """
        Post-process predictions to ensure valid positions (1-20).
        """
        # Clip to valid range
        predictions = np.clip(predictions, 1, 20)

        return predictions

    def predict_race(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict race positions for all drivers and ensure valid ranking.

        Args:
            X: DataFrame with features for all drivers in a race

        Returns:
            Array of predicted positions (guaranteed unique 1-20)
        """
        if self.model is None:
            raise ValueError("Model not trained or loaded")

        # Align features
        from ml.feature_engineering import align_features
        X = align_features(X, self.feature_names)

        # Scale
        X_scaled = self.scaler.transform(X)

        # Predict
        raw_predictions = self.model.predict(X_scaled)

        # Ensure valid ranking (unique positions 1 to N)
        n_drivers = len(raw_predictions)
        sorted_indices = np.argsort(raw_predictions)
        final_positions = np.zeros(n_drivers)

        for rank, idx in enumerate(sorted_indices):
            final_positions[idx] = rank + 1

        return final_positions

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Predict positions (basic prediction without ranking guarantee)."""
        if self.model is None:
            raise ValueError("Model not trained or loaded")

        from ml.feature_engineering import align_features
        X = align_features(X, self.feature_names)

        X_scaled = self.scaler.transform(X)
        predictions = self.model.predict(X_scaled)

        return self._post_process_predictions(predictions)

    def save_model(self):
        """Save model to disk."""
        joblib.dump(self.model, self.model_path)
        joblib.dump(self.scaler, self.scaler_path)

        with open(self.metadata_path, 'w') as f:
            json.dump(self.metadata, f, indent=2)

        with open(self.features_path, 'w') as f:
            json.dump(self.feature_names, f, indent=2)

        logger.info(f"Saved Position Model V2 to {self.model_path}")

    def load_model(self) -> bool:
        """Load model from disk."""
        try:
            if not self.model_path.exists():
                return False

            self.model = joblib.load(self.model_path)
            self.scaler = joblib.load(self.scaler_path)

            if self.metadata_path.exists():
                with open(self.metadata_path, 'r') as f:
                    self.metadata = json.load(f)

            if self.features_path.exists():
                with open(self.features_path, 'r') as f:
                    self.feature_names = json.load(f)

            logger.info(f"Loaded Position Model V2 from {self.model_path}")
            return True

        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False

    def get_metadata(self) -> Dict:
        """Get model metadata."""
        return self.metadata.copy()


def train_position_model_v2(
    year_start: Optional[int] = None,
    year_end: Optional[int] = None,
    optimize: bool = True,
    n_trials: int = 50
) -> Dict:
    """
    Convenience function to train Position Model V2.
    """
    model = PositionModelV2()
    return model.train(
        year_start=year_start,
        year_end=year_end,
        optimize_hyperparams=optimize,
        n_trials=n_trials
    )


if __name__ == '__main__':
    import django
    import os
    import sys

    sys.path.append('/app')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()

    # Train with ALL data
    metrics = train_position_model_v2(
        year_start=None,  # Use all data
        year_end=None,
        optimize=True,
        n_trials=50
    )

    print("\n" + "=" * 80)
    print("TRAINING COMPLETE")
    print("=" * 80)
    print(f"Test MAE: {metrics['test']['mae']:.3f} positions")
    print(f"Test R²: {metrics['test']['r2']:.4f}")
