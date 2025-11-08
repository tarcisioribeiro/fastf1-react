import { useMemo } from 'react';
import { useTheme } from '../contexts/ThemeContext';

/**
 * Hook para obter as cores dos gráficos de acordo com o tema atual
 */
export const useChartTheme = () => {
  const { theme } = useTheme();

  const chartColors = useMemo(() => {
    const isDark = theme === 'dark';

    return {
      // Grid e bordas
      gridColor: isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)',
      borderColor: isDark ? '#38383F' : '#E5E5EA',

      // Texto
      textPrimary: isDark ? '#FAFAFA' : '#1C1C1E',
      textSecondary: isDark ? '#B8B8B8' : '#636366',

      // Background
      tooltipBg: isDark ? '#252530' : '#FFFFFF',

      // Eixos
      axisStroke: isDark ? '#B8B8B8' : '#636366',

      // Cores de destaque
      accentRed: '#E10600',
      accentMagenta: '#D946EF',
      accentPurple: '#9333EA',

      // Opacidades para áreas
      areaOpacity: isDark ? 0.3 : 0.2,
      hoverOpacity: isDark ? 0.5 : 0.4,
    };
  }, [theme]);

  return chartColors;
};

/**
 * Configurações padrão para gráficos Recharts
 */
export const useChartConfig = () => {
  const colors = useChartTheme();
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  return {
    cartesianGrid: {
      strokeDasharray: '3 3',
      stroke: colors.gridColor,
      strokeOpacity: 0.5,
    },
    xAxis: {
      stroke: colors.axisStroke,
      tick: { fill: colors.textSecondary, fontSize: 12, fontFamily: 'Rajdhani, sans-serif', fontWeight: 600 },
      label: { fill: colors.textSecondary, fontSize: 14, fontFamily: 'Exo 2, sans-serif', fontWeight: 600 },
    },
    yAxis: {
      stroke: colors.axisStroke,
      tick: { fill: colors.textSecondary, fontSize: 12, fontFamily: 'Rajdhani, sans-serif', fontWeight: 600 },
      label: { fill: colors.textSecondary, fontSize: 14, fontFamily: 'Exo 2, sans-serif', fontWeight: 600 },
    },
    tooltip: {
      contentStyle: {
        backgroundColor: colors.tooltipBg,
        border: `2px solid ${colors.accentRed}`,
        borderRadius: '8px',
        padding: '16px',
        boxShadow: isDark
          ? '0 8px 32px rgba(0, 0, 0, 0.6), 0 0 0 1px rgba(255, 255, 255, 0.1)'
          : '0 8px 32px rgba(0, 0, 0, 0.25)',
        minWidth: '200px',
        zIndex: 9999,
      },
      labelStyle: {
        color: colors.textPrimary,
        fontWeight: 700,
        marginBottom: '12px',
        fontFamily: 'Exo 2, sans-serif',
        fontSize: '14px',
        borderBottom: `1px solid ${colors.borderColor}`,
        paddingBottom: '8px',
      },
      itemStyle: {
        color: colors.textPrimary,
        fontFamily: 'Rajdhani, sans-serif',
        fontWeight: 600,
        fontSize: '13px',
        padding: '4px 0',
      },
      wrapperStyle: {
        zIndex: 9999,
        pointerEvents: 'none',
      },
    },
    legend: {
      wrapperStyle: {
        color: colors.textPrimary,
        fontFamily: 'Rajdhani, sans-serif',
        fontWeight: 600,
      },
    },
    line: {
      strokeWidth: 3,
      strokeOpacity: 0.9,
      dot: { r: 4, strokeWidth: 2, fill: 'white' },
      activeDot: { r: 8, strokeWidth: 3, fill: 'white' },
    },
    area: {
      strokeWidth: 2.5,
      fillOpacity: colors.areaOpacity,
    },
    bar: {
      radius: [4, 4, 0, 0] as [number, number, number, number],
    },
  };
};
