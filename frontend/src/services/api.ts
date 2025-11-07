import axios, { AxiosError, AxiosRequestConfig } from 'axios';
import { Driver, Constructor, SessionData, QualifyingData, PitStopData, WeatherSessionData } from '../types/f1';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

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
  }): Promise<any> => {
    const { data } = await api.get('/predictions/driver/', { params });
    return data;
  },

  // Constructor Prediction
  getConstructorPrediction: async (params: {
    team: string;
    circuit: string;
    year?: string;
  }): Promise<any> => {
    const { data } = await api.get('/predictions/constructor/', { params });
    return data;
  },

  // Available Options for Dropdowns
  getAvailableDrivers: async (): Promise<any> => {
    const { data } = await api.get('/options/drivers/');
    return data;
  },

  getAvailableTeams: async (): Promise<any> => {
    const { data } = await api.get('/options/teams/');
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
};

export default api;
