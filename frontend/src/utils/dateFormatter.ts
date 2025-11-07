/**
 * Formata uma data para o formato brasileiro (DD/MM/YYYY)
 */
export function formatDateBR(date: string | Date): string {
  const dateObj = typeof date === 'string' ? new Date(date) : date;

  return dateObj.toLocaleDateString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  });
}

/**
 * Formata uma data com hora para o formato brasileiro (DD/MM/YYYY HH:mm)
 */
export function formatDateTimeBR(date: string | Date): string {
  const dateObj = typeof date === 'string' ? new Date(date) : date;

  return dateObj.toLocaleString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * Formata apenas a hora (HH:mm:ss)
 */
export function formatTime(time: string): string {
  if (!time) return '-';

  // Se já está formatado (tem +), retorna direto
  if (time.includes('+')) return time;

  // Se é um horário no formato HH:mm:ss.SSS
  if (time.match(/^\d{1,2}:\d{2}:\d{2}/)) {
    return time;
  }

  return time;
}

/**
 * Formata um tempo de lap (ex: "1:23.456")
 */
export function formatLapTime(seconds: number): string {
  const minutes = Math.floor(seconds / 60);
  const secs = (seconds % 60).toFixed(3);
  return `${minutes}:${secs.padStart(6, '0')}`;
}

/**
 * Formata data de forma relativa (ex: "há 2 dias")
 */
export function formatRelativeDate(date: string | Date): string {
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  const now = new Date();
  const diffMs = now.getTime() - dateObj.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffDays === 0) return 'Hoje';
  if (diffDays === 1) return 'Ontem';
  if (diffDays < 7) return `Há ${diffDays} dias`;
  if (diffDays < 30) return `Há ${Math.floor(diffDays / 7)} semanas`;
  if (diffDays < 365) return `Há ${Math.floor(diffDays / 30)} meses`;
  return `Há ${Math.floor(diffDays / 365)} anos`;
}

/**
 * Formata data para exibição em card (ex: "25 de Outubro de 2025")
 */
export function formatDateLongBR(date: string | Date): string {
  const dateObj = typeof date === 'string' ? new Date(date) : date;

  return dateObj.toLocaleDateString('pt-BR', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  });
}
