export interface Driver {
  position: number;
  name: string;
  team: string;
  points: number;
  wins: number;
  teamColor?: string;
}

export interface Constructor {
  position: number;
  team: string;
  points: number;
  wins: number;
  teamColor?: string;
}

export interface RaceResult {
  position: number;
  driver: string;
  team: string;
  time: string;
  points: number;
  teamColor?: string;
}

export interface QualifyingResult {
  position: number;
  driver: string;
  team: string;
  q1?: string;
  q2?: string;
  q3?: string;
  teamColor?: string;
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
