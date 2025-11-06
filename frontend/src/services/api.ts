import axios, { AxiosError, AxiosRequestConfig } from 'axios';
import { Driver, Constructor, SessionData, QualifyingData } from '../types/f1';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

// Configuração de retry
const MAX_RETRIES = 10;
const INITIAL_RETRY_DELAY = 1000; // 1 segundo
const MAX_RETRY_DELAY = 30000; // 30 segundos

const api = axios.create({
  baseURL: API_URL,
  timeout: 120000, // 2 minutos - FastF1 pode demorar para processar dados
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

  // Retry em erro 404 se for endpoint de dados (podem ainda não estar disponíveis)
  if (error.response.status === 404) {
    const url = error.config?.url || '';
    if (url.includes('/latest') || url.includes('/standings')) {
      return true;
    }
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
    const { data } = await api.get('/drivers/standings');
    return data;
  },

  // Constructor Standings
  getConstructorStandings: async (): Promise<Constructor[]> => {
    const { data } = await api.get('/constructors/standings');
    return data;
  },

  // Latest Race
  getLatestRace: async (): Promise<SessionData> => {
    const { data } = await api.get('/races/latest');
    return data;
  },

  // Latest Qualifying
  getLatestQualifying: async (): Promise<QualifyingData> => {
    const { data } = await api.get('/qualifying/latest');
    return data;
  },
};

export default api;
