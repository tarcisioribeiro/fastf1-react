# Documentação da API REST

Esta documentação descreve todos os endpoints da API REST da aplicação FastF1 React.

## URL Base

```
http://localhost:8000/api/
```

## Índice

- [Autenticação](#autenticação)
- [Cache](#cache)
- [ViewSets](#viewsets)
  - [Teams](#teams)
  - [Drivers](#drivers)
  - [Circuits](#circuits)
  - [Seasons](#seasons)
  - [Events](#events)
  - [Sessions](#sessions)
  - [Race Results](#race-results)
  - [Qualifying Results](#qualifying-results)
  - [Sprint Results](#sprint-results)
  - [Driver Standings](#driver-standings)
  - [Constructor Standings](#constructor-standings)
  - [Lap Times](#lap-times)
  - [Tyre Strategies](#tyre-strategies)
  - [Pit Stops](#pit-stops)
  - [Weather Data](#weather-data)
- [Endpoints Customizados](#endpoints-customizados)
  - [Driver Prediction](#driver-prediction)
  - [Constructor Prediction](#constructor-prediction)
  - [Available Filters](#available-filters)
  - [Data Status](#data-status)

---

## Autenticação

Atualmente a API é somente leitura e não requer autenticação.

---

## Cache

A maioria dos endpoints usa cache do Django:

- **5 minutos**: Endpoints `/latest/`
- **10 minutos**: Endpoints `/history/`, `/evolution/`, `/analytics/`
- **15 minutos**: Endpoints de predição

O cache é limpo automaticamente após expiração.

---

## ViewSets

### Teams

**Base URL:** `/api/teams/`

#### Listar todas as equipes

```http
GET /api/teams/
```

**Parâmetros de Query:**
- `search` (string): Buscar por nome ou team_id
- `ordering` (string): Ordenar por campos (name, -name)

**Resposta:**
```json
[
  {
    "id": 1,
    "team_id": "red_bull_racing",
    "name": "Red Bull Racing",
    "full_name": "Oracle Red Bull Racing",
    "color": "#3671C6",
    "color_secondary": ""
  }
]
```

#### Detalhes de uma equipe

```http
GET /api/teams/{id}/
```

---

### Drivers

**Base URL:** `/api/drivers/`

#### Listar todos os pilotos

```http
GET /api/drivers/
```

**Parâmetros de Query:**
- `search` (string): Buscar por nome ou código
- `ordering` (string): Ordenar por campos (last_name, number, -last_name)

**Resposta:**
```json
[
  {
    "id": 1,
    "driver_id": "ver",
    "code": "VER",
    "number": 1,
    "first_name": "Max",
    "last_name": "Verstappen",
    "full_name": "Max Verstappen",
    "nationality": "Dutch",
    "date_of_birth": "1997-09-30"
  }
]
```

#### Detalhes de um piloto

```http
GET /api/drivers/{id}/
```

---

### Circuits

**Base URL:** `/api/circuits/`

#### Listar todos os circuitos

```http
GET /api/circuits/
```

**Parâmetros de Query:**
- `country` (string): Filtrar por país
- `search` (string): Buscar por nome, localização ou país
- `ordering` (string): Ordenar por campos

**Resposta:**
```json
[
  {
    "id": 1,
    "circuit_id": "bahrain",
    "name": "Bahrain International Circuit",
    "location": "Sakhir",
    "country": "Bahrain",
    "latitude": 26.0325,
    "longitude": 50.5106,
    "length_km": 5.412
  }
]
```

---

### Seasons

**Base URL:** `/api/seasons/`

#### Listar todas as temporadas

```http
GET /api/seasons/
```

**Resposta:**
```json
[
  {
    "id": 1,
    "year": 2025
  }
]
```

---

### Events

**Base URL:** `/api/events/`

#### Listar todos os eventos

```http
GET /api/events/
```

**Parâmetros de Query:**
- `season` (int): ID da temporada
- `season__year` (int): Ano da temporada
- `event_type` (string): race, sprint, testing
- `circuit` (int): ID do circuito
- `search` (string): Buscar por nome do evento

**Resposta:**
```json
[
  {
    "id": 1,
    "event_id": "2025_1",
    "season": 1,
    "round_number": 1,
    "circuit": {
      "id": 1,
      "name": "Bahrain International Circuit",
      "location": "Sakhir",
      "country": "Bahrain"
    },
    "event_name": "Bahrain Grand Prix",
    "event_type": "race",
    "event_date": "2025-03-02"
  }
]
```

---

### Sessions

**Base URL:** `/api/sessions/`

#### Listar todas as sessões

```http
GET /api/sessions/
```

**Parâmetros de Query:**
- `event` (int): ID do evento
- `event__season__year` (int): Ano da temporada
- `session_type` (string): FP1, FP2, FP3, Q, S, SQ, R
- `is_complete` (boolean): true/false
- `data_collected` (boolean): true/false

**Resposta:**
```json
[
  {
    "id": 1,
    "session_id": "2025_1_R",
    "event": {
      "id": 1,
      "event_name": "Bahrain Grand Prix",
      "round_number": 1
    },
    "session_type": "R",
    "session_date": "2025-03-02T18:00:00Z",
    "is_complete": true,
    "data_collected": true,
    "collection_date": "2025-03-02T20:30:00Z"
  }
]
```

---

### Race Results

**Base URL:** `/api/races/`

#### Listar resultados de corrida

```http
GET /api/races/
```

**Parâmetros de Query:**
- `session` (int): ID da sessão
- `driver` (int): ID do piloto
- `team` (int): ID da equipe
- `session__event__season__year` (int): Ano
- `ordering` (string): position, points, -position

**Resposta:**
```json
[
  {
    "id": 1,
    "session": 1,
    "driver": {
      "id": 1,
      "code": "VER",
      "full_name": "Max Verstappen",
      "number": 1
    },
    "team": {
      "id": 1,
      "name": "Red Bull Racing",
      "color": "#3671C6"
    },
    "position": 1,
    "grid_position": 1,
    "points": 25.0,
    "laps_completed": 57,
    "total_race_time": "01:32:15.123456",
    "fastest_lap_time": "00:01:32.456",
    "fastest_lap_number": 45,
    "status": "Finished",
    "dnf": false
  }
]
```

#### Última corrida

```http
GET /api/races/latest/
```

**Parâmetros de Query:**
- `year` (int, opcional): Ano (padrão: ano atual)

**Resposta:**
```json
{
  "status": "success",
  "raceInfo": {
    "eventName": "Bahrain Grand Prix",
    "location": "Sakhir",
    "date": "2025-03-02",
    "round": 1
  },
  "results": [
    {
      "id": 1,
      "driver": {...},
      "team": {...},
      "position": 1,
      "points": 25.0,
      ...
    }
  ]
}
```

#### Histórico de corridas

```http
GET /api/races/history/
```

**Parâmetros de Query:**
- `year` (int): Filtrar por ano
- `circuit` (int): Filtrar por circuito (ID)
- `driver` (int): Filtrar por piloto (ID)
- `team` (int): Filtrar por equipe (ID)

**Resposta:**
```json
{
  "status": "success",
  "count": 5,
  "races": [
    {
      "sessionId": 1,
      "eventName": "Bahrain Grand Prix",
      "circuit": "Bahrain International Circuit",
      "location": "Sakhir",
      "country": "Bahrain",
      "date": "2025-03-02",
      "year": 2025,
      "round": 1,
      "results": [...]
    }
  ]
}
```

---

### Qualifying Results

**Base URL:** `/api/qualifying/`

#### Listar resultados de classificação

```http
GET /api/qualifying/
```

**Parâmetros similares aos Race Results**

**Resposta:**
```json
[
  {
    "id": 1,
    "session": 1,
    "driver": {...},
    "team": {...},
    "position": 1,
    "q1_time": "00:01:30.123",
    "q2_time": "00:01:29.456",
    "q3_time": "00:01:28.789"
  }
]
```

#### Última classificação

```http
GET /api/qualifying/latest/
```

**Parâmetros e resposta similares a `/api/races/latest/`**

#### Histórico de classificações

```http
GET /api/qualifying/history/
```

**Parâmetros de Query:**
- `year` (int): Ano
- `circuit` (string): Nome do circuito (busca parcial)
- `driver` (string): Código do piloto (busca parcial)
- `team` (string): Nome da equipe (busca parcial)

---

### Sprint Results

**Base URL:** `/api/sprints/`

#### Última sprint

```http
GET /api/sprints/latest/
```

**Resposta:**
```json
{
  "status": "success",
  "raceInfo": {
    "eventName": "São Paulo Grand Prix",
    "location": "São Paulo",
    "date": "2024-11-02",
    "round": 21
  },
  "results": [
    {
      "id": 1,
      "driver": {...},
      "team": {...},
      "position": 1,
      "grid_position": 2,
      "points": 8.0,
      "laps_completed": 24,
      "total_sprint_time": "00:30:45.123",
      "status": "Finished"
    }
  ]
}
```

#### Histórico de sprints

```http
GET /api/sprints/history/
```

**Parâmetros similares aos de corridas**

---

### Driver Standings

**Base URL:** `/api/driver-standings/`

#### Listar classificações

```http
GET /api/driver-standings/
```

**Parâmetros de Query:**
- `season` (int): ID da temporada
- `season__year` (int): Ano
- `event` (int): ID do evento
- `driver` (int): ID do piloto
- `team` (int): ID da equipe

**Resposta:**
```json
[
  {
    "id": 1,
    "season": 1,
    "event": 1,
    "driver": {
      "id": 1,
      "code": "VER",
      "full_name": "Max Verstappen",
      "number": 1
    },
    "team": {...},
    "position": 1,
    "points": 25.0,
    "wins": 1,
    "podiums": 1
  }
]
```

#### Classificação mais recente

```http
GET /api/driver-standings/latest/?year=2025
```

**Parâmetros de Query:**
- `year` (int, obrigatório): Ano da temporada

**Resposta:**
```json
[
  {
    "id": 1,
    "driver": {...},
    "team": {...},
    "position": 1,
    "points": 375.0,
    "wins": 12,
    "podiums": 18
  }
]
```

#### Evolução de pontos

```http
GET /api/driver-standings/evolution/?year=2025
```

**Parâmetros de Query:**
- `year` (int, obrigatório): Ano
- `drivers` (string, opcional): Códigos de pilotos separados por vírgula (ex: VER,HAM,LEC)
- `start_round` (int, opcional): Rodada inicial (padrão: 1)
- `end_round` (int, opcional): Rodada final (padrão: última)

**Resposta:**
```json
{
  "status": "success",
  "year": "2025",
  "drivers": [
    {
      "driver": {
        "code": "VER",
        "fullName": "Max Verstappen",
        "number": 1
      },
      "team": {
        "name": "Red Bull Racing",
        "color": "#3671C6"
      },
      "points_by_round": [
        {
          "round": 1,
          "eventName": "Bahrain Grand Prix",
          "points": 25.0,
          "position": 1,
          "wins": 1,
          "podiums": 1
        },
        {
          "round": 2,
          "eventName": "Saudi Arabian Grand Prix",
          "points": 43.0,
          "position": 1,
          "wins": 1,
          "podiums": 2
        }
      ]
    }
  ]
}
```

---

### Constructor Standings

**Base URL:** `/api/constructor-standings/`

#### Classificação mais recente

```http
GET /api/constructor-standings/latest/?year=2025
```

**Resposta:**
```json
[
  {
    "id": 1,
    "team": {
      "id": 1,
      "name": "Red Bull Racing",
      "color": "#3671C6"
    },
    "position": 1,
    "points": 589.0,
    "wins": 15,
    "podiums": 25
  }
]
```

#### Evolução de pontos

```http
GET /api/constructor-standings/evolution/?year=2025
```

**Parâmetros de Query:**
- `year` (int, obrigatório): Ano
- `teams` (string, opcional): Nomes de equipes separados por vírgula
- `start_round` (int, opcional): Rodada inicial
- `end_round` (int, opcional): Rodada final

---

### Lap Times

**Base URL:** `/api/lap-times/`

#### Listar tempos de volta

```http
GET /api/lap-times/
```

**Parâmetros de Query:**
- `session` (int): ID da sessão
- `driver` (int): ID do piloto
- `team` (int): ID da equipe
- `lap_number` (int): Número da volta
- `compound` (string): Composto de pneu
- `is_personal_best` (boolean): true/false

**Resposta:**
```json
[
  {
    "id": 1,
    "session": 1,
    "driver": {...},
    "team": {...},
    "lap_number": 1,
    "lap_time": "00:01:35.123",
    "sector1_time": "00:00:28.456",
    "sector2_time": "00:00:38.789",
    "sector3_time": "00:00:27.878",
    "is_personal_best": false,
    "is_accurate": true,
    "compound": "SOFT",
    "tyre_life": 1
  }
]
```

---

### Tyre Strategies

**Base URL:** `/api/tyre-strategies/`

#### Listar estratégias de pneus

```http
GET /api/tyre-strategies/
```

**Parâmetros de Query:**
- `session` (int): ID da sessão
- `driver` (int): ID do piloto
- `team` (int): ID da equipe
- `compound` (string): SOFT, MEDIUM, HARD, INTERMEDIATE, WET

**Resposta:**
```json
[
  {
    "id": 1,
    "session": 1,
    "driver": {...},
    "team": {...},
    "stint_number": 1,
    "compound": "MEDIUM",
    "start_lap": 1,
    "end_lap": 25,
    "stint_length": 25,
    "avg_lap_time": "00:01:34.567",
    "fastest_lap_time": "00:01:32.123"
  }
]
```

---

### Pit Stops

**Base URL:** `/api/pit-stops/`

#### Listar pit stops

```http
GET /api/pit-stops/
```

**Parâmetros de Query:**
- `session` (int): ID da sessão
- `driver` (int): ID do piloto
- `team` (int): ID da equipe

**Resposta:**
```json
[
  {
    "id": 1,
    "session": 1,
    "driver": {...},
    "team": {...},
    "stop_number": 1,
    "lap": 15,
    "duration": "00:00:02.345"
  }
]
```

#### Pit stops da última corrida

```http
GET /api/pit-stops/latest/
```

**Parâmetros de Query:**
- `year` (int, opcional): Ano

**Resposta:**
```json
{
  "status": "success",
  "raceInfo": {...},
  "pitStops": [...]
}
```

#### Analytics de pit stops

```http
GET /api/pit-stops/analytics/?year=2025
```

**Parâmetros de Query:**
- `year` (int, obrigatório): Ano
- `round` (int, opcional): Rodada específica
- `team` (string, opcional): Nome da equipe

**Resposta:**
```json
{
  "status": "success",
  "year": "2025",
  "data": {
    "sessions": [
      {
        "sessionId": 1,
        "eventName": "Bahrain Grand Prix",
        "round": 1,
        "pit_stops": [
          {
            "lap": 15,
            "driver": "VER",
            "team": "Red Bull Racing",
            "duration": 2.345,
            "stopNumber": 1
          }
        ]
      }
    ],
    "team_stats": [
      {
        "team": "Red Bull Racing",
        "color": "#3671C6",
        "total_stops": 40,
        "avg_duration": 2.456,
        "min_duration": 2.123,
        "max_duration": 3.456
      }
    ],
    "driver_stats": [
      {
        "driver": "VER",
        "total_stops": 20,
        "avg_duration": 2.345,
        "min_duration": 2.100,
        "max_duration": 3.200
      }
    ]
  }
}
```

---

### Weather Data

**Base URL:** `/api/weather/`

#### Listar dados meteorológicos

```http
GET /api/weather/
```

**Parâmetros de Query:**
- `session` (int): ID da sessão
- `rainfall` (boolean): true/false

**Resposta:**
```json
[
  {
    "id": 1,
    "session": 1,
    "timestamp": "2025-03-02T18:30:00Z",
    "air_temp": 28.5,
    "track_temp": 42.3,
    "humidity": 45.0,
    "pressure": 1013.25,
    "rainfall": false,
    "wind_speed": 3.5,
    "wind_direction": 180
  }
]
```

#### Dados meteorológicos da última corrida

```http
GET /api/weather/latest/
```

**Resposta:**
```json
{
  "status": "success",
  "raceInfo": {...},
  "weatherData": [...]
}
```

#### Analytics meteorológicos

```http
GET /api/weather/analytics/?year=2025&round=1
```

**Parâmetros de Query:**
- `year` (int, obrigatório): Ano
- `round` (int, obrigatório): Rodada
- `session_type` (string, opcional): Tipo de sessão (padrão: R)

**Resposta:**
```json
{
  "status": "success",
  "sessionInfo": {
    "eventName": "Bahrain Grand Prix",
    "circuit": "Bahrain International Circuit",
    "round": 1,
    "sessionType": "R",
    "date": "2025-03-02"
  },
  "data": [
    {
      "index": 0,
      "timestamp": "2025-03-02T18:00:00Z",
      "airTemp": 28.5,
      "trackTemp": 42.3,
      "humidity": 45.0,
      "pressure": 1013.25,
      "windSpeed": 3.5,
      "windDirection": 180,
      "rainfall": false
    }
  ],
  "stats": {
    "airTemp": {"avg": 28.3, "min": 27.5, "max": 29.0},
    "trackTemp": {"avg": 41.5, "min": 40.0, "max": 43.0},
    "humidity": {"avg": 45.5, "min": 42.0, "max": 48.0},
    "rainfall": false
  }
}
```

---

## Endpoints Customizados

### Driver Prediction

Prever desempenho de um piloto em um circuito específico.

```http
GET /api/driver-prediction/?driver=VER&circuit=Bahrain
```

**Parâmetros de Query:**
- `driver` (string, obrigatório): Código do piloto (ex: VER, HAM)
- `circuit` (string, obrigatório): Nome do circuito
- `year` (int, opcional): Ano para previsão (padrão: ano atual)

**Resposta:**
```json
{
  "status": "success",
  "driver": {
    "code": "VER",
    "fullName": "Max Verstappen",
    "number": 1
  },
  "circuit": {
    "name": "Bahrain International Circuit",
    "location": "Sakhir",
    "country": "Bahrain"
  },
  "prediction": {
    "averagePosition": 2.5,
    "averagePoints": 18.3,
    "predictedPositionRange": {
      "min": 1,
      "max": 4
    },
    "probabilities": {
      "win": 45.5,
      "podium": 78.2,
      "points": 95.0
    }
  },
  "statistics": {
    "totalRaces": 6,
    "wins": 3,
    "podiums": 5,
    "pointsFinishes": 6
  },
  "history": [
    {
      "year": 2024,
      "position": 1,
      "points": 25.0,
      "team": "Red Bull Racing"
    }
  ]
}
```

**Algoritmo:**
- Usa média ponderada com viés de recência (corridas mais recentes têm maior peso)
- Corridas recentes têm peso exponencial: `0.7^i`
- Considera consistência (boost para resultados consistentes)
- Calcula intervalo de posição usando desvio padrão

---

### Constructor Prediction

Prever desempenho de uma equipe em um circuito específico.

```http
GET /api/constructor-prediction/?team=Red Bull Racing&circuit=Bahrain
```

**Parâmetros de Query:**
- `team` (string, obrigatório): Nome da equipe
- `circuit` (string, obrigatório): Nome do circuito
- `year` (int, opcional): Ano para previsão

**Resposta:**
```json
{
  "status": "success",
  "team": {
    "name": "Red Bull Racing",
    "color": "#3671C6"
  },
  "circuit": {...},
  "prediction": {
    "averagePosition": 2.1,
    "averagePointsPerRace": 35.6,
    "predictedPositionRange": {
      "min": 1,
      "max": 3
    },
    "probabilities": {
      "win": 55.0,
      "podium": 85.0
    }
  },
  "statistics": {
    "totalRaces": 6,
    "wins": 4,
    "podiums": 10,
    "totalPoints": 214.0
  },
  "history": [
    {
      "year": 2024,
      "results": [
        {"driver": "VER", "position": 1, "points": 25.0},
        {"driver": "PER", "position": 3, "points": 15.0}
      ],
      "totalPoints": 40.0
    }
  ]
}
```

---

### Available Filters

Endpoints para popular dropdowns e filtros no frontend.

#### Pilotos disponíveis

```http
GET /api/available-drivers/
```

**Resposta:**
```json
{
  "status": "success",
  "drivers": [
    {
      "code": "VER",
      "full_name": "Max Verstappen",
      "number": 1
    }
  ]
}
```

#### Equipes disponíveis

```http
GET /api/available-teams/
```

**Resposta:**
```json
{
  "status": "success",
  "teams": [
    {
      "name": "Red Bull Racing",
      "color": "#3671C6"
    }
  ]
}
```

#### Circuitos disponíveis

```http
GET /api/available-circuits/
```

**Resposta:**
```json
{
  "status": "success",
  "circuits": [
    {
      "name": "Bahrain International Circuit",
      "location": "Sakhir",
      "country": "Bahrain"
    }
  ]
}
```

#### Anos disponíveis

```http
GET /api/available-years/
```

**Resposta:**
```json
{
  "status": "success",
  "years": [2025, 2024, 2023, 2022]
}
```

---

### Data Status

Status do banco de dados e workers Celery.

```http
GET /api/status/
```

**Resposta:**
```json
{
  "status": "success",
  "timestamp": "2025-03-02T20:00:00Z",
  "stats": {
    "database": {
      "seasons": 4,
      "events": 96,
      "sessions": 480,
      "drivers": 40,
      "teams": 10,
      "circuits": 24,
      "race_results": 1920,
      "qualifying_results": 1920,
      "sprint_results": 240,
      "driver_standings": 960,
      "constructor_standings": 960,
      "lap_times": 115200,
      "tyre_strategies": 3840,
      "pit_stops": 5760,
      "weather_data": 96000
    },
    "sessions_by_type": {
      "races": 96,
      "qualifying": 96,
      "sprints": 12
    },
    "sessions_status": {
      "complete": 200,
      "incomplete": 280,
      "data_collected": 180
    },
    "latest_updates": {
      "race": {
        "event_name": "Bahrain Grand Prix",
        "round": 1,
        "session_date": "2025-03-02T18:00:00Z",
        "collection_date": "2025-03-02T20:30:00Z"
      },
      "qualifying": {...},
      "sprint": {...}
    },
    "celery": {
      "active_tasks": {},
      "scheduled_tasks": {},
      "workers_online": ["celery@worker1"]
    },
    "celery_beat": {
      "periodic_tasks": [
        {
          "name": "collect-all-data",
          "task": "data_collector.tasks.start_all_data_collection",
          "enabled": true,
          "last_run_at": "2025-03-02T00:00:00Z"
        }
      ]
    }
  }
}
```

---

## Códigos de Status HTTP

- `200 OK` - Requisição bem-sucedida
- `400 Bad Request` - Parâmetros inválidos ou faltando
- `404 Not Found` - Recurso não encontrado
- `500 Internal Server Error` - Erro no servidor

---

## Exemplos de Uso

### Com cURL

```bash
# Última corrida
curl http://localhost:8000/api/races/latest/?year=2025

# Classificação de pilotos
curl http://localhost:8000/api/driver-standings/latest/?year=2025

# Predição de piloto
curl "http://localhost:8000/api/driver-prediction/?driver=VER&circuit=Bahrain"

# Histórico de corridas com filtros
curl "http://localhost:8000/api/races/history/?year=2024&circuit=1"
```

### Com JavaScript (Axios)

```javascript
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api/',
});

// Última corrida
const response = await api.get('/races/latest/', {
  params: { year: 2025 }
});

// Evolução de pontos
const evolution = await api.get('/driver-standings/evolution/', {
  params: {
    year: 2025,
    drivers: 'VER,HAM,LEC'
  }
});
```

---

## Paginação

Atualmente a API não usa paginação. Todos os resultados são retornados de uma vez.

Para grandes volumes de dados (como lap times), considere usar filtros para reduzir o volume.

---

## Rate Limiting

Não há rate limiting implementado atualmente.

---

## Versionamento

A API não tem versionamento explícito. Mudanças futuras serão backward-compatible quando possível.
