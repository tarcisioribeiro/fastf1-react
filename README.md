# F1 Data Platform

Uma plataforma completa para visualização e análise de dados de Fórmula 1, com coleta assíncrona de dados, API REST robusta e frontend moderno.

## Arquitetura

```
┌─────────────────────────────────────────────────────────────────┐
│                         F1 Data Platform                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐     │
│  │   Frontend   │◄───┤  Django API  │◄───┤    MySQL     │     │
│  │  (Next.js)   │    │   (REST)     │    │  (Database)  │     │
│  └──────────────┘    └──────────────┘    └──────────────┘     │
│                              │                                   │
│                              ▼                                   │
│                      ┌──────────────┐                           │
│                      │    Redis     │                           │
│                      │   (Broker)   │                           │
│                      └──────────────┘                           │
│                              │                                   │
│                              ▼                                   │
│                      ┌──────────────┐                           │
│                      │ Celery (5x)  │◄──────────┐              │
│                      │   Workers    │           │              │
│                      └──────────────┘           │              │
│                              │                   │              │
│                              ▼                   │              │
│                      ┌──────────────┐           │              │
│                      │  FastF1 API  │───────────┘              │
│                      │ (F1 Data)    │                           │
│                      └──────────────┘                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Características

### Backend Completo
- ✅ Django REST API com 15+ endpoints
- ✅ Coleta assíncrona de dados (5 workers paralelos)
- ✅ 16 modelos de dados completos
- ✅ MySQL como banco de dados
- ✅ Redis para cache e message broker
- ✅ Celery para tarefas assíncronas
- ✅ Sistema de agendamento automático
- ✅ Documentação Swagger/OpenAPI
- ✅ Dados de 2022 até hoje (pneus 2025+)

### Frontend
- ✅ React 18 com TypeScript
- ✅ Vite para build otimizado
- ✅ Interface responsiva e moderna
- ✅ Cores oficiais F1 (tema escuro)
- ✅ Páginas: Dashboard, Classificação, Resultados
- ✅ Integração completa com API Backend

## Tecnologias

### Backend
- **Django 5.0** - Framework web Python
- **Django REST Framework** - API REST
- **Celery** - Processamento assíncrono
- **Redis** - Message broker e cache
- **MySQL 8.0** - Banco de dados
- **FastF1** - Biblioteca de dados F1

### Frontend
- **React 18** - Biblioteca UI
- **Vite** - Build tool moderno
- **TypeScript** - Tipagem estática
- **React Router** - Navegação SPA
- **Axios** - Cliente HTTP

### DevOps
- **Docker & Docker Compose**
- **Nginx** - Reverse proxy
- **GitHub Actions** - CI/CD

## 🚀 Instalação Rápida (Recomendado)

### Opção 1: Usando o Script Interativo (Recomendado)

O script `setup.sh` configura tudo automaticamente de forma interativa:

```bash
git clone <repo-url>
cd fastf1-react
./setup.sh
```

O script irá:
1. ✅ Verificar se Docker está instalado
2. ✅ Perguntar as configurações (portas, senhas, etc)
3. ✅ Criar arquivo `.env` automaticamente
4. ✅ Fazer build dos containers
5. ✅ Subir a aplicação completa

**Configurações que o script pergunta:**
- Portas (MySQL, Redis, Backend, Frontend)
- Credenciais do banco de dados
- Configurações do Django (DEBUG, SECRET_KEY)
- Hosts permitidos e CORS (importante para VPS)

Após concluído, acesse:
- **Frontend**: `http://localhost:3000` (ou porta configurada)
- **Backend API**: `http://localhost:8000` (ou porta configurada)
- **Swagger Docs**: `http://localhost:8000/api/docs/`

### Opção 2: Instalação Manual

Se preferir configurar manualmente:

#### 1. Clone e configure

```bash
git clone <repo-url>
cd fastf1-react
cp .env.example .env
```

Edite o arquivo `.env` com suas configurações.

