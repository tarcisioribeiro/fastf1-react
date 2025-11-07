import { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { f1Api } from '../services/api';
import LoadingWithRetry from '../components/LoadingWithRetry';
import './AnalyticsStandings.css'; // Reusing the same CSS

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
  const [year, setYear] = useState(new Date().getFullYear().toString());
  const [round, setRound] = useState('');
  const [sessionType, setSessionType] = useState('R');

  const [weatherData, setWeatherData] = useState<WeatherDataPoint[]>([]);
  const [stats, setStats] = useState<WeatherStats | null>(null);
  const [sessionInfo, setSessionInfo] = useState<SessionInfo | null>(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [activeMetrics, setActiveMetrics] = useState({
    airTemp: true,
    trackTemp: true,
    humidity: false,
    pressure: false,
    windSpeed: false
  });

  useEffect(() => {
    if (round) {
      loadWeatherData();
    }
  }, [year, round, sessionType]);

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
        <h1>🌤️ Análise Meteorológica</h1>
        <p className="analytics-subtitle">
          Acompanhe as condições climáticas durante as sessões
        </p>
      </div>

      {/* Filters */}
      <div className="analytics-filters">
        <div className="filter-group">
          <label>Ano</label>
          <input
            type="number"
            value={year}
            onChange={(e) => setYear(e.target.value)}
            className="filter-input"
            min="2022"
            max={new Date().getFullYear()}
          />
        </div>
        <div className="filter-group">
          <label>Round</label>
          <input
            type="number"
            value={round}
            onChange={(e) => setRound(e.target.value)}
            className="filter-input"
            min="1"
            placeholder="Ex: 1"
          />
        </div>
        <div className="filter-group">
          <label>Tipo de Sessão</label>
          <select
            value={sessionType}
            onChange={(e) => setSessionType(e.target.value)}
            className="filter-input"
          >
            <option value="R">Corrida</option>
            <option value="Q">Qualifying</option>
            <option value="S">Sprint</option>
            <option value="FP1">Treino Livre 1</option>
            <option value="FP2">Treino Livre 2</option>
            <option value="FP3">Treino Livre 3</option>
          </select>
        </div>
      </div>

      {/* Session Info */}
      {sessionInfo && (
        <div className="selection-container">
          <h3>📍 {sessionInfo.eventName} - {sessionInfo.circuit}</h3>
          <p style={{ color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
            Round {sessionInfo.round} • {sessionInfo.date} • Sessão: {sessionInfo.sessionType}
          </p>
        </div>
      )}

      {/* Stats Cards */}
      {stats && (
        <div className="stats-grid">
          <div className="stat-card">
            <h4>🌡️ Temperatura do Ar</h4>
            <div className="stat-value">{stats.airTemp.avg.toFixed(1)}°C</div>
            <div className="stat-range">
              Min: {stats.airTemp.min.toFixed(1)}°C • Max: {stats.airTemp.max.toFixed(1)}°C
            </div>
          </div>
          <div className="stat-card">
            <h4>🏁 Temperatura da Pista</h4>
            <div className="stat-value">{stats.trackTemp.avg.toFixed(1)}°C</div>
            <div className="stat-range">
              Min: {stats.trackTemp.min.toFixed(1)}°C • Max: {stats.trackTemp.max.toFixed(1)}°C
            </div>
          </div>
          <div className="stat-card">
            <h4>💧 Umidade</h4>
            <div className="stat-value">{stats.humidity.avg.toFixed(1)}%</div>
            <div className="stat-range">
              Min: {stats.humidity.min.toFixed(1)}% • Max: {stats.humidity.max.toFixed(1)}%
            </div>
          </div>
          <div className="stat-card">
            <h4>🌧️ Chuva</h4>
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
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
              <XAxis
                dataKey="index"
                stroke="var(--text-secondary)"
                label={{ value: 'Ponto de Medição', position: 'insideBottom', offset: -10, fill: 'var(--text-secondary)' }}
              />
              <YAxis
                stroke="var(--text-secondary)"
                label={{ value: 'Valor', angle: -90, position: 'insideLeft', fill: 'var(--text-secondary)' }}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend wrapperStyle={{ color: 'var(--text-primary)' }} />

              {activeMetrics.airTemp && (
                <Line
                  type="monotone"
                  dataKey="airTemp"
                  name="Temp. do Ar (°C)"
                  stroke="#FF6B6B"
                  strokeWidth={2}
                  dot={false}
                />
              )}
              {activeMetrics.trackTemp && (
                <Line
                  type="monotone"
                  dataKey="trackTemp"
                  name="Temp. da Pista (°C)"
                  stroke="#FFA500"
                  strokeWidth={2}
                  dot={false}
                />
              )}
              {activeMetrics.humidity && (
                <Line
                  type="monotone"
                  dataKey="humidity"
                  name="Umidade (%)"
                  stroke="#4ECDC4"
                  strokeWidth={2}
                  dot={false}
                />
              )}
              {activeMetrics.pressure && (
                <Line
                  type="monotone"
                  dataKey="pressure"
                  name="Pressão (mbar)"
                  stroke="#95E1D3"
                  strokeWidth={2}
                  dot={false}
                />
              )}
              {activeMetrics.windSpeed && (
                <Line
                  type="monotone"
                  dataKey="windSpeed"
                  name="Vel. Vento (km/h)"
                  stroke="#AA96DA"
                  strokeWidth={2}
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
