import { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ScatterChart, Scatter } from 'recharts';
import { f1Api } from '../services/api';
import LoadingWithRetry from '../components/LoadingWithRetry';
import { useChartConfig, useChartTheme } from '../hooks/useChartTheme';
import FilterDropdown, { DropdownOption } from '../components/FilterDropdown';
import '../components/FiltersContainer.css';
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
  const chartConfig = useChartConfig();
  const chartColors = useChartTheme();

  const [year, setYear] = useState(new Date().getFullYear().toString());
  const [round, setRound] = useState('');
  const [teamFilter, setTeamFilter] = useState('');
  const [viewMode, setViewMode] = useState<'teams' | 'drivers'>('teams');

  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filter options
  const [yearOptions, setYearOptions] = useState<DropdownOption[]>([]);
  const [gpOptions, setGpOptions] = useState<DropdownOption[]>([]);
  const [teamOptions, setTeamOptions] = useState<DropdownOption[]>([]);
  const [loadingOptions, setLoadingOptions] = useState(true);

  // Load filter options on mount
  useEffect(() => {
    loadFilterOptions();
  }, []);

  // Load GPs and teams when year changes (filtros hierárquicos)
  useEffect(() => {
    if (year) {
      loadDependentOptions(year);
    } else {
      // Limpar opções dependentes se não houver ano
      setGpOptions([]);
      setTeamOptions([]);
      setRound('');
      setTeamFilter('');
    }
  }, [year]);

  // Load pit stops data when filters change
  useEffect(() => {
    if (year && !loadingOptions) {
      loadPitStopsData();
    }
  }, [year, round, teamFilter, loadingOptions]);

  const loadFilterOptions = async () => {
    try {
      setLoadingOptions(true);
      const yearsData = await f1Api.getAvailableYears();

      // Set year options
      const years = (yearsData.years || []).map((y: number) => ({
        value: y.toString(),
        label: y.toString(),
      }));
      setYearOptions(years);
    } catch (err) {
      console.error('Error loading filter options:', err);
    } finally {
      setLoadingOptions(false);
    }
  };

  const loadDependentOptions = async (selectedYear: string) => {
    try {
      // Resetar filtros dependentes
      setRound('');
      setTeamFilter('');

      // Carregar GPs e equipes do ano selecionado
      const [gps, teams] = await Promise.all([
        f1Api.getGrandsPrix(selectedYear),
        f1Api.getTeamsByYear(selectedYear)
      ]);

      // Map GPs (sem índice, apenas nome)
      const gpOpts = gps.map((gp: any) => ({
        value: gp.round.toString(),
        label: gp.name, // Apenas nome, sem índice
      }));
      setGpOptions(gpOpts);

      // Map teams
      const teamOpts = teams.map((team: any) => ({
        value: team.name,
        label: team.name,
      }));
      setTeamOptions(teamOpts);
    } catch (err) {
      console.error('Error loading dependent options:', err);
      setGpOptions([]);
      setTeamOptions([]);
    }
  };

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
    ? [...(analyticsData?.team_stats || [])].sort((a, b) => a.avg_duration - b.avg_duration)
    : [...(analyticsData?.driver_stats || [])].sort((a, b) => a.avg_duration - b.avg_duration).slice(0, 15);

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
      <div className="filters-row">
        <FilterDropdown
          label="Ano"
          value={year}
          options={yearOptions}
          onChange={setYear}
          placeholder="Selecione o ano"
          icon="📅"
          disabled={loadingOptions}
        />
        <FilterDropdown
          label="GP (opcional)"
          value={round}
          options={gpOptions}
          onChange={setRound}
          placeholder={year ? "Todos os GPs" : "Selecione um ano primeiro"}
          icon="🏁"
          disabled={!year}
        />
        <FilterDropdown
          label="Equipe (opcional)"
          value={teamFilter}
          options={teamOptions}
          onChange={setTeamFilter}
          placeholder={year ? "Todas as equipes" : "Selecione um ano primeiro"}
          icon="🏆"
          disabled={!year}
        />
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
                <CartesianGrid {...chartConfig.cartesianGrid} />
                <XAxis
                  dataKey={viewMode === 'teams' ? 'team' : 'driver'}
                  {...chartConfig.xAxis}
                  angle={-45}
                  textAnchor="end"
                  height={100}
                />
                <YAxis
                  {...chartConfig.yAxis}
                  label={{ value: 'Segundos', angle: -90, position: 'insideLeft', ...chartConfig.yAxis.label }}
                />
                <Tooltip content={<CustomTooltip />} {...chartConfig.tooltip} />
                <Legend {...chartConfig.legend} />
                <Bar
                  dataKey="avg_duration"
                  name="Tempo Médio (s)"
                  fill={chartColors.accentRed}
                  {...chartConfig.bar}
                />
                <Bar
                  dataKey="min_duration"
                  name="Tempo Mínimo (s)"
                  fill="#4ECDC4"
                  {...chartConfig.bar}
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
                  <CartesianGrid {...chartConfig.cartesianGrid} />
                  <XAxis
                    dataKey="lap"
                    name="Volta"
                    {...chartConfig.xAxis}
                    label={{ value: 'Volta', position: 'insideBottom', offset: -10, ...chartConfig.xAxis.label }}
                  />
                  <YAxis
                    dataKey="duration"
                    name="Duração"
                    {...chartConfig.yAxis}
                    label={{ value: 'Duração (s)', angle: -90, position: 'insideLeft', ...chartConfig.yAxis.label }}
                  />
                  <Tooltip
                    cursor={{ strokeDasharray: '3 3' }}
                    {...chartConfig.tooltip}
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
                    fill={chartColors.accentMagenta}
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
