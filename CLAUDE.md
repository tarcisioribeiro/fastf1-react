# CLAUDE.md

Este arquivo fornece orientações ao Claude Code (claude.ai/code) ao trabalhar com código neste repositório.

## Visão Geral do Projeto

Esta é uma aplicação web full-stack para exibição de dados da Fórmula 1 usando a biblioteca FastF1. O projeto consiste em:

- **Frontend**: React 18 com TypeScript e Vite
- **Backend**: Django REST Framework com Celery para tarefas assíncronas
- **Banco de Dados**: MySQL 8.0
- **Cache/Message Broker**: Redis
- **ML**: Modelos preditivos (scikit-learn/XGBoost/LightGBM/CatBoost) para previsão de resultados

### ⚠️ Arquivos Legados na Raiz

Os arquivos `api.py`, `app.py`, `database.py`, `f1_data.py`, `start_api.py`, `requirements.txt` e `README.md` na raiz do repositório são de um protótipo anterior (Flask + Streamlit + SQLite) e **não fazem parte da aplicação atual**. A aplicação real vive em `backend/` (Django) e `frontend/` (React), documentada abaixo. Ignore esses arquivos ao investigar ou implementar algo — o `README.md` da raiz também descreve essa arquitetura antiga e está desatualizado.

## Comandos de Desenvolvimento

**Importante:** toda a aplicação atual roda via Docker/container (ver seção "Docker e Deployment"). Os comandos de venv abaixo servem apenas como referência de setup local; no dia a dia, prefira `docker compose exec django-api ...` / `docker compose exec frontend ...`.

### Backend (Django + Celery)

```bash
# Configurar ambiente virtual
cd backend
python -m venv backend_venv
source backend_venv/bin/activate  # No Windows: backend_venv\Scripts\activate
pip install -r requirements.txt

# Rodar migrações
python manage.py migrate

# Criar superusuário
python manage.py createsuperuser

# Iniciar servidor de desenvolvimento
python manage.py runserver

# Iniciar Celery worker
celery -A config worker -l info

# Iniciar Celery beat (tarefas agendadas)
celery -A config beat -l info
```

**Comandos de management mais usados** (rodar com `docker compose exec django-api python manage.py <comando>`):
- `train_ml_models` / `retrain_prediction_models` — treina/retreina os modelos de previsão
- `populate_data` — popula o banco com dados históricos da FastF1
- `clean_duplicates` / `remove_duplicates` — limpeza de dados duplicados
- `consolidate_drivers` / `consolidate_teams` / `update_team_consolidation` — normaliza pilotos/equipes que mudaram de nome ao longo do tempo
- `fix_driver_codes` — corrige códigos de piloto inconsistentes
- `recalculate_podiums` — recalcula pódios/vitórias/poles a partir dos resultados salvos
- `download_circuit_previews` — baixa os SVGs de traçado de circuito (repo `f1-circuits-svg`)
- `sync_task_descriptions` — sincroniza descrições das tarefas periódicas do Celery Beat exibidas no admin/frontend

### Frontend (React + Vite)

```bash
# Instalar dependências
cd frontend
npm install

# Rodar servidor de desenvolvimento
npm run dev

# Build para produção
npm run build

# Preview do build
npm run preview

# Lint
npm run lint
```

### Docker (Produção)

```bash
# Iniciar todos os serviços
docker compose up -d

# Ver logs
docker compose logs -f

# Rebuild após mudanças
docker compose build
docker compose restart

# Parar todos os serviços
docker compose down
```

## Arquitetura do Projeto

### Frontend (React + TypeScript)

