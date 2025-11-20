import axios, { AxiosError, AxiosRequestConfig } from 'axios';
import { Driver, Constructor, SessionData, QualifyingData, SprintData, PitStopData, WeatherSessionData } from '../types/f1';

// Em desenvolvimento, usar proxy relativo do Vite
// Em produção, usar variável de ambiente
const API_URL = import.meta.env.MODE === 'development' ? '/api' : (import.meta.env.VITE_API_URL || '/api');

// Configuração de retry - Reduzido para evitar overhead
const MAX_RETRIES = 3;
const INITIAL_RETRY_DELAY = 1000; // 1 segundo
const MAX_RETRY_DELAY = 10000; // 10 segundos (reduzido de 30s)

const api = axios.create({
  baseURL: API_URL,
  timeout: 30000, // 30 segundos (reduzido de 2 minutos para evitar long polling)
  headers: {
    'Content-Type': 'application/json',
  },
});

// Função para calcular delay com exponential backoff
const getRetryDelay = (retryCount: number): number => {
  const delay = Math.min(INITIAL_RETRY_DELAY * Math.pow(2, retryCount), MAX_RETRY_DELAY);
  // Adiciona jitter (variação aleatória) para evitar thundering herd
  return delay + Math.random() * 1000;
};

// Função para verificar se deve fazer retry
const shouldRetry = (error: AxiosError): boolean => {
  // Retry em erros de rede ou timeout
  if (!error.response) {
    return true;
  }

  // Retry em erros 5xx (servidor)
  if (error.response.status >= 500) {
    return true;
  }

  // NÃO fazer retry em 404 - dados não existem ainda
  // O polling do componente vai tentar novamente mais tarde
  if (error.response.status === 404) {
    return false;
  }

  return false;
};

// Interceptor para adicionar retry logic
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const config = error.config as AxiosRequestConfig & { _retryCount?: number };

    if (!config) {
      return Promise.reject(error);
    }

    // Inicializar contador de retry
    config._retryCount = config._retryCount || 0;

    // Verificar se deve fazer retry
    if (config._retryCount >= MAX_RETRIES || !shouldRetry(error)) {
      return Promise.reject(error);
    }

    // Incrementar contador
    config._retryCount += 1;

    // Calcular delay
    const delay = getRetryDelay(config._retryCount);

    console.log(
      `Tentativa ${config._retryCount}/${MAX_RETRIES} falhou. ` +
      `Tentando novamente em ${(delay / 1000).toFixed(1)}s...`
    );

    // Aguardar antes de tentar novamente
    await new Promise(resolve => setTimeout(resolve, delay));

    // Tentar novamente
    return api(config);
  }
);

