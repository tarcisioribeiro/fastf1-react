# Documentação do Frontend (React + TypeScript)

Esta documentação descreve a arquitetura, componentes e tipos do frontend da aplicação FastF1 React.

## Sumário

- [Tipos TypeScript](#tipos-typescript)
- [Estrutura de Diretórios](#estrutura-de-diretórios)
- [Componentes](#componentes)
- [Serviços](#serviços)
- [Contextos](#contextos)
- [Rotas](#rotas)
- [Estilização](#estilização)

---

## Tipos TypeScript

Arquivo: `frontend/src/types/f1.ts`

### Driver

Representa um piloto na classificação do campeonato.

```typescript
export interface Driver {
  position: number;          // Posição no campeonato
  name: string;              // Nome completo
  driver_number?: number;    // Número do piloto (opcional)
  team: string;              // Nome da equipe
  points: number;            // Pontos acumulados
  wins: number;              // Número de vitórias
  podiums?: number;          // Número de pódios (opcional)
  teamColor?: string;        // Cor da equipe em hex (opcional)
}
```

**Exemplo:**
```json
{
  "position": 1,
  "name": "Max Verstappen",
  "driver_number": 1,
  "team": "Red Bull Racing",
  "points": 375.0,
  "wins": 12,
  "podiums": 18,
  "teamColor": "#3671C6"
}
```

---

### Constructor

Representa uma equipe na classificação de construtores.

```typescript
export interface Constructor {
  position: number;          // Posição no campeonato
  team: string;              // Nome da equipe
  points: number;            // Pontos acumulados
  wins: number;              // Número de vitórias
  podiums?: number;          // Número de pódios (opcional)
  teamColor?: string;        // Cor da equipe (opcional)
}
```

**Exemplo:**
```json
{
  "position": 1,
  "team": "Red Bull Racing",
  "points": 589.0,
  "wins": 15,
  "podiums": 25,
  "teamColor": "#3671C6"
}
```

---

### RaceResult

Representa o resultado de um piloto em uma corrida.

```typescript
export interface RaceResult {
  position: number;          // Posição final
  driver: string;            // Nome do piloto
  driver_code: string;       // Código de 3 letras (ex: VER)
  driver_number?: number;    // Número do piloto
  team: string;              // Nome da equipe
  teamColor: string;         // Cor da equipe
  time: string;              // Tempo total ou gap
  points: number;            // Pontos conquistados
  status: string;            // Status (Finished, DNF, +1 Lap, etc.)
}
```

**Exemplo:**
```json
{
  "position": 1,
  "driver": "Max Verstappen",
  "driver_code": "VER",
  "driver_number": 1,
  "team": "Red Bull Racing",
  "teamColor": "#3671C6",
  "time": "1:32:15.123",
  "points": 25.0,
  "status": "Finished"
}
```

**Formatação de Tempo:**
- Vencedor: tempo total (ex: "1:32:15.123")
- Outros: gap para o vencedor (ex: "+5.234" ou "+1 Lap")

---

### QualifyingResult

Representa o resultado de um piloto na classificação.

```typescript
export interface QualifyingResult {
  position: number;          // Posição final
  driver: string;            // Nome do piloto
  driver_code: string;       // Código (ex: VER)
  driver_number?: number;    // Número do piloto
  team: string;              // Nome da equipe
  teamColor: string;         // Cor da equipe
  q1?: string;               // Tempo Q1 (opcional)
  q2?: string;               // Tempo Q2 (opcional)
  q3?: string;               // Tempo Q3 (opcional)
}
```

**Exemplo:**
```json
{
  "position": 1,
  "driver": "Max Verstappen",
  "driver_code": "VER",
  "driver_number": 1,
  "team": "Red Bull Racing",
  "teamColor": "#3671C6",
  "q1": "1:30.123",
  "q2": "1:29.456",
  "q3": "1:28.789"
}
```

**Observações:**
- Q1: 20 pilotos
- Q2: 15 pilotos (top 15 do Q1)
- Q3: 10 pilotos (top 10 do Q2)
- Pilotos eliminados não têm tempos para fases seguintes

---

### SprintResult

Representa o resultado de um piloto em uma corrida sprint.

```typescript
export interface SprintResult {
  position: number;          // Posição final
  driver: string;            // Nome do piloto
  driver_code: string;       // Código
  driver_number?: number;    // Número do piloto
  team: string;              // Nome da equipe
  teamColor: string;         // Cor da equipe
  time: string;              // Tempo total ou gap
  points: number;            // Pontos (8-7-6-5-4-3-2-1 para top 8)
  status: string;            // Status
}
```

**Pontos de Sprint:**
- 1º: 8 pontos
- 2º: 7 pontos
- 3º: 6 pontos
- 4º: 5 pontos
- 5º: 4 pontos
- 6º: 3 pontos
- 7º: 2 pontos
- 8º: 1 ponto

---

### PitStop

Representa um pit stop.

```typescript
export interface PitStop {
  id: number;                // ID do pit stop
  driver: string;            // Nome do piloto
  driver_code: string;       // Código do piloto
  team: string;              // Nome da equipe
  stop_number: number;       // Número do stop (1, 2, 3...)
  lap: number;               // Volta em que ocorreu
  duration: string;          // Duração em segundos (ex: "2.345")
}
```

**Exemplo:**
```json
{
  "id": 1,
  "driver": "Max Verstappen",
  "driver_code": "VER",
  "team": "Red Bull Racing",
  "stop_number": 1,
  "lap": 15,
  "duration": "2.345"
}
```

---

### WeatherData

Representa dados meteorológicos em um momento da sessão.

```typescript
export interface WeatherData {
  id: number;                // ID do registro
  timestamp: string;         // Timestamp ISO (ex: "2025-03-02T18:30:00Z")
  air_temp: number;          // Temperatura do ar (°C)
  track_temp: number;        // Temperatura da pista (°C)
  humidity: number;          // Umidade (%)
  pressure: number;          // Pressão atmosférica (mbar)
  rainfall: boolean;         // Se está chovendo
  wind_speed?: number;       // Velocidade do vento (m/s)
  wind_direction?: number;   // Direção do vento (graus)
}
```

**Exemplo:**
```json
{
  "id": 1,
  "timestamp": "2025-03-02T18:30:00Z",
  "air_temp": 28.5,
  "track_temp": 42.3,
  "humidity": 45.0,
  "pressure": 1013.25,
  "rainfall": false,
  "wind_speed": 3.5,
  "wind_direction": 180
}
```

---

### RaceInfo

Informações sobre um evento/corrida.

```typescript
export interface RaceInfo {
  eventName: string;         // Nome do evento (ex: "Bahrain Grand Prix")
  location: string;          // Localização (ex: "Sakhir")
  date: string;              // Data (formato: YYYY-MM-DD)
  round: number;             // Número da rodada
}
```

---

### SessionData

Dados completos de uma sessão de corrida.

```typescript
export interface SessionData {
  raceInfo: RaceInfo;        // Informações do evento
  results: RaceResult[];     // Resultados dos pilotos
}
```

---

### QualifyingData

Dados completos de uma sessão de classificação.

```typescript
export interface QualifyingData {
  raceInfo: RaceInfo;        // Informações do evento
  results: QualifyingResult[]; // Resultados dos pilotos
}
```

---

### SprintData

Dados completos de uma sessão de sprint.

```typescript
export interface SprintData {
  raceInfo: RaceInfo;        // Informações do evento
  results: SprintResult[];   // Resultados dos pilotos
}
```

---

### PitStopData

Dados de pit stops de uma sessão.

```typescript
export interface PitStopData {
  raceInfo: RaceInfo;        // Informações do evento
  pitStops: PitStop[];       // Pit stops da sessão
}
```

---

### WeatherSessionData

Dados meteorológicos de uma sessão.

```typescript
export interface WeatherSessionData {
  raceInfo: RaceInfo;        // Informações do evento
  weatherData: WeatherData[]; // Dados meteorológicos
}
```

---

## Estrutura de Diretórios

```
frontend/src/
├── components/           # Componentes reutilizáveis
│   ├── Navbar.tsx       # Barra de navegação
│   ├── ThemeToggle.tsx  # Botão de alternância de tema
│   ├── LoadingSpinner.tsx
│   ├── ErrorMessage.tsx
│   ├── Card.tsx
│   ├── Table.tsx
│   ├── Podium.tsx
│   └── HistoryFilters.tsx
├── pages/               # Páginas da aplicação
│   ├── Home.tsx         # Dashboard
│   ├── Race.tsx         # Última corrida
│   ├── Qualifying.tsx   # Última classificação
│   ├── Sprint.tsx       # Última sprint
│   ├── Drivers.tsx      # Classificação de pilotos
│   ├── Constructors.tsx # Classificação de construtores
│   ├── HistoryRaces.tsx # Histórico de corridas
│   ├── HistoryQualifying.tsx # Histórico de classificações
│   ├── HistorySprints.tsx # Histórico de sprints
│   └── Status.tsx       # Status do sistema
├── contexts/            # Contextos React
│   └── ThemeContext.tsx # Gerenciamento de tema
├── services/            # Serviços de API
│   └── api.ts           # Cliente Axios
├── styles/              # Arquivos CSS
│   ├── globals.css      # Variáveis CSS e tema global
│   └── *.css            # Estilos específicos
├── types/               # Tipos TypeScript
│   └── f1.ts            # Interfaces F1
├── App.tsx              # Componente raiz
└── main.tsx             # Entry point
```

---

## Componentes

### Navbar

Barra de navegação com links para todas as páginas.

**Localização:** `components/Navbar.tsx`

**Props:** Nenhuma

**Funcionalidades:**
- Links para todas as páginas
- Destaque do link ativo
- Responsivo (menu hambúrguer em mobile)

---

### ThemeToggle

Botão para alternar entre tema claro e escuro.

**Localização:** `components/ThemeToggle.tsx`

**Props:** Nenhuma

**Funcionalidades:**
- Alterna tema via ThemeContext
- Ícone muda (sol/lua)
- Persiste preferência no localStorage

---

### LoadingSpinner

Spinner de carregamento.

**Localização:** `components/LoadingSpinner.tsx`

**Props:**
- `message?: string` - Mensagem opcional

**Uso:**
```tsx
<LoadingSpinner message="Carregando dados..." />
```

---

### ErrorMessage

Mensagem de erro.

**Localização:** `components/ErrorMessage.tsx`

**Props:**
- `message: string` - Mensagem de erro

**Uso:**
```tsx
<ErrorMessage message="Erro ao carregar dados" />
```

---

### Card

Card genérico para conteúdo.

**Localização:** `components/Card.tsx`

**Props:**
- `title?: string` - Título do card
- `children: ReactNode` - Conteúdo

**Uso:**
```tsx
<Card title="Classificação">
  <Table data={data} />
</Card>
```

---

### Table

Tabela genérica responsiva.

**Localização:** `components/Table.tsx`

**Props:**
- `columns: Column[]` - Definição das colunas
- `data: any[]` - Dados da tabela

**Uso:**
```tsx
const columns = [
  { key: 'position', label: 'Pos' },
  { key: 'name', label: 'Piloto' },
  { key: 'points', label: 'Pontos' }
];

<Table columns={columns} data={drivers} />
```

---

### Podium

Componente de pódio para top 3.

**Localização:** `components/Podium.tsx`

**Props:**
- `results: RaceResult[]` - Resultados (top 3)

**Funcionalidades:**
- Mostra top 3 em formato de pódio
- Cores dourado/prateado/bronze
- Animações

---

### HistoryFilters

Filtros para páginas de histórico.

**Localização:** `components/HistoryFilters.tsx`

**Props:**
- `onFilterChange: (filters: Filters) => void` - Callback de mudança

**Funcionalidades:**
- Filtros por ano, circuito, piloto, equipe
- Dropdowns populados dinamicamente via API
- Debounce em buscas

---

## Serviços

### API Client

Cliente Axios configurado com retry logic.

**Localização:** `services/api.ts`

**Configuração:**
```typescript
import axios from 'axios';
import axiosRetry from 'axios-retry';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Retry automático
axiosRetry(api, {
  retries: 3,
  retryDelay: axiosRetry.exponentialDelay,
  retryCondition: (error) => {
    return axiosRetry.isNetworkOrIdempotentRequestError(error) ||
           error.response?.status === 429; // Rate limit
  },
});
```

**Métodos:**
```typescript
// GET
const response = await api.get('/races/latest/', {
  params: { year: 2025 }
});

// POST (se necessário no futuro)
const response = await api.post('/endpoint/', data);
```

**Interceptors:**
```typescript
// Request interceptor (adicionar auth tokens, etc)
api.interceptors.request.use((config) => {
  // Modificar config
  return config;
});

// Response interceptor (tratar erros globalmente)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Tratar erro
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);
```

---

## Contextos

### ThemeContext

Gerenciamento de tema (claro/escuro).

**Localização:** `contexts/ThemeContext.tsx`

**Contexto:**
```typescript
interface ThemeContextType {
  theme: 'light' | 'dark';
  toggleTheme: () => void;
}

export const ThemeContext = createContext<ThemeContextType | undefined>(undefined);
```

**Provider:**
```tsx
export const ThemeProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [theme, setTheme] = useState<'light' | 'dark'>('light');

  useEffect(() => {
    // Carregar tema do localStorage
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
      setTheme(savedTheme as 'light' | 'dark');
    } else {
      // Detectar preferência do sistema
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      setTheme(prefersDark ? 'dark' : 'light');
    }
  }, []);

  useEffect(() => {
    // Aplicar tema ao HTML
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => prev === 'light' ? 'dark' : 'light');
  };

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
};
```

**Hook:**
```typescript
export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within ThemeProvider');
  }
  return context;
};
```

**Uso:**
```tsx
import { useTheme } from '../contexts/ThemeContext';

function MyComponent() {
  const { theme, toggleTheme } = useTheme();

  return (
    <button onClick={toggleTheme}>
      Current theme: {theme}
    </button>
  );
}
```

---

## Rotas

**Arquivo:** `App.tsx`

```tsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';

function App() {
  return (
    <BrowserRouter>
      <ThemeProvider>
        <Navbar />
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/race" element={<Race />} />
          <Route path="/qualifying" element={<Qualifying />} />
          <Route path="/sprint" element={<Sprint />} />
          <Route path="/drivers" element={<Drivers />} />
          <Route path="/constructors" element={<Constructors />} />
          <Route path="/history/races" element={<HistoryRaces />} />
          <Route path="/history/qualifying" element={<HistoryQualifying />} />
          <Route path="/history/sprints" element={<HistorySprints />} />
          <Route path="/status" element={<Status />} />
        </Routes>
      </ThemeProvider>
    </BrowserRouter>
  );
}
```

**Navegação:**
```tsx
import { useNavigate } from 'react-router-dom';

function MyComponent() {
  const navigate = useNavigate();

  const goToRace = () => {
    navigate('/race');
  };

  return <button onClick={goToRace}>Ver Corrida</button>;
}
```

---

## Estilização

### Sistema de Temas

**Arquivo:** `styles/globals.css`

**Variáveis CSS:**
```css
[data-theme="light"] {
  --color-background: #ffffff;
  --color-text: #1a1a1a;
  --color-primary: #e10600;
  --color-secondary: #15151e;
  --color-border: #e0e0e0;
  --color-card: #f5f5f5;
  --color-hover: #f0f0f0;

  /* Pódio */
  --color-gold: #ffd700;
  --color-silver: #c0c0c0;
  --color-bronze: #cd7f32;
}

[data-theme="dark"] {
  --color-background: #1a1a1a;
  --color-text: #ffffff;
  --color-primary: #e10600;
  --color-secondary: #38383f;
  --color-border: #2a2a2a;
  --color-card: #2a2a2a;
  --color-hover: #333333;

  /* Pódio */
  --color-gold: #ffd700;
  --color-silver: #c0c0c0;
  --color-bronze: #cd7f32;
}
```

**Uso:**
```css
.my-component {
  background-color: var(--color-background);
  color: var(--color-text);
  border: 1px solid var(--color-border);
}

.my-component:hover {
  background-color: var(--color-hover);
}
```

### Cores de Equipes

**Uso direto do backend:**
```tsx
<div style={{ backgroundColor: result.teamColor }}>
  {result.team}
</div>
```

### CSS Modules

**Uso:**
```tsx
// Component.module.css
.container {
  padding: 20px;
}

// Component.tsx
import styles from './Component.module.css';

function Component() {
  return <div className={styles.container}>Content</div>;
}
```

---

## Boas Práticas

1. **Tipagem forte:** Sempre use interfaces TypeScript
2. **Props opcionais:** Use `?` para props opcionais
3. **Default props:** Use valores padrão quando apropriado
4. **Separação de concerns:** Componentes, lógica e estilos separados
5. **Reutilização:** Crie componentes genéricos
6. **Lazy loading:** Use `React.lazy()` para code splitting
7. **Error boundaries:** Implemente error boundaries
8. **Acessibilidade:** Use ARIA labels e semântica HTML

---

## Exemplos de Uso

### Fetch de Dados

```tsx
import { useState, useEffect } from 'react';
import api from '../services/api';
import type { Driver } from '../types/f1';

function DriversPage() {
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDrivers = async () => {
      try {
        const response = await api.get('/driver-standings/latest/', {
          params: { year: 2025 }
        });
        setDrivers(response.data);
      } catch (err) {
        setError('Erro ao carregar pilotos');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchDrivers();
  }, []);

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorMessage message={error} />;

  return (
    <div>
      {drivers.map(driver => (
        <div key={driver.position}>
          {driver.name} - {driver.points} pts
        </div>
      ))}
    </div>
  );
}
```

### Formulário com Filtros

```tsx
import { useState } from 'react';

interface Filters {
  year?: number;
  driver?: string;
  team?: string;
}

function FilterForm() {
  const [filters, setFilters] = useState<Filters>({});

  const handleChange = (key: keyof Filters, value: any) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const handleSubmit = async () => {
    const response = await api.get('/races/history/', {
      params: filters
    });
    // Processar resultados
  };

  return (
    <form onSubmit={(e) => { e.preventDefault(); handleSubmit(); }}>
      <input
        type="number"
        placeholder="Ano"
        onChange={(e) => handleChange('year', parseInt(e.target.value))}
      />
      <button type="submit">Filtrar</button>
    </form>
  );
}
```

---

## Referências

- [React Documentation](https://react.dev/)
- [TypeScript Documentation](https://www.typescriptlang.org/docs/)
- [Vite Documentation](https://vitejs.dev/)
- [React Router Documentation](https://reactrouter.com/)
