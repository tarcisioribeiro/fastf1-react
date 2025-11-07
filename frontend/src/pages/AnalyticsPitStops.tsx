import { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ScatterChart, Scatter } from 'recharts';
import { f1Api } from '../services/api';
import LoadingWithRetry from '../components/LoadingWithRetry';
import './AnalyticsStandings.css';

interface PitStop {
  lap: number;
  driver: string;
  team: string;
  duration: number | null;
  stopNumber: number;
}

interface SessionData {
  sessionId: number;
  eventName: string;
  round: number;
  pit_stops: PitStop[];
}

interface TeamStats {
  team: string;
  color: string;
  total_stops: number;
  avg_duration: number;
  min_duration: number;
  max_duration: number;
}

interface DriverStats {
  driver: string;
  total_stops: number;
  avg_duration: number;
  min_duration: number;
  max_duration: number;
}

interface AnalyticsData {
  sessions: SessionData[];
  team_stats: TeamStats[];
  driver_stats: DriverStats[];
}

export default function AnalyticsPitStops() {
  const [year, setYear] = useState(new Date().getFullYear().toString());
  const [round, setRound] = useState('');
  const [teamFilter, setTeamFilter] = useState('');
  const [viewMode, setViewMode] = useState<'teams' | 'drivers'>('teams');

  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (year) {
      loadPitStopsData();
    }
  }, [year, round, teamFilter]);

  const loadPitStopsData = async () => {
    try {
      setLoading(true);
      setError(null);

      const params: any = { year };
      if (round) params.round = round;
      if (teamFilter) params.team = teamFilter;

      const data = await f1Api.getPitStopsAnalytics(params);
      setAnalyticsData(data.data);
    } catch (err: any) {
      setError(err.message || 'Erro ao carregar dados de pit stops');
      console.error('Error loading pit stops data:', err);
    } finally {
      setLoading(false);
    }
  };

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="custom-tooltip">
          <p className="tooltip-title">{viewMode === 'teams' ? data.team : data.driver}</p>
          <p style={{ color: payload[0].color }}>
            Média: {data.avg_duration?.toFixed(2)}s
          </p>
          {data.min_duration !== undefined && (
            <p style={{ color: '#4ECDC4' }}>
              Mínimo: {data.min_duration?.toFixed(2)}s
            </p>
          )}
          {data.max_duration !== undefined && (
            <p style={{ color: '#FF6B6B' }}>
              Máximo: {data.max_duration?.toFixed(2)}s
            </p>
          )}
          <p style={{ color: 'var(--text-secondary)' }}>
            Total de Stops: {data.total_stops}
          </p>
        </div>
      );
    }
    return null;
  };

  if (loading && !analyticsData) {
    return (
      <div className="analytics-page">
        <LoadingWithRetry
          message="Carregando dados de pit stops"
          hint="Processando estratégias de parada..."
        />
      </div>
    );
  }

  // Prepare chart data
  const chartData = viewMode === 'teams'
    ? analyticsData?.team_stats.sort((a, b) => a.avg_duration - b.avg_duration) || []
    : analyticsData?.driver_stats.sort((a, b) => a.avg_duration - b.avg_duration).slice(0, 15) || [];

  // Prepare scatter data for lap vs duration
  const scatterData = analyticsData?.sessions.flatMap(session =>
    session.pit_stops
      .filter(stop => stop.duration !== null)
      .map(stop => ({
        lap: stop.lap,
        duration: stop.duration,
        driver: stop.driver,
        team: stop.team
      }))
  ) || [];

  return (
    <div className="analytics-page">
      <div className="analytics-header">
        <h1>⛽ Análise de Pit Stops</h1>
        <p className="analytics-subtitle">
          Compare estratégias e tempos de parada das equipes
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
          <label>Round (opcional)</label>
          <input
            type="number"
            value={round}
            onChange={(e) => setRound(e.target.value)}
            className="filter-input"
            placeholder="Todos os rounds"
            min="1"
          />
        </div>
        <div className="filter-group">
          <label>Equipe (opcional)</label>
          <input
            type="text"
            value={teamFilter}
            onChange={(e) => setTeamFilter(e.target.value)}
            className="filter-input"
            placeholder="Ex: Red Bull"
          />
        </div>
      </div>

      {/* Mode Toggle */}
      <div className="mode-toggle">
        <button
          className={`mode-btn ${viewMode === 'teams' ? 'active' : ''}`}
          onClick={() => setViewMode('teams')}
        >
          🏁 Por Equipe
        </button>
        <button
          className={`mode-btn ${viewMode === 'drivers' ? 'active' : ''}`}
          onClick={() => setViewMode('drivers')}
        >
          🏎️ Por Piloto
        </button>
      </div>

      {/* Stats Summary */}
      {analyticsData && (
        <div className="stats-grid">
          <div className="stat-card">
            <h4>⚡ Total de Pit Stops</h4>
            <div className="stat-value">
              {analyticsData.sessions.reduce((sum, s) => sum + s.pit_stops.length, 0)}
            </div>
            <div className="stat-range">
              Em {analyticsData.sessions.length} {analyticsData.sessions.length === 1 ? 'corrida' : 'corridas'}
            </div>
          </div>
          <div className="stat-card">
            <h4>🏁 Equipes Ativas</h4>
            <div className="stat-value">{analyticsData.team_stats.length}</div>
            <div className="stat-range">
              Com pit stops registrados
            </div>
          </div>
          <div className="stat-card">
            <h4>⏱️ Pit Stop Mais Rápido</h4>
            <div className="stat-value">
              {Math.min(...analyticsData.team_stats.map(t => t.min_duration)).toFixed(2)}s
            </div>
            <div className="stat-range">
              Melhor tempo registrado
            </div>
          </div>
          <div className="stat-card">
            <h4>📊 Média Geral</h4>
            <div className="stat-value">
              {(analyticsData.team_stats.reduce((sum, t) => sum + t.avg_duration, 0) / analyticsData.team_stats.length).toFixed(2)}s
            </div>
            <div className="stat-range">
              Entre todas as equipes
            </div>
          </div>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="error-message">
          <p>{error}</p>
        </div>
      )}

      {/* Average Duration Chart */}
      {!error && chartData.length > 0 && (
        <>
          <div className="chart-container">
            <h3 style={{ marginBottom: '1rem', color: 'var(--text-primary)' }}>
              Tempo Médio de Pit Stop
            </h3>
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 80 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
                <XAxis
                  dataKey={viewMode === 'teams' ? 'team' : 'driver'}
                  stroke="var(--text-secondary)"
                  angle={-45}
                  textAnchor="end"
                  height={100}
                />
                <YAxis
                  stroke="var(--text-secondary)"
                  label={{ value: 'Segundos', angle: -90, position: 'insideLeft', fill: 'var(--text-secondary)' }}
                />
                <Tooltip content={<CustomTooltip />} />
                <Legend wrapperStyle={{ color: 'var(--text-primary)' }} />
                <Bar
                  dataKey="avg_duration"
                  name="Tempo Médio (s)"
                  fill="var(--accent-red)"
                />
                <Bar
                  dataKey="min_duration"
                  name="Tempo Mínimo (s)"
                  fill="#4ECDC4"
                />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Lap vs Duration Scatter */}
          {scatterData.length > 0 && (
            <div className="chart-container">
              <h3 style={{ marginBottom: '1rem', color: 'var(--text-primary)' }}>
                Duração de Pit Stop por Volta
              </h3>
              <ResponsiveContainer width="100%" height={400}>
                <ScatterChart margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
                  <XAxis
                    dataKey="lap"
                    name="Volta"
                    stroke="var(--text-secondary)"
                    label={{ value: 'Volta', position: 'insideBottom', offset: -10, fill: 'var(--text-secondary)' }}
                  />
                  <YAxis
                    dataKey="duration"
                    name="Duração"
                    stroke="var(--text-secondary)"
                    label={{ value: 'Duração (s)', angle: -90, position: 'insideLeft', fill: 'var(--text-secondary)' }}
                  />
                  <Tooltip
                    cursor={{ strokeDasharray: '3 3' }}
                    content={({ active, payload }: any) => {
                      if (active && payload && payload.length) {
                        const data = payload[0].payload;
                        return (
                          <div className="custom-tooltip">
                            <p className="tooltip-title">{data.driver} ({data.team})</p>
                            <p>Volta: {data.lap}</p>
                            <p>Duração: {data.duration?.toFixed(2)}s</p>
                          </div>
                        );
                      }
                      return null;
                    }}
                  />
                  <Scatter
                    name="Pit Stops"
                    data={scatterData}
                    fill="var(--accent-magenta)"
                  />
                </ScatterChart>
              </ResponsiveContainer>
            </div>
          )}
        </>
      )}

      {!error && chartData.length === 0 && !loading && (
        <div className="no-data">
          <p>Selecione um ano para visualizar os dados de pit stops</p>
        </div>
      )}
    </div>
  );
}
