/**
 * Utilitários de formatação para dados da F1
 */

/**
 * Formata o nome do piloto com número (se disponível)
 */
export function formatDriverName(driver: {
  driver?: string;
  name?: string;
  driver_name?: string;
  driver_number?: number;
}): string {
  const name = driver.driver_name || driver.name || driver.driver || 'Desconhecido';

  if (driver.driver_number) {
    return `${driver.driver_number} ${name}`;
  }

  return name;
}

/**
 * Formata o nome da equipe
 */
export function formatTeamName(team: {
  team?: string;
  team_name?: string;
}): string {
  return team.team_name || team.team || 'Desconhecida';
}

/**
 * Formata tempo de corrida/qualificação
 */
export function formatTime(time?: string | null): string {
  if (!time || time === '' || time === 'null' || time === 'undefined') {
    return '-';
  }
  return time;
}

/**
 * Calcula se uma cor é clara ou escura (para determinar contraste)
 * @param color Cor em formato hex (#RRGGBB)
 * @returns true se a cor for clara, false se for escura
 */
export function isLightColor(color: string): boolean {
  if (!color || !color.startsWith('#')) {
    return false;
  }

  // Remove o # e converte para RGB
  const hex = color.replace('#', '');
  const r = parseInt(hex.substr(0, 2), 16);
  const g = parseInt(hex.substr(2, 2), 16);
  const b = parseInt(hex.substr(4, 2), 16);

  // Calcula a luminância relativa (fórmula WCAG)
  // https://www.w3.org/TR/WCAG20/#relativeluminancedef
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;

  // Se luminância > 0.5, a cor é clara
  return luminance > 0.5;
}

/**
 * Retorna a cor de texto adequada para uma cor de fundo
 * @param backgroundColor Cor de fundo em formato hex
 * @returns '#000000' para fundos claros, '#FFFFFF' para fundos escuros
 */
export function getContrastColor(backgroundColor: string): string {
  return isLightColor(backgroundColor) ? '#000000' : '#FFFFFF';
}

/**
 * Formata o status de forma visual para exibição
 * @param status Status do piloto
 * @param translatedStatus Status já traduzido
 * @returns Objeto com status formatado e classe CSS
 */
export function formatStatusDisplay(status: string, translatedStatus: string): {
  display: string;
  className: string;
} {
  if (status === 'Finished' || translatedStatus === 'Completou') {
    return {
      display: 'Completou',
      className: 'status-finished'
    };
  }
  return {
    display: translatedStatus,
    className: 'status-dnf'
  };
}
