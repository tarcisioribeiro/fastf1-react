# -*- coding: utf-8 -*-
"""
Histórico curado de mudanças de regulamento da Fórmula 1.

A API FastF1 não fornece informação sobre regulamento. Este módulo mantém, de
forma versionada, o histórico de mudanças relevantes cobrindo TODOS os anos
presentes na base de dados (2018 em diante) e o ciclo seguinte (2026).

Cada ano é descrito por:
- ``cycle``: identificador do ciclo de regulamento (era técnica)
- ``cycle_name``: nome legível do ciclo
- ``change_magnitude``: 0.0 a 1.0 — quão disruptiva foi a mudança em relação ao
  ano anterior (0 = regras estáveis, 1 = reformulação completa)
- ``aero_reset``: houve reformulação aerodinâmica profunda
- ``pu_reset``: houve reformulação da unidade de potência
- ``notes``: descrição em português das principais mudanças

As funções auxiliares traduzem esse histórico em:
- features numéricas para os modelos de ML (``regulation_features``)
- um peso de "quanto os dados de uma temporada antiga ainda valem para prever
  outra temporada" (``cross_season_weight``)
- um acréscimo de incerteza para a faixa de posições prevista
  (``regulation_uncertainty``)
"""
from typing import Dict

# Limiar de magnitude a partir do qual o ano é considerado "ano de transição"
TRANSITION_THRESHOLD = 0.40

# Peso mínimo que uma temporada anterior a uma reformulação total mantém.
# Evita zerar completamente o histórico (ainda há sinal de talento do piloto).
MIN_CROSS_SEASON_WEIGHT = 0.15


REGULATION_HISTORY: Dict[int, Dict] = {
    2018: {
        'cycle': 3,
        'cycle_name': 'Era de alta carga aerodinâmica (2017-2021)',
        'change_magnitude': 0.15,
        'aero_reset': False,
        'pu_reset': False,
        'notes': (
            'Introdução obrigatória do Halo (proteção de cockpit). Proibição das '
            'barbatanas de tubarão e das T-wings. Redução de três para dois '
            'componentes de unidade de potência por temporada sem punição. '
            'Peso mínimo elevado para 733 kg.'
        ),
    },
    2019: {
        'cycle': 3,
        'cycle_name': 'Era de alta carga aerodinâmica (2017-2021)',
        'change_magnitude': 0.45,
        'aero_reset': False,
        'pu_reset': False,
        'notes': (
            'Pacote aerodinâmico voltado a favorecer ultrapassagens: asa dianteira '
            'mais larga e simplificada (menos outwash), bargeboards mais baixos, '
            'asa traseira mais larga e alta com abertura de DRS maior. Peso mínimo '
            '+10 kg (740 kg) com peso do piloto contabilizado à parte. Luvas '
            'biométricas obrigatórias.'
        ),
    },
    2020: {
        'cycle': 3,
        'cycle_name': 'Era de alta carga aerodinâmica (2017-2021)',
        'change_magnitude': 0.05,
        'aero_reset': False,
        'pu_reset': False,
        'notes': (
            'Regras essencialmente estáveis (evolução do pacote de 2019). '
            'Restrição a um único modo de motor para classificação e corrida a '
            'partir de Monza. Congelamento de desenvolvimento e sistema de fichas '
            'para 2021 por causa da pandemia.'
        ),
    },
    2021: {
        'cycle': 3,
        'cycle_name': 'Era de alta carga aerodinâmica (2017-2021)',
        'change_magnitude': 0.30,
        'aero_reset': False,
        'pu_reset': False,
        'notes': (
            'Cortes de carga aerodinâmica (~10%): recortes no assoalho à frente do '
            'pneu traseiro, aletas do difusor mais curtas, dutos de freio traseiros '
            'menores — para aliviar a carga sobre os pneus Pirelli. Homologação de '
            'chassi com sistema de fichas. Teto orçamentário em vigor (US$ 145 mi). '
            'Introdução da classificação sprint em três etapas.'
        ),
    },
    2022: {
        'cycle': 4,
        'cycle_name': 'Era do efeito solo (2022-2025)',
        'change_magnitude': 1.00,
        'aero_reset': True,
        'pu_reset': False,
        'notes': (
            'Reformulação completa: aerodinâmica de efeito solo com túneis Venturi, '
            'asas dianteira e traseira simplificadas, rodas aro 18 com pneus de '
            'perfil baixo, calotas e defletores sobre as rodas, assoalho e bico '
            'padronizados. Combustível E10 (10% de etanol). Peso mínimo 798 kg. '
            'Congelamento das unidades de potência. Surgimento do "porpoising".'
        ),
    },
    2023: {
        'cycle': 4,
        'cycle_name': 'Era do efeito solo (2022-2025)',
        'change_magnitude': 0.20,
        'aero_reset': False,
        'pu_reset': False,
        'notes': (
            'Borda do assoalho elevada em 15 mm e garganta do difusor elevada para '
            'mitigar o porpoising. Testes de santantônio mais rígidos após o '
            'acidente de Zhou. Escala deslizante de tempo de túnel de vento por '
            'posição no campeonato.'
        ),
    },
    2024: {
        'cycle': 4,
        'cycle_name': 'Era do efeito solo (2022-2025)',
        'change_magnitude': 0.08,
        'aero_reset': False,
        'pu_reset': False,
        'notes': (
            'Regras estáveis. Ajuste na ativação do DRS (uma volta após a largada '
            'ou relargada, em vez de duas).'
        ),
    },
    2025: {
        'cycle': 4,
        'cycle_name': 'Era do efeito solo (2022-2025)',
        'change_magnitude': 0.10,
        'aero_reset': False,
        'pu_reset': False,
        'notes': (
            'Último ano da era do efeito solo. Peso mínimo do piloto elevado para '
            '82 kg (contabilizado à parte). Testes de flexibilidade da asa dianteira '
            'endurecidos a partir de Barcelona. Regras de aerodinâmica estáveis.'
        ),
    },
    2026: {
        'cycle': 5,
        'cycle_name': 'Era 2026',
        'change_magnitude': 1.00,
        'aero_reset': True,
        'pu_reset': True,
        'notes': (
            'Reformulação completa: novas unidades de potência (~50% de potência '
            'elétrica, fim do MGU-H, mais MGU-K, combustível 100% sustentável), '
            'aerodinâmica ativa (asas móveis dianteira e traseira), carros mais '
            'curtos e estreitos (-100 mm de largura), mais leves, e modo "override" '
            'no lugar do DRS. Redução de carga aerodinâmica e arrasto.'
        ),
    },
}

