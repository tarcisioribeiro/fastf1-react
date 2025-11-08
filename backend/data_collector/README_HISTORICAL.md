# Ingestão de Dados Históricos F1 (1950-2017)

Este módulo permite coletar e processar dados históricos da Fórmula 1 do período anterior ao FastF1 (1950-2017) utilizando a API Jolpica F1 (compatível com Ergast).

## Visão Geral

### Arquivos Criados

```
backend/data_collector/
├── jolpica_client.py          # Cliente HTTP para API Jolpica F1
├── historical_processor.py    # Processadores de dados históricos
├── historical_tasks.py        # Tarefas Celery
└── README_HISTORICAL.md       # Esta documentação

backend/core/management/commands/
└── ingest_historical_data.py  # Django management command
```

### Dados Coletados

- **Metadados**: Pilotos, equipes (construtores), circuitos
- **Resultados de Corrida**: Posições, pontos, tempos, voltas completadas, status
- **Resultados de Qualifying**: Q1, Q2, Q3 tempos
- **Pit Stops**: Disponível de 2012 em diante
- **Classificações**: Driver standings e constructor standings após cada corrida

### Limitações

Dados **NÃO disponíveis** para período histórico (1950-2017):
- ❌ Telemetria detalhada
- ❌ Tempos de setores (sector times)
- ❌ Dados de pneus (tyre compounds, tyre life)
- ❌ Dados meteorológicos (weather data)
- ❌ Tempos de volta individuais (lap times limitados, disponíveis parcialmente a partir de 1996)

Esses campos serão preenchidos com `NULL` no banco de dados.

## Uso

### 1. Via Django Management Command (Recomendado)

#### Ingestão Completa (1950-2017)

```bash
# Executa dentro do container Docker
docker exec -it fastf1-react-django-api-1 python manage.py ingest_historical_data --mode complete
```

Este comando executa:
1. Coleta de metadados (drivers, teams, circuits)
2. Coleta de dados de todas as temporadas (1950-2017)
3. Validação dos dados coletados

**Tempo estimado**: Várias horas (depende da conexão e rate limiting da API)

#### Coletar Apenas Metadados

```bash
docker exec -it fastf1-react-django-api-1 python manage.py ingest_historical_data --mode metadata
```

#### Coletar uma Temporada Específica

```bash
docker exec -it fastf1-react-django-api-1 python manage.py ingest_historical_data --mode season --year 2010
```

#### Coletar Intervalo de Anos

```bash
docker exec -it fastf1-react-django-api-1 python manage.py ingest_historical_data --mode year-range --start-year 2000 --end-year 2010
```

#### Atualização Incremental (preencher lacunas)

```bash
docker exec -it fastf1-react-django-api-1 python manage.py ingest_historical_data --mode incremental --target-year 2017
```

Este modo identifica anos faltantes e coleta apenas os dados ausentes.

#### Validar Dados Coletados

```bash
docker exec -it fastf1-react-django-api-1 python manage.py ingest_historical_data --mode validate
```

Exibe relatório detalhado:
- Total de corridas, resultados e classificações
- Dados por temporada
- Issues encontrados (anos sem dados, etc)

### 2. Via Celery Tasks (Programático)

#### No Django Shell

```python
# Acessar shell Django
docker exec -it fastf1-react-django-api-1 python manage.py shell

# Importar tasks
from data_collector.historical_tasks import (
    start_complete_historical_ingestion,
    collect_historical_season,
    collect_historical_metadata,
    validate_historical_data
)

# Iniciar ingestão completa
start_complete_historical_ingestion.delay()

# Coletar apenas uma temporada
collect_historical_season.delay(2005)

# Validar dados
result = validate_historical_data()
print(result)
```

#### Tarefas Disponíveis

| Tarefa | Descrição |
|--------|-----------|
| `start_complete_historical_ingestion()` | Ingestão completa (recomendado) |
| `collect_historical_metadata()` | Coleta drivers, teams, circuits |
| `collect_historical_season(year)` | Coleta uma temporada específica |
| `collect_historical_race(year, round_num)` | Coleta uma corrida específica |
| `collect_historical_standings(year, round_num)` | Coleta classificações após uma corrida |
| `collect_all_historical_data(start, end)` | Coleta intervalo de anos |
| `incremental_historical_update(target_year)` | Preenche lacunas |
| `validate_historical_data()` | Valida e gera relatório |