export const f1Api = {
  // Driver Standings
  getDriverStandings: async (): Promise<Driver[]> => {
    const { data } = await api.get('/driver-standings/latest/', {
      params: { year: new Date().getFullYear() }
    });
    return data;
  },

  // Constructor Standings
  getConstructorStandings: async (): Promise<Constructor[]> => {
    const { data } = await api.get('/constructor-standings/latest/', {
      params: { year: new Date().getFullYear() }
    });
    return data;
  },

  // Teams for Filters (apenas equipes atuais consolidadas)
  getTeamsForFilters: async (): Promise<Array<{
    id: number;
    current_name: string;
    color: string;
    operation_line_id: number;
    succession_line: Array<{
      name: string;
      years_active: string;
      is_current: boolean;
      status: string;
    }>;
  }>> => {
    const { data} = await api.get('/teams/for_filters/');
    return data;
  },

  // Latest Race
  getLatestRace: async (): Promise<SessionData> => {
    const { data } = await api.get('/races/latest/');
    return data;
  },

  // Latest Qualifying
  getLatestQualifying: async (): Promise<QualifyingData> => {
    const { data } = await api.get('/qualifying/latest/');
    return data;
  },

  // Latest Sprint
  getLatestSprint: async (): Promise<SprintData> => {
    const { data } = await api.get('/sprints/latest/');
    return data;
  },

  // System Status
  getStatus: async (): Promise<any> => {
    const { data } = await api.get('/status/');
    return data;
  },

  // Latest Pit Stops
  getLatestPitStops: async (): Promise<PitStopData> => {
    const { data } = await api.get('/pit-stops/latest/');
    return data;
  },

  // Latest Weather Data
  getLatestWeather: async (): Promise<WeatherSessionData> => {
    const { data } = await api.get('/weather/latest/');
    return data;
  },

  // Race History
  getRaceHistory: async (filters?: {
    year?: string;
    circuit?: string;
    driver?: string;
    team?: string;
  }): Promise<any> => {
    const { data } = await api.get('/races/history/', { params: filters });
    return data;
  },

  // Qualifying History
  getQualifyingHistory: async (filters?: {
    year?: string;
    circuit?: string;
    driver?: string;
    team?: string;
  }): Promise<any> => {
    const { data } = await api.get('/qualifying/history/', { params: filters });
    return data;
  },

  // Sprint History
  getSprintHistory: async (filters?: {
    year?: string;
    circuit?: string;
    driver?: string;
    team?: string;
  }): Promise<any> => {
    const { data } = await api.get('/sprints/history/', { params: filters });
    return data;
  },

  // Driver Standings Evolution
  getDriverStandingsEvolution: async (params: {
    year: string;
    drivers?: string;
    start_round?: number;
    end_round?: number;
  }): Promise<any> => {
    const { data } = await api.get('/driver-standings/evolution/', { params });
    return data;
  },

  // Constructor Standings Evolution
  getConstructorStandingsEvolution: async (params: {
    year: string;
    teams?: string;
    start_round?: number;
    end_round?: number;
  }): Promise<any> => {
    const { data } = await api.get('/constructor-standings/evolution/', { params });
    return data;
  },

  // Weather Analytics
  getWeatherAnalytics: async (params: {
    year: string;
    round: string;
    session_type?: string;
  }): Promise<any> => {
    const { data } = await api.get('/weather/analytics/', { params });
    return data;
  },

  // Pit Stops Analytics
  getPitStopsAnalytics: async (params: {
    year: string;
    round?: string;
    team?: string;
  }): Promise<any> => {
    const { data } = await api.get('/pit-stops/analytics/', { params });
    return data;
  },

  // Driver Prediction
  getDriverPrediction: async (params: {
    driver: string;
    circuit: string;
    year?: string;
    params?: any;
  }): Promise<any> => {
    const queryParams: any = {
      driver: params.driver,
      circuit: params.circuit,
      year: params.year
    };

    // Serialize params to JSON string if provided
    if (params.params) {
      queryParams.params = JSON.stringify(params.params);
    }

    const { data } = await api.get('/predictions/driver/', { params: queryParams });
    return data;
  },

  // Constructor Prediction
  getConstructorPrediction: async (params: {
    team: string;
    circuit: string;
    year?: string;
    params?: any;
  }): Promise<any> => {
    const queryParams: any = {
      team: params.team,
      circuit: params.circuit,
      year: params.year
    };

    // Serialize params to JSON string if provided
    if (params.params) {
      queryParams.params = JSON.stringify(params.params);
    }

    const { data } = await api.get('/predictions/constructor/', { params: queryParams });
    return data;
  },

  // Available Options for Dropdowns (ALL drivers/teams from database)
  getAvailableDrivers: async (): Promise<any> => {
    const { data } = await api.get('/options/drivers/');
    return data;
  },

  getAvailableTeams: async (): Promise<any> => {
    const { data } = await api.get('/options/teams/');
    return data;
  },

  // Active Grid Options (ONLY current season drivers/teams for predictions)
  getActiveDriversGrid: async (): Promise<any> => {
    const { data } = await api.get('/options/grid/drivers/');
    return data;
  },

  getActiveTeamsGrid: async (): Promise<any> => {
    const { data } = await api.get('/options/grid/teams/');
    return data;
  },

  getAvailableCircuits: async (): Promise<any> => {
    const { data } = await api.get('/options/circuits/');
    return data;
  },

  getAvailableYears: async (): Promise<any> => {
    const { data } = await api.get('/options/years/');
    return data;
  },

  getCircuitRaceStatus: async (circuit: string, year: number): Promise<{
    status: string;
    has_race: boolean;
    race_date: string | null;
    circuit: string;
    year: number;
  }> => {
    const { data } = await api.get('/options/circuit-race-status/', {
      params: { circuit, year }
    });
    return data;
  },

  // New Filter Options Endpoints
  getFilterOptions: async (): Promise<{
    years: number[];
    teams: Array<{ id: number; name: string; color: string }>;
    sessionTypes: Array<{ value: string; label: string }>;
  }> => {
    const { data } = await api.get('/filters/options/');
    return data;
  },

  getGrandsPrix: async (year: string): Promise<Array<{
    round: number;
    name: string;
    location: string;
    country: string;
    date: string;
  }>> => {
    const { data } = await api.get('/filters/grands-prix/', { params: { year } });
    return data.grandsPrix || [];
  },

  getDriversByYear: async (year: string): Promise<Array<{
    id: number;
    code: string;
    name: string;
    number: number;
  }>> => {
    const { data } = await api.get('/filters/drivers/', { params: { year } });
    return data.drivers || [];
  },

  getTeamsByYear: async (year: string): Promise<Array<{
    id: number;
    name: string;
    color: string;
  }>> => {
    const { data } = await api.get('/filters/teams/', { params: { year } });
    return data.teams || [];
  },

  // Celery Tasks Status
  getTasksStatus: async (): Promise<any> => {
    const { data } = await api.get('/tasks/status/');
    return data;
  },

  // ML Models
  getMlModelsStatus: async (): Promise<any> => {
    const { data } = await api.get('/ml/status/');
    return data;
  },

  // Pole Position Predictions
  getPolePredictionDriver: async (params?: {
    circuit_id?: number;
    year?: number;
  }): Promise<any> => {
    const { data } = await api.get('/predictions/pole-driver/', { params });
    return data;
  },

  getPolePredictionConstructor: async (params?: {
    circuit_id?: number;
    year?: number;
  }): Promise<any> => {
    const { data } = await api.get('/predictions/pole-constructor/', { params });
    return data;
  },

  getPoleTimePrediction: async (params: {
    circuit_id: number;
    year: number;
    air_temp?: number;
    track_temp?: number;
    humidity?: number;
    rainfall?: boolean;
  }): Promise<any> => {
    const { data } = await api.get('/predictions/pole-time/', { params });
    return data;
  },

  // Data Audit Reports
  getLatestAuditReport: async (): Promise<any> => {
    const { data } = await api.get('/data-audit-reports/latest/');
    return data;
  },

  runDataAudit: async (): Promise<any> => {
    const { data } = await api.post('/data-audit-reports/run_audit/');
    return data;
  },

  // Periodic Tasks Management
  getPeriodicTasks: async (): Promise<any[]> => {
    const { data } = await api.get('/periodic-tasks/');
    return data;
  },

  getPeriodicTask: async (id: number): Promise<any> => {
    const { data } = await api.get(`/periodic-tasks/${id}/`);
    return data;
  },

  createPeriodicTask: async (taskData: any): Promise<any> => {
    const { data } = await api.post('/periodic-tasks/', taskData);
    return data;
  },

  updatePeriodicTask: async (id: number, taskData: any): Promise<any> => {
    const { data } = await api.patch(`/periodic-tasks/${id}/`, taskData);
    return data;
  },

  deletePeriodicTask: async (id: number): Promise<void> => {
    await api.delete(`/periodic-tasks/${id}/`);
  },

  togglePeriodicTask: async (id: number): Promise<any> => {
    const { data } = await api.post(`/periodic-tasks/${id}/toggle/`);
    return data;
  },

  // Crontab Schedules
  getCrontabSchedules: async (): Promise<any[]> => {
    const { data } = await api.get('/crontab-schedules/');
    return data;
  },

  createCrontabSchedule: async (scheduleData: any): Promise<any> => {
    const { data } = await api.post('/crontab-schedules/', scheduleData);
    return data;
  },

  // Interval Schedules
  getIntervalSchedules: async (): Promise<any[]> => {
    const { data } = await api.get('/interval-schedules/');
    return data;
  },

  createIntervalSchedule: async (scheduleData: any): Promise<any> => {
    const { data } = await api.post('/interval-schedules/', scheduleData);
    return data;
  },

  // Explain Crontab
  explainCrontab: async (schedule: string): Promise<any> => {
    const { data } = await api.get('/crontab/explain/', {
      params: { schedule }
    });
    return data;
  },

  // ============================================================================
  // DATA AUDIT SUGGESTIONS - Novos métodos
  // ============================================================================

  getPendingDataAuditSuggestions: async (): Promise<any> => {
    const { data } = await api.get('/data-audit-suggestions/pending/');
    return data;
  },

  getSuggestionsByTable: async (): Promise<any> => {
    const { data } = await api.get('/data-audit-suggestions/by_table/');
    return data;
  },

  applySuggestion: async (id: number): Promise<any> => {
    const { data } = await api.post(`/data-audit-suggestions/${id}/apply_suggestion/`);
    return data;
  },

  rejectSuggestion: async (id: number, reason?: string): Promise<any> => {
    const { data } = await api.post(`/data-audit-suggestions/${id}/reject_suggestion/`, {
      reason: reason || ''
    });
    return data;
  },

  updateSuggestion: async (id: number, suggestedValue: string): Promise<any> => {
    const { data } = await api.patch(`/data-audit-suggestions/${id}/update_suggestion/`, {
      suggested_value: suggestedValue
    });
    return data;
  },

  bulkApplySuggestions: async (suggestionIds: number[]): Promise<any> => {
    const { data } = await api.post('/data-audit-suggestions/bulk_apply/', {
      suggestion_ids: suggestionIds
    });
    return data;
  },

  bulkRejectSuggestions: async (suggestionIds: number[], reason?: string): Promise<any> => {
    const { data } = await api.post('/data-audit-suggestions/bulk_reject/', {
      suggestion_ids: suggestionIds,
      reason: reason || ''
    });
    return data;
  },
};

export default f1Api;
