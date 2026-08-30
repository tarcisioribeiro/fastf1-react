# -*- coding: utf-8 -*-
"""
Fatores de ajuste para as previsões de F1.

Cada fator transforma dados brutos do banco em:

- ``features``: dicionário de features numéricas para os modelos de ML
- ``position_delta``: ajuste aditivo à posição prevista (negativo = melhora)
- ``prob_multiplier``: multiplicador para probabilidades de vitória/pódio/pontos
- ``uncertainty_delta``: posições extras a somar na faixa prevista
- ``explanation``: texto em português para exibição
- ``label`` / ``key``: identificação do fator

Fatores implementados:

1. ``regulation``  — mudanças de regulamento (via ``ml.regulation_config``)
2. ``car_update``  — atualizações de carro (proxy: degrau de ritmo da equipe)
3. ``weather``     — clima (climatologia histórica do circuito + skill de chuva)
4. ``strategy``    — estratégia (paradas esperadas, perda de pit lane, execução)
5. ``current_form``— forma atual (momentum de piloto e equipe)

Os módulos ``predictor`` e ``feature_engineering`` usam ``factor_feature_vector``
para alimentar o ML; ``api.views`` usa ``compute_all_factors`` para ajustar o
motor estatístico e listar as explicações.
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import numpy as np

from django.db.models import Avg, Count
from django.utils import timezone as dj_timezone

from core.models import (
    RaceResult, QualifyingResult, WeatherData, PitStop, LapTime, Session,
)
from ml.regulation_config import (
    regulation_features, regulation_uncertainty, cross_season_weight,
    describe_regulation, get_regulation, TRANSITION_THRESHOLD,
)
from ml.feature_engineering import (
    calculate_driver_momentum, calculate_team_momentum,
    calculate_season_progression, safe_timedelta_to_seconds,
)

logger = logging.getLogger('ml')

FACTOR_KEYS = ('regulation', 'car_update', 'weather', 'strategy', 'current_form')

# Mapeia as chaves de parâmetro vindas do frontend para as chaves de fator
PARAM_TO_FACTOR = {
    'regulationChanges': 'regulation',
    'carUpgrades': 'car_update',
    'weather': 'weather',
    'strategy': 'strategy',
    'currentForm': 'current_form',
}


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _aware(dt: Optional[datetime]) -> datetime:
    """Garante datetime timezone-aware (usa TZ atual do Django se vier naive)."""
    if dt is None:
        return dj_timezone.now()
    if dj_timezone.is_naive(dt):
        return dj_timezone.make_aware(dt, dj_timezone.get_current_timezone())
    return dt


@dataclass
class FactorResult:
    key: str
    label: str
    features: Dict[str, float] = field(default_factory=dict)
    position_delta: float = 0.0
    prob_multiplier: float = 1.0
    uncertainty_delta: float = 0.0
    explanation: str = ''
    # Peso a aplicar sobre dados de temporadas anteriores (só o fator regulation usa)
    history_weight: float = 1.0

    def as_applied(self) -> Dict:
        """Representação enxuta para a resposta da API."""
        # Fator que só mexe na incerteza (ex.: regulamento) e não empurra
        # a previsão numa direção clara
        if abs(self.position_delta) < 0.15 and self.uncertainty_delta > 0.1:
            effect = 'incerteza'
        elif self.position_delta < -0.15:
            effect = 'positivo'
        elif self.position_delta > 0.15:
            effect = 'negativo'
        elif self.prob_multiplier > 1.03:
            effect = 'positivo'
        elif self.prob_multiplier < 0.97:
            effect = 'incerteza'
        else:
            effect = 'neutro'
        return {
            'key': self.key,
            'label': self.label,
            'effect': effect,
            'positionDelta': round(self.position_delta, 2),
            'probMultiplier': round(self.prob_multiplier, 3),
            'uncertaintyDelta': round(self.uncertainty_delta, 2),
            'explanation': self.explanation,
        }


def _neutral(key: str, label: str, explanation: str = '') -> FactorResult:
    return FactorResult(key=key, label=label, explanation=explanation or 'Sem dados suficientes para este fator.')


# ---------------------------------------------------------------------------
# Caches (reaproveitados durante a preparação de features de treino)
# ---------------------------------------------------------------------------
_circuit_weather_cache: Dict[int, Dict] = {}
_circuit_strategy_cache: Dict[int, Dict] = {}
_team_pace_cache: Dict[str, Dict] = {}
_team_pit_cache: Dict[str, float] = {}


def clear_factor_caches():
    """Limpa os caches. Chamar no início de cada rotina de preparação/treino."""
    _circuit_weather_cache.clear()
    _circuit_strategy_cache.clear()
    _team_pace_cache.clear()
    _team_pit_cache.clear()


# ---------------------------------------------------------------------------
# 1. Regulamento
# ---------------------------------------------------------------------------
def compute_regulation_factor(year: int, prev_reference_year: Optional[int] = None) -> FactorResult:
    try:
        feats = regulation_features(year)
        uncertainty = regulation_uncertainty(year)
        reg = get_regulation(year)
        magnitude = reg['change_magnitude']

        # Peso do histórico da temporada anterior sob o novo regulamento
        hist_weight = cross_season_weight(year - 1, year)

        # Em ano de transição, puxa probabilidades levemente em direção à média
        prob_mult = 1.0
        if magnitude >= TRANSITION_THRESHOLD:
            prob_mult = _clamp(1.0 - (magnitude - TRANSITION_THRESHOLD) * 0.5, 0.75, 1.0)

        return FactorResult(
            key='regulation',
            label='Mudanças de regulamento',
            features=feats,
            position_delta=0.0,
            prob_multiplier=prob_mult,
            uncertainty_delta=uncertainty,
            history_weight=hist_weight,
            explanation=describe_regulation(year),
        )
    except Exception as e:  # pragma: no cover - proteção
        logger.warning(f"compute_regulation_factor falhou: {e}")
        return _neutral('regulation', 'Mudanças de regulamento')


# ---------------------------------------------------------------------------
# 2. Atualizações de carro (proxy de ritmo)
# ---------------------------------------------------------------------------
def _team_pace_trend(team, reference_date: datetime, num_events: int = 6) -> Dict:
    cache_key = f"{team.id}:{reference_date.date().isoformat()}"
    if cache_key in _team_pace_cache:
        return _team_pace_cache[cache_key]

    # Classificação: gap percentual da equipe para a pole, por evento
    q_sessions = list(
        Session.objects.filter(
            session_type='Q',
            session_date__lt=reference_date,
            qualifying_results__team=team,
        ).distinct().order_by('-session_date')[:num_events]
    )

    quali_gaps: List[float] = []
    for s in reversed(q_sessions):  # cronológico
        results = list(QualifyingResult.objects.filter(session=s))
        if not results:
            continue
        best_times = []
        team_best = None
        for r in results:
            t = (safe_timedelta_to_seconds(r.q3_time)
                 or safe_timedelta_to_seconds(r.q2_time)
                 or safe_timedelta_to_seconds(r.q1_time))
            if t and t > 0:
                best_times.append(t)
                if r.team_id == team.id and (team_best is None or t < team_best):
                    team_best = t
        if team_best and best_times:
            pole = min(best_times)
            if pole > 0:
                quali_gaps.append((team_best - pole) / pole * 100.0)

    # Corrida: gap percentual do ritmo mediano da equipe para o ritmo mediano da sessão
    r_sessions = list(
        Session.objects.filter(
            session_type='R',
            session_date__lt=reference_date,
            lap_times__team=team,
        ).distinct().order_by('-session_date')[:num_events]
    )

    race_gaps: List[float] = []
    for s in reversed(r_sessions):
        # Agregação no banco (evita trazer milhares de voltas para memória)
        base = LapTime.objects.filter(session=s, is_accurate=True, lap_time__isnull=False)
        field_agg = base.aggregate(avg=Avg('lap_time'), n=Count('id'))
        team_agg = base.filter(team=team).aggregate(avg=Avg('lap_time'), n=Count('id'))
        if not field_agg['n'] or field_agg['n'] < 20 or not team_agg['n'] or team_agg['n'] < 5:
            continue
        field_avg = safe_timedelta_to_seconds(field_agg['avg'])
        team_avg = safe_timedelta_to_seconds(team_agg['avg'])
        if field_avg and team_avg and field_avg > 0:
            race_gaps.append((team_avg - field_avg) / field_avg * 100.0)

    def _slope(values: List[float]) -> float:
        if len(values) < 3:
            return 0.0
        x = np.arange(len(values), dtype=float)
        return float(np.polyfit(x, np.array(values), 1)[0])

    def _step(values: List[float]) -> float:
        if len(values) < 4:
            return 0.0
        recent = np.mean(values[-2:])
        prior = np.mean(values[:-2])
        return float(recent - prior)

    result = {
        'quali_gap_slope': _slope(quali_gaps),
        'quali_gap_step': _step(quali_gaps),
        'race_gap_slope': _slope(race_gaps),
        'quali_gap_current': quali_gaps[-1] if quali_gaps else None,
        'n_quali': len(quali_gaps),
        'n_race': len(race_gaps),
    }
    _team_pace_cache[cache_key] = result
    return result


def compute_car_update_factor(team, reference_date: datetime) -> FactorResult:
    try:
        trend = _team_pace_trend(team, reference_date)
        if trend['n_quali'] < 3 and trend['n_race'] < 3:
            return _neutral('car_update', 'Atualizações de carro',
                            'Poucas corridas recentes para estimar evolução do carro.')

        # slope negativo => gap diminuindo => carro melhorando
        quali_slope = trend['quali_gap_slope']
        race_slope = trend['race_gap_slope']
        combined_slope = 0.6 * quali_slope + 0.4 * race_slope

        # ~0.15 %/corrida de melhora => ~ -1.8 posições
        position_delta = _clamp(combined_slope * 12.0, -2.5, 2.5)
        prob_multiplier = _clamp(1.0 - position_delta * 0.05, 0.80, 1.25)

        features = {
            'car_quali_gap_slope': quali_slope,
            'car_race_gap_slope': race_slope,
            'car_pace_step': trend['quali_gap_step'],
            'car_dev_trend': combined_slope,
            'car_quali_gap_current': trend['quali_gap_current'] if trend['quali_gap_current'] is not None else 1.5,
        }

        if combined_slope < -0.03:
            direction = f'evoluindo (ganho de ~{abs(combined_slope):.2f}%/corrida no ritmo)'
        elif combined_slope > 0.03:
            direction = f'perdendo terreno (~{combined_slope:.2f}%/corrida)'
        else:
            direction = 'estável nas últimas corridas'
        explanation = (
            f'Ritmo recente de {team.name}: {direction}. Serve como indício '
            f'indireto de pacotes de atualização (a FastF1 não fornece dados de '
            f'upgrades).'
        )

        return FactorResult(
            key='car_update', label='Atualizações de carro',
            features=features, position_delta=position_delta,
            prob_multiplier=prob_multiplier, explanation=explanation,
        )
    except Exception as e:  # pragma: no cover
        logger.warning(f"compute_car_update_factor falhou: {e}")
        return _neutral('car_update', 'Atualizações de carro')


# ---------------------------------------------------------------------------
# 3. Clima (climatologia histórica)
# ---------------------------------------------------------------------------
def _circuit_climatology(circuit) -> Dict:
    if circuit.id in _circuit_weather_cache:
        return _circuit_weather_cache[circuit.id]

    race_session_ids = list(
        Session.objects.filter(
            session_type='R', event__circuit=circuit
        ).values_list('id', flat=True)
    )

    agg = WeatherData.objects.filter(session_id__in=race_session_ids).aggregate(
        air=Avg('air_temp'), track=Avg('track_temp'),
        hum=Avg('humidity'), wind=Avg('wind_speed'),
    )

    rain_sessions = set(
        WeatherData.objects.filter(session_id__in=race_session_ids, rainfall=True)
        .values_list('session_id', flat=True)
    )
    n_races = len(race_session_ids)
    rain_prob = (len(rain_sessions) / n_races) if n_races else 0.0

    result = {
        'expected_air_temp': agg['air'] if agg['air'] is not None else 22.0,
        'expected_track_temp': agg['track'] if agg['track'] is not None else 32.0,
        'expected_humidity': agg['hum'] if agg['hum'] is not None else 55.0,
        'expected_wind_speed': agg['wind'] if agg['wind'] is not None else 2.0,
        'rain_probability': round(rain_prob, 3),
        'n_races': n_races,
        'rain_session_ids': rain_sessions,
        'race_session_ids': set(race_session_ids),
    }
    _circuit_weather_cache[circuit.id] = result
    return result


def _wet_skill(driver, climate: Dict, reference_date: datetime) -> Optional[float]:
    """Diferença média de posição do piloto em corridas com chuva vs secas.

    Positivo => piloto rende melhor no molhado.
    """
    rain_ids = climate['rain_session_ids']
    results = list(
        RaceResult.objects.filter(
            driver=driver, session__session_type='R',
            session__session_date__lt=reference_date, position__isnull=False,
        ).values_list('session_id', 'position')
    )
    wet = [p for sid, p in results if sid in rain_ids]
    dry = [p for sid, p in results if sid not in rain_ids]
    if len(wet) < 2 or len(dry) < 3:
        return None
    return float(np.mean(dry) - np.mean(wet))


def compute_weather_factor(circuit, driver=None, team=None,
                           reference_date: Optional[datetime] = None) -> FactorResult:
    try:
        reference_date = _aware(reference_date)
        climate = _circuit_climatology(circuit)

        features = {
            'expected_air_temp': climate['expected_air_temp'],
            'expected_track_temp': climate['expected_track_temp'],
            'expected_humidity': climate['expected_humidity'],
            'rain_probability': climate['rain_probability'],
            'driver_wet_skill': 0.0,
        }

        wet_skill = None
        if driver is not None:
            wet_skill = _wet_skill(driver, climate, reference_date)
            if wet_skill is not None:
                features['driver_wet_skill'] = wet_skill

        rain_prob = climate['rain_probability']
        position_delta = 0.0
        prob_multiplier = 1.0
        uncertainty = 0.0

        if rain_prob >= 0.20:
            # Chuva aumenta a incerteza independentemente do piloto
            uncertainty = _clamp(rain_prob * 2.5, 0.0, 2.0)
            if wet_skill is not None:
                position_delta = _clamp(-wet_skill * rain_prob * 0.45, -2.0, 2.0)
                prob_multiplier = _clamp(1.0 - position_delta * 0.04, 0.85, 1.15)

        pct = int(round(rain_prob * 100))
        if rain_prob >= 0.20:
            skill_txt = ''
            if wet_skill is not None:
                if wet_skill > 0.5:
                    skill_txt = f' {driver.code} costuma render ~{wet_skill:.1f} posições melhor no molhado.'
                elif wet_skill < -0.5:
                    skill_txt = f' {driver.code} costuma render ~{abs(wet_skill):.1f} posições pior no molhado.'
            explanation = (
                f'Probabilidade histórica de chuva em {circuit.name}: {pct}% '
                f'(temp. de pista média ~{climate["expected_track_temp"]:.0f}°C).{skill_txt}'
            )
        else:
            explanation = (
                f'Clima historicamente seco em {circuit.name} (chuva em {pct}% das '
                f'corridas, temp. de pista média ~{climate["expected_track_temp"]:.0f}°C).'
            )

        return FactorResult(
            key='weather', label='Clima',
            features=features, position_delta=position_delta,
            prob_multiplier=prob_multiplier, uncertainty_delta=uncertainty,
            explanation=explanation,
        )
    except Exception as e:  # pragma: no cover
        logger.warning(f"compute_weather_factor falhou: {e}")
        return _neutral('weather', 'Clima')


# ---------------------------------------------------------------------------
# 4. Estratégia
# ---------------------------------------------------------------------------
def _circuit_strategy(circuit) -> Dict:
    if circuit.id in _circuit_strategy_cache:
        return _circuit_strategy_cache[circuit.id]

    race_session_ids = list(
        Session.objects.filter(
            session_type='R', event__circuit=circuit
        ).values_list('id', flat=True)
    )

    # Paradas por piloto por corrida
    per_driver = (
        PitStop.objects.filter(session_id__in=race_session_ids)
        .values('session_id', 'driver_id')
        .annotate(n=Count('id'))
    )
    counts = [row['n'] for row in per_driver]
    expected_stops = float(np.median(counts)) if counts else 2.0

    # Perda de pit lane (duração média das paradas válidas)
    durations = [
        safe_timedelta_to_seconds(d) for d in
        PitStop.objects.filter(
            session_id__in=race_session_ids, duration__isnull=False
        ).values_list('duration', flat=True)
    ]
    durations = [d for d in durations if d and 15.0 <= d <= 45.0]
    pit_loss = float(np.mean(durations)) if durations else 24.0

    result = {
        'expected_pit_stops': round(expected_stops, 2),
        'circuit_pit_loss_s': round(pit_loss, 2),
        'n_races': len(race_session_ids),
    }
    _circuit_strategy_cache[circuit.id] = result
    return result


def _team_pit_execution(team, reference_date: datetime) -> Optional[float]:
    """Duração média de parada da equipe menos a média geral do grid (12 meses).

    Negativo => equipe mais rápida que a média (boa execução).
    """
    since = reference_date - timedelta(days=365)
    cache_key = f"{team.id}:{since.date().isoformat()}:{reference_date.date().isoformat()}"
    if cache_key in _team_pit_cache:
        return _team_pit_cache[cache_key]

    def _avg(qs):
        vals = [safe_timedelta_to_seconds(d) for d in qs.values_list('duration', flat=True)]
        vals = [v for v in vals if v and 15.0 <= v <= 45.0]
        return float(np.mean(vals)) if len(vals) >= 5 else None

    base = PitStop.objects.filter(
        duration__isnull=False,
        session__session_date__lt=reference_date,
        session__session_date__gte=since,
    )
    field_avg = _avg(base)
    team_avg = _avg(base.filter(team=team))

    delta = None
    if field_avg is not None and team_avg is not None:
        delta = team_avg - field_avg
    _team_pit_cache[cache_key] = delta
    return delta


def compute_strategy_factor(circuit, team=None, driver=None,
                            reference_date: Optional[datetime] = None) -> FactorResult:
    try:
        reference_date = _aware(reference_date)
        strat = _circuit_strategy(circuit)

        features = {
            'expected_pit_stops': strat['expected_pit_stops'],
            'circuit_pit_loss_s': strat['circuit_pit_loss_s'],
            'team_pit_exec_delta': 0.0,
        }

        exec_delta = None
        if team is not None:
            exec_delta = _team_pit_execution(team, reference_date)
            if exec_delta is not None:
                features['team_pit_exec_delta'] = exec_delta

        position_delta = 0.0
        prob_multiplier = 1.0
        if exec_delta is not None:
            # 0.5s mais lento que a média => ~ +0.4 posição
            position_delta = _clamp(exec_delta * 0.8, -1.2, 1.2)
            prob_multiplier = _clamp(1.0 - position_delta * 0.04, 0.9, 1.1)

        stops_txt = f'{strat["expected_pit_stops"]:.0f}'
        if exec_delta is not None and abs(exec_delta) >= 0.15:
            if exec_delta < 0:
                exec_txt = f' {team.name} vem parando ~{abs(exec_delta):.1f}s mais rápido que a média do grid.'
            else:
                exec_txt = f' {team.name} vem parando ~{exec_delta:.1f}s mais lento que a média do grid.'
        else:
            exec_txt = ''
        explanation = (
            f'Estratégia típica em {circuit.name}: ~{stops_txt} parada(s), perda '
            f'de pit lane ~{strat["circuit_pit_loss_s"]:.0f}s.{exec_txt}'
        )

        return FactorResult(
            key='strategy', label='Estratégia',
            features=features, position_delta=position_delta,
            prob_multiplier=prob_multiplier, explanation=explanation,
        )
    except Exception as e:  # pragma: no cover
        logger.warning(f"compute_strategy_factor falhou: {e}")
        return _neutral('strategy', 'Estratégia')


# ---------------------------------------------------------------------------
# 5. Forma atual
# ---------------------------------------------------------------------------
def compute_form_factor(driver, team, reference_date: Optional[datetime] = None) -> FactorResult:
    try:
        reference_date = _aware(reference_date)

        dm = calculate_driver_momentum(driver, reference_date, num_races=5)
        tm = calculate_team_momentum(team, reference_date, num_races=5)
        prog = calculate_season_progression(driver, team, reference_date)

        features = {
            'driver_avg_position_recent': dm['avg_position_recent'],
            'driver_avg_points_recent': dm['avg_points_recent'],
            'driver_wins_recent': float(dm['wins_recent']),
            'driver_podiums_recent': float(dm['podiums_recent']),
            'driver_momentum_score': dm['momentum_score'],
            'team_avg_position_recent': tm['team_avg_position_recent'],
            'team_avg_points_recent': tm['team_avg_points_recent'],
            'team_momentum': tm['team_momentum'],
            'position_trend': prog['position_trend'],
            'points_trend': prog['points_trend'],
            'form_improving': prog['form_improving'],
        }

        avg_recent = dm['avg_position_recent']
        # Melhor forma recente (posição baixa) => delta negativo
        position_delta = _clamp((avg_recent - 10.5) * 0.28, -3.0, 3.0)
        # Tendência de melhora reforça
        if prog['position_trend'] < -0.5:
            position_delta -= 0.4
        elif prog['position_trend'] > 0.5:
            position_delta += 0.4
        position_delta = _clamp(position_delta, -3.5, 3.5)

        prob_multiplier = _clamp(0.7 + dm['momentum_score'] * 0.6, 0.7, 1.35)

        trend_txt = ''
        if prog['position_trend'] < -0.5:
            trend_txt = ' em curva ascendente na temporada'
        elif prog['position_trend'] > 0.5:
            trend_txt = ' em queda de rendimento na temporada'
        explanation = (
            f'Forma recente de {driver.code}: média de {avg_recent:.1f}º nas '
            f'últimas 5 corridas, {dm["podiums_recent"]} pódio(s){trend_txt}. '
            f'Equipe com média recente de {tm["team_avg_position_recent"]:.1f}º.'
        )

        return FactorResult(
            key='current_form', label='Forma atual',
            features=features, position_delta=position_delta,
            prob_multiplier=prob_multiplier, explanation=explanation,
        )
    except Exception as e:  # pragma: no cover
        logger.warning(f"compute_form_factor falhou: {e}")
        return _neutral('current_form', 'Forma atual')


# ---------------------------------------------------------------------------
# Agregadores
# ---------------------------------------------------------------------------
def compute_all_factors(driver=None, team=None, circuit=None, year: Optional[int] = None,
                        reference_date: Optional[datetime] = None,
                        skip: Optional[set] = None) -> Dict[str, FactorResult]:
    """Calcula todos os fatores aplicáveis. Chaves ausentes são omitidas.

    ``skip`` permite pular fatores caros já cobertos por outras features
    (ex.: ``{'current_form'}`` no treino do modelo de posição V2).
    """
    if year is None:
        year = datetime.now().year
    reference_date = _aware(reference_date)
    skip = skip or set()

    out: Dict[str, FactorResult] = {}
    if 'regulation' not in skip:
        out['regulation'] = compute_regulation_factor(year)
    if team is not None and 'car_update' not in skip:
        out['car_update'] = compute_car_update_factor(team, reference_date)
    if circuit is not None and 'weather' not in skip:
        out['weather'] = compute_weather_factor(circuit, driver, team, reference_date)
    if circuit is not None and 'strategy' not in skip:
        out['strategy'] = compute_strategy_factor(circuit, team, driver, reference_date)
    if driver is not None and team is not None and 'current_form' not in skip:
        out['current_form'] = compute_form_factor(driver, team, reference_date)
    return out


def factor_feature_vector(driver=None, team=None, circuit=None, year: Optional[int] = None,
                          reference_date: Optional[datetime] = None,
                          skip: Optional[set] = None) -> Dict[str, float]:
    """Junta as features numéricas de todos os fatores num único dicionário.

    Usado para alimentar os modelos de ML (treino e previsão).
    """
    factors = compute_all_factors(driver, team, circuit, year, reference_date, skip)
    merged: Dict[str, float] = {}
    for fr in factors.values():
        merged.update(fr.features)
    return merged


# Valores default para todas as features de fator — usados no treino quando um
# cálculo não retorna valor, para manter o conjunto de colunas estável.
FACTOR_FEATURE_DEFAULTS: Dict[str, float] = {
    # regulation
    'regulation_cycle': 4.0,
    'regulation_change_magnitude': 0.1,
    'regulation_is_transition_year': 0.0,
    'regulation_is_aero_reset': 0.0,
    'regulation_is_pu_reset': 0.0,
    'regulation_years_into_cycle': 2.0,
    # car_update
    'car_quali_gap_slope': 0.0,
    'car_race_gap_slope': 0.0,
    'car_pace_step': 0.0,
    'car_dev_trend': 0.0,
    'car_quali_gap_current': 1.5,
    # weather
    'expected_air_temp': 22.0,
    'expected_track_temp': 32.0,
    'expected_humidity': 55.0,
    'rain_probability': 0.15,
    'driver_wet_skill': 0.0,
    # strategy
    'expected_pit_stops': 2.0,
    'circuit_pit_loss_s': 24.0,
    'team_pit_exec_delta': 0.0,
    # current_form
    'driver_avg_position_recent': 10.5,
    'driver_avg_points_recent': 5.0,
    'driver_wins_recent': 0.0,
    'driver_podiums_recent': 0.0,
    'driver_momentum_score': 0.5,
    'team_avg_position_recent': 10.5,
    'team_avg_points_recent': 10.0,
    'team_momentum': 0.5,
    'position_trend': 0.0,
    'points_trend': 0.0,
    'form_improving': 0.0,
}


def merge_factor_features(raw: Dict[str, float]) -> Dict[str, float]:
    """Completa um dicionário de features de fator com os defaults."""
    out = dict(FACTOR_FEATURE_DEFAULTS)
    out.update({k: v for k, v in raw.items() if v is not None})
    return out
