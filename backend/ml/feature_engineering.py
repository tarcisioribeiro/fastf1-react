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
    year_start: Optional[int] = None,
    year_end: Optional[int] = None,
    session_types: List[str] = None,
    min_samples: int = 100
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Prepare features for lap time prediction from database.

    Args:
        year_start: Starting year for data collection (default: None = all years)
        year_end: Ending year for data collection (default: None = all years)
        session_types: List of session types to include (default: ['R', 'Q'])
        min_samples: Minimum number of samples required (default: 100)

    Returns:
        Tuple of (X, y) where:
        - X: DataFrame with features
        - y: Series with target (lap_time in seconds)
    """
    if session_types is None:
        session_types = ['R', 'Q']  # Race and Qualifying

    year_filter_msg = "all years"
    if year_start is not None and year_end is not None:
        year_filter_msg = f"{year_start} to {year_end}"
    elif year_start is not None:
        year_filter_msg = f"{year_start} onwards"
    elif year_end is not None:
        year_filter_msg = f"up to {year_end}"

    logger.info(f"Preparing lap time features from {year_filter_msg}")

    # Query lap times with related data
    query_filter = {
        'session__session_type__in': session_types,
        'is_accurate': True,
        'lap_time__isnull': False
    }

    # Only add year filters if specified
    if year_start is not None:
        query_filter['session__event__season__year__gte'] = year_start
    if year_end is not None:
        query_filter['session__event__season__year__lte'] = year_end

    lap_times = LapTime.objects.filter(
        **query_filter
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
    year_start: Optional[int] = None,
    year_end: Optional[int] = None,
    min_samples: int = 50
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Prepare features for race position prediction from database.

    Args:
        year_start: Starting year for data collection (default: None = all years)
        year_end: Ending year for data collection (default: None = all years)
        min_samples: Minimum number of samples required (default: 50)

    Returns:
        Tuple of (X, y) where:
        - X: DataFrame with features
        - y: Series with target (final position)
    """
    year_filter_msg = "all years"
    if year_start is not None and year_end is not None:
        year_filter_msg = f"{year_start} to {year_end}"
    elif year_start is not None:
        year_filter_msg = f"{year_start} onwards"
    elif year_end is not None:
        year_filter_msg = f"up to {year_end}"

    logger.info(f"Preparing position features from {year_filter_msg}")

    # Query race results
    query_filter = {
        'session__session_type': 'R'
    }

    # Only add year filters if specified
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


def calculate_overtaking_difficulty(circuit):
    """
    Calculate overtaking difficulty score for a circuit based on historical data.

    Args:
        circuit: Circuit object

    Returns:
        Float score (0-1, higher = harder to overtake)
    """
    # Get historical position changes at this circuit
    from django.db.models import Avg, F

    # Calculate average grid-to-finish position change
    position_changes = RaceResult.objects.filter(
        session__event__circuit=circuit,
        session__session_type='R',
        grid_position__isnull=False,
        position__isnull=False
    ).annotate(
        position_change=F('grid_position') - F('position')
    ).aggregate(
        avg_change=Avg('position_change'),
        count=Count('id')
    )

    if position_changes['count'] and position_changes['count'] > 10:
        # Low average change = hard to overtake
        avg_change = abs(position_changes['avg_change']) if position_changes['avg_change'] else 0
        # Normalize to 0-1 (assuming typical range is 0-5 positions)
        overtaking_score = max(0, min(1, 1 - (avg_change / 5.0)))
        return overtaking_score

    return 0.5  # Default neutral score


def calculate_teammate_performance_gap(driver, teammate, reference_date):
    """
    Calculate performance gap between driver and teammate.

    Args:
        driver: Driver object
        teammate: Driver object (or None)
        reference_date: Date to calculate from

    Returns:
        Dict with teammate comparison metrics
    """
    if not teammate:
        return {
            'teammate_quali_gap': 0.0,
            'teammate_race_gap': 0.0,
            'teammate_head_to_head': 0.5
        }

    # Recent qualifying comparisons
    quali_comparisons = []

    # Get recent events where both qualified
    recent_events = Event.objects.filter(
        sessions__session_type='Q',
        sessions__session_date__lt=reference_date
    ).distinct().order_by('-event_date')[:10]

    for event in recent_events:
        driver_quali = QualifyingResult.objects.filter(
            driver=driver,
            session__event=event,
            session__session_type='Q'
        ).first()

        teammate_quali = QualifyingResult.objects.filter(
            driver=teammate,
            session__event=event,
            session__session_type='Q'
        ).first()

        if driver_quali and teammate_quali and driver_quali.position and teammate_quali.position:
            quali_comparisons.append(driver_quali.position - teammate_quali.position)

    # Race comparisons
    race_comparisons = []

    for event in recent_events:
        driver_race = RaceResult.objects.filter(
            driver=driver,
            session__event=event,
            session__session_type='R'
        ).first()

        teammate_race = RaceResult.objects.filter(
            driver=teammate,
            session__event=event,
            session__session_type='R'
        ).first()

        if driver_race and teammate_race and driver_race.position and teammate_race.position:
            race_comparisons.append(driver_race.position - teammate_race.position)

    # Calculate metrics
    avg_quali_gap = np.mean(quali_comparisons) if quali_comparisons else 0.0
    avg_race_gap = np.mean(race_comparisons) if race_comparisons else 0.0

    # Head-to-head (% of times driver beat teammate)
    h2h = sum(1 for x in race_comparisons if x < 0) / len(race_comparisons) if race_comparisons else 0.5

    return {
        'teammate_quali_gap': avg_quali_gap,
        'teammate_race_gap': avg_race_gap,
        'teammate_head_to_head': h2h
    }