**Estrutura de Diretórios:**
```
frontend/src/
├── components/       # Componentes reutilizáveis (Navbar, Sidebar, Table, Podium, filtros, etc.)
├── pages/           # Páginas da aplicação (ver "Rotas Disponíveis" abaixo)
├── contexts/        # Contextos React
│   └── ThemeContext.tsx  # Gerenciamento de tema (claro/escuro)
├── hooks/           # Hooks customizados (ex: useChartTheme.ts)
├── services/        # Serviços de API
│   └── api.ts       # Cliente Axios com retry logic
├── styles/          # Arquivos CSS (um `*.css` por componente/página + globals.css)
├── types/           # Tipos TypeScript
│   └── f1.ts        # Interfaces para dados F1
├── utils/           # Utilitários (formatação de datas, tradução, helpers de dados F1)
├── App.tsx          # Componente raiz com rotas
└── main.tsx         # Entry point da aplicação
```

**Tecnologias Principais:**
- **React 18.2**: Framework UI
- **TypeScript 5.2**: Tipagem estática
- **Vite 5.1**: Build tool e dev server
- **React Router 6.22**: Roteamento
- **Axios 1.6**: Cliente HTTP com retry automático

**Sistema de Temas:**
- Implementado via Context API (`ThemeContext.tsx`)
- Suporta tema claro e escuro
- Persiste preferência no localStorage
- Detecta preferência do sistema automaticamente
- Aplica tema via atributo `data-theme` no HTML

**Rotas Disponíveis** (ver `App.tsx` para a lista completa/atual):
- Resultados recentes: Home, Race, Qualifying, Sprint, Drivers, Constructors, Circuits
- Histórico: HistoryRaces, HistoryQualifying, HistorySprints, TeamHistory, DriverCareer
- Analytics: AnalyticsStandings, AnalyticsPitStops, AnalyticsWeather
- Previsões (ML): PredictionsDriver, PredictionsConstructor, PredictionsPoleDriver, PredictionsPoleConstructor
- Administração: DataAudit, PeriodicTasks, Status

### Backend (Django REST Framework)

**Estrutura de Diretórios:**
```
backend/
├── api/                 # API REST
│   ├── views.py        # ViewSets para endpoints
│   ├── serializers.py  # Serializers DRF
│   └── urls.py         # Rotas da API
├── core/               # Modelos principais, admin e comandos de manutenção
│   ├── models.py       # Modelos Django (Driver, Team, Race, etc.)
│   ├── admin.py        # Admin Django
│   └── management/commands/  # consolidate_drivers, fix_driver_codes, recalculate_podiums, etc.
├── data_collector/     # Coleta de dados F1
│   └── tasks.py        # Tarefas Celery para coletar dados
├── data_auditor/       # Auditoria de qualidade dos dados coletados
│   ├── auditor.py       # Regras de auditoria (gera DataAuditReport/Suggestion)
│   └── web_sources.py   # Cross-checagem com fontes externas
├── ml/                  # Modelos de previsão (posição, pole, tempo de pole)
│   ├── factors.py        # 5 fatores de previsão: regulamento, carro, clima, estratégia, forma
│   ├── regulation_config.py  # Config de mudanças de regulamento por temporada
│   ├── feature_engineering.py / trainer.py / predictor.py
│   └── position_model_v2.py
├── config/             # Configurações Django
│   ├── settings.py     # Configurações principais
│   ├── celery.py       # Configuração Celery
│   └── urls.py         # URLs principais
├── requirements.txt    # Dependências Python
└── manage.py           # CLI Django
```

**Principais Dependências:**
- **Django 5.0.6**: Framework web
- **djangorestframework 3.15.1**: API REST
- **Celery 5.4.0**: Tarefas assíncronas
- **Redis 5.0.4**: Message broker e cache
- **MySQL Client 2.2.4**: Conector MySQL
- **FastF1 3.6.1**: Biblioteca para dados F1
- **Pandas 2.3.3**: Manipulação de dados