#### 2. Inicie os containers

```bash
docker compose up --build -d
docker system prune -f
```

Serviços iniciados:
- MySQL: `localhost:3306` (configurável via `MYSQL_PORT`)
- Redis: `localhost:6379` (configurável via `REDIS_PORT`)
- Django API: `http://localhost:8000` (configurável via `DJANGO_PORT`)
- Frontend: `http://localhost:3000` (configurável via `FRONTEND_PORT`)
- Celery Workers: 5 workers paralelos
- Celery Beat: Tarefas agendadas

#### 3. Execute as migrations

```bash
docker compose exec django-api python manage.py migrate
```

#### 4. Inicie a coleta de dados

```bash
docker compose exec django-api python manage.py shell
```

```python
from data_collector.tasks import start_all_data_collection
start_all_data_collection.delay()
```

## API Endpoints

Base URL: `http://localhost:8000/api/`

### Principais Endpoints

**Básicos**
- `GET /api/teams/` - Equipes
- `GET /api/drivers/` - Pilotos
- `GET /api/circuits/` - Circuitos
- `GET /api/seasons/` - Temporadas

**Resultados**
- `GET /api/races/` - Resultados de corridas
- `GET /api/qualifying/` - Classificações
- `GET /api/sprints/` - Sprints

**Campeonatos**
- `GET /api/driver-standings/latest/?year=2024` - Classificação atual de pilotos
- `GET /api/constructor-standings/latest/?year=2024` - Classificação atual de equipes

**Dados Detalhados**
- `GET /api/lap-times/` - Tempos de volta
- `GET /api/tyre-strategies/` - Estratégias de pneus
- `GET /api/pit-stops/` - Paradas nos boxes
- `GET /api/weather/` - Dados meteorológicos

**Documentação**
- `http://localhost:8000/api/docs/` - Swagger UI
- `http://localhost:8000/admin/` - Django Admin

## Modelos de Dados (16 modelos)

1. **Team** - Equipes (com cores oficiais)
2. **Driver** - Pilotos
3. **Circuit** - Circuitos
4. **Season** - Temporadas (2022+)
5. **Event** - Grandes Prêmios
6. **Session** - Sessões (FP1/2/3, Q, S, R)
7. **RaceResult** - Resultados de corridas
8. **QualifyingResult** - Resultados de classificações
9. **SprintResult** - Resultados de sprints
10. **DriverStanding** - Pontuação de pilotos
11. **ConstructorStanding** - Pontuação de equipes
12. **LapTime** - Tempos de volta
13. **TyreStrategy** - Estratégias de pneus
14. **PitStop** - Paradas nos boxes
15. **WeatherData** - Dados meteorológicos
16. **TelemetryData** - Telemetria

## Sistema de Coleta Assíncrona

**5 Tasks Principais** (executam em paralelo):

1. `collect_all_race_data()` - Corridas (2022-hoje)
2. `collect_all_qualifying_data()` - Classificações (2022-hoje)
3. `collect_all_sprint_data()` - Sprints (2022-hoje)
4. `collect_all_standings_data()` - Pontuação (2022-hoje)
5. `collect_tyre_data()` - Pneus (2025-hoje)

**Agendamento Automático (Celery Beat):**
- Segunda 02:00 - Corridas
- Domingo 03:00 - Classificações
- Sexta 04:00 - Sprints
- Diariamente 05:00 - Pontuação
- Segunda 06:00 - Pneus

## 📋 Comandos Úteis

```bash
# Ver logs
docker compose logs -f
docker compose logs -f django-api
docker compose logs -f celery-worker
docker compose logs -f frontend

# Acessar shell Django
docker compose exec django-api python manage.py shell

# Executar testes
docker compose exec django-api python manage.py test

# Acessar MySQL
docker compose exec mysql mysql -u f1_user -p f1_database

# Monitorar Celery
docker compose exec celery-worker celery -A config inspect active

# Parar containers
docker compose down

# Parar e remover volumes (cuidado!)
docker compose down -v

# Rebuild apenas o frontend
docker compose up --build -d frontend

# Rebuild apenas o backend
docker compose up --build -d django-api
```

