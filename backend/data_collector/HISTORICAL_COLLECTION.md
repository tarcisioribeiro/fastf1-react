# Sistema de Coleta de Dados Históricos de F1 (1950-2024)

## Visão Geral

Sistema automatizado e escalável para coleta de dados históricos de Fórmula 1 desde 1950, com varredura inteligente de gaps, processamento paralelo e controle completo via Django Admin.

## Arquitetura

### Componentes Principais

1. **Gap Scanner** (`gap_scanner.py`)
   - Varre o banco de dados identificando dados faltantes
   - Prioriza automaticamente (anos mais recentes = maior prioridade)
   - Registra gaps em `HistoricalDataGap`

2. **Ergast API Scraper** (`ergast_scraper.py`)
   - Cliente robusto com retry logic e rate limiting
   - Suporte completo à API Ergast (fonte oficial de dados históricos)
   - Endpoints: corridas, qualificação, sprints, classificações, pilotos, equipes, circuitos

3. **Historical Collector** (`historical_collector.py`)
   - Processa gaps identificados pelo scanner
   - Mapeia dados da Ergast API para modelos Django
   - Transações atômicas para garantir integridade

4. **Celery Tasks** (`historical_tasks.py`)
   - `scan_historical_data_gaps`: Varredura periódica
   - `collect_historical_data_parallel`: Coleta massiva paralela
   - `incremental_historical_update`: Task principal (a cada 5 min por padrão)
   - Tasks auxiliares para coleta individual e cálculos

## Modelos Django

### HistoricalDataCollectionConfig

Modelo singleton para configuração via Django Admin.

**Campos principais:**
- `enabled`: Ativar/desativar coleta
- `max_workers`: Número de workers Celery (1-50)
- `tasks_per_batch`: Tarefas paralelas por lote (1-100)
- `scan_interval_minutes`: Intervalo de varredura (1-60 min)
- `start_year` / `end_year`: Período de coleta (ex: 2024 → 1950)
- Flags para tipos de dados: races, qualifying, sprints, standings, etc.
- Fontes: `use_wikipedia`, `use_ergast_api`

**Estatísticas:**
- `last_scan_at`: Última varredura
- `last_year_processed`: Último ano processado
- `total_records_collected`: Total de registros coletados

### HistoricalDataGap

Rastreamento de lacunas de dados.

**Campos principais:**
- `gap_type`: season, event, session, result, standing, driver, team, circuit
- `status`: pending, collecting, completed, failed, skipped
- `year` / `round_number` / `session_type`: Identificação do gap
- `priority`: 0-1000 (maior = mais prioritário)
- `attempt_count` / `max_attempts`: Controle de tentativas
- `error_message`: Mensagem de erro se falhou

## Configuração

### 1. Django Admin

Acesse `/admin` e vá para **Historical Data Collection Configs**.

**Configuração recomendada para início:**
- Enabled: ✓
- Max workers: 10
- Tasks per batch: 20
- Scan interval: 5 minutos
- Start year: 2024
- End year: 1950
- Todas as fontes ativadas

### 2. Variáveis de Ambiente Docker

Adicione ao seu `.env`:

```bash
# Celery Workers - Paralelismo
CELERY_WORKER_CONCURRENCY=10
CELERY_MAX_TASKS_PER_CHILD=50

# Recursos (Docker Compose)
CELERY_WORKER_CPU_LIMIT=4.0
CELERY_WORKER_MEMORY_LIMIT=4G
CELERY_WORKER_CPU_RESERVE=2.0
CELERY_WORKER_MEMORY_RESERVE=2G
```

**Escalonamento:**
- Para **mais velocidade**: Aumente `CELERY_WORKER_CONCURRENCY` (até 20-30)
- Para **menos recursos**: Reduza para 4-6 workers
- Ajuste `tasks_per_batch` no Django Admin para controlar quantas tarefas rodam em paralelo por lote

## Uso

### Inicialização Automática

O sistema inicia automaticamente quando `enabled=True` no Django Admin.

**Task periódica:** Executa a cada 5 minutos (configurável via `scan_interval_minutes`)

### Comandos Manuais (Django Shell)

```python
# Executar varredura manual
from data_collector.gap_scanner import run_gap_scan
stats = run_gap_scan()
print(f"Encontrados {stats['total']} gaps")

# Coletar dados manualmente (10 gaps)
from data_collector.historical_collector import collect_historical_data
result = collect_historical_data(max_gaps=10)
print(result)

# Coletar um ano específico
from data_collector.historical_tasks import collect_year_data
result = collect_year_data.delay(1975)
```

### Endpoints API

#### GET /api/options/years/
Retorna anos disponíveis no banco.

**Response:**
```json
{
  "years": [2025, 2024, 2023, ..., 1950],
  "latest_year": 2025,
  "earliest_year": 1950,
  "total_years": 76
}
```

#### GET /api/historical/stats/
Estatísticas da coleta histórica.

**Response:**
```json
{
  "config": {
    "enabled": true,
    "max_workers": 10,
    "tasks_per_batch": 20,
    "start_year": 2024,
    "end_year": 1950,
    "total_records_collected": 150000
  },
  "gaps": {
    "total": 120,
    "pending": 80,
    "collecting": 5,
    "completed": 30,
    "failed": 5,
    "by_type": {...}
  },
  "progress": {
    "total_seasons": 76,
    "seasons_with_data": 50,
    "completion_percentage": 65.8
  }
}
```

## Fluxo de Funcionamento

1. **Varredura** (a cada N minutos configurável):
   ```
   scan_historical_data_gaps
   ↓
   Identifica temporadas, eventos, sessões faltantes
   ↓
   Cria registros HistoricalDataGap (pendente)
   ```

2. **Coleta Paralela** (a cada 5 minutos):
   ```
   incremental_historical_update
   ↓
   Busca gaps pendentes (ordenados por prioridade)
   ↓
   collect_historical_data_parallel
   ↓
   Cria N tasks paralelas (N = tasks_per_batch)
   ↓
   Cada task processa 1 gap via Ergast API
   ↓
   Atualiza status: completed/failed
   ```

3. **Prioritização**:
   - Anos mais recentes têm prioridade maior
   - Corridas > Qualificação > Sprint > Classificações
   - Gaps com falhas (attempt_count < 3) são retriados

## Monitoramento

### Django Admin

1. **Historical Data Collection Configs**
   - Ver última varredura
   - Ver total de registros coletados
   - Ajustar configurações em tempo real

2. **Historical Data Gaps**
   - Ver todos os gaps identificados
   - Filtrar por status (pending, completed, failed)
   - Filtrar por tipo e ano
   - Actions: marcar como pendente, marcar como concluído

### Logs

```bash
# Ver logs do Celery worker
docker compose logs -f celery-worker

# Ver logs do Celery beat
docker compose logs -f celery-beat

# Ver logs do Django
docker compose logs -f django-api
```

### Celery Flower (Opcional)

Adicione ao docker-compose.yml para UI de monitoramento:

```yaml
flower:
  build: ./backend
  command: celery -A config flower --port=5555
  ports:
    - "5555:5555"
  environment:
    - CELERY_BROKER_URL=redis://redis:6379/0
    - CELERY_RESULT_BACKEND=redis://redis:6379/0
  depends_on:
    - redis
    - celery-worker
```

Acesse em `http://localhost:5555`

## Otimizações de Performance

### 1. Escalonar Workers

Para coleta mais rápida:

```bash
# No .env
CELERY_WORKER_CONCURRENCY=20
```

E no Django Admin:
- `max_workers`: 20
- `tasks_per_batch`: 50

### 2. Múltiplos Workers

Adicione workers extras no docker-compose.yml:

```yaml
celery-worker-2:
  build: ./backend
  command: celery -A config worker -l info --concurrency=10
  # ... mesma config do celery-worker
```

### 3. Priorizar Anos Específicos

Via Django Shell:

```python
from core.models import HistoricalDataGap

# Aumentar prioridade de gaps de 2020+
HistoricalDataGap.objects.filter(year__gte=2020).update(priority=900)
```

## Troubleshooting

### Problema: Coleta muito lenta

**Soluções:**
1. Aumentar `CELERY_WORKER_CONCURRENCY`
2. Aumentar `tasks_per_batch` no Admin
3. Adicionar mais workers no docker-compose

### Problema: Muitos gaps falhando

**Causas comuns:**
1. Rate limiting da Ergast API → O scraper já tem proteção, mas pode estar sobrecarregado
2. Dados realmente não existem → Marcar como `skipped` no Admin
3. Erro de parsing → Ver logs para detalhes

**Soluções:**
1. Reduzir `tasks_per_batch` para não sobrecarregar a API
2. Revisar gaps falhados no Admin e marcar como skipped se necessário

### Problema: Varredura não executa

**Verificar:**
1. Config `enabled=True` no Admin
2. Celery Beat está rodando: `docker compose ps celery-beat`
3. Verificar logs: `docker compose logs celery-beat`

### Problema: Workers travam / Out of Memory

**Soluções:**
1. Reduzir `CELERY_WORKER_CONCURRENCY`
2. Aumentar `CELERY_WORKER_MEMORY_LIMIT`
3. Configurar `CELERY_MAX_TASKS_PER_CHILD` (força restart periódico)

## Dados Coletados

### Fontes

- **Ergast API** (principal): http://ergast.com/mrd/
  - Dados oficiais de 1950-2024
  - Cobertura completa de resultados, classificações e estatísticas

- **Wikipedia** (futuro): Dados complementares e metadados

### Tipos de Dados

✅ **Implementado:**
- Temporadas (Season)
- Circuitos (Circuit)
- Pilotos (Driver)
- Equipes (Team)
- Eventos/GPs (Event)
- Sessões (Session)
- Resultados de Corrida (RaceResult)
- Resultados de Qualificação (QualifyingResult)
- Resultados de Sprint (SprintResult) [2021+]
- Classificação de Pilotos (DriverStanding)
- Classificação de Construtores (ConstructorStanding)
- Pit Stops (PitStop) [2012+]

🔄 **Planejado:**
- Dados complementares da Wikipedia
- Lap times históricos
- Weather data histórico

## Contribuindo

Para adicionar novos tipos de dados:

1. Criar método em `HistoricalDataGapScanner._scan_missing_X()`
2. Implementar coleta em `HistoricalDataCollector._collect_X()`
3. Adicionar novo `gap_type` em `HistoricalDataGap.GAP_TYPE_CHOICES`
4. Atualizar config flags em `HistoricalDataCollectionConfig`

## Referências

- **Ergast API Docs**: https://ergast.com/mrd/
- **Celery Docs**: https://docs.celeryproject.org/
- **Django Docs**: https://docs.djangoproject.com/

## Licença

Este sistema faz parte do projeto FastF1-React.