**Modelos Principais:**
- `Season`: Temporada F1
- `Circuit`: Circuitos
- `Team`: Equipes
- `Driver`: Pilotos
- `Event`: Eventos (GP)
- `Session`: Sessões (FP1, FP2, FP3, Q, S, R)
- `RaceResult`: Resultados de corrida
- `QualifyingResult`: Resultados de qualifying
- `SprintResult`: Resultados de sprint
- `DriverStanding`: Classificação de pilotos
- `ConstructorStanding`: Classificação de construtores
- `LapTime`: Tempos de volta
- `PitStop`: Pit stops
- `WeatherData`: Dados meteorológicos
- `TyreStrategy`: Estratégia de pneus
- `DataAuditReport` / `DataAuditSuggestion`: Resultados da auditoria de qualidade de dados

**API Endpoints** (ver `backend/api/urls.py` para a lista completa; principais grupos):
- `GET /api/status/` - Status do sistema
- ViewSets padrão DRF em `/api/{teams,drivers,circuits,seasons,events,sessions,races,qualifying,sprints,driver-standings,constructor-standings,lap-times,tyre-strategies,pit-stops,weather}/`
- `/api/predictions/{driver,constructor,pole-driver,pole-constructor,pole-time}/` - Previsões ML
- `/api/ml/{status,train}/` - Status e treino dos modelos ML
- `/api/data-audit-reports/`, `/api/data-audit-suggestions/` - Auditoria de dados
- `/api/history/{team,driver}/` - Histórico de equipe/piloto (Team History, Driver Career)
- `/api/filters/*`, `/api/options/*` - Opções para dropdowns/filtros do frontend
- `/api/maintenance/{clean-duplicates,health}/` - Manutenção do banco
- `/api/periodic-tasks/`, `/api/crontab-schedules/`, `/api/tasks/status/` - Administração das tarefas periódicas do Celery Beat

### Estratégia de Cache

O aplicativo usa um sistema de cache de duas camadas:

1. **Cache FastF1** (`.fastf1_cache/`) - Cache de dados brutos da API FastF1
2. **Banco de Dados MySQL** - Dados processados e persistidos

### Coleta de Dados (Celery Tasks)

As tarefas Celery são executadas periodicamente para coletar dados:

- `collect_session_data(year, round, session_type)` - Coleta dados de uma sessão específica
- `collect_all_race_data()` - Coleta todas as corridas
- `collect_all_qualifying_data()` - Coleta todos os qualifyings
- `collect_all_sprint_data()` - Coleta todas as sprints
- `collect_all_standings_data()` - Calcula classificações

**Importante sobre Sprints:**
- Sprints contribuem APENAS com pontos (8-7-6-5-4-3-2-1 para os 8 primeiros)
- Pódios, vitórias e poles das sprints NÃO contam para as estatísticas oficiais
- Apenas pódios, vitórias e poles de corridas principais contam

**Cálculo de Tempo Total:**
- Na FastF1, o tempo do vencedor é o tempo total
- Para outros pilotos, o 'Time' é o gap em relação ao vencedor
- O backend calcula o tempo total somando: tempo_vencedor + gap

### Formatação de Dados

- Todas as datas são formatadas em formato brasileiro (DD/MM/YYYY)
- Todos os dados são exibidos para a temporada 2025
- A aplicação encontra automaticamente a última corrida/qualifying disponível
- Posições de pódio são destacadas com estilo dourado/prateado/bronze

## Docker e Deployment

A aplicação inclui suporte Docker completo:

**Serviços:**
- `mysql`: MySQL 8.0
- `redis`: Redis 7
- `django-api`: Backend Django
- `celery-worker-1`, `celery-worker-2`, `celery-worker-3`: 3 workers Celery fixos (fila genérica)
- `celery-beat`: Scheduler Celery (usa `django_celery_beat` como scheduler persistido no banco)
- `frontend`: Frontend React

**Dispatch adaptativo de coleta:** além dos 3 workers fixos, `data_collector` limita quantas tarefas de coleta roda em paralelo com base na RAM livre do container, via `COLLECTION_MAX_PARALLEL`, `COLLECTION_EST_MB_PER_TASK`, `COLLECTION_SAFETY_MARGIN_MB` e `COLLECTION_DISPATCH_INTERVAL_SEC` (`.env`). Evita OOM ao coletar muitas sessões de uma vez.