## 🌐 Deploy em VPS

Para fazer deploy em uma VPS (DigitalOcean, AWS, etc):

1. **Execute o setup.sh** e configure:
   - Adicione o IP/domínio da VPS em `ALLOWED_HOSTS`
   - Configure `CORS_ALLOWED_ORIGINS` com URLs públicas
   - Use `DEBUG=False` em produção
   - Configure uma `SECRET_KEY` forte

2. **Exemplo de configuração para VPS:**
   ```
   ALLOWED_HOSTS=192.168.1.100,meudominio.com,localhost
   CORS_ALLOWED_ORIGINS=http://192.168.1.100:3000,http://meudominio.com
   VITE_API_URL=http://192.168.1.100:8000
   ```

3. **Portas:**
   - Certifique-se de que as portas estão abertas no firewall da VPS
   - Use `ufw allow 3000` e `ufw allow 8000` no Ubuntu

4. **Configurações adicionais recomendadas:**
   - Configure HTTPS com Nginx + Let's Encrypt
   - Use PostgreSQL ao invés de MySQL em produção (opcional)
   - Configure backups automáticos do banco
   - Use Docker volumes para persistência de dados

## Status do Projeto

### ✅ FASE 1: Infraestrutura (Completo)
- MySQL configurado
- Redis configurado
- Docker Compose completo

### ✅ FASE 2: Backend Django (Completo)
- 16 modelos de dados
- API REST completa (15+ endpoints)
- Celery configurado (5 workers)
- Sistema de coleta assíncrona
- Documentação Swagger

### ✅ FASE 3: Frontend (Completo)
- React + TypeScript + Vite
- Componentes base (Layout, Loading, Error)
- 3 páginas principais (Dashboard, Standings, Results)
- Integração com API
- Design responsivo

### ⏳ FASE 4: Integração
- Conectar frontend com backend
- Testes end-to-end

### ⏳ FASE 5: DevOps
- CI/CD
- Deploy em produção
- Monitoramento

## Estrutura do Projeto

```
fastf1-react/
├── backend/                    # Django backend ✅
│   ├── config/                # Configurações Django
│   ├── core/                  # Modelos de dados
│   ├── api/                   # REST API endpoints
│   ├── data_collector/        # Celery tasks
│   ├── Dockerfile            # Container backend
│   └── requirements.txt
├── frontend/                  # React frontend ✅
│   ├── src/
│   │   ├── components/       # Componentes React
│   │   ├── pages/            # Páginas da aplicação
│   │   ├── services/         # API client
│   │   ├── types/            # TypeScript types
│   │   └── styles/           # CSS files
│   ├── Dockerfile            # Container frontend
│   ├── package.json
│   └── vite.config.ts
├── docker-compose.yml         # Orquestração ✅
├── .env.example              # Template de variáveis ✅
├── setup.sh                  # Script de setup ✅
└── README.md                 # Documentação ✅
```

## Contribuição

Projeto em desenvolvimento ativo. Contribuições bem-vindas!

## Licença

MIT

---

**Status**: ✅ Backend completo | ✅ Frontend completo | 🔄 Integração em andamento
**Última atualização**: 2025-10-26

## 🎯 Próximos Passos

1. **Melhorias no Frontend:**
   - Adicionar gráficos interativos (Recharts)
   - Implementar filtros avançados
   - Adicionar tema claro/escuro
   - Melhorar responsividade mobile

2. **Backend:**
   - Implementar cache Redis para API
   - Adicionar endpoints de telemetria
   - Otimizar queries do banco

3. **DevOps:**
   - Configurar CI/CD
   - Adicionar Nginx para produção
   - Configurar SSL/HTTPS
   - Implementar monitoramento
