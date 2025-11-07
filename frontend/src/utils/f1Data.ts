/**
 * F1 2025 Teams and Drivers Data
 * Official colors and driver numbers
 */

export const TEAM_COLORS: Record<string, { primary: string; secondary?: string }> = {
  // Red Bull Racing
  'red_bull': { primary: '#3671C6', secondary: '#FF1E00' },
  'red bull racing': { primary: '#3671C6', secondary: '#FF1E00' },
  'red bull': { primary: '#3671C6', secondary: '#FF1E00' },

  // Ferrari
  'ferrari': { primary: '#E8002D', secondary: '#FFF500' },

  // Mercedes
  'mercedes': { primary: '#27F4D2', secondary: '#000000' },

  // McLaren
  'mclaren': { primary: '#FF8000', secondary: '#47C7FC' },

  // Aston Martin
  'aston_martin': { primary: '#229971', secondary: '#2D826D' },
  'aston martin': { primary: '#229971', secondary: '#2D826D' },

  // Alpine
  'alpine': { primary: '#FF87BC', secondary: '#2293D1' },

  // Williams
  'williams': { primary: '#64C4FF', secondary: '#041E42' },

  // RB (AlphaTauri/Racing Bulls)
  'rb': { primary: '#6692FF', secondary: '#1634CB' },
  'racing bulls': { primary: '#6692FF', secondary: '#1634CB' },
  'alphatauri': { primary: '#6692FF', secondary: '#1634CB' },

  // Kick Sauber (Alfa Romeo)
  'sauber': { primary: '#00E701', secondary: '#000000' },
  'kick sauber': { primary: '#00E701', secondary: '#000000' },
  'alfa romeo': { primary: '#00E701', secondary: '#000000' },

  // Haas
  'haas': { primary: '#B6BABD', secondary: '#ED1B24' },
  'haas f1 team': { primary: '#B6BABD', secondary: '#ED1B24' },
};

export const DRIVER_NUMBERS: Record<string, number> = {
  // Red Bull Racing
  'max verstappen': 1,
  'max': 1,
  'verstappen': 1,
  'ver': 1,
  'sergio perez': 11,
  'sergio pérez': 11,
  'perez': 11,
  'per': 11,

  // Ferrari
  'charles leclerc': 16,
  'leclerc': 16,
  'lec': 16,
  'carlos sainz': 55,
  'sainz': 55,
  'sai': 55,

  // Mercedes
  'lewis hamilton': 44,
  'hamilton': 44,
  'ham': 44,
  'george russell': 63,
  'russell': 63,
  'rus': 63,

  // McLaren
  'lando norris': 4,
  'norris': 4,
  'nor': 4,
  'oscar piastri': 81,
  'piastri': 81,
  'pia': 81,

  // Aston Martin
  'fernando alonso': 14,
  'alonso': 14,
  'alo': 14,
  'lance stroll': 18,
  'stroll': 18,
  'str': 18,

  // Alpine
  'pierre gasly': 10,
  'gasly': 10,
  'gas': 10,
  'esteban ocon': 31,
  'ocon': 31,
  'oco': 31,

  // Williams
  'alex albon': 23,
  'albon': 23,
  'alb': 23,
  'logan sargeant': 2,
  'sargeant': 2,
  'sar': 2,
  'franco colapinto': 43,
  'colapinto': 43,
  'col': 43,

  // RB
  'yuki tsunoda': 22,
  'tsunoda': 22,
  'tsu': 22,
  'daniel ricciardo': 3,
  'ricciardo': 3,
  'ric': 3,
  'liam lawson': 40,
  'lawson': 40,
  'law': 40,

  // Kick Sauber
  'valtteri bottas': 77,
  'bottas': 77,
  'bot': 77,
  'zhou guanyu': 24,
  'zhou': 24,
  'zho': 24,

  // Haas
  'kevin magnussen': 20,
  'magnussen': 20,
  'mag': 20,
  'nico hulkenberg': 27,
  'hulkenberg': 27,
  'hul': 27,
};

/**
 * Get team color by team name
 */
export function getTeamColor(teamName: string | undefined): string {
  if (!teamName) return '#888888';

  const normalizedName = teamName.toLowerCase().trim();
  const teamColor = TEAM_COLORS[normalizedName];

  return teamColor?.primary || '#888888';
}

/**
 * Get driver number by driver name or code
 */
export function getDriverNumber(driverName: string | undefined): number | null {
  if (!driverName) return null;

  const normalizedName = driverName.toLowerCase().trim();
  return DRIVER_NUMBERS[normalizedName] || null;
}