def calculate_season_progression(driver, team, reference_date):
    """
    Calculate how the driver/team performance is evolving during the season.

    Args:
        driver: Driver object
        team: Team object
        reference_date: Current race date

    Returns:
        Dict with progression metrics
    """
    # Get season year
    season_year = reference_date.year

    # Get results from current season up to this race
    season_results = RaceResult.objects.filter(
        driver=driver,
        session__event__season__year=season_year,
        session__session_date__lt=reference_date,
        session__session_type='R',
        position__isnull=False
    ).order_by('session__session_date')

    if len(season_results) < 2:
        return {
            'position_trend': 0.0,
            'points_trend': 0.0,
            'form_improving': 0.0
        }

    # Calculate trends (early season vs recent)
    positions = [r.position for r in season_results]
    points_list = [r.points for r in season_results if r.points]

    # Split into first half and second half
    mid_point = len(positions) // 2

    first_half_avg = np.mean(positions[:mid_point]) if mid_point > 0 else 15.0
    second_half_avg = np.mean(positions[mid_point:]) if len(positions) > mid_point else 15.0

    # Negative trend = improving (lower position numbers)
    position_trend = second_half_avg - first_half_avg

    # Points trend
    if len(points_list) >= 2:
        first_half_points = np.mean(points_list[:len(points_list)//2])
        second_half_points = np.mean(points_list[len(points_list)//2:])
        points_trend = second_half_points - first_half_points
    else:
        points_trend = 0.0

    # Is form improving? (1 if yes, 0 if no)
    form_improving = 1.0 if (position_trend < -0.5 or points_trend > 1.0) else 0.0

    return {
        'position_trend': position_trend,
        'points_trend': points_trend,
        'form_improving': form_improving
    }


def prepare_position_features_enhanced(
    year_start: Optional[int] = None,
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
    - Overtaking difficulty by circuit
    - Teammate performance comparison
    - Season progression and development trends
    - Feature interactions (grid × momentum, quali × circuit history)

    Args:
        year_start: Starting year for data collection (default: None = all years)
        year_end: Ending year for data collection (default: None = all years)
        min_samples: Minimum number of samples required (default: 50)

    Returns:
        Tuple of (X, y) where:
        - X: DataFrame with enhanced features
        - y: Series with target (final position)
    """
    year_filter_msg = "all years"
    if year_start is not None and year_end is not None:
        year_filter_msg = f"{year_start} to {year_end}"
    elif year_start is not None:
        year_filter_msg = f"{year_start} onwards"
    elif year_end is not None:
        year_filter_msg = f"up to {year_end}"

    logger.info(f"Preparing ENHANCED position features from {year_filter_msg}")

    # Query race results
    query_filter = {
        'session__session_type': 'R',
        'position__isnull': False  # Only finished races
    }

    # Only add year filters if specified
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

            # NEW: Calculate overtaking difficulty at this circuit
            overtaking_difficulty = calculate_overtaking_difficulty(result.session.event.circuit)

            # NEW: Find teammate and calculate performance gap
            teammate = RaceResult.objects.filter(
                session=result.session,
                team=result.team
            ).exclude(driver=result.driver).first()

            teammate_metrics = calculate_teammate_performance_gap(
                result.driver,
                teammate.driver if teammate else None,
                result.session.session_date
            )

            # NEW: Calculate season progression
            season_progression = calculate_season_progression(
                result.driver,
                result.team,
                result.session.session_date
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

                # NEW: Circuit overtaking difficulty
                'overtaking_difficulty': overtaking_difficulty,

                # NEW: Teammate comparison
                'teammate_quali_gap': teammate_metrics['teammate_quali_gap'],
                'teammate_race_gap': teammate_metrics['teammate_race_gap'],
                'teammate_head_to_head': teammate_metrics['teammate_head_to_head'],

                # NEW: Season progression
                'position_trend': season_progression['position_trend'],
                'points_trend': season_progression['points_trend'],
                'form_improving': season_progression['form_improving'],

                # NEW: Feature interactions (capturing non-linear relationships)
                'grid_x_momentum': (result.grid_position if result.grid_position else 20) * driver_momentum['momentum_score'],
                'quali_x_circuit_history': (quali_position if quali_position else 20) * circuit_history['avg_position_at_circuit'],
                'team_momentum_x_overtaking': team_momentum['team_momentum'] * overtaking_difficulty,
                'grid_x_overtaking': (result.grid_position if result.grid_position else 20) * overtaking_difficulty,
                'recent_form_x_circuit': driver_momentum['avg_position_recent'] * circuit_history['circuit_familiarity'],

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
    year_start: Optional[int] = None,
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
        year_start: Starting year for data collection (default: None = all years)
        year_end: Ending year for data collection (default: None = all years)
        min_samples: Minimum number of samples required

    Returns:
        Tuple of (X, y) where:
        - X: DataFrame with features
        - y: Series with target (1 if pole, 0 otherwise)
    """
    year_filter_msg = "all years"
    if year_start is not None and year_end is not None:
        year_filter_msg = f"{year_start} to {year_end}"
    elif year_start is not None:
        year_filter_msg = f"{year_start} onwards"
    elif year_end is not None:
        year_filter_msg = f"up to {year_end}"

    logger.info(f"Preparing pole position features from {year_filter_msg}")

    # Query qualifying results
    query_filter = {
        'session__session_type': 'Q',
        'position__isnull': False
    }

    # Only add year filters if specified
    if year_start is not None:
        query_filter['session__event__season__year__gte'] = year_start
    if year_end is not None:
        query_filter['session__event__season__year__lte'] = year_end

    results = QualifyingResult.objects.filter(
        **query_filter
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
    year_start: Optional[int] = None,
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
        year_start: Starting year for data collection (default: None = all years)
        year_end: Ending year for data collection (default: None = all years)
        min_samples: Minimum number of samples required

    Returns:
        Tuple of (X, y) where:
        - X: DataFrame with features
        - y: Series with target (1 if fastest lap, 0 otherwise)
    """
    year_filter_msg = "all years"
    if year_start is not None and year_end is not None:
        year_filter_msg = f"{year_start} to {year_end}"
    elif year_start is not None:
        year_filter_msg = f"{year_start} onwards"
    elif year_end is not None:
        year_filter_msg = f"up to {year_end}"

    logger.info(f"Preparing fastest lap features from {year_filter_msg}")

    # Query race results
    query_filter = {
        'session__session_type': 'R',
        'position__isnull': False
    }

    # Only add year filters if specified
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


def prepare_pole_time_features(
    year_start: Optional[int] = None,
    year_end: Optional[int] = None,
    min_samples: int = 50
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Prepare features for POLE TIME prediction (qualifying lap time in seconds).

    This is a REGRESSION model to predict the actual pole position lap time.

    Features include:
    - Circuit characteristics (length, corners, type, altitude)
    - Historical pole times at circuit (trend analysis)
    - Year/era (technological evolution)
    - Weather conditions
    - Season round (early vs late season car development)

    Args:
        year_start: Starting year for data collection (default: None = all years)
        year_end: Ending year for data collection (default: None = all years)
        min_samples: Minimum number of samples required

    Returns:
        Tuple of (X, y) where:
        - X: DataFrame with features
        - y: Series with target (pole time in seconds)
    """
    year_filter_msg = "all years"
    if year_start is not None and year_end is not None:
        year_filter_msg = f"{year_start} to {year_end}"
    elif year_start is not None:
        year_filter_msg = f"{year_start} onwards"
    elif year_end is not None:
        year_filter_msg = f"up to {year_end}"

    logger.info(f"Preparing pole time features from {year_filter_msg}")

    # Query qualifying results for pole positions only
    query_filter = {
        'session__session_type': 'Q',
        'position': 1,  # Only pole positions
        'q3_time__isnull': False  # Must have Q3 time
    }

    # Only add year filters if specified
    if year_start is not None:
        query_filter['session__event__season__year__gte'] = year_start
    if year_end is not None:
        query_filter['session__event__season__year__lte'] = year_end

    results = QualifyingResult.objects.filter(
        **query_filter
    ).select_related(
        'session', 'session__event', 'session__event__circuit',
        'session__event__season', 'driver', 'team'
    ).order_by('session__session_date')

    logger.info(f"Found {results.count()} pole position qualifying results")

    if results.count() < min_samples:
        logger.warning(f"Not enough samples: {results.count()} < {min_samples}")
        return pd.DataFrame(), pd.Series(dtype=float)

    data = []

    for result in results:
        try:
            circuit = result.session.event.circuit
            year = result.session.event.season.year
            event_round = result.session.event.round_number if hasattr(result.session.event, 'round_number') else 1

            # Get pole time in seconds
            pole_time_seconds = safe_timedelta_to_seconds(result.q3_time)
            if not pole_time_seconds or pole_time_seconds <= 0:
                continue

            # Historical pole times at this circuit (before this event)
            historical_poles = QualifyingResult.objects.filter(
                session__event__circuit=circuit,
                session__session_date__lt=result.session.session_date,
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
            avg_pole_time = np.mean(historical_times) if historical_times else pole_time_seconds
            min_pole_time = np.min(historical_times) if historical_times else pole_time_seconds
            max_pole_time = np.max(historical_times) if historical_times else pole_time_seconds
            std_pole_time = np.std(historical_times) if len(historical_times) > 1 else 0.0

            # Calculate time trend (improvement over years)
            time_trend = 0.0
            if len(historical_times) >= 2 and len(historical_years) >= 2:
                # Simple linear regression for trend
                x = np.array(historical_years)
                y_hist = np.array(historical_times)
                if len(set(x)) > 1:  # Need at least 2 different years
                    slope = np.polyfit(x, y_hist, 1)[0]
                    time_trend = slope  # Negative = times getting faster

            # Era indicator (regulation changes affect lap times significantly)
            era = 0
            if year < 2014:
                era = 1  # V8 era
            elif year < 2017:
                era = 2  # Early hybrid era
            elif year < 2022:
                era = 3  # High downforce era
            else:
                era = 4  # Ground effect era (2022+)

            # Get weather during qualifying
            weather_avg = WeatherData.objects.filter(
                session=result.session
            ).aggregate(
                avg_air_temp=Avg('air_temp'),
                avg_track_temp=Avg('track_temp'),
                avg_humidity=Avg('humidity'),
                rainfall=Max('rainfall')
            )

            # Circuit characteristics
            circuit_length = circuit.length_km if circuit.length_km else 5.0  # Default 5km
            num_corners = circuit.number_of_corners if circuit.number_of_corners else 15

            # Determine circuit type score
            circuit_type_score = 0.5  # Default
            if circuit.circuit_type:
                if 'street' in circuit.circuit_type.lower():
                    circuit_type_score = 1.0  # Street circuits typically slower
                elif 'permanent' in circuit.circuit_type.lower():
                    circuit_type_score = 0.0  # Permanent circuits typically faster

            # Direction (clockwise vs anti-clockwise can affect tyres)
            is_clockwise = 1.0 if hasattr(circuit, 'direction') and circuit.direction == 'clockwise' else 0.0

            # Altitude effect (higher altitude = less air density = less downforce)
            altitude_effect = 0.0
            if circuit.latitude:
                # Rough approximation: circuits at higher latitudes often at higher altitudes
                # Mexico City (2240m), Interlagos (800m), etc.
                # This is a proxy - ideally we'd have actual altitude data
                altitude_effect = abs(circuit.latitude) / 90.0  # Normalize

            # Season progression (car development through season)
            season_progression = event_round / 24.0 if event_round else 0.5  # Normalize to 0-1

            # Build feature dict
            features = {
                # Circuit characteristics
                'circuit_length_km': circuit_length,
                'number_of_corners': num_corners,
                'circuit_type_score': circuit_type_score,
                'is_clockwise': is_clockwise,
                'altitude_effect': altitude_effect,

                # Time characteristics
                'year': year,
                'era': era,
                'season_progression': season_progression,

                # Historical pole times at this circuit
                'avg_pole_time_historical': avg_pole_time,
                'min_pole_time_historical': min_pole_time,
                'max_pole_time_historical': max_pole_time,
                'std_pole_time_historical': std_pole_time,
                'time_trend': time_trend,
                'num_historical_poles': len(historical_times),

                # Weather conditions
                'air_temp': weather_avg['avg_air_temp'] if weather_avg['avg_air_temp'] else 20.0,
                'track_temp': weather_avg['avg_track_temp'] if weather_avg['avg_track_temp'] else 30.0,
                'humidity': weather_avg['avg_humidity'] if weather_avg['avg_humidity'] else 50.0,
                'rainfall': 1.0 if weather_avg['rainfall'] else 0.0,

                # Derived features
                'corners_per_km': num_corners / circuit_length if circuit_length > 0 else 3.0,
                'expected_time_per_km': avg_pole_time / circuit_length if circuit_length > 0 else 20.0,

                # Year-based improvement factor (cars get faster each year)
                'year_normalized': (year - 2018) / 12.0,  # 2018-2030 normalized

                # Interaction features
                'length_x_corners': circuit_length * num_corners,
                'era_x_length': era * circuit_length,
                'temp_x_humidity': (weather_avg['avg_track_temp'] if weather_avg['avg_track_temp'] else 30.0) *
                                   (weather_avg['avg_humidity'] if weather_avg['avg_humidity'] else 50.0) / 100.0,

                # Circuit name for encoding (helps model learn circuit-specific patterns)
                'circuit_name': circuit.name,

                # Target: pole time in seconds
                'pole_time': pole_time_seconds
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
    y = df['pole_time']
    X = df.drop(columns=['pole_time'])

    # Encode categorical variables
    X = encode_categorical(X, 'circuit_name', 'circuit')

    # Fill any remaining NaN values
    X = X.fillna(0)

    logger.info(f"Final pole time feature matrix: {X.shape}, Target: {y.shape}")
    logger.info(f"Pole time range: {y.min():.3f}s - {y.max():.3f}s (mean: {y.mean():.3f}s)")

    return X, y
