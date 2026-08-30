import { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { f1Api } from '../services/api';
import LoadingWithRetry from '../components/LoadingWithRetry';
import { useChartConfig, useChartTheme } from '../hooks/useChartTheme';
import FilterDropdown, { DropdownOption } from '../components/FilterDropdown';
import '../components/FiltersContainer.css';
import './AnalyticsStandings.css'; // Reusing the same CSS
import Icon from '../components/Icon';

interface WeatherDataPoint {
  index: number;
  timestamp: string | null;
  airTemp: number | null;
  trackTemp: number | null;
  humidity: number | null;
  pressure: number | null;
  windSpeed: number | null;
  windDirection: number | null;
  rainfall: boolean;
}

interface WeatherStats {
  airTemp: { avg: number; min: number; max: number };
  trackTemp: { avg: number; min: number; max: number };
  humidity: { avg: number; min: number; max: number };
  rainfall: boolean;
}

interface SessionInfo {
  eventName: string;
  circuit: string;
  round: number;
  sessionType: string;
  date: string;
}

export default function AnalyticsWeather() {
  const chartConfig = useChartConfig();
  const chartColors = useChartTheme();

  const [year, setYear] = useState(new Date().getFullYear().toString());
  const [round, setRound] = useState('');
  const [sessionType, setSessionType] = useState('R');

  const [weatherData, setWeatherData] = useState<WeatherDataPoint[]>([]);
  const [stats, setStats] = useState<WeatherStats | null>(null);
  const [sessionInfo, setSessionInfo] = useState<SessionInfo | null>(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filter options
  const [yearOptions, setYearOptions] = useState<DropdownOption[]>([]);
  const [gpOptions, setGpOptions] = useState<DropdownOption[]>([]);
  const [sessionTypeOptions, setSessionTypeOptions] = useState<DropdownOption[]>([]);
  const [loadingOptions, setLoadingOptions] = useState(true);

  const [activeMetrics, setActiveMetrics] = useState({
    airTemp: true,
    trackTemp: true,
    humidity: false,
    pressure: false,
    windSpeed: false
  });

  // Load filter options on mount
  useEffect(() => {
    loadFilterOptions();
  }, []);

  // Load GPs when year changes (filtros hierárquicos)
  useEffect(() => {
    if (year) {
      loadDependentOptions(year);
    } else {
      setGpOptions([]);
      setRound('');
    }
  }, [year]);

  // Load weather data when filters change
  useEffect(() => {
    if (round && !loadingOptions) {
      loadWeatherData();
    }
  }, [year, round, sessionType, loadingOptions]);

  const loadFilterOptions = async () => {
    try {
      setLoadingOptions(true);
      const [yearsData, options] = await Promise.all([
        f1Api.getAvailableYears(),
        f1Api.getFilterOptions()
      ]);

      // Set year options
      const years = (yearsData.years || []).map((y: number) => ({
        value: y.toString(),
        label: y.toString(),
      }));
      setYearOptions(years);

      // Set session type options (não depende do ano)
      setSessionTypeOptions(options.sessionTypes);
    } catch (err) {
      console.error('Error loading filter options:', err);
    } finally {
      setLoadingOptions(false);
    }
  };

  const loadDependentOptions = async (selectedYear: string) => {
    try {
      // Resetar round quando ano mudar
      setRound('');

      // Carregar GPs do ano selecionado
      const gps = await f1Api.getGrandsPrix(selectedYear);

      // Map GPs (sem índice, apenas nome)
      const gpOpts = gps.map((gp: any) => ({
        value: gp.round.toString(),
        label: gp.name, // Apenas nome, sem índice
      }));
      setGpOptions(gpOpts);
    } catch (err) {
      console.error('Error loading GPs:', err);
      setGpOptions([]);
    }
  };

  const loadWeatherData = async () => {
    try {
      setLoading(true);
      setError(null);

      const data = await f1Api.getWeatherAnalytics({
        year,
        round,
        session_type: sessionType
      });

      setWeatherData(data.data);
      setStats(data.stats);
      setSessionInfo(data.sessionInfo);
    } catch (err: any) {
      setError(err.message || 'Erro ao carregar dados meteorológicos');
      console.error('Error loading weather data:', err);
    } finally {
      setLoading(false);
    }
  };

  const toggleMetric = (metric: keyof typeof activeMetrics) => {
    setActiveMetrics(prev => ({
      ...prev,
      [metric]: !prev[metric]
    }));
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="custom-tooltip">
          <p className="tooltip-title">Ponto #{label}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} style={{ color: entry.color }}>
              {entry.name}: {entry.value?.toFixed(1)} {getUnit(entry.dataKey)}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  const getUnit = (metric: string): string => {
    switch (metric) {
      case 'airTemp':
      case 'trackTemp':
        return '°C';
      case 'humidity':
        return '%';
      case 'pressure':
        return 'mbar';
      case 'windSpeed':
        return 'km/h';
      default:
        return '';
    }
  };

  const getMetricLabel = (metric: string): string => {
    const labels: Record<string, string> = {
      airTemp: 'Temp. do Ar',
      trackTemp: 'Temp. da Pista',
      humidity: 'Umidade',
      pressure: 'Pressão',
      windSpeed: 'Vel. do Vento'
    };
    return labels[metric] || metric;
  };

  if (loading && weatherData.length === 0) {
    return (
      <div className="analytics-page">
        <LoadingWithRetry
          message="Carregando dados meteorológicos"
          hint="Processando informações do clima..."
        />
      </div>
    );
  }

  return (
    <div className="analytics-page">
      <div className="analytics-header">
        <h1><Icon name="weather" size={16} /> Análise Meteorológica</h1>
        <p className="analytics-subtitle">
          Acompanhe as condições climáticas durante as sessões
        </p>
      </div>

      {/* Filters */}
      <div className="filters-row">
        <FilterDropdown
          label="Ano"
          value={year}
          options={yearOptions}
          onChange={setYear}
          placeholder="Selecione o ano"
          icon="calendar"
          disabled={loadingOptions}
        />
        <FilterDropdown
          label="GP"
          value={round}
          options={gpOptions}
          onChange={setRound}
          placeholder={year ? "Selecione o GP" : "Selecione um ano primeiro"}
          icon="flag"
          disabled={!year}
        />
        <FilterDropdown
          label="Tipo de Sessão"
          value={sessionType}
          options={sessionTypeOptions}
          onChange={setSessionType}
          placeholder="Selecione a sessão"
          icon="car"
          disabled={loadingOptions}
        />
      </div>

      {/* Session Info */}
      {sessionInfo && (
        <div className="selection-container">
          <h3><Icon name="pin" size={16} /> {sessionInfo.eventName} - {sessionInfo.circuit}</h3>
          <p style={{ color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
            Round {sessionInfo.round} • {sessionInfo.date} • Sessão: {sessionInfo.sessionType}
          </p>
        </div>
      )}

      {/* Stats Cards */}
      {stats && (
        <div className="stats-grid">
          <div className="stat-card">
            <h4><Icon name="thermometer" size={16} /> Temperatura do Ar</h4>
            <div className="stat-value">{stats.airTemp.avg.toFixed(1)}°C</div>
            <div className="stat-range">
              Min: {stats.airTemp.min.toFixed(1)}°C • Max: {stats.airTemp.max.toFixed(1)}°C
            </div>
          </div>
          <div className="stat-card">
            <h4><Icon name="flag" size={16} /> Temperatura da Pista</h4>
            <div className="stat-value">{stats.trackTemp.avg.toFixed(1)}°C</div>
            <div className="stat-range">
              Min: {stats.trackTemp.min.toFixed(1)}°C • Max: {stats.trackTemp.max.toFixed(1)}°C
            </div>
          </div>
          <div className="stat-card">
            <h4><Icon name="droplet" size={16} /> Umidade</h4>
            <div className="stat-value">{stats.humidity.avg.toFixed(1)}%</div>
            <div className="stat-range">
              Min: {stats.humidity.min.toFixed(1)}% • Max: {stats.humidity.max.toFixed(1)}%
            </div>
          </div>
          <div className="stat-card">
            <h4><Icon name="rain" size={16} /> Chuva</h4>
            <div className="stat-value">{stats.rainfall ? 'Sim' : 'Não'}</div>
            <div className="stat-range">
              {stats.rainfall ? 'Houve precipitação' : 'Sessão seca'}
            </div>
          </div>
        </div>
      )}

      {/* Metric Selection */}
      {weatherData.length > 0 && (
        <div className="selection-container">
          <h3>Selecione as Métricas para Visualizar</h3>
          <div className="selection-grid">
            {Object.keys(activeMetrics).map((metric) => (
              <button
                key={metric}
                className={`selection-item ${activeMetrics[metric as keyof typeof activeMetrics] ? 'selected' : ''}`}
                onClick={() => toggleMetric(metric as keyof typeof activeMetrics)}
              >
                <span className="selection-name">{getMetricLabel(metric)}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Chart */}
      {error && (
        <div className="error-message">
          <p>{error}</p>
        </div>
      )}

      {!error && weatherData.length > 0 && (
        <div className="chart-container">
          <ResponsiveContainer width="100%" height={500}>
            <LineChart data={weatherData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
              <CartesianGrid {...chartConfig.cartesianGrid} />
              <XAxis
                dataKey="index"
                {...chartConfig.xAxis}
                label={{ value: 'Ponto de Medição', position: 'insideBottom', offset: -10, ...chartConfig.xAxis.label }}
              />
              <YAxis
                {...chartConfig.yAxis}
                label={{ value: 'Valor', angle: -90, position: 'insideLeft', ...chartConfig.yAxis.label }}
              />
              <Tooltip content={<CustomTooltip />} {...chartConfig.tooltip} />
              <Legend {...chartConfig.legend} />

              {activeMetrics.airTemp && (
                <Line
                  type="monotone"
                  dataKey="airTemp"
                  name="Temp. do Ar (°C)"
                  stroke={chartColors.accentRed}
                  {...chartConfig.line}
                  dot={false}
                />
              )}
              {activeMetrics.trackTemp && (
                <Line
                  type="monotone"
                  dataKey="trackTemp"
                  name="Temp. da Pista (°C)"
                  stroke="#FFA500"
                  {...chartConfig.line}
                  dot={false}
                />
              )}
              {activeMetrics.humidity && (
                <Line
                  type="monotone"
                  dataKey="humidity"
                  name="Umidade (%)"
                  stroke="#4ECDC4"
                  {...chartConfig.line}
                  dot={false}
                />
              )}
              {activeMetrics.pressure && (
                <Line
                  type="monotone"
                  dataKey="pressure"
                  name="Pressão (mbar)"
                  stroke="#95E1D3"
                  {...chartConfig.line}
                  dot={false}
                />
              )}
              {activeMetrics.windSpeed && (
                <Line
                  type="monotone"
                  dataKey="windSpeed"
                  name="Vel. Vento (km/h)"
                  stroke={chartColors.accentPurple}
                  {...chartConfig.line}
                  dot={false}
                />
              )}
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {!error && weatherData.length === 0 && !loading && (
        <div className="no-data">
          <p>Selecione um ano e round para visualizar os dados meteorológicos</p>
        </div>
      )}
    </div>
  );
}
