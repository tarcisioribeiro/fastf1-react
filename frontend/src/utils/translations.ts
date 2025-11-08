/**
 * Traduções e formatações de dados da F1
 */

/**
 * Traduz status de classificação do piloto
 */
export const translateDriverStatus = (status: string | number): string => {
  // Se for número, retorna a posição
  if (typeof status === 'number') {
    return `${status}º`;
  }

  // Se for string numérica, converte e formata
  const numStatus = parseInt(status);
  if (!isNaN(numStatus)) {
    return `${numStatus}º`;
  }

  // Traduções de status
  const statusMap: Record<string, string> = {
    // Resultados de corrida
    'Finished': 'Completou',
    'Completed': 'Completou',
    'Finished+1Lap': '+1 Volta',
    'Finished+2Laps': '+2 Voltas',
    'Finished+3Laps': '+3 Voltas',
    'Lapped': 'Com volta(s) a menos',
    '+1 Lap': '+1 Volta',
    '+2 Laps': '+2 Voltas',
    '+3 Laps': '+3 Voltas',
    '+4 Laps': '+4 Voltas',
    '+5 Laps': '+5 Voltas',

    // Status de não finalização
    'R': 'Abandonou',
    'Retired': 'Abandonou',
    'D': 'Desclassificado',
    'Disqualified': 'Desclassificado',
    'E': 'Excluído',
    'Excluded': 'Excluído',
    'W': 'Retirado',
    'Withdrawn': 'Retirado',
    'F': 'Não se classificou',
    'Failed to qualify': 'Não se classificou',
    'N': 'Não classificado',
    'Not classified': 'Não classificado',

    // Status de DNF (Did Not Finish)
    'Accident': 'Acidente',
    'Collision': 'Colisão',
    'Engine': 'Motor',
    'Gearbox': 'Câmbio',
    'Transmission': 'Transmissão',
    'Clutch': 'Embreagem',
    'Hydraulics': 'Hidráulica',
    'Electrical': 'Elétrico',
    'Power Unit': 'Unidade de Potência',
    'Spun off': 'Rodou',
    'Damage': 'Avaria',
    'Brakes': 'Freios',
    'Suspension': 'Suspensão',
    'Wheel': 'Roda',
    'Puncture': 'Furo',
    'Radiator': 'Radiador',
    'Overheating': 'Superaquecimento',
    'Fire': 'Incêndio',
    'Fuel pressure': 'Pressão de combustível',
    'Fuel system': 'Sistema de combustível',
    'Oil pressure': 'Pressão de óleo',
    'Throttle': 'Acelerador',
    'Steering': 'Direção',
    'Technical': 'Problema técnico',
    'Oil leak': 'Vazamento de óleo',
    'Drivetrain': 'Trem de força',
    'ERS': 'ERS',
    'Electronics': 'Eletrônica',
    'Exhaust': 'Escapamento',
    'Vibrations': 'Vibrações',
    'Driveshaft': 'Eixo de transmissão',
    'Rear wing': 'Asa traseira',
    'Front wing': 'Asa dianteira',
    'Water pressure': 'Pressão da água',
    'Safety': 'Segurança',
    'Did not start': 'Não largou',
    'DNS': 'Não largou',
    'DNF': 'Não terminou',
    'DNQ': 'Não se classificou',
    'DSQ': 'Desclassificado',
    'NC': 'Não classificado',
    'Illness': 'Doença',
  };

  // Retorna tradução ou status original
  return statusMap[status] || status;
};

/**
 * Traduz compound de pneu
 */
export const translateTyreCompound = (compound: string): string => {
  const compoundMap: Record<string, string> = {
    'SOFT': 'Macio',
    'MEDIUM': 'Médio',
    'HARD': 'Duro',
    'INTERMEDIATE': 'Intermediário',
    'WET': 'Chuva',
    'UNKNOWN': 'Desconhecido',
    'TEST_UNKNOWN': 'Teste',
  };

  return compoundMap[compound?.toUpperCase()] || compound;
};

/**
 * Traduz tipo de sessão
 */
export const translateSessionType = (sessionType: string): string => {
  const sessionMap: Record<string, string> = {
    'R': 'Corrida',
    'Race': 'Corrida',
    'Q': 'Classificação',
    'Qualifying': 'Classificação',
    'S': 'Sprint',
    'Sprint': 'Sprint',
    'FP1': 'Treino Livre 1',
    'FP2': 'Treino Livre 2',
    'FP3': 'Treino Livre 3',
    'Practice 1': 'Treino Livre 1',
    'Practice 2': 'Treino Livre 2',
    'Practice 3': 'Treino Livre 3',
  };

  return sessionMap[sessionType] || sessionType;
};

/**
 * Traduz status da pista
 */
export const translateTrackStatus = (status: number | string): string => {
  const statusMap: Record<string, string> = {
    '1': 'Pista Livre',
    '2': 'Bandeira Amarela',
    '3': 'Bandeira Verde',
    '4': 'Bandeira Vermelha',
    '5': 'Safety Car',
    '6': 'Virtual Safety Car',
    '7': 'VSC Encerrando',
  };

  return statusMap[String(status)] || `Status ${status}`;
};

/**
 * Formata tempo de volta
 */
export const formatLapTime = (seconds: number | null): string => {
  if (seconds === null || seconds === undefined || isNaN(seconds)) {
    return '--:--:---';
  }

  const minutes = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  const millis = Math.floor((seconds % 1) * 1000);

  return `${minutes}:${secs.toString().padStart(2, '0')}.${millis.toString().padStart(3, '0')}`;
};

/**
 * Formata duração em segundos
 */
export const formatDuration = (seconds: number | null): string => {
  if (seconds === null || seconds === undefined || isNaN(seconds)) {
    return '--';
  }

  return `${seconds.toFixed(3)}s`;
};
