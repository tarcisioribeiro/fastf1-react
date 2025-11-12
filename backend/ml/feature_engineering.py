"""
Feature engineering module for F1 ML predictions.
Prepares features from database for model training and predictions.

Enhanced with advanced features for improved prediction accuracy:
- Recent performance metrics (momentum)
- Circuit-specific historical data
- Team performance trends
- Weather impact factors
"""
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

from django.db.models import Q, Avg, Count, Min, Max, F
from core.models import (
    LapTime, RaceResult, WeatherData, PitStop, TyreStrategy,
    Session, Driver, Team, Circuit, Event, QualifyingResult
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


def calculate_driver_momentum(driver, reference_date, num_races=5):
    """
    Calculate driver's recent performance momentum.

    Args:
        driver: Driver object
        reference_date: Date to calculate momentum from
        num_races: Number of recent races to consider

    Returns:
        Dict with momentum metrics
    """
    recent_results = RaceResult.objects.filter(
        driver=driver,
        session__session_date__lt=reference_date,
        session__session_type='R'
    ).order_by('-session__session_date')[:num_races]

    if not recent_results:
        return {
            'avg_position_recent': 15.0,
            'avg_points_recent': 0.0,
            'wins_recent': 0,
            'podiums_recent': 0,
            'momentum_score': 0.0
        }

    positions = [r.position for r in recent_results if r.position]
    points = [r.points for r in recent_results if r.points]

    avg_pos = sum(positions) / len(positions) if positions else 15.0
    avg_pts = sum(points) / len(points) if points else 0.0
    wins = sum(1 for r in recent_results if r.position == 1)
    podiums = sum(1 for r in recent_results if r.position in [1, 2, 3])

    # Momentum score: weighted by recency (exponential decay)
    momentum = 0.0
    for i, result in enumerate(recent_results):
        if result.position:
            weight = np.exp(-0.3 * i)  # Exponential decay
            # Better position = higher score
            position_score = (21 - result.position) / 20.0
            momentum += position_score * weight

    momentum = momentum / sum(np.exp(-0.3 * i) for i in range(len(recent_results))) if recent_results else 0.0

    return {
        'avg_position_recent': avg_pos,
        'avg_points_recent': avg_pts,
        'wins_recent': wins,
        'podiums_recent': podiums,
        'momentum_score': momentum
    }


def calculate_team_momentum(team, reference_date, num_races=5):
    """
    Calculate team's recent performance momentum.

    Args:
        team: Team object
        reference_date: Date to calculate momentum from
        num_races: Number of recent races to consider

    Returns:
        Dict with team momentum metrics
    """
    recent_results = RaceResult.objects.filter(
        team=team,
        session__session_date__lt=reference_date,
        session__session_type='R'
    ).order_by('-session__session_date')[:num_races * 2]  # Both drivers

    if not recent_results:
        return {
            'team_avg_position_recent': 15.0,
            'team_avg_points_recent': 0.0,
            'team_momentum': 0.0
        }

    positions = [r.position for r in recent_results if r.position]
    points = [r.points for r in recent_results if r.points]

    avg_pos = sum(positions) / len(positions) if positions else 15.0
    avg_pts = sum(points) / len(points) if points else 0.0

    # Team momentum
    momentum = 0.0
    for i, result in enumerate(recent_results):
        if result.position:
            weight = np.exp(-0.3 * i)
            position_score = (21 - result.position) / 20.0
            momentum += position_score * weight

    momentum = momentum / sum(np.exp(-0.3 * i) for i in range(len(recent_results))) if recent_results else 0.0

    return {
        'team_avg_position_recent': avg_pos,
        'team_avg_points_recent': avg_pts,
        'team_momentum': momentum
    }


def calculate_circuit_history(driver, circuit, reference_date, num_races=5):
    """
    Calculate driver's historical performance at a specific circuit.

    Args:
        driver: Driver object
        circuit: Circuit object
        reference_date: Date to look back from
        num_races: Number of races at this circuit to consider

    Returns:
        Dict with circuit-specific metrics
    """
    circuit_results = RaceResult.objects.filter(
        driver=driver,
        session__event__circuit=circuit,
        session__session_date__lt=reference_date,
        session__session_type='R'
    ).order_by('-session__session_date')[:num_races]

    if not circuit_results:
        return {
            'avg_position_at_circuit': 15.0,
            'wins_at_circuit': 0,
            'podiums_at_circuit': 0,
            'circuit_familiarity': 0.0
        }

    positions = [r.position for r in circuit_results if r.position]
    avg_pos = sum(positions) / len(positions) if positions else 15.0
    wins = sum(1 for r in circuit_results if r.position == 1)
    podiums = sum(1 for r in circuit_results if r.position in [1, 2, 3])

    # Familiarity: more races = better familiarity
    familiarity = min(len(circuit_results) / 10.0, 1.0)

    return {
        'avg_position_at_circuit': avg_pos,
        'wins_at_circuit': wins,
        'podiums_at_circuit': podiums,
        'circuit_familiarity': familiarity
    }


def prepare_position_features_enhanced(
    year_start: int = 2018,
    year_end: Optional[int] = None,
    min_samples: int = 50
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    ENHANCED version of prepare_position_features with advanced features.

    Includes:
    - Recent performance momentum
    - Circuit-specific history
    - Team performance trends
    - Qualifying-to-race conversion rates

    Args:
        year_start: Starting year for data collection (default: 2018)
        year_end: Ending year for data collection (default: current year)
        min_samples: Minimum number of samples required (default: 50)

    Returns:
        Tuple of (X, y) where:
        - X: DataFrame with enhanced features
        - y: Series with target (final position)
    """
    if year_end is None:
        year_end = datetime.now().year

    logger.info(f"Preparing ENHANCED position features from {year_start} to {year_end}")

    # Query race results
    results = RaceResult.objects.filter(
        session__event__season__year__gte=year_start,
        session__event__season__year__lte=year_end,
        session__session_type='R',
        position__isnull=False  # Only finished races
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
            # Get driver's qualifying position
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

            # Calculate momentum features
            driver_momentum = calculate_driver_momentum(
                result.driver,
                result.session.session_date,
                num_races=5
            )

            team_momentum = calculate_team_momentum(
                result.team,
                result.session.session_date,
                num_races=5
            )

            # Calculate circuit history
            circuit_history = calculate_circuit_history(
                result.driver,
                result.session.event.circuit,
                result.session.session_date,
                num_races=5
            )

            # Get weather
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

            # Build enhanced feature dict
            features = {
                # Basic grid info
                'grid_position': result.grid_position if result.grid_position else 20,
                'quali_position': quali_position if quali_position else (result.grid_position if result.grid_position else 20),

                # Driver and team (categorical)
                'driver_code': result.driver.code,
                'team_name': result.team.name,
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

                # ENHANCED: Driver momentum features
                'driver_avg_position_recent': driver_momentum['avg_position_recent'],
                'driver_avg_points_recent': driver_momentum['avg_points_recent'],
                'driver_wins_recent': driver_momentum['wins_recent'],
                'driver_podiums_recent': driver_momentum['podiums_recent'],
                'driver_momentum_score': driver_momentum['momentum_score'],

                # ENHANCED: Team momentum features
                'team_avg_position_recent': team_momentum['team_avg_position_recent'],
                'team_avg_points_recent': team_momentum['team_avg_points_recent'],
                'team_momentum': team_momentum['team_momentum'],

                # ENHANCED: Circuit-specific features
                'avg_position_at_circuit': circuit_history['avg_position_at_circuit'],
                'wins_at_circuit': circuit_history['wins_at_circuit'],
                'podiums_at_circuit': circuit_history['podiums_at_circuit'],
                'circuit_familiarity': circuit_history['circuit_familiarity'],

                # ENHANCED: Quali-to-race conversion
                'quali_race_gap': abs((quali_position if quali_position else 20) - (result.grid_position if result.grid_position else 20)),

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

    logger.info(f"Final ENHANCED feature matrix: {X.shape}, Target: {y.shape}")
    logger.info(f"Added {X.shape[1] - 20} enhanced features")

    return X, y


def prepare_pole_position_features(
    year_start: int = 2018,
    year_end: Optional[int] = None,
    min_samples: int = 50
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Prepare features for POLE POSITION (qualifying P1) prediction.

    Features include:
    - Recent qualifying performance
    - Historical pole positions
    - Circuit-specific qualifying performance
    - Team qualifying pace
    - Weather conditions

    Args:
        year_start: Starting year for data collection
        year_end: Ending year for data collection
        min_samples: Minimum number of samples required

    Returns:
        Tuple of (X, y) where:
        - X: DataFrame with features
        - y: Series with target (1 if pole, 0 otherwise)
    """
    if year_end is None:
        year_end = datetime.now().year

    logger.info(f"Preparing pole position features from {year_start} to {year_end}")

    # Query qualifying results
    results = QualifyingResult.objects.filter(
        session__event__season__year__gte=year_start,
        session__event__season__year__lte=year_end,
        session__session_type='Q',
        position__isnull=False
    ).select_related(
        'session', 'session__event', 'session__event__circuit',
        'session__event__season', 'driver', 'team'
    ).order_by('session__session_date')

    logger.info(f"Found {results.count()} qualifying results")

    if results.count() < min_samples:
        logger.warning(f"Not enough samples: {results.count()} < {min_samples}")
        return pd.DataFrame(), pd.Series(dtype=float)

    data = []

    for result in results:
        try:
            # Calculate recent qualifying momentum (last 5 qualifyings)
            recent_quali = QualifyingResult.objects.filter(
                driver=result.driver,
                session__session_date__lt=result.session.session_date,
                session__session_type='Q'
            ).order_by('-session__session_date')[:5]

            avg_quali_pos = 15.0
            poles_recent = 0
            front_row_recent = 0

            if recent_quali:
                positions = [r.position for r in recent_quali if r.position]
                avg_quali_pos = sum(positions) / len(positions) if positions else 15.0
                poles_recent = sum(1 for r in recent_quali if r.position == 1)
                front_row_recent = sum(1 for r in recent_quali if r.position in [1, 2])

            # Historical performance at this circuit in qualifying
            circuit_quali_history = QualifyingResult.objects.filter(
                driver=result.driver,
                session__event__circuit=result.session.event.circuit,
                session__session_date__lt=result.session.session_date,
                session__session_type='Q'
            ).order_by('-session__session_date')[:5]

            avg_quali_circuit = 15.0
            poles_at_circuit = 0

            if circuit_quali_history:
                positions = [r.position for r in circuit_quali_history if r.position]
                avg_quali_circuit = sum(positions) / len(positions) if positions else 15.0
                poles_at_circuit = sum(1 for r in circuit_quali_history if r.position == 1)

            # Team's recent qualifying performance
            team_quali = QualifyingResult.objects.filter(
                team=result.team,
                session__session_date__lt=result.session.session_date,
                session__session_type='Q'
            ).order_by('-session__session_date')[:10]

            team_avg_quali = 15.0
            if team_quali:
                positions = [r.position for r in team_quali if r.position]
                team_avg_quali = sum(positions) / len(positions) if positions else 15.0

            # Get weather during qualifying
            weather_avg = WeatherData.objects.filter(
                session=result.session
            ).aggregate(
                avg_air_temp=Avg('air_temp'),
                avg_track_temp=Avg('track_temp'),
                avg_humidity=Avg('humidity'),
                rainfall=Max('rainfall')
            )

            # Build feature dict
            features = {
                # Driver and identifiers
                'driver_code': result.driver.code,
                'team_name': result.team.name,
                'circuit_name': result.session.event.circuit.name,
                'year': result.session.event.season.year,

                # Recent qualifying performance
                'avg_quali_position_recent': avg_quali_pos,
                'poles_recent': poles_recent,
                'front_row_recent': front_row_recent,

                # Circuit-specific qualifying
                'avg_quali_position_at_circuit': avg_quali_circuit,
                'poles_at_circuit': poles_at_circuit,

                # Team qualifying performance
                'team_avg_quali_position': team_avg_quali,

                # Weather
                'air_temp': weather_avg['avg_air_temp'] if weather_avg['avg_air_temp'] else 20.0,
                'track_temp': weather_avg['avg_track_temp'] if weather_avg['avg_track_temp'] else 30.0,
                'humidity': weather_avg['avg_humidity'] if weather_avg['avg_humidity'] else 50.0,
                'rainfall': 1.0 if weather_avg['rainfall'] else 0.0,

                # Target: 1 if pole position, 0 otherwise
                'is_pole': 1.0 if result.position == 1 else 0.0
            }

            data.append(features)

        except Exception as e:
            logger.error(f"Error processing qualifying result {result.id}: {e}")
            continue

    if not data:
        logger.warning("No valid data after processing")
        return pd.DataFrame(), pd.Series(dtype=float)

    # Convert to DataFrame
    df = pd.DataFrame(data)

    logger.info(f"Created DataFrame with {len(df)} rows and {len(df.columns)} columns")

    # Separate features and target
    y = df['is_pole']
    X = df.drop(columns=['is_pole'])

    # Encode categorical variables
    X = encode_categorical(X, 'driver_code', 'driver')
    X = encode_categorical(X, 'team_name', 'team')
    X = encode_categorical(X, 'circuit_name', 'circuit')

    # Fill any remaining NaN values
    X = X.fillna(0)

    logger.info(f"Final pole position feature matrix: {X.shape}, Target: {y.shape}")
    logger.info(f"Pole positions in dataset: {y.sum()}")

    return X, y


def prepare_fastest_lap_features(
    year_start: int = 2018,
    year_end: Optional[int] = None,
    min_samples: int = 50
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Prepare features for FASTEST LAP prediction.

    Features include:
    - Recent fastest lap performance
    - Historical fastest laps
    - Race position (often low-positioned drivers go for fastest lap)
    - Tyre strategy
    - Weather conditions

    Args:
        year_start: Starting year for data collection
        year_end: Ending year for data collection
        min_samples: Minimum number of samples required

    Returns:
        Tuple of (X, y) where:
        - X: DataFrame with features
        - y: Series with target (1 if fastest lap, 0 otherwise)
    """
    if year_end is None:
        year_end = datetime.now().year

    logger.info(f"Preparing fastest lap features from {year_start} to {year_end}")

    # Query race results
    results = RaceResult.objects.filter(
        session__event__season__year__gte=year_start,
        session__event__season__year__lte=year_end,
        session__session_type='R',
        position__isnull=False
    ).select_related(
        'session', 'session__event', 'session__event__circuit',
        'session__event__season', 'driver', 'team'
    ).order_by('session__session_date')

    logger.info(f"Found {results.count()} race results")

    if results.count() < min_samples:
        logger.warning(f"Not enough samples: {results.count()} < {min_samples}")
        return pd.DataFrame(), pd.Series(dtype=float)

    # First pass: identify fastest lap for each session
    session_fastest_laps = {}
    for result in results:
        if result.fastest_lap_time:
            session_id = result.session.id
            lap_time_seconds = safe_timedelta_to_seconds(result.fastest_lap_time)

            if lap_time_seconds and lap_time_seconds > 0:
                if session_id not in session_fastest_laps:
                    session_fastest_laps[session_id] = {'time': lap_time_seconds, 'driver_id': result.driver.id}
                elif lap_time_seconds < session_fastest_laps[session_id]['time']:
                    session_fastest_laps[session_id] = {'time': lap_time_seconds, 'driver_id': result.driver.id}

    logger.info(f"Found {len(session_fastest_laps)} sessions with fastest lap data")

    data = []

    for result in results:
        try:
            # Check if this driver had fastest lap in this session
            session_id = result.session.id
            has_fastest_lap = False

            if session_id in session_fastest_laps:
                has_fastest_lap = session_fastest_laps[session_id]['driver_id'] == result.driver.id

            # Recent fastest lap history
            recent_races = RaceResult.objects.filter(
                driver=result.driver,
                session__session_date__lt=result.session.session_date,
                session__session_type='R',
                fastest_lap_time__isnull=False
            ).order_by('-session__session_date')[:10]

            # Count fastest laps in recent races
            fastest_laps_recent = 0
            avg_fastest_lap_time = 0.0

            if recent_races:
                times = []
                for r in recent_races:
                    # Check if this driver had fastest lap in that race
                    r_session_id = r.session.id
                    if r_session_id in session_fastest_laps:
                        if session_fastest_laps[r_session_id]['driver_id'] == result.driver.id:
                            fastest_laps_recent += 1

                    # Collect lap times for average
                    lap_time = safe_timedelta_to_seconds(r.fastest_lap_time)
                    if lap_time and lap_time > 0:
                        times.append(lap_time)

                avg_fastest_lap_time = sum(times) / len(times) if times else 0.0

            # Historical at circuit
            circuit_history = RaceResult.objects.filter(
                driver=result.driver,
                session__event__circuit=result.session.event.circuit,
                session__session_date__lt=result.session.session_date,
                session__session_type='R',
                fastest_lap_time__isnull=False
            ).order_by('-session__session_date')[:5]

            # Count fastest laps at this circuit
            fastest_laps_at_circuit = 0
            for r in circuit_history:
                r_session_id = r.session.id
                if r_session_id in session_fastest_laps:
                    if session_fastest_laps[r_session_id]['driver_id'] == result.driver.id:
                        fastest_laps_at_circuit += 1

            # Team performance
            team_recent = RaceResult.objects.filter(
                team=result.team,
                session__session_date__lt=result.session.session_date,
                session__session_type='R',
                fastest_lap_time__isnull=False
            ).order_by('-session__session_date')[:10]

            # Count team fastest laps
            team_fastest_laps = 0
            for r in team_recent:
                r_session_id = r.session.id
                if r_session_id in session_fastest_laps:
                    if session_fastest_laps[r_session_id]['driver_id'] in [driver.id for driver in [r.driver]]:
                        team_fastest_laps += 1

            # Get pit stop count (more stops = fresher tyres = better chance)
            pit_count = PitStop.objects.filter(
                session=result.session,
                driver=result.driver
            ).count()

            # Weather
            weather_avg = WeatherData.objects.filter(
                session=result.session
            ).aggregate(
                avg_air_temp=Avg('air_temp'),
                avg_track_temp=Avg('track_temp'),
                avg_humidity=Avg('humidity'),
                rainfall=Max('rainfall')
            )

            # Build feature dict
            features = {
                # Identifiers
                'driver_code': result.driver.code,
                'team_name': result.team.name,
                'circuit_name': result.session.event.circuit.name,
                'year': result.session.event.season.year,

                # Race position (often affects strategy)
                'race_position': result.position,
                'points_scored': result.points if result.points else 0.0,

                # Recent fastest lap performance
                'fastest_laps_recent': fastest_laps_recent,
                'avg_fastest_lap_time_recent': avg_fastest_lap_time,

                # Circuit-specific
                'fastest_laps_at_circuit': fastest_laps_at_circuit,

                # Team performance
                'team_fastest_laps_recent': team_fastest_laps,

                # Strategy
                'pit_stops': pit_count,

                # Weather
                'air_temp': weather_avg['avg_air_temp'] if weather_avg['avg_air_temp'] else 20.0,
                'track_temp': weather_avg['avg_track_temp'] if weather_avg['avg_track_temp'] else 30.0,
                'humidity': weather_avg['avg_humidity'] if weather_avg['avg_humidity'] else 50.0,
                'rainfall': 1.0 if weather_avg['rainfall'] else 0.0,

                # Target: 1 if fastest lap, 0 otherwise
                'has_fastest_lap': 1.0 if has_fastest_lap else 0.0
            }

            data.append(features)

        except Exception as e:
            logger.error(f"Error processing race result {result.id}: {e}")
            continue

    if not data:
        logger.warning("No valid data after processing")
        return pd.DataFrame(), pd.Series(dtype=float)

    # Convert to DataFrame
    df = pd.DataFrame(data)

    logger.info(f"Created DataFrame with {len(df)} rows and {len(df.columns)} columns")

    # Separate features and target
    y = df['has_fastest_lap']
    X = df.drop(columns=['has_fastest_lap'])

    # Encode categorical variables
    X = encode_categorical(X, 'driver_code', 'driver')
    X = encode_categorical(X, 'team_name', 'team')
    X = encode_categorical(X, 'circuit_name', 'circuit')

    # Fill any remaining NaN values
    X = X.fillna(0)

    logger.info(f"Final fastest lap feature matrix: {X.shape}, Target: {y.shape}")
    logger.info(f"Fastest laps in dataset: {y.sum()}")

    return X, y
