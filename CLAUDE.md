# CLAUDE.md

Este arquivo fornece orientações ao Claude Code (claude.ai/code) ao trabalhar com código neste repositório.

## Visão Geral do Projeto

Esta é uma aplicação web full-stack para exibição de dados da Fórmula 1 usando a biblioteca FastF1. O projeto consiste em:

- **Frontend**: React 18 com TypeScript e Vite
- **Backend**: Django REST Framework com Celery para tarefas assíncronas
- **Banco de Dados**: MySQL 8.0
- **Cache/Message Broker**: Redis

## Comandos de Desenvolvimento

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
├── components/       # Componentes reutilizáveis
│   ├── Navbar.tsx   # Barra de navegação com links
│   ├── ThemeToggle.tsx  # Botão de alternância de tema
│   ├── LoadingSpinner.tsx
│   ├── ErrorMessage.tsx
│   ├── Card.tsx
│   ├── Table.tsx
│   └── Podium.tsx
├── pages/           # Páginas da aplicação
│   ├── Home.tsx     # Página inicial com dashboard
│   ├── Race.tsx     # Resultados da última corrida
│   ├── Qualifying.tsx  # Resultados do último qualifying
│   ├── Drivers.tsx  # Classificação de pilotos
│   ├── Constructors.tsx  # Classificação de construtores
│   └── Status.tsx   # Status do sistema e banco de dados
├── contexts/        # Contextos React
│   └── ThemeContext.tsx  # Gerenciamento de tema (claro/escuro)
├── services/        # Serviços de API
│   └── api.ts       # Cliente Axios com retry logic
├── styles/          # Arquivos CSS
│   ├── globals.css  # Variáveis CSS e tema global
│   └── *.css        # Estilos específicos de componentes
├── types/           # Tipos TypeScript
│   └── f1.ts        # Interfaces para dados F1
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

**Rotas Disponíveis:**
- `/` - Home (Dashboard com resumo)
- `/race` - Resultados da última corrida
- `/qualifying` - Resultados do último qualifying
- `/drivers` - Classificação de pilotos
- `/constructors` - Classificação de construtores
- `/status` - Status do sistema

### Backend (Django REST Framework)

**Estrutura de Diretórios:**
```
backend/
├── api/                 # API REST
│   ├── views.py        # ViewSets para endpoints
│   ├── serializers.py  # Serializers DRF
│   └── urls.py         # Rotas da API
├── core/               # Modelos principais
│   ├── models.py       # Modelos Django (Driver, Team, Race, etc.)
│   └── admin.py        # Admin Django
├── data_collector/     # Coleta de dados F1
│   └── tasks.py        # Tarefas Celery para coletar dados
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

**API Endpoints:**
- `GET /api/status/` - Status do sistema
- `GET /api/driver-standings/latest/` - Classificação de pilotos
- `GET /api/constructor-standings/latest/` - Classificação de construtores
- `GET /api/races/latest/` - Última corrida
- `GET /api/qualifying/latest/` - Último qualifying
- `GET /api/sprints/latest/` - Última sprint
- `GET /api/pit-stops/latest/` - Pit stops da última corrida
- `GET /api/weather/latest/` - Dados meteorológicos

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
- `celery-worker`: Worker Celery
- `celery-beat`: Scheduler Celery
- `frontend`: Frontend React

**Portas:**
- Frontend: 3000 (ou porta configurada via `FRONTEND_PORT`)
- Backend API: 8000 (ou porta configurada via `DJANGO_PORT`)
- MySQL: 3306
- Redis: 6379

**Volumes Persistentes:**
- `mysql-data`: Dados do MySQL
- `redis-data`: Dados do Redis
- `fastf1-cache`: Cache da FastF1

**Variáveis de Ambiente:**
Configurar via arquivo `.env` (criar baseado em `.env.example` se existir):
- `DEBUG`: Debug mode (True/False)
- `SECRET_KEY`: Django secret key
- `MYSQL_DATABASE`: Nome do banco
- `MYSQL_USER`: Usuário do banco
- `MYSQL_PASSWORD`: Senha do banco
- `VITE_API_URL`: URL da API para o frontend

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