"""
Feature engineering module for F1 ML predictions.
Prepares features from database for model training and predictions.
"""
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

from django.db.models import Q, Avg, Count, Min, Max
from core.models import (
    LapTime, RaceResult, WeatherData, PitStop, TyreStrategy,
    Session, Driver, Team, Circuit, Event
)

logger = logging.getLogger('ml')


def safe_timedelta_to_seconds(td) -> Optional[float]:
    """Convert timedelta to seconds, handling None and NaN values."""
    if td is None or pd.isna(td):
        return None
    if isinstance(td, timedelta):
        return td.total_seconds()
    return float(td)


def encode_categorical(df: pd.DataFrame, column: str, prefix: str = None) -> pd.DataFrame:
    """
    One-hot encode a categorical column.

    Args:
        df: DataFrame with the column to encode
        column: Name of the column to encode
        prefix: Prefix for the new columns (defaults to column name)

    Returns:
        DataFrame with encoded columns
    """
    if prefix is None:
        prefix = column

    # Get dummies and ensure column names are strings
    dummies = pd.get_dummies(df[column], prefix=prefix, dtype=float)

    # Drop the original column and concatenate the dummies
    df = df.drop(columns=[column])
    df = pd.concat([df, dummies], axis=1)

    return df


def prepare_lap_time_features(
    year_start: int = 2018,
    year_end: Optional[int] = None,
    session_types: List[str] = None,
    min_samples: int = 100
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Prepare features for lap time prediction from database.

    Args:
        year_start: Starting year for data collection (default: 2018)
        year_end: Ending year for data collection (default: current year)
        session_types: List of session types to include (default: ['R', 'Q'])
        min_samples: Minimum number of samples required (default: 100)

    Returns:
        Tuple of (X, y) where:
        - X: DataFrame with features
        - y: Series with target (lap_time in seconds)
    """
    if year_end is None:
        year_end = datetime.now().year

    if session_types is None:
        session_types = ['R', 'Q']  # Race and Qualifying

    logger.info(f"Preparing lap time features from {year_start} to {year_end}")

    # Query lap times with related data
    lap_times = LapTime.objects.filter(
        session__event__season__year__gte=year_start,
        session__event__season__year__lte=year_end,
        session__session_type__in=session_types,
        is_accurate=True,
        lap_time__isnull=False
    ).select_related(
        'session', 'session__event', 'session__event__circuit',
        'session__event__season', 'driver', 'team'
    ).order_by('session__session_date', 'lap_number')

    logger.info(f"Found {lap_times.count()} lap times")

    if lap_times.count() < min_samples:
        logger.warning(f"Not enough samples: {lap_times.count()} < {min_samples}")
        return pd.DataFrame(), pd.Series(dtype=float)

    # Convert to list for processing
    data = []

    for lap in lap_times[:50000]:  # Limit to prevent memory issues
        try:
            # Get weather data for this lap (closest timestamp)
            weather = WeatherData.objects.filter(
                session=lap.session,
                timestamp__lte=lap.session.session_date + timedelta(
                    seconds=lap.lap_number * 90  # Approximate lap time
                )
            ).order_by('-timestamp').first()

            # Build feature dict
            features = {
                # Lap info
                'lap_number': lap.lap_number,
                'sector1_time': safe_timedelta_to_seconds(lap.sector1_time),
                'sector2_time': safe_timedelta_to_seconds(lap.sector2_time),
                'sector3_time': safe_timedelta_to_seconds(lap.sector3_time),

                # Tyre info
                'compound': lap.compound if lap.compound else 'UNKNOWN',
                'tyre_life': lap.tyre_life if lap.tyre_life else 0,

                # Session info
                'session_type': lap.session.session_type,
                'year': lap.session.event.season.year,

                # Driver and team
                'driver_code': lap.driver.code,
                'team_name': lap.team.name,

                # Circuit
                'circuit_name': lap.session.event.circuit.name,

                # Target
                'lap_time': safe_timedelta_to_seconds(lap.lap_time)
            }

            # Add weather features if available
            if weather:
                features['air_temp'] = weather.air_temp
                features['track_temp'] = weather.track_temp
                features['humidity'] = weather.humidity
                features['rainfall'] = 1.0 if weather.rainfall else 0.0
                features['wind_speed'] = weather.wind_speed if weather.wind_speed else 0.0
            else:
                features['air_temp'] = 20.0  # Default values
                features['track_temp'] = 30.0
                features['humidity'] = 50.0
                features['rainfall'] = 0.0
                features['wind_speed'] = 0.0

            data.append(features)

        except Exception as e:
            logger.error(f"Error processing lap {lap.id}: {e}")
            continue

    if not data:
        logger.warning("No valid data after processing")
        return pd.DataFrame(), pd.Series(dtype=float)

    # Convert to DataFrame
    df = pd.DataFrame(data)

    logger.info(f"Created DataFrame with {len(df)} rows and {len(df.columns)} columns")

    # Handle missing values in sector times
    # If any sector time is missing, we can't use this lap
    df = df.dropna(subset=['sector1_time', 'sector2_time', 'sector3_time', 'lap_time'])

    logger.info(f"After removing missing sectors: {len(df)} rows")

    # Separate features and target
    y = df['lap_time']
    X = df.drop(columns=['lap_time'])

    # Encode categorical variables
    X = encode_categorical(X, 'compound', 'compound')
    X = encode_categorical(X, 'session_type', 'session')
    X = encode_categorical(X, 'driver_code', 'driver')
    X = encode_categorical(X, 'team_name', 'team')
    X = encode_categorical(X, 'circuit_name', 'circuit')

    # Fill any remaining NaN values
    X = X.fillna(0)

    logger.info(f"Final feature matrix: {X.shape}, Target: {y.shape}")
    logger.info(f"Feature columns: {list(X.columns)}")

    return X, y


def prepare_position_features(
    year_start: int = 2018,
    year_end: Optional[int] = None,
    min_samples: int = 50
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Prepare features for race position prediction from database.

    Args:
        year_start: Starting year for data collection (default: 2018)
        year_end: Ending year for data collection (default: current year)
        min_samples: Minimum number of samples required (default: 50)

    Returns:
        Tuple of (X, y) where:
        - X: DataFrame with features
        - y: Series with target (final position)
    """
    if year_end is None:
        year_end = datetime.now().year

    logger.info(f"Preparing position features from {year_start} to {year_end}")

    # Query race results
    results = RaceResult.objects.filter(
        session__event__season__year__gte=year_start,
        session__event__season__year__lte=year_end,
        session__session_type='R'
    ).select_related(
        'session', 'session__event', 'session__event__circuit',
        'session__event__season', 'driver', 'team'
    ).order_by('session__session_date')

    logger.info(f"Found {results.count()} race results")

    if results.count() < min_samples:
        logger.warning(f"Not enough samples: {results.count()} < {min_samples}")
        return pd.DataFrame(), pd.Series(dtype=float)

    data = []

    for result in results:
        try:
            # Get driver's qualifying position for this race
            quali_session = Session.objects.filter(
                event=result.session.event,
                session_type='Q'
            ).first()

            quali_position = None
            if quali_session:
                from core.models import QualifyingResult
                quali_result = QualifyingResult.objects.filter(
                    session=quali_session,
                    driver=result.driver
                ).first()
                if quali_result:
                    quali_position = quali_result.position

            # Get average weather during race
            weather_avg = WeatherData.objects.filter(
                session=result.session
            ).aggregate(
                avg_air_temp=Avg('air_temp'),
                avg_track_temp=Avg('track_temp'),
                avg_humidity=Avg('humidity'),
                rainfall=Max('rainfall')
            )

            # Get pit stop count
            pit_count = PitStop.objects.filter(
                session=result.session,
                driver=result.driver
            ).count()

            # Build feature dict
            features = {
                # Grid position
                'grid_position': result.grid_position if result.grid_position else 20,
                'quali_position': quali_position if quali_position else result.grid_position if result.grid_position else 20,

                # Driver and team
                'driver_code': result.driver.code,
                'team_name': result.team.name,

                # Circuit
                'circuit_name': result.session.event.circuit.name,

                # Race info
                'year': result.session.event.season.year,
                'laps_completed': result.laps_completed,
                'pit_stops': pit_count,
                'dnf': 1.0 if result.dnf else 0.0,

                # Weather
                'air_temp': weather_avg['avg_air_temp'] if weather_avg['avg_air_temp'] else 20.0,
                'track_temp': weather_avg['avg_track_temp'] if weather_avg['avg_track_temp'] else 30.0,
                'humidity': weather_avg['avg_humidity'] if weather_avg['avg_humidity'] else 50.0,
                'rainfall': 1.0 if weather_avg['rainfall'] else 0.0,

                # Target
                'position': result.position
            }

            data.append(features)

        except Exception as e:
            logger.error(f"Error processing result {result.id}: {e}")
            continue

    if not data:
        logger.warning("No valid data after processing")
        return pd.DataFrame(), pd.Series(dtype=float)

    # Convert to DataFrame
    df = pd.DataFrame(data)

    logger.info(f"Created DataFrame with {len(df)} rows and {len(df.columns)} columns")

    # Separate features and target
    y = df['position']
    X = df.drop(columns=['position'])

    # Encode categorical variables
    X = encode_categorical(X, 'driver_code', 'driver')
    X = encode_categorical(X, 'team_name', 'team')
    X = encode_categorical(X, 'circuit_name', 'circuit')

    # Fill any remaining NaN values
    X = X.fillna(0)

    logger.info(f"Final feature matrix: {X.shape}, Target: {y.shape}")

    return X, y


def get_feature_names(X: pd.DataFrame) -> List[str]:
    """Get list of feature names from a DataFrame."""
    return list(X.columns)


def align_features(X: pd.DataFrame, feature_names: List[str]) -> pd.DataFrame:
    """
    Align features in X to match the expected feature names.
    Adds missing columns with zeros and removes extra columns.

    Args:
        X: DataFrame with features
        feature_names: Expected list of feature names

    Returns:
        DataFrame with aligned features
    """
    # Add missing columns with zeros
    for col in feature_names:
        if col not in X.columns:
            X[col] = 0.0

    # Remove extra columns
    X = X[feature_names]

    return X
