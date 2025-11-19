export interface Driver {
  position: number;
  name: string;
  driver_number?: number;
  team: string;
  points: number;
  wins: number;
  podiums?: number;
  teamColor?: string;
}

export interface Constructor {
  position: number;
  team: string;
  points: number;
  wins: number;
  podiums?: number;
  teamColor?: string;
}

export interface RaceResult {
  position: number;
  driver: string;
  driver_code: string;
  driver_number?: number;
  team: string;
  teamColor: string;
  time: string;
  points: number;
  status: string;
}

export interface QualifyingResult {
  position: number;
  driver: string;
  driver_code: string;
  driver_number?: number;
  team: string;
  teamColor: string;
  q1?: string;
  q2?: string;
  q3?: string;
}

export interface SprintResult {
  position: number;
  driver: string;
  driver_code: string;
  driver_number?: number;
  driver_name?: string;
  team: string;
  team_name?: string;
  teamColor?: string;
  team_color?: string;
  time?: string;
  total_sprint_time?: string;
  points: number;
  status?: string;
}

export interface PitStop {
  id: number;
  driver: string;
  driver_code: string;
  team: string;
  stop_number: number;
  lap: number;
  duration: string;
}

export interface WeatherData {
  id: number;
  timestamp: string;
  air_temp: number;
  track_temp: number;
  humidity: number;
  pressure: number;
  rainfall: boolean;
  wind_speed?: number;
  wind_direction?: number;
}

export interface RaceInfo {
  eventName: string;
  location: string;
  date: string;
  round: number;
}

export interface SessionData {
  raceInfo: RaceInfo;
  results: RaceResult[];
}

export interface QualifyingData {
  raceInfo: RaceInfo;
  results: QualifyingResult[];
}

export interface SprintData {
  raceInfo: RaceInfo;
  results: SprintResult[];
}

export interface PitStopData {
  raceInfo: RaceInfo;
  pitStops: PitStop[];
}

export interface WeatherSessionData {
  raceInfo: RaceInfo;
  weatherData: WeatherData[];
}

export interface Circuit {
  id: number;
  circuit_id: string;
  name: string;
  location: string;
  country: string;
  latitude?: number;
  longitude?: number;
  length_km?: number;
  number_of_corners?: number;
  number_of_laps?: number;
  race_distance_km?: number;
  lap_record?: string;
  lap_record_formatted?: string;
  lap_record_driver?: string;
  lap_record_year?: number;
  first_grand_prix?: number;
  total_races_held?: number;
  circuit_type?: string;
  direction?: string;
  history?: string;
  description?: string;
  layout_id?: string;
  svg_url?: string;
  svg_url_black?: string;
  svg_url_white?: string;
  svg_url_black_outline?: string;
  svg_url_white_outline?: string;
}