## Migrações do Banco de Dados

Após modificar o modelo `Season`, é necessário criar e aplicar migrações:

```bash
# Criar migrações
docker exec -it fastf1-react-django-api-1 python manage.py makemigrations

# Aplicar migrações
docker exec -it fastf1-react-django-api-1 python manage.py migrate
```

## Monitoramento

### Logs do Celery Worker

```bash
# Acompanhar logs do worker
docker compose logs -f celery-worker
```

### Verificar Progresso no Banco

```python
# Django shell
from core.models import Season, RaceResult

# Verificar temporadas coletadas
seasons = Season.objects.filter(year__lt=2018).order_by('year')
for season in seasons:
    results_count = RaceResult.objects.filter(session__event__season=season).count()
    print(f"{season.year}: {results_count} resultados")
```

## Troubleshooting

### Rate Limiting

Se houver erros de rate limiting da API:

1. O cliente já possui delay de 0.5s entre requests
2. Para aumentar o delay, edite `jolpica_client.py`:

```python
# Linha 20
def __init__(self, rate_limit_delay: float = 1.0):  # Aumentar para 1s ou mais
```

### Erros de Conexão

Se a API Jolpica estiver indisponível:

1. Verifique conexão: `curl http://api.jolpi.ca/ergast/f1/2010/1/results.json`
2. O sistema possui retry automático (3 tentativas com intervalo de 60s)

### Dados Incompletos

Alguns anos/corridas podem ter dados incompletos na API:

- Qualifying data pode estar ausente para corridas antigas
- Lap times só disponíveis de 1996 em diante
- Pit stops só de 2012 em diante

Isso é normal e os campos serão preenchidos com `NULL`.

## Estrutura de Dados

### Mapeamento API → Modelo Django

#### Driver
```
API                  → Django Model
driverId            → driver_id
givenName           → first_name
familyName          → last_name
dateOfBirth         → date_of_birth
nationality         → nationality
code (gerado)       → code (3 letras)
permanentNumber     → number
```

#### Constructor/Team
```
API                  → Django Model
constructorId       → team_id
name                → name
nationality         → (ignorado)
```

#### Race Result
```
API                  → Django Model
position            → position
grid                → grid_position
points              → points
laps                → laps_completed
status              → status
Time.millis         → total_race_time
FastestLap.Time     → fastest_lap_time
FastestLap.lap      → fastest_lap_number
```

#### Qualifying Result
```
API                  → Django Model
position            → position
Q1                  → q1_time
Q2                  → q2_time
Q3                  → q3_time
```

### Parsing de Tempo

Formatos suportados:
- `"1:23:45.678"` → 1h 23min 45.678s
- `"23:45.678"` → 23min 45.678s
- `"45.678"` → 45.678s
- `"+1.234"` → gap de +1.234s (convertido para tempo total)

## Performance

### Tempo Estimado de Coleta

| Escopo | Corridas | Tempo Aproximado |
|--------|----------|------------------|
| 1 temporada (~20 corridas) | 20 | 5-10 minutos |
| 10 anos (~200 corridas) | 200 | 1-2 horas |
| Completo 1950-2017 (~1000 corridas) | 1000+ | 4-8 horas |

*Tempos variam com conexão, rate limiting e carga do servidor API*

### Otimização

- Tasks são executadas em paralelo via Celery
- Rate limiting configurável
- Transações atômicas por corrida
- Update/Create para evitar duplicações

## Próximos Passos

Após coletar dados históricos:

1. **Validar dados**:
   ```bash
   docker exec -it fastf1-react-django-api-1 python manage.py ingest_historical_data --mode validate
   ```

2. **Atualizar frontend** para exibir dados históricos

3. **Treinar modelos de ML** com dados completos (1950-2025)

## API Jolpica F1

- **URL Base**: `http://api.jolpi.ca/ergast/f1/`
- **Documentação**: https://github.com/jolpica/jolpica-f1
- **Compatibilidade**: 100% compatível com Ergast API
- **Rate Limit**: Não documentado oficialmente (usando 0.5s entre requests)
- **Formato**: JSON

## Suporte

Em caso de problemas:

1. Verifique logs: `docker compose logs -f celery-worker`
2. Valide dados: `python manage.py ingest_historical_data --mode validate`
3. Consulte issues da API Jolpica: https://github.com/jolpica/jolpica-f1/issues