**Portas:** todas configuráveis via `.env` (ver `.env.example`); os defaults do próprio `.env.example` já usam portas não-padrão (ex.: `FRONTEND_PORT=22444`, `DJANGO_PORT=22333`, `MYSQL_PORT=22111`, `REDIS_PORT=22222`) para evitar conflito com outros serviços na máquina. Internamente os containers sempre escutam em 3000 (frontend), 8000 (Django), 3306 (MySQL) e 6379 (Redis).

**Volumes Persistentes:**
- `mysql-data`: Dados do MySQL
- `redis-data`: Dados do Redis
- `fastf1-cache`: Cache da FastF1

**Variáveis de Ambiente:**
Configurar via arquivo `.env` (copiar de `.env.example`). Além das portas e credenciais de banco/Django, destacam-se:
- `CELERY_WORKER_CONCURRENCY`, `CELERY_MAX_TASKS_PER_CHILD`, `CELERY_PREFETCH_MULTIPLIER`: tuning dos workers Celery
- `COLLECTION_*`: parâmetros do dispatch adaptativo de coleta (ver acima)
- `ML_N_JOBS`, `ML_STACK_CV`, `ML_N_ESTIMATORS`, `ML_MAX_DEPTH`: parâmetros de treino dos modelos ML
- `*_CPU_LIMIT`/`*_CPU_RESERVE`/`*_MEMORY_LIMIT`/`*_MEMORY_RESERVE`: limites de recursos por serviço (`docker compose` `deploy.resources`)

## Notas de Desenvolvimento

### FastF1 Data

- Tipos de sessão: 'FP1', 'FP2', 'FP3', 'Q' (Qualifying), 'S' (Sprint), 'R' (Race)
- Dados disponíveis desde 2018
- Dados geralmente disponíveis 30-120 minutos após o fim da sessão
- A aplicação itera retroativamente do round 24 para encontrar a última corrida disponível

### Frontend

- Vite automaticamente recarrega durante desenvolvimento
- Build otimizado para produção em `frontend/dist/`
- Proxy configurado para `/api` apontar para backend em desenvolvimento

### Backend

- Django admin disponível em `/admin`
- API navegável em modo DEBUG
- Celery beat usa Django Celery Beat para persistir tarefas agendadas
- Logs detalhados para debugging de coleta de dados

### Temas (Claro/Escuro)

O sistema de temas usa CSS Variables definidas em `globals.css`:
- Tema é aplicado via atributo `[data-theme]` no `<html>`
- Todas as cores devem usar variáveis CSS (`var(--color-name)`)
- Temas devem ter contraste adequado para acessibilidade

## Solução de Problemas

### Dados não aparecem no frontend
1. Verificar se o backend está rodando
2. Verificar logs do Celery worker
3. Verificar `/status` para ver estado do banco de dados
4. Rodar manualmente tarefas de coleta via Django shell

### Erros de timezone
- Todos os timestamps devem ser timezone-aware
- Usar `django.utils.timezone.make_aware()` quando necessário

### Pit stops não gravados
- Campo `duration` pode ser NULL (nem todos os pit stops têm duração válida)
- Durações negativas ou > 300s são consideradas inválidas

### Weather data não gravado
- Timestamps devem ser convertidos de timedelta relativo para datetime absoluto
- Usar `session.date + timestamp` para calcular tempo absoluto
- Sempre me responda em português brasileiro.
- Sempre rode tudo via docker, tudo roda via container.
- Sempre consulte a documentação oficial da API da fastf1 para saber como proceder nas melhorias, correções, investigações e novas implementações.
- Sempre que eu lhe passar pedidos de melhoria, entenda, me explique o que entendeu e me pergunte se entendeu e se pode prosseguir assim.