import axios from 'axios'
import type { Driver, Constructor, RaceResult, Race, ApiResponse } from '../types'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: `${API_URL}/api`,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

export const f1Api = {
  // Driver Standings
  getDriverStandings: async (year: number = 2025): Promise<Driver[]> => {
    const response = await api.get<ApiResponse<Driver[]>>(`/drivers/standings/${year}/`)
    return response.data.data
  },

  // Constructor Standings
  getConstructorStandings: async (year: number = 2025): Promise<Constructor[]> => {
    const response = await api.get<ApiResponse<Constructor[]>>(`/constructors/standings/${year}/`)
    return response.data.data
  },

  // Race Results
  getRaceResults: async (year: number = 2025, round?: number): Promise<RaceResult[]> => {
    const url = round
      ? `/races/${year}/${round}/results/`
      : `/races/${year}/latest/results/`
    const response = await api.get<ApiResponse<RaceResult[]>>(url)
    return response.data.data
  },

  // Get All Races
  getRaces: async (year: number = 2025): Promise<Race[]> => {
    const response = await api.get<ApiResponse<Race[]>>(`/races/${year}/`)
    return response.data.data
  },

  // Trigger data collection
  triggerDataCollection: async () => {
    const response = await api.post('/data-collection/trigger/')
    return response.data
  },

  // Health check
  healthCheck: async () => {
    const response = await api.get('/health/')
    return response.data
  }
}

export default api