# Anos ordenados para busca de vizinhos
_YEARS_SORTED = sorted(REGULATION_HISTORY.keys())
_MIN_YEAR = _YEARS_SORTED[0]
_MAX_YEAR = _YEARS_SORTED[-1]


def get_regulation(year: int) -> Dict:
    """
    Retorna a descrição de regulamento de um ano.

    Para anos fora do intervalo conhecido, retorna o registro do ano mais
    próximo, mas com ``change_magnitude`` reduzido (assume-se estabilidade fora
    do horizonte curado).
    """
    if year in REGULATION_HISTORY:
        return REGULATION_HISTORY[year]

    if year < _MIN_YEAR:
        base = dict(REGULATION_HISTORY[_MIN_YEAR])
    else:
        base = dict(REGULATION_HISTORY[_MAX_YEAR])

    base['change_magnitude'] = 0.10
    base['aero_reset'] = False
    base['pu_reset'] = False
    base['notes'] = (
        f'Ano fora do histórico curado ({_MIN_YEAR}-{_MAX_YEAR}); assumida '
        f'estabilidade de regulamento em relação a {year - 1}.'
    )
    return base


def years_into_cycle(year: int) -> int:
    """Quantos anos o ano informado está dentro do ciclo de regulamento atual."""
    reg = get_regulation(year)
    cycle = reg['cycle']
    count = 0
    y = year
    while y >= _MIN_YEAR and get_regulation(y)['cycle'] == cycle:
        count += 1
        y -= 1
    return count


def regulation_features(year: int) -> Dict[str, float]:
    """
    Features numéricas de regulamento para os modelos de ML.

    Todas as chaves são estáveis para permitir alinhamento de features.
    """
    reg = get_regulation(year)
    magnitude = float(reg['change_magnitude'])
    return {
        'regulation_cycle': float(reg['cycle']),
        'regulation_change_magnitude': magnitude,
        'regulation_is_transition_year': 1.0 if magnitude >= TRANSITION_THRESHOLD else 0.0,
        'regulation_is_aero_reset': 1.0 if reg['aero_reset'] else 0.0,
        'regulation_is_pu_reset': 1.0 if reg['pu_reset'] else 0.0,
        'regulation_years_into_cycle': float(years_into_cycle(year)),
    }


def cross_season_weight(from_year: int, to_year: int) -> float:
    """
    Peso (0..1) de quanto os dados de ``from_year`` ainda valem para prever
    ``to_year``.

    Para cada mudança de regulamento ocorrida DEPOIS de ``from_year`` e até
    ``to_year``, o peso é multiplicado por ``(1 - change_magnitude)``. Assim,
    dados anteriores a uma reformulação total (magnitude 1.0) são fortemente
    descontados, mas nunca abaixo de ``MIN_CROSS_SEASON_WEIGHT``.
    """
    if from_year >= to_year:
        return 1.0

    weight = 1.0
    for y in range(from_year + 1, to_year + 1):
        magnitude = get_regulation(y)['change_magnitude']
        weight *= (1.0 - magnitude)

    return max(MIN_CROSS_SEASON_WEIGHT, weight)


def regulation_uncertainty(year: int) -> float:
    """
    Acréscimo de incerteza (em posições) para a faixa prevista, proporcional à
    magnitude da mudança de regulamento do ano. Máximo de ~3 posições num ano de
    reformulação completa.
    """
    magnitude = get_regulation(year)['change_magnitude']
    return round(magnitude * 3.0, 2)


def describe_regulation(year: int, prev_year: int = None) -> str:
    """Texto explicativo (pt-BR) sobre o impacto do regulamento na previsão."""
    reg = get_regulation(year)
    magnitude = reg['change_magnitude']

    if magnitude >= TRANSITION_THRESHOLD:
        kind = 'reformulação profunda' if magnitude >= 0.9 else 'mudança significativa'
        w = cross_season_weight(year - 1, year)
        return (
            f'{year}: {kind} de regulamento ({reg["cycle_name"]}). '
            f'{reg["notes"]} O histórico de temporadas anteriores foi reduzido a '
            f'~{int(round(w * 100))}% do peso e a faixa de posições foi ampliada '
            f'para refletir a maior incerteza.'
        )

    return (
        f'{year}: regulamento estável ({reg["cycle_name"]}, '
        f'{years_into_cycle(year)}º ano do ciclo). {reg["notes"]}'
    )
