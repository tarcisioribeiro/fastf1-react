# Documentação dos Modelos do Banco de Dados

Esta documentação descreve todos os modelos Django usados na aplicação FastF1 React.

## Sumário

- [Modelos Base](#modelos-base)
  - [Season](#season)
  - [Team](#team)
  - [Driver](#driver)
  - [Circuit](#circuit)
  - [Event](#event)
  - [Session](#session)
- [Resultados](#resultados)
  - [RaceResult](#raceresult)
  - [QualifyingResult](#qualifyingresult)
  - [SprintResult](#sprintresult)
- [Classificações](#classificações)
  - [DriverStanding](#driverstanding)
  - [ConstructorStanding](#constructorstanding)
- [Dados de Sessão](#dados-de-sessão)
  - [LapTime](#laptime)
  - [TyreStrategy](#tyrestrategy)
  - [PitStop](#pitstop)
  - [WeatherData](#weatherdata)
  - [TelemetryData](#telemetrydata)

---

## Modelos Base

### Season

Representa uma temporada da Fórmula 1.

**Campos:**
- `year` (IntegerField) - Ano da temporada (>=2022)
- `created_at` (DateTimeField) - Data de criação do registro
- `updated_at` (DateTimeField) - Data da última atualização

**Índices:**
- `year` é unique
- Ordenação padrão: `-year` (mais recente primeiro)

**Relações:**
- `events` (reverse ForeignKey) - Eventos desta temporada
- `driver_standings` (reverse ForeignKey) - Classificações de pilotos
- `constructor_standings` (reverse ForeignKey) - Classificações de construtores

---

### Team

Representa uma equipe/construtor de F1.

**Campos:**
- `team_id` (CharField, max=50) - ID único da equipe (lowercase com underscore)
- `name` (CharField, max=100) - Nome da equipe
- `full_name` (CharField, max=200, opcional) - Nome completo
- `color` (CharField, max=7) - Cor principal em hexadecimal (ex: #FF0000)
- `color_secondary` (CharField, max=7, opcional) - Cor secundária
- `created_at` (DateTimeField) - Data de criação
- `updated_at` (DateTimeField) - Data da última atualização

**Índices:**
- `team_id` é unique
- Ordenação padrão: `name`

**Cores Padrão (2024/2025):**
```python
{
    'red_bull_racing': '#3671C6',
    'ferrari': '#E8002D',
    'mclaren': '#FF8000',
    'mercedes': '#27F4D2',
    'aston_martin': '#229971',
    'alpine': '#FF87BC',
    'williams': '#64C4FF',
    'rb': '#6692FF',
    'sauber': '#52E252',
    'haas': '#B6BABD',
}
```

**Relações:**
- `race_results` (reverse ForeignKey) - Resultados de corrida
- `qualifying_results` (reverse ForeignKey) - Resultados de classificação
- `sprint_results` (reverse ForeignKey) - Resultados de sprint
- `driver_standings` (reverse ForeignKey) - Classificações de pilotos
- `standings` (reverse ForeignKey) - Classificações de construtores

---

### Driver

Representa um piloto de F1.

**Campos:**
- `driver_id` (CharField, max=50) - ID único do piloto
- `code` (CharField, max=3) - Código de 3 letras (ex: VER, HAM)
- `number` (IntegerField) - Número do piloto (1-99)
- `first_name` (CharField, max=100) - Primeiro nome
- `last_name` (CharField, max=100) - Sobrenome
- `nationality` (CharField, max=100) - Nacionalidade
- `date_of_birth` (DateField, opcional) - Data de nascimento
- `created_at` (DateTimeField) - Data de criação
- `updated_at` (DateTimeField) - Data da última atualização

**Propriedades:**
- `full_name` - Retorna "{first_name} {last_name}"

**Índices:**
- `driver_id` é unique
- Ordenação padrão: `last_name`, `first_name`

**Relações:**
- `race_results` (reverse ForeignKey) - Resultados de corrida
- `qualifying_results` (reverse ForeignKey) - Resultados de classificação
- `sprint_results` (reverse ForeignKey) - Resultados de sprint
- `standings` (reverse ForeignKey) - Classificações

---

### Circuit

Representa um circuito de F1.

**Campos:**
- `circuit_id` (CharField, max=50) - ID único do circuito
- `name` (CharField, max=200) - Nome do circuito
- `location` (CharField, max=100) - Localização (cidade)
- `country` (CharField, max=100) - País
- `latitude` (FloatField, opcional) - Latitude
- `longitude` (FloatField, opcional) - Longitude
- `length_km` (FloatField, opcional) - Comprimento em quilômetros
- `created_at` (DateTimeField) - Data de criação
- `updated_at` (DateTimeField) - Data da última atualização

**Índices:**
- `circuit_id` é unique
- Ordenação padrão: `name`

**Relações:**
- `events` (reverse ForeignKey) - Eventos neste circuito

---

### Event

Representa um evento/Grande Prêmio.

**Campos:**
- `event_id` (CharField, max=50) - ID único do evento (formato: {year}_{round})
- `season` (ForeignKey → Season) - Temporada
- `round_number` (IntegerField) - Número da rodada (>=1)
- `circuit` (ForeignKey → Circuit) - Circuito
- `event_name` (CharField, max=200) - Nome oficial do evento
- `event_type` (CharField, max=20) - Tipo: 'race', 'sprint', 'testing'
- `event_date` (DateField) - Data do evento
- `created_at` (DateTimeField) - Data de criação
- `updated_at` (DateTimeField) - Data da última atualização

**Índices:**
- `event_id` é unique
- (`season`, `round_number`) é unique together
- Índice em `event_date`
- Ordenação padrão: `season`, `round_number`

**Relações:**
- `sessions` (reverse ForeignKey) - Sessões deste evento
- `driver_standings` (reverse ForeignKey) - Classificações após este evento
- `constructor_standings` (reverse ForeignKey) - Classificações de construtores

---

### Session

Representa uma sessão (treino, classificação, corrida, sprint).

**Campos:**
- `session_id` (CharField, max=100) - ID único da sessão
- `event` (ForeignKey → Event) - Evento pai
- `session_type` (CharField, max=3) - Tipo: 'FP1', 'FP2', 'FP3', 'Q', 'S', 'SQ', 'R'
- `session_date` (DateTimeField) - Data/hora da sessão
- `is_complete` (BooleanField) - Se a sessão foi concluída
- `data_collected` (BooleanField) - Se os dados foram coletados
- `collection_date` (DateTimeField, opcional) - Data da coleta de dados
- `created_at` (DateTimeField) - Data de criação
- `updated_at` (DateTimeField) - Data da última atualização

**Tipos de Sessão:**
- `FP1` - Free Practice 1
- `FP2` - Free Practice 2
- `FP3` - Free Practice 3
- `Q` - Qualifying
- `S` - Sprint
- `SQ` - Sprint Qualifying
- `R` - Race

**Índices:**
- `session_id` é unique
- Índice composto: (`event`, `session_type`)
- Índice em `session_date`
- Ordenação padrão: `event`, `session_date`

**Relações:**
- `race_results` (reverse ForeignKey) - Resultados de corrida
- `qualifying_results` (reverse ForeignKey) - Resultados de classificação
- `sprint_results` (reverse ForeignKey) - Resultados de sprint
- `lap_times` (reverse ForeignKey) - Tempos de volta
- `pit_stops` (reverse ForeignKey) - Pit stops
- `weather_data` (reverse ForeignKey) - Dados meteorológicos

---

## Resultados

### RaceResult

Resultado de corrida para cada piloto.

**Campos:**
- `session` (ForeignKey → Session) - Sessão da corrida
- `driver` (ForeignKey → Driver) - Piloto
- `team` (ForeignKey → Team) - Equipe
- `position` (IntegerField) - Posição final (>=1)
- `grid_position` (IntegerField, opcional) - Posição no grid
- `points` (FloatField) - Pontos conquistados
- `laps_completed` (IntegerField) - Voltas completadas
- `total_race_time` (DurationField, opcional) - Tempo total de corrida
- `fastest_lap_time` (DurationField, opcional) - Tempo da volta mais rápida
- `fastest_lap_number` (IntegerField, opcional) - Número da volta mais rápida
- `status` (CharField, max=50) - Status (ex: 'Finished', 'DNF', '+1 Lap')
- `dnf` (BooleanField) - Did Not Finish
- `created_at` (DateTimeField) - Data de criação
- `updated_at` (DateTimeField) - Data da última atualização

**Cálculo de Tempo Total:**
- Vencedor: `total_race_time` = tempo bruto da FastF1
- Outros: `total_race_time` = tempo_vencedor + gap

**Índices:**
- (`session`, `driver`) é unique together
- Índice em (`session`, `position`)
- Ordenação padrão: `session`, `position`

---

### QualifyingResult

Resultado de classificação para cada piloto.

**Campos:**
- `session` (ForeignKey → Session) - Sessão da classificação
- `driver` (ForeignKey → Driver) - Piloto
- `team` (ForeignKey → Team) - Equipe
- `position` (IntegerField) - Posição final (>=1)
- `q1_time` (DurationField, opcional) - Tempo do Q1
- `q2_time` (DurationField, opcional) - Tempo do Q2
- `q3_time` (DurationField, opcional) - Tempo do Q3
- `created_at` (DateTimeField) - Data de criação
- `updated_at` (DateTimeField) - Data da última atualização

**Índices:**
- (`session`, `driver`) é unique together
- Índice em (`session`, `position`)
- Ordenação padrão: `session`, `position`

---

### SprintResult

Resultado de corrida sprint para cada piloto.

**Campos:**
- `session` (ForeignKey → Session) - Sessão da sprint
- `driver` (ForeignKey → Driver) - Piloto
- `team` (ForeignKey → Team) - Equipe
- `position` (IntegerField) - Posição final (>=1)
- `grid_position` (IntegerField, opcional) - Posição no grid
- `points` (FloatField) - Pontos conquistados (8-7-6-5-4-3-2-1 para top 8)
- `laps_completed` (IntegerField) - Voltas completadas
- `total_sprint_time` (DurationField, opcional) - Tempo total da sprint
- `fastest_lap_time` (DurationField, opcional) - Tempo da volta mais rápida
- `status` (CharField, max=50) - Status
- `created_at` (DateTimeField) - Data de criação
- `updated_at` (DateTimeField) - Data da última atualização

**IMPORTANTE:**
- Sprints contribuem APENAS com pontos para o campeonato
- Vitórias, pódios e poles de sprints NÃO contam nas estatísticas oficiais
- Apenas corridas principais (tipo 'R') contam para vitórias/pódios/poles

**Índices:**
- (`session`, `driver`) é unique together
- Índice em (`session`, `position`)
- Ordenação padrão: `session`, `position`

---

## Classificações

### DriverStanding

Classificação do campeonato de pilotos após cada evento.

**Campos:**
- `season` (ForeignKey → Season) - Temporada
- `event` (ForeignKey → Event) - Evento (após o qual esta classificação é válida)
- `driver` (ForeignKey → Driver) - Piloto
- `team` (ForeignKey → Team) - Equipe atual do piloto
- `position` (IntegerField) - Posição no campeonato (>=1)
- `points` (FloatField) - Pontos acumulados
- `wins` (IntegerField) - Vitórias (apenas corridas principais)
- `podiums` (IntegerField) - Pódios (apenas corridas principais)
- `created_at` (DateTimeField) - Data de criação
- `updated_at` (DateTimeField) - Data da última atualização

**Cálculo:**
- Pontos: soma de race_results.points + sprint_results.points
- Vitórias: contagem de position=1 em corridas (tipo 'R')
- Pódios: contagem de position in [1,2,3] em corridas (tipo 'R')

**Índices:**
- (`season`, `event`, `driver`) é unique together
- Índice composto: (`season`, `event`, `position`)
- Ordenação padrão: `season`, `event`, `position`

---

### ConstructorStanding

Classificação do campeonato de construtores após cada evento.

**Campos:**
- `season` (ForeignKey → Season) - Temporada
- `event` (ForeignKey → Event) - Evento
- `team` (ForeignKey → Team) - Equipe
- `position` (IntegerField) - Posição no campeonato (>=1)
- `points` (FloatField) - Pontos acumulados (soma dos dois pilotos)
- `wins` (IntegerField) - Vitórias (apenas corridas principais)
- `podiums` (IntegerField) - Pódios (apenas corridas principais)
- `created_at` (DateTimeField) - Data de criação
- `updated_at` (DateTimeField) - Data da última atualização

**Cálculo:**
- Pontos: soma de todos os pontos dos pilotos da equipe
- Vitórias: contagem de vitórias em corridas principais
- Pódios: contagem de pódios em corridas principais

**Índices:**
- (`season`, `event`, `team`) é unique together
- Índice composto: (`season`, `event`, `position`)
- Ordenação padrão: `season`, `event`, `position`

---

## Dados de Sessão

### LapTime

Tempos de volta individuais para cada piloto.

**Campos:**
- `session` (ForeignKey → Session) - Sessão
- `driver` (ForeignKey → Driver) - Piloto
- `team` (ForeignKey → Team) - Equipe
- `lap_number` (IntegerField) - Número da volta (>=1)
- `lap_time` (DurationField) - Tempo da volta
- `sector1_time` (DurationField, opcional) - Tempo do setor 1
- `sector2_time` (DurationField, opcional) - Tempo do setor 2
- `sector3_time` (DurationField, opcional) - Tempo do setor 3
- `is_personal_best` (BooleanField) - Se é o melhor tempo pessoal
- `is_accurate` (BooleanField) - Se o tempo é preciso
- `compound` (CharField, max=20) - Composto de pneu usado
- `tyre_life` (IntegerField, opcional) - Idade dos pneus em voltas
- `created_at` (DateTimeField) - Data de criação

**Índices:**
- (`session`, `driver`, `lap_number`) é unique together
- Índice composto: (`session`, `driver`)
- Índice composto: (`session`, `lap_number`)
- Ordenação padrão: `session`, `lap_number`, `driver`

---

### TyreStrategy

Estratégia de pneus e dados de stint (2025+).

**Campos:**
- `session` (ForeignKey → Session) - Sessão
- `driver` (ForeignKey → Driver) - Piloto
- `team` (ForeignKey → Team) - Equipe
- `stint_number` (IntegerField) - Número do stint (>=1)
- `compound` (CharField, max=15) - Composto: SOFT, MEDIUM, HARD, INTERMEDIATE, WET
- `start_lap` (IntegerField) - Volta inicial do stint
- `end_lap` (IntegerField) - Volta final do stint
- `stint_length` (IntegerField) - Duração do stint em voltas
- `avg_lap_time` (DurationField, opcional) - Tempo médio de volta
- `fastest_lap_time` (DurationField, opcional) - Volta mais rápida no stint
- `created_at` (DateTimeField) - Data de criação
- `updated_at` (DateTimeField) - Data da última atualização

**Compostos:**
- `SOFT` - Macio (vermelho)
- `MEDIUM` - Médio (amarelo)
- `HARD` - Duro (branco)
- `INTERMEDIATE` - Intermediário (verde)
- `WET` - Chuva (azul)

**Índices:**
- (`session`, `driver`, `stint_number`) é unique together
- Índice em (`session`, `driver`)
- Ordenação padrão: `session`, `driver`, `stint_number`

---

### PitStop

Dados de pit stop para cada piloto.

**Campos:**
- `session` (ForeignKey → Session) - Sessão
- `driver` (ForeignKey → Driver) - Piloto
- `team` (ForeignKey → Team) - Equipe
- `stop_number` (IntegerField) - Número do pit stop (>=1)
- `lap` (IntegerField) - Volta em que ocorreu o pit stop (>=1)
- `duration` (DurationField, opcional) - Duração do pit stop
- `created_at` (DateTimeField) - Data de criação

**Validação:**
- Durações < 0 ou > 300 segundos são consideradas inválidas e definidas como NULL
- Nem todos os pit stops têm duração válida disponível

**Índices:**
- (`session`, `driver`, `stop_number`) é unique together
- Índice em (`session`, `driver`)
- Ordenação padrão: `session`, `lap`

---

### WeatherData

Condições meteorológicas durante uma sessão.

**Campos:**
- `session` (ForeignKey → Session) - Sessão
- `timestamp` (DateTimeField) - Data/hora da medição
- `air_temp` (FloatField) - Temperatura do ar (Celsius)
- `track_temp` (FloatField) - Temperatura da pista (Celsius)
- `humidity` (FloatField) - Umidade (0-100%)
- `pressure` (FloatField) - Pressão atmosférica (mbar)
- `rainfall` (BooleanField) - Se está chovendo
- `wind_speed` (FloatField, opcional) - Velocidade do vento (m/s)
- `wind_direction` (IntegerField, opcional) - Direção do vento (0-360 graus)
- `created_at` (DateTimeField) - Data de criação

**Conversão de Timestamp:**
- FastF1 fornece timestamps relativos (timedelta desde início da sessão)
- São convertidos para timestamps absolutos: `session.date + timedelta`

**Índices:**
- Índice em (`session`, `timestamp`)
- Ordenação padrão: `session`, `timestamp`

---

### TelemetryData

Dados de telemetria para voltas de pilotos (dados amostrados).

**Campos:**
- `lap_time` (ForeignKey → LapTime) - Volta associada
- `distance` (FloatField) - Distância ao longo da pista (metros)
- `speed` (FloatField) - Velocidade (km/h)
- `throttle` (FloatField) - Aceleração (0-100%)
- `brake` (BooleanField) - Se está freando
- `drs` (IntegerField) - Status do DRS
- `gear` (IntegerField) - Marcha (0-8)
- `rpm` (IntegerField, opcional) - RPM do motor
- `created_at` (DateTimeField) - Data de criação

**Nota:**
- Dados de telemetria são volumosos e amostrados
- Úteis para análises detalhadas de desempenho

**Índices:**
- Índice em (`lap_time`, `distance`)
- Ordenação padrão: `lap_time`, `distance`

---

## Relacionamentos Entre Modelos

```
Season
  └── Event
      ├── Session
      │   ├── RaceResult
      │   ├── QualifyingResult
      │   ├── SprintResult
      │   ├── LapTime
      │   │   └── TelemetryData
      │   ├── TyreStrategy
      │   ├── PitStop
      │   └── WeatherData
      ├── DriverStanding
      └── ConstructorStanding

Driver ←→ Team (através de resultados)
Event → Circuit
```

## Boas Práticas

1. **Timezone Awareness**: Sempre use timestamps timezone-aware
2. **Validação**: Use `safe_value()` para converter NaN/NaT para None
3. **Índices**: Use select_related() e prefetch_related() para otimizar queries
4. **Cálculo de Pontos**: Sprints contribuem com pontos mas não com vitórias/pódios
5. **Durações**: DurationField aceita timedelta do pandas diretamente
