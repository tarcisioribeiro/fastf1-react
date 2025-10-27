export interface Driver {
  id: number
  position: number
  driver_name: string
  team: string
  points: number
  wins?: number
}

export interface Constructor {
  id: number
  position: number
  team_name: string
  points: number
  wins?: number
}

export interface RaceResult {
  id: number
  position: number
  driver_name: string
  team: string
  time: string
  points: number
  status: string
}

export interface Race {
  id: number
  round: number
  race_name: string
  date: string
  country: string
}

export interface ApiResponse<T> {
  data: T
  message?: string
}
