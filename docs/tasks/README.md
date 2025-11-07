# Documentação das Celery Tasks

Esta documentação descreve todas as tarefas assíncronas do Celery usadas para coletar dados da API FastF1.

## Sumário

- [Configuração](#configuração)
- [Funções Auxiliares](#funções-auxiliares)
- [Tasks Principais](#tasks-principais)
  - [collect_session_data](#collect_session_data)
  - [collect_all_race_data](#collect_all_race_data)
  - [collect_all_qualifying_data](#collect_all_qualifying_data)
  - [collect_all_sprint_data](#collect_all_sprint_data)
  - [collect_all_standings_data](#collect_all_standings_data)
  - [collect_tyre_data](#collect_tyre_data)
  - [start_all_data_collection](#start_all_data_collection)
- [Processadores de Dados](#processadores-de-dados)
- [Execução Manual](#execução-manual)
- [Monitoramento](#monitoramento)

---

## Configuração

### Cache do FastF1

```python
import fastf1
from django.conf import settings

fastf1.Cache.enable_cache(str(settings.FASTF1_CACHE_DIR))
```

O cache é armazenado em `.fastf1_cache/` no diretório raiz do projeto.

### Logger

```python
import logging
logger = logging.getLogger('data_collector')
```

Todas as tasks registram logs detalhados para debugging.

---

## Funções Auxiliares

### safe_value(value)

Converte valores NaN, NaT e None para None (compatível com MySQL).

```python
def safe_value(value: Any) -> Any:
    """Convert NaN, NaT and None values to None for MySQL compatibility."""
    if pd.isna(value) or (isinstance(value, float) and np.isnan(value)):
        return None
    return value
```

**Uso:**
```python
points = safe_value(row.get('Points', 0))
```

---

### get_or_create_season(year)

Obtém ou cria uma temporada.

```python
def get_or_create_season(year: int) -> Season:
    season, created = Season.objects.get_or_create(year=year)
    if created:
        logger.info(f"Created new season: {year}")
    return season
```

---

### get_or_create_team(team_name, team_color, **kwargs)

Obtém ou cria uma equipe com cores padrão.

```python
def get_or_create_team(team_name: str, team_color: str = None, **kwargs) -> Team:
    team_id = team_name.lower().replace(' ', '_')

    # Default team colors (F1 2024/2025 season)
    default_colors = {
        'red_bull_racing': '#3671C6',
        'ferrari': '#E8002D',
        'mclaren': '#FF8000',
        # ...
    }

    if not team_color:
        team_color = default_colors.get(team_id, '#FFFFFF')

    team, created = Team.objects.get_or_create(
        team_id=team_id,
        defaults={'name': team_name, 'color': team_color, **kwargs}
    )
    return team
```

**Cores Padrão:**
- Red Bull Racing: `#3671C6`
- Ferrari: `#E8002D`
- McLaren: `#FF8000`
- Mercedes: `#27F4D2`
- Aston Martin: `#229971`
- Alpine: `#FF87BC`
- Williams: `#64C4FF`
- RB (AlphaTauri): `#6692FF`
- Sauber: `#52E252`
- Haas: `#B6BABD`

---

### get_or_create_driver(driver_info)

Obtém ou cria um piloto.

```python
def get_or_create_driver(driver_info: dict) -> Driver:
    driver, created = Driver.objects.get_or_create(
        driver_id=driver_info.get('driver_id'),
        defaults=driver_info
    )
    return driver
```

**Formato de driver_info:**
```python
{
    'driver_id': 'ver',
    'code': 'VER',
    'number': 1,
    'first_name': 'Max',
    'last_name': 'Verstappen'
}
```

---

### get_or_create_circuit(circuit_info)

Obtém ou cria um circuito.

```python
def get_or_create_circuit(circuit_info: dict) -> Circuit:
    circuit, created = Circuit.objects.get_or_create(
        circuit_id=circuit_info.get('circuit_id'),
        defaults=circuit_info
    )
    return circuit
```

---

## Tasks Principais

### collect_session_data

Task principal para coletar dados de uma sessão específica.

**Assinatura:**
```python
@shared_task(bind=True, max_retries=3)
def collect_session_data(self, year: int, round_num: int, session_type: str):
```

**Parâmetros:**
- `year` (int) - Ano da temporada
- `round_num` (int) - Número da rodada (1-24)
- `session_type` (str) - Tipo de sessão:
  - `'R'` - Race
  - `'Q'` - Qualifying
  - `'S'` - Sprint
  - `'SQ'` - Sprint Qualifying
  - `'FP1'`, `'FP2'`, `'FP3'` - Free Practice

**Retry:**
- Máximo de 3 tentativas
- Intervalo de 60 segundos entre tentativas

**Fluxo:**
1. Carrega sessão do FastF1
2. Cria/atualiza Season, Event, Circuit
3. Cria/atualiza Session
4. Processa resultados (race/qualifying/sprint)
5. Coleta lap times
6. Coleta pit stops (apenas corridas)
7. Coleta weather data

**Exemplo de Uso:**
```python
from data_collector.tasks import collect_session_data

# Coletar corrida do Bahrain 2025
collect_session_data.delay(2025, 1, 'R')

# Coletar classificação
collect_session_data.delay(2025, 1, 'Q')
```

**Logs:**
```
INFO: Collecting R data for 2025 Round 1
INFO: Successfully collected R data for 2025 Round 1
```

---

### collect_all_race_data

Coleta dados de todas as corridas de 2018 até o ano atual.

**Assinatura:**
```python
@shared_task
def collect_all_race_data():
```

**Fluxo:**
1. Itera de 2018 até ano atual
2. Obtém schedule de cada ano
3. Cria tasks para cada corrida em paralelo

**Exemplo de Uso:**
```python
from data_collector.tasks import collect_all_race_data

# Iniciar coleta de todas as corridas
collect_all_race_data.delay()
```

**Logs:**
```
INFO: Started collecting race data for 96 races
```

**Tempo estimado:**
- ~2-4 horas para coleta completa (depende da rede e cache)

---

### collect_all_qualifying_data

Coleta dados de todas as classificações de 2018 até o ano atual.

**Assinatura:**
```python
@shared_task
def collect_all_qualifying_data():
```

**Fluxo:**
Similar a `collect_all_race_data`, mas para sessões tipo 'Q'.

**Exemplo de Uso:**
```python
from data_collector.tasks import collect_all_qualifying_data

collect_all_qualifying_data.delay()
```

---

### collect_all_sprint_data

Coleta dados de todas as sprints de 2021 até o ano atual.

**Assinatura:**
```python
@shared_task
def collect_all_sprint_data():
```

**Fluxo:**
1. Itera de 2021 (início das sprints) até ano atual
2. Tenta carregar sessão sprint para cada rodada
3. Se não existir sprint, pula silenciosamente

**Nota:**
Nem todos os eventos têm sprints. A task trata exceções automaticamente.

**Exemplo de Uso:**
```python
from data_collector.tasks import collect_all_sprint_data

collect_all_sprint_data.delay()
```

---

### collect_all_standings_data

Calcula e salva classificações a partir dos resultados coletados.

**Assinatura:**
```python
@shared_task
def collect_all_standings_data():
```

**Fluxo:**
1. Para cada temporada (2018-atual)
2. Para cada evento da temporada (ordenado por round)
3. Acumula pontos de corridas e sprints
4. Conta vitórias e pódios (APENAS de corridas principais)
5. Calcula classificações de pilotos e construtores
6. Salva standings após cada evento

**Cálculo de Pontos:**
- **Pilotos:** Soma de race_results.points + sprint_results.points
- **Construtores:** Soma dos pontos de ambos os pilotos

**Cálculo de Vitórias/Pódios:**
- **IMPORTANTE:** Apenas corridas principais (tipo 'R') contam
- Sprints contribuem APENAS com pontos
- position = 1 → vitória
- position in [1, 2, 3] → pódio

**Exemplo de Uso:**
```python
from data_collector.tasks import collect_all_standings_data

collect_all_standings_data.delay()
```

**Logs:**
```
INFO: Calculating standings for 2025
INFO: Finished calculating standings for 2025
```

**Nota:**
Esta task deve ser executada APÓS coletar todos os resultados de corridas e sprints.

---

### collect_tyre_data

Coleta dados de pneus de 2025 em diante.

**Assinatura:**
```python
@shared_task
def collect_tyre_data():
```

**Fluxo:**
- Similar a `collect_all_race_data`, mas apenas para 2025+
- Dados de pneus estão disponíveis apenas a partir de 2025

**Exemplo de Uso:**
```python
from data_collector.tasks import collect_tyre_data

collect_tyre_data.delay()
```

---

### start_all_data_collection

Task principal que inicia todas as coletas em paralelo.

**Assinatura:**
```python
@shared_task
def start_all_data_collection():
```

**Fluxo:**
Executa em paralelo:
1. `collect_all_race_data()`
2. `collect_all_qualifying_data()`
3. `collect_all_sprint_data()`
4. `collect_all_standings_data()`
5. `collect_tyre_data()`

**Exemplo de Uso:**
```python
from data_collector.tasks import start_all_data_collection

# Iniciar coleta completa de todos os dados
start_all_data_collection.delay()
```

**Logs:**
```
INFO: Starting all F1 data collection tasks
INFO: All data collection tasks started
```

**Tempo estimado:**
- 3-6 horas para coleta completa inicial
- Coletas subsequentes são mais rápidas devido ao cache

**Requisitos:**
- Mínimo de 5 workers Celery para execução paralela eficiente
- Conexão estável com internet
- Espaço em disco para cache (~5-10 GB)

---

## Processadores de Dados

### process_race_results(session, session_obj)

Processa resultados de corrida.

**Fluxo:**
1. Obtém resultados do FastF1
2. Identifica tempo do vencedor
3. Calcula tempo total para cada piloto:
   - Vencedor: tempo direto
   - Outros: tempo_vencedor + gap
4. Cria/atualiza RaceResult para cada piloto

**Campos processados:**
- position, grid_position, points
- laps_completed, total_race_time
- fastest_lap_time, fastest_lap_number
- status, dnf

---

### process_qualifying_results(session, session_obj)

Processa resultados de classificação.

**Fluxo:**
1. Obtém resultados do FastF1
2. Extrai tempos Q1, Q2, Q3
3. Cria/atualiza QualifyingResult para cada piloto

**Campos processados:**
- position
- q1_time, q2_time, q3_time

---

### process_sprint_results(session, session_obj)

Processa resultados de sprint.

**Fluxo:**
Similar a `process_race_results`, mas para sprints.

**Campos processados:**
- position, grid_position, points
- laps_completed, total_sprint_time
- fastest_lap_time, status

**Pontos de Sprint:**
- Top 8: 8-7-6-5-4-3-2-1 pontos

---

### process_lap_times(session, session_obj)

Processa tempos de volta para todos os pilotos.

**Fluxo:**
1. Obtém laps do FastF1
2. Para cada volta:
   - Identifica piloto e equipe
   - Extrai tempos de setores
   - Extrai informações de pneu
   - Salva LapTime

**Campos processados:**
- lap_number, lap_time
- sector1_time, sector2_time, sector3_time
- compound, tyre_life
- is_personal_best, is_accurate

**Nota:**
Pode gerar MUITOS registros (milhares por sessão).

---

### process_weather_data(session, session_obj)

Processa dados meteorológicos.

**Fluxo:**
1. Obtém weather_data do FastF1
2. Para cada registro:
   - Converte timestamp relativo para absoluto
   - `absolute_time = session.date + timedelta`
   - Torna timezone-aware
3. Salva WeatherData

**Campos processados:**
- timestamp (convertido)
- air_temp, track_temp
- humidity, pressure
- rainfall, wind_speed, wind_direction

**Conversão de Timestamp:**
```python
# FastF1 fornece timedelta desde início da sessão
timestamp = row.get('Time')  # timedelta

# Converter para datetime absoluto
absolute_time = session.date + timestamp

# Tornar timezone-aware
from django.utils import timezone as django_tz
if absolute_time.tzinfo is None:
    absolute_time = django_tz.make_aware(absolute_time, django_tz.get_current_timezone())
```

---

### process_pit_stops(session, session_obj)

Processa pit stops de corridas.

**Fluxo:**
1. Filtra laps com `PitInTime` não nulo
2. Para cada pit stop:
   - Calcula duração: `PitOutTime - PitInTime`
   - Valida duração (0-300 segundos)
   - Atribui stop_number sequencial por piloto
3. Salva PitStop

**Validação de Duração:**
```python
if duration_seconds < 0 or duration_seconds > 300:
    logger.warning(f"Invalid pit stop duration: {duration_seconds}s")
    pit_duration = None
```

**Campos processados:**
- stop_number, lap, duration

---

## Execução Manual

### Via Django Shell

```bash
docker compose exec django-api python manage.py shell
```

```python
from data_collector.tasks import *

# Coletar sessão específica
collect_session_data(2025, 1, 'R')

# Coletar todas as corridas
collect_all_race_data()

# Calcular standings
collect_all_standings_data()

# Coleta completa
start_all_data_collection()
```

### Via Celery

```bash
# Entrar no container
docker compose exec django-api bash

# Executar task
celery -A config call data_collector.tasks.collect_session_data --args='[2025, 1, "R"]'

# Executar coleta completa
celery -A config call data_collector.tasks.start_all_data_collection
```

### Via Management Command (se criado)

```bash
docker compose exec django-api python manage.py collect_f1_data --year 2025 --round 1 --session R
```

---

## Monitoramento

### Celery Flower

Interface web para monitorar tasks:

```bash
docker compose exec django-api celery -A config flower
```

Acesse: http://localhost:5555

### Logs

```bash
# Logs do worker
docker compose logs -f celery-worker

# Logs do beat
docker compose logs -f celery-beat

# Logs do Django
docker compose logs -f django-api
```

### Status via API

```bash
curl http://localhost:8000/api/status/
```

Retorna:
- Contadores de registros no banco
- Tasks ativas
- Workers online
- Últimas atualizações

---

## Troubleshooting

### Erro: "No module named 'fastf1'"

**Solução:**
```bash
docker compose exec django-api pip install fastf1
```

### Erro: "Session not available"

**Causa:** Dados ainda não disponíveis na API do FastF1

**Solução:**
- Aguardar 30-120 minutos após fim da sessão
- Verificar se a sessão realmente ocorreu

### Erro: "NaN values in database"

**Causa:** Valores NaN não convertidos

**Solução:**
Sempre usar `safe_value()`:
```python
points = safe_value(row.get('Points', 0))
```

### Tasks ficam travadas

**Solução:**
```bash
# Reiniciar worker
docker compose restart celery-worker

# Limpar tasks pendentes
docker compose exec django-api python manage.py shell
>>> from celery import current_app
>>> current_app.control.purge()
```

### Cache corrompido

**Solução:**
```bash
# Limpar cache do FastF1
rm -rf .fastf1_cache/
```

---

## Boas Práticas

1. **Sempre use delay()** para execução assíncrona:
   ```python
   collect_session_data.delay(2025, 1, 'R')  # Correto
   collect_session_data(2025, 1, 'R')  # Executa sincronamente (NÃO recomendado)
   ```

2. **Monitore logs** durante coletas grandes

3. **Execute standings** APÓS coletar todos os resultados

4. **Use cache** - não limpe a menos que necessário

5. **Valide dados** - sempre use `safe_value()` para pandas

6. **Teste com uma sessão** antes de coletar tudo:
   ```python
   # Testar com uma corrida
   collect_session_data.delay(2024, 1, 'R')

   # Se OK, coletar tudo
   start_all_data_collection.delay()
   ```

---

## Tarefas Agendadas (Celery Beat)

Você pode agendar coletas automáticas usando Celery Beat:

```python
# config/celery.py
from celery.schedules import crontab

app.conf.beat_schedule = {
    'collect-latest-race': {
        'task': 'data_collector.tasks.collect_session_data',
        'schedule': crontab(hour=22, minute=0, day_of_week='sunday'),
        'args': (2025, 'latest', 'R')
    },
}
```

---

## Referências

- [FastF1 Documentation](https://docs.fastf1.dev/)
- [Celery Documentation](https://docs.celeryq.dev/)
- [Django ORM](https://docs.djangoproject.com/en/stable/topics/db/)
