import { useEffect, useState, useCallback } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { f1Api } from '../services/api';
import LoadingWithRetry from '../components/LoadingWithRetry';
import Button from '../components/Button';
import { useChartConfig } from '../hooks/useChartTheme';
import FilterDropdown, { DropdownOption } from '../components/FilterDropdown';
import CollapsibleSection from '../components/CollapsibleSection';
import '../components/FiltersContainer.css';
import './AnalyticsStandings.css';

interface DriverEvolution {
  driver: {
    code: string;
    fullName: string;
    number: string;
  };
  team: {
    name: string;
    color: string;
  };
  points_by_round: {
    round: number;
    eventName: string;
    points: number;
    position: number;
    wins: number;
    podiums: number;
  }[];
}

interface TeamEvolution {
  team: {
    name: string;
    color: string;
  };
  points_by_round: {
    round: number;
    eventName: string;
    points: number;
    position: number;
    wins: number;
    podiums: number;
  }[];
}

export default function AnalyticsStandings() {
  const chartConfig = useChartConfig();

  const [mode, setMode] = useState<'drivers' | 'constructors'>('drivers');
  const [year, setYear] = useState(new Date().getFullYear().toString());
  const [startRound, setStartRound] = useState('1');
  const [endRound, setEndRound] = useState('');
  const [selectedDrivers, setSelectedDrivers] = useState<string[]>([]);
  const [selectedTeams, setSelectedTeams] = useState<string[]>([]);
  const [availableDrivers, setAvailableDrivers] = useState<string[]>([]);
  const [availableTeams, setAvailableTeams] = useState<string[]>([]);

  const [driversData, setDriversData] = useState<DriverEvolution[]>([]);
  const [teamsData, setTeamsData] = useState<TeamEvolution[]>([]);
  const [chartData, setChartData] = useState<any[]>([]);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filter options
  const [yearOptions, setYearOptions] = useState<DropdownOption[]>([]);
  const [gpOptions, setGpOptions] = useState<DropdownOption[]>([]);
  const [loadingOptions, setLoadingOptions] = useState(true);

  const loadDriversEvolution = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const params: any = {
        year,
        drivers: selectedDrivers.join(','),
        start_round: parseInt(startRound) || 1,
      };
      if (endRound) params.end_round = parseInt(endRound);

      const data = await f1Api.getDriverStandingsEvolution(params);
      setDriversData(data.drivers);

      // Transform data for Recharts
      const transformed = transformDriverDataForChart(data.drivers);
      setChartData(transformed);
    } catch (err: any) {
      setError(err.message || 'Erro ao carregar dados');
      console.error('Error loading drivers evolution:', err);
    } finally {
      setLoading(false);
    }
  }, [year, selectedDrivers, startRound, endRound]);

  const loadTeamsEvolution = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const params: any = {
        year,
        teams: selectedTeams.join(','),
        start_round: parseInt(startRound) || 1,
      };
      if (endRound) params.end_round = parseInt(endRound);

      const data = await f1Api.getConstructorStandingsEvolution(params);
      setTeamsData(data.teams);

      // Transform data for Recharts
      const transformed = transformTeamDataForChart(data.teams);
      setChartData(transformed);
    } catch (err: any) {
      setError(err.message || 'Erro ao carregar dados');
      console.error('Error loading teams evolution:', err);
    } finally {
      setLoading(false);
    }
  }, [year, selectedTeams, startRound, endRound]);

  // Load filter options on mount
  useEffect(() => {
    loadFilterOptions();
  }, []);

  // Load GPs when year changes
  useEffect(() => {
    if (year) {
      loadGrandsPrix(year);
    }
  }, [year]);

  const loadFilterOptions = async () => {
    try {
      setLoadingOptions(true);
      const options = await f1Api.getFilterOptions();

      // Set year options
      const years = options.years.map(y => ({
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

  const loadGrandsPrix = async (selectedYear: string) => {
    try {
      const gps = await f1Api.getGrandsPrix(selectedYear);
      const gpOpts = gps.map((gp: any) => ({
        value: gp.round.toString(),
        label: gp.name, // Apenas nome, sem índice
      }));
      setGpOptions(gpOpts);
      setStartRound('1');
      setEndRound('');
    } catch (err) {
      console.error('Error loading GPs:', err);
      setGpOptions([]);
    }
  };

  // Load available drivers/teams when year or mode changes
  useEffect(() => {
    const loadAvailableOptions = async () => {
      try {
        // Load all drivers/teams data to get available options
        if (mode === 'drivers') {
          const data = await f1Api.getDriverStandingsEvolution({ year });
          const drivers = data.drivers.map((d: DriverEvolution) => d.driver.code);
          setAvailableDrivers(drivers);
          // Auto-select top 5 if nothing selected
          if (selectedDrivers.length === 0 && drivers.length > 0) {
            setSelectedDrivers(drivers.slice(0, 5));
          }
        } else {
          const data = await f1Api.getConstructorStandingsEvolution({ year });
          const teams = data.teams.map((t: TeamEvolution) => t.team.name);
          setAvailableTeams(teams);
          // Auto-select top 3 if nothing selected
          if (selectedTeams.length === 0 && teams.length > 0) {
            setSelectedTeams(teams.slice(0, 3));
          }
        }
      } catch (err: any) {
        console.error('Error loading available options:', err);
      }
    };

    loadAvailableOptions();
  }, [year, mode]);

  // Load data when filters change
  useEffect(() => {
    if (mode === 'drivers' && selectedDrivers.length > 0) {
      loadDriversEvolution();
    } else if (mode === 'constructors' && selectedTeams.length > 0) {
      loadTeamsEvolution();
    }
  }, [mode, loadDriversEvolution, loadTeamsEvolution, selectedDrivers.length, selectedTeams.length]);

  const transformDriverDataForChart = (drivers: DriverEvolution[]) => {
    if (!drivers || drivers.length === 0) return [];

    // Get all unique rounds
    const roundsSet = new Set<number>();
    drivers.forEach(driver => {
      driver.points_by_round.forEach(round => roundsSet.add(round.round));
    });
    const rounds = Array.from(roundsSet).sort((a, b) => a - b);

    // Create chart data
    return rounds.map(round => {
      const dataPoint: any = { round };
      drivers.forEach(driver => {
        const roundData = driver.points_by_round.find(r => r.round === round);
        if (roundData) {
          dataPoint[driver.driver.code] = roundData.points;
          dataPoint[`${driver.driver.code}_eventName`] = roundData.eventName;
        }
      });
      return dataPoint;
    });
  };

  const transformTeamDataForChart = (teams: TeamEvolution[]) => {
    if (!teams || teams.length === 0) return [];

    // Get all unique rounds
    const roundsSet = new Set<number>();
    teams.forEach(team => {
      team.points_by_round.forEach(round => roundsSet.add(round.round));
    });
    const rounds = Array.from(roundsSet).sort((a, b) => a - b);

    // Create chart data
    return rounds.map(round => {
      const dataPoint: any = { round };
      teams.forEach(team => {
        const roundData = team.points_by_round.find(r => r.round === round);
        if (roundData) {
          dataPoint[team.team.name] = roundData.points;
          dataPoint[`${team.team.name}_eventName`] = roundData.eventName;
        }
      });
      return dataPoint;
    });
  };

  const toggleDriver = (driverCode: string) => {
    setSelectedDrivers(prev =>
      prev.includes(driverCode)
        ? prev.filter(d => d !== driverCode)
        : [...prev, driverCode]
    );
  };

  const toggleTeam = (teamName: string) => {
    setSelectedTeams(prev =>
      prev.includes(teamName)
        ? prev.filter(t => t !== teamName)
        : [...prev, teamName]
    );
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const eventName = payload[0]?.payload[`${payload[0].dataKey}_eventName`];
      return (
        <div className="custom-tooltip">
          <p className="tooltip-title">Round {label}{eventName ? ` - ${eventName}` : ''}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} style={{ color: entry.color }}>
              {entry.name}: {entry.value} pts
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  if (loading && chartData.length === 0) {
    return (
      <div className="analytics-page">
        <LoadingWithRetry
          message="Carregando dados de evolução"
          hint="Processando histórico de pontuação..."
        />
      </div>
    );
  }

  return (
    <div className="analytics-page">
      <div className="analytics-header">
        <h1>📈 Evolução de Pontos</h1>
        <p className="analytics-subtitle">
          Acompanhe a evolução da pontuação ao longo das corridas
        </p>
      </div>

      {/* Mode Toggle */}
      <div className="mode-toggle">
        <Button
          variant={mode === 'drivers' ? 'primary' : 'secondary'}
          onClick={() => setMode('drivers')}
        >
          🏎️ Pilotos
        </Button>
        <Button
          variant={mode === 'constructors' ? 'primary' : 'secondary'}
          onClick={() => setMode('constructors')}
        >
          🏁 Construtores
        </Button>
      </div>

      {/* Filters */}
      <CollapsibleSection className="filters-row-wrapper" title="🔎 Filtros">
      <div className="filters-row">
        <FilterDropdown
          label="Ano"
          value={year}
          options={yearOptions}
          onChange={setYear}
          placeholder="Selecione o ano"
          icon="📅"
        />
        <FilterDropdown
          label="GP Inicial"
          value={startRound}
          options={gpOptions}
          onChange={setStartRound}
          placeholder="Primeiro GP"
          icon="🏁"
          disabled={!year || gpOptions.length === 0}
        />
        <FilterDropdown
          label="GP Final (opcional)"
          value={endRound}
          options={gpOptions}
          onChange={setEndRound}
          placeholder="Último disponível"
          icon="🏁"
          disabled={!year || gpOptions.length === 0}
        />
      </div>
      </CollapsibleSection>

      {/* Selection */}
      {mode === 'drivers' ? (
        <div className="selection-container">
          <h3>Selecione os Pilotos</h3>
          <div className="selection-grid">
            {availableDrivers.map(driverCode => {
              const driverData = driversData.find(d => d.driver.code === driverCode);
              return (
                <button
                  key={driverCode}
                  className={`selection-item ${selectedDrivers.includes(driverCode) ? 'selected' : ''}`}
                  onClick={() => toggleDriver(driverCode)}
                  style={{
                    borderLeft: driverData ? `4px solid ${driverData.team.color}` : undefined
                  }}
                >
                  <span className="selection-code">{driverCode}</span>
                  {driverData && (
                    <span className="selection-team">{driverData.team.name}</span>
                  )}
                </button>
              );
            })}
          </div>
        </div>
      ) : (
        <div className="selection-container">
          <h3>Selecione as Equipes</h3>
          <div className="selection-grid">
            {availableTeams.map(teamName => {
              const teamData = teamsData.find(t => t.team.name === teamName);
              return (
                <button
                  key={teamName}
                  className={`selection-item ${selectedTeams.includes(teamName) ? 'selected' : ''}`}
                  onClick={() => toggleTeam(teamName)}
                  style={{
                    borderLeft: teamData ? `4px solid ${teamData.team.color}` : undefined
                  }}
                >
                  <span className="selection-name">{teamName}</span>
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Chart */}
      {error && (
        <div className="error-message">
          <p>{error}</p>
        </div>
      )}

      {!error && chartData.length > 0 && (
        <div className="chart-container">
          <ResponsiveContainer width="100%" height={500}>
            <LineChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
              <CartesianGrid {...chartConfig.cartesianGrid} />
              <XAxis
                dataKey="round"
                {...chartConfig.xAxis}
                label={{ value: 'Round', position: 'insideBottom', offset: -10, ...chartConfig.xAxis.label }}
              />
              <YAxis
                {...chartConfig.yAxis}
                label={{ value: 'Pontos', angle: -90, position: 'insideLeft', ...chartConfig.yAxis.label }}
              />
              <Tooltip content={<CustomTooltip />} {...chartConfig.tooltip} />
              <Legend {...chartConfig.legend} />
              {mode === 'drivers' && driversData.map(driver => (
                <Line
                  key={driver.driver.code}
                  type="monotone"
                  dataKey={driver.driver.code}
                  name={driver.driver.code}
                  stroke={driver.team.color}
                  {...chartConfig.line}
                />
              ))}
              {mode === 'constructors' && teamsData.map(team => (
                <Line
                  key={team.team.name}
                  type="monotone"
                  dataKey={team.team.name}
                  name={team.team.name}
                  stroke={team.team.color}
                  {...chartConfig.line}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {!error && chartData.length === 0 && !loading && (
        <div className="no-data">
          <p>Selecione {mode === 'drivers' ? 'pilotos' : 'equipes'} para visualizar o gráfico</p>
        </div>
      )}
    </div>
  );
}
