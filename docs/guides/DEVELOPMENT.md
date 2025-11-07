# Guia de Desenvolvimento

Este guia contém padrões, convenções e melhores práticas para desenvolvimento neste projeto.

## Sumário

- [Setup do Ambiente](#setup-do-ambiente)
- [Workflow de Desenvolvimento](#workflow-de-desenvolvimento)
- [Padrões de Código](#padrões-de-código)
- [Estrutura de Commits](#estrutura-de-commits)
- [Testing](#testing)
- [Debugging](#debugging)
- [Consulta à Documentação FastF1](#consulta-à-documentação-fastf1)
- [Troubleshooting Comum](#troubleshooting-comum)

---

## Setup do Ambiente

### Pré-requisitos

- Docker & Docker Compose
- Git
- Editor de código (recomendado: VS Code)

### Primeira Configuração

```bash
# Clonar repositório
git clone <repo-url>
cd fastf1-react

# Criar arquivo .env (baseado em .env.example se existir)
cp .env.example .env

# Editar variáveis de ambiente
nano .env

# Iniciar containers
docker compose up -d

# Verificar se tudo está rodando
docker compose ps

# Ver logs
docker compose logs -f
```

### Variáveis de Ambiente Essenciais

```bash
# Django
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1

# MySQL
MYSQL_DATABASE=f1_db
MYSQL_USER=f1_user
MYSQL_PASSWORD=f1_password
MYSQL_ROOT_PASSWORD=root_password

# Redis
REDIS_URL=redis://redis:6379/0

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Frontend
VITE_API_URL=http://localhost:8000/api/
```

---

## Workflow de Desenvolvimento

### Branch Strategy

```
main
  ├── develop
  │   ├── feature/nome-da-feature
  │   ├── fix/nome-do-bug
  │   └── refactor/nome-da-refatoracao
```

**Regras:**
- `main` - código em produção
- `develop` - código em desenvolvimento
- `feature/*` - novas funcionalidades
- `fix/*` - correção de bugs
- `refactor/*` - refatoração de código

### Criando uma Nova Feature

```bash
# Atualizar develop
git checkout develop
git pull origin develop

# Criar branch da feature
git checkout -b feature/adicionar-telemetry-endpoint

# Fazer alterações, testar, commitar

# Merge para develop
git checkout develop
git merge feature/adicionar-telemetry-endpoint

# Push
git push origin develop
```

---

## Padrões de Código

### Python (Backend)

#### PEP 8

Seguir [PEP 8](https://pep8.org/) para Python:

```python
# BOM
def calculate_driver_points(driver_id: int, season_year: int) -> float:
    """Calculate total points for a driver in a season."""
    results = RaceResult.objects.filter(
        driver_id=driver_id,
        session__event__season__year=season_year
    )
    return sum(r.points for r in results)

# RUIM
def calc_pts(d,s):
    r=RaceResult.objects.filter(driver_id=d,session__event__season__year=s)
    return sum([x.points for x in r])
```

#### Type Hints

Sempre usar type hints:

```python
from typing import List, Optional, Dict, Any

def get_race_results(
    session_id: int,
    limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    pass
```

#### Docstrings

Usar docstrings estilo Google:

```python
def collect_session_data(year: int, round_num: int, session_type: str):
    """
    Collect data for a specific session.

    Args:
        year: Season year
        round_num: Round number (1-24)
        session_type: Session type ('R', 'Q', 'S', etc.)

    Returns:
        str: Success message

    Raises:
        ValueError: If session_type is invalid
        ConnectionError: If FastF1 API is unavailable
    """
    pass
```

#### Imports

Organizar imports:

```python
# Stdlib
import logging
from datetime import datetime
from typing import Optional

# Django
from django.db import models
from django.utils import timezone

# Third-party
import fastf1
import pandas as pd

# Local
from core.models import Driver, Team
from .utils import safe_value
```

#### Django Models

```python
class Driver(models.Model):
    """F1 Driver model."""

    # Fields organized logically
    driver_id = models.CharField(max_length=50, unique=True)
    code = models.CharField(max_length=3)
    number = models.IntegerField()

    # Personal info
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max=100)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['last_name', 'first_name']
        verbose_name = 'Driver'
        verbose_name_plural = 'Drivers'

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.code})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
```

#### Django Views

```python
class RaceResultViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for race results.

    list: Get all race results
    retrieve: Get specific race result
    latest: Get latest race results
    """

    queryset = RaceResult.objects.select_related(
        'driver', 'team', 'session'
    ).all()
    serializer_class = RaceResultSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]

    @action(detail=False, methods=['get'])
    @method_decorator(cache_page(60 * 5))
    def latest(self, request):
        """Get latest race results."""
        # Implementation
        pass
```

---

### TypeScript (Frontend)

#### Interfaces vs Types

```typescript
// Use interface para objetos
interface Driver {
  id: number;
  name: string;
  points: number;
}

// Use type para unions, primitivos, etc
type Status = 'loading' | 'success' | 'error';
type ID = string | number;
```

#### Componentes Funcionais

```tsx
import { FC, useState, useEffect } from 'react';
import type { Driver } from '../types/f1';

interface DriversListProps {
  year: number;
  onSelect?: (driver: Driver) => void;
}

export const DriversList: FC<DriversListProps> = ({ year, onSelect }) => {
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch drivers
  }, [year]);

  return (
    <div>
      {/* Render */}
    </div>
  );
};
```

#### Hooks Customizados

```typescript
import { useState, useEffect } from 'react';
import api from '../services/api';

interface UseFetchResult<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useFetch<T>(url: string): UseFetchResult<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      setLoading(true);
      const response = await api.get(url);
      setData(response.data);
      setError(null);
    } catch (err) {
      setError('Erro ao carregar dados');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [url]);

  return { data, loading, error, refetch: fetchData };
}

// Uso
const { data: drivers, loading, error } = useFetch<Driver[]>('/drivers/');
```

---

### CSS

#### Naming Convention (BEM)

```css
/* Block */
.driver-card { }

/* Element */
.driver-card__name { }
.driver-card__points { }

/* Modifier */
.driver-card--highlighted { }
.driver-card__name--gold { }
```

#### Variáveis CSS

Sempre usar variáveis do tema:

```css
/* BOM */
.component {
  background-color: var(--color-background);
  color: var(--color-text);
  border: 1px solid var(--color-border);
}

/* RUIM */
.component {
  background-color: #ffffff;
  color: #000000;
  border: 1px solid #cccccc;
}
```

---

## Estrutura de Commits

### Conventional Commits

Seguir [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat` - Nova funcionalidade
- `fix` - Correção de bug
- `docs` - Documentação
- `style` - Formatação, sem mudança de código
- `refactor` - Refatoração
- `test` - Adicionar/modificar tests
- `chore` - Manutenção, deps, config

**Exemplos:**

```bash
# Feature
git commit -m "feat(api): add telemetry endpoint"

# Bug fix
git commit -m "fix(frontend): correct driver standings sort order"

# Documentação
git commit -m "docs(api): add endpoint documentation"

# Refatoração
git commit -m "refactor(tasks): extract pit stop processing logic"

# Chore
git commit -m "chore(deps): update fastf1 to 3.6.2"
```

**Mensagens Completas:**

```
feat(api): add driver prediction endpoint

- Implement historical data analysis
- Calculate weighted probabilities
- Add consistency factor for recent form
- Include prediction range based on std deviation

Closes #123
```

---

## Testing

### Backend (Python)

#### Unit Tests

```python
# tests/test_models.py
from django.test import TestCase
from core.models import Driver, Team

class DriverModelTest(TestCase):
    def setUp(self):
        self.team = Team.objects.create(
            team_id='red_bull',
            name='Red Bull Racing',
            color='#3671C6'
        )
        self.driver = Driver.objects.create(
            driver_id='ver',
            code='VER',
            number=1,
            first_name='Max',
            last_name='Verstappen'
        )

    def test_full_name_property(self):
        self.assertEqual(self.driver.full_name, 'Max Verstappen')

    def test_str_method(self):
        expected = 'Max Verstappen (VER)'
        self.assertEqual(str(self.driver), expected)
```

#### API Tests

```python
# tests/test_api.py
from rest_framework.test import APITestCase
from rest_framework import status

class RaceResultAPITest(APITestCase):
    def test_latest_race_endpoint(self):
        response = self.client.get('/api/races/latest/?year=2024')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)

    def test_invalid_year_returns_404(self):
        response = self.client.get('/api/races/latest/?year=1900')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
```

#### Executar Tests

```bash
# Todos os tests
docker compose exec django-api python manage.py test

# Tests específicos
docker compose exec django-api python manage.py test core.tests.test_models

# Com coverage
docker compose exec django-api coverage run --source='.' manage.py test
docker compose exec django-api coverage report
```

---

### Frontend (React)

#### Component Tests (Jest + React Testing Library)

```typescript
// __tests__/DriversList.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import { DriversList } from '../components/DriversList';
import api from '../services/api';

jest.mock('../services/api');

describe('DriversList', () => {
  it('renders drivers list', async () => {
    const mockDrivers = [
      { position: 1, name: 'Max Verstappen', points: 375 }
    ];

    (api.get as jest.Mock).mockResolvedValue({ data: mockDrivers });

    render(<DriversList year={2025} />);

    await waitFor(() => {
      expect(screen.getByText('Max Verstappen')).toBeInTheDocument();
    });
  });

  it('shows loading state', () => {
    render(<DriversList year={2025} />);
    expect(screen.getByText('Carregando...')).toBeInTheDocument();
  });
});
```

#### Executar Tests

```bash
cd frontend

# Todos os tests
npm test

# Com coverage
npm run test:coverage

# Watch mode
npm test -- --watch
```

---

## Debugging

### Backend

#### Django Shell

```bash
docker compose exec django-api python manage.py shell
```

```python
# Testar queries
from core.models import Driver, RaceResult
drivers = Driver.objects.all()
print(drivers.query)  # Ver SQL gerado

# Testar tasks
from data_collector.tasks import collect_session_data
result = collect_session_data(2025, 1, 'R')
```

#### Django Debug Toolbar

Adicionar ao `requirements.txt`:
```
django-debug-toolbar==4.2.0
```

Configurar em `settings.py`:
```python
if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
    INTERNAL_IPS = ['127.0.0.1', 'localhost']
```

#### Logging

```python
import logging
logger = logging.getLogger(__name__)

logger.debug('Debug message')
logger.info('Info message')
logger.warning('Warning message')
logger.error('Error message')
logger.exception('Exception with traceback')
```

### Frontend

#### React DevTools

Instalar extensão do navegador: [React DevTools](https://react.dev/learn/react-developer-tools)

#### Console Debugging

```typescript
// Logging estruturado
console.log('Driver data:', driver);
console.table(drivers);
console.group('API Call');
console.log('URL:', url);
console.log('Params:', params);
console.groupEnd();

// Timing
console.time('API Call');
await api.get('/endpoint/');
console.timeEnd('API Call');
```

#### Network Tab

Use DevTools Network tab para inspecionar requisições:
1. Abrir DevTools (F12)
2. Network tab
3. Filter por "XHR" para ver chamadas API
4. Inspecionar request/response

---

## Consulta à Documentação FastF1

### Quando Consultar

**SEMPRE consulte a documentação oficial da FastF1 antes de:**
- Implementar nova coleta de dados
- Corrigir bugs relacionados a dados
- Investigar problemas de formato de dados
- Adicionar novos campos aos modelos
- Modificar processadores de dados

### Links Importantes

**Documentação Oficial:**
- [FastF1 Docs](https://docs.fastf1.dev/)
- [API Reference](https://docs.fastf1.dev/api.html)
- [Examples](https://docs.fastf1.dev/examples/index.html)

**Principais Módulos:**
- [Session](https://docs.fastf1.dev/api.html#session)
- [Laps](https://docs.fastf1.dev/api.html#laps)
- [Weather](https://docs.fastf1.dev/api.html#weather)
- [Telemetry](https://docs.fastf1.dev/api.html#telemetry)

### Como Consultar no Código

```python
import fastf1

# Carregar sessão
session = fastf1.get_session(2025, 1, 'R')
session.load()

# Ver dados disponíveis
print("Results columns:", session.results.columns.tolist())
print("Laps columns:", session.laps.columns.tolist())
print("Weather columns:", session.weather_data.columns.tolist())

# Inspecionar dados
print(session.results.head())
print(session.results.dtypes)

# Ver documentação inline
help(fastf1.get_session)
help(session.load)
```

### Exemplo de Consulta

**Problema:** Pit stops não estão sendo salvos corretamente

**Passos:**
1. Consultar [Laps API](https://docs.fastf1.dev/api.html#fastf1.core.Laps)
2. Ver campos disponíveis: `PitInTime`, `PitOutTime`, `PitDuration`
3. Verificar exemplo de uso nos [exemplos oficiais](https://docs.fastf1.dev/examples/index.html)
4. Ajustar código baseado na documentação

```python
# Antes (incorreto - consultou documentação)
pit_stops = laps['PitStop']  # Campo não existe

# Depois (correto - baseado na doc)
pit_stops = laps[laps['PitInTime'].notna()]
duration = pit_stops['PitOutTime'] - pit_stops['PitInTime']
```

---

## Troubleshooting Comum

### Problema: Containers não iniciam

**Solução:**
```bash
# Ver logs
docker compose logs

# Rebuild
docker compose down
docker compose build --no-cache
docker compose up -d
```

### Problema: MySQL Connection Error

**Solução:**
```bash
# Verificar se MySQL está rodando
docker compose ps

# Reiniciar MySQL
docker compose restart mysql

# Verificar variáveis de ambiente
docker compose exec django-api env | grep MYSQL
```

### Problema: Celery tasks não executam

**Solução:**
```bash
# Verificar workers
docker compose exec celery-worker celery -A config inspect active

# Verificar conexão com Redis
docker compose exec redis redis-cli ping

# Reiniciar worker
docker compose restart celery-worker
```

### Problema: Frontend não conecta ao backend

**Solução:**
```bash
# Verificar VITE_API_URL
cat frontend/.env

# Verificar CORS no Django
docker compose exec django-api python manage.py shell
>>> from django.conf import settings
>>> print(settings.CORS_ALLOWED_ORIGINS)

# Adicionar ao settings.py se necessário
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
]
```

### Problema: Dados não aparecem no frontend

**Checklist:**
1. Backend está rodando? `curl http://localhost:8000/api/status/`
2. Dados estão no banco? `/api/status/` retorna contadores?
3. Celery coletou dados? Ver logs do worker
4. API retorna dados? `curl http://localhost:8000/api/races/latest/?year=2025`
5. Frontend está fazendo request correto? Ver Network tab

### Problema: FastF1 Session not available

**Causa:** Dados ainda não disponíveis ou sessão não existe

**Solução:**
- Aguardar 30-120 min após fim da sessão
- Verificar se rodada/ano/tipo estão corretos
- Consultar [FastF1 Schedule](https://docs.fastf1.dev/api.html#fastf1.get_event_schedule)

---

## Performance

### Backend

#### Database Queries

```python
# BOM - use select_related para ForeignKeys
results = RaceResult.objects.select_related(
    'driver', 'team', 'session'
).all()

# BOM - use prefetch_related para reverse FKs
drivers = Driver.objects.prefetch_related('race_results').all()

# RUIM - N+1 queries
for result in results:
    print(result.driver.name)  # Query por iteração
```

#### Cache

```python
from django.core.cache import cache

# Set cache
cache.set('drivers_2025', drivers, 300)  # 5 minutos

# Get cache
drivers = cache.get('drivers_2025')
if not drivers:
    drivers = fetch_drivers()
    cache.set('drivers_2025', drivers, 300)
```

### Frontend

#### Code Splitting

```typescript
import { lazy, Suspense } from 'react';

const Drivers = lazy(() => import('./pages/Drivers'));

function App() {
  return (
    <Suspense fallback={<LoadingSpinner />}>
      <Drivers />
    </Suspense>
  );
}
```

#### Memoization

```typescript
import { useMemo, useCallback } from 'react';

function DriversList({ drivers }) {
  // Memoizar cálculos pesados
  const sortedDrivers = useMemo(() => {
    return drivers.sort((a, b) => b.points - a.points);
  }, [drivers]);

  // Memoizar callbacks
  const handleClick = useCallback((driver) => {
    console.log(driver);
  }, []);

  return <div>{/* Render */}</div>;
}
```

---

## Deployment

### Build de Produção

```bash
# Frontend
cd frontend
npm run build

# Backend - coletar static files
docker compose exec django-api python manage.py collectstatic --noinput

# Build Docker images
docker compose -f docker-compose.prod.yml build
```

### Checklist Pré-Deploy

- [ ] Todos os tests passando
- [ ] Variáveis de ambiente configuradas
- [ ] DEBUG=False
- [ ] SECRET_KEY forte
- [ ] ALLOWED_HOSTS configurado
- [ ] Banco de dados com backup
- [ ] Cache configurado
- [ ] Logs configurados
- [ ] Monitoramento ativo

---

## Recursos Adicionais

### Documentação Interna

- [Modelos](/docs/models/README.md)
- [API](/docs/api/README.md)
- [Tasks](/docs/tasks/README.md)
- [Frontend](/docs/frontend/README.md)

### Documentação Externa

- [Django](https://docs.djangoproject.com/)
- [DRF](https://www.django-rest-framework.org/)
- [FastF1](https://docs.fastf1.dev/)
- [React](https://react.dev/)
- [TypeScript](https://www.typescriptlang.org/)
- [Celery](https://docs.celeryq.dev/)

### Ferramentas Úteis

- [Postman](https://www.postman.com/) - Testar API
- [DB Browser for SQLite](https://sqlitebrowser.org/) - Inspecionar banco
- [Redis Commander](https://github.com/joeferner/redis-commander) - Visualizar Redis
- [Celery Flower](https://flower.readthedocs.io/) - Monitor Celery

---

## Contribuindo

1. Fork o repositório
2. Criar branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'feat: add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Abrir Pull Request

**PR Checklist:**
- [ ] Código segue os padrões
- [ ] Tests adicionados/atualizados
- [ ] Documentação atualizada
- [ ] Commits seguem Conventional Commits
- [ ] Sem erros de lint
- [ ] Todas as CI checks passando
