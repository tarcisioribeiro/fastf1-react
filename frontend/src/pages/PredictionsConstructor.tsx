import { useState, useEffect } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts';
import { f1Api } from '../services/api';
import LoadingWithRetry from '../components/LoadingWithRetry';
import FilterDropdown, { DropdownOption } from '../components/FilterDropdown';
import { useChartTheme, useChartConfig } from '../hooks/useChartTheme';
import '../components/FiltersContainer.css';
import './Predictions.css';

interface ConstructorPrediction {
  team: {
    name: string;
    color: string;
  };
  circuit: {
    name: string;
    location: string;
    country: string;
  };
  prediction: {
    averagePosition: number;
    averagePointsPerRace: number;
    predictedPositionRange: {
      min: number;
      max: number;
    };
    probabilities: {
      win: number;
      podium: number;
    };
  };
  statistics: {
    totalRaces: number;
    wins: number;
    podiums: number;
    totalPoints: number;
  };
  history: Array<{
    year: number;
    totalPoints: number;
    results: Array<{
      driver: string;
      position: number;
      points: number;
    }>;
  }>;
}

export default function PredictionsConstructor() {
  const chartColors = useChartTheme();
  const chartConfig = useChartConfig();

  const [teamName, setTeamName] = useState('');
  const [circuitName, setCircuitName] = useState('');
  const [year, setYear] = useState(new Date().getFullYear().toString());

  const [teamOptions, setTeamOptions] = useState<DropdownOption[]>([]);
  const [circuitOptions, setCircuitOptions] = useState<DropdownOption[]>([]);
  const [yearOptions, setYearOptions] = useState<DropdownOption[]>([]);
  const [baseYearOptions, setBaseYearOptions] = useState<DropdownOption[]>([]); // Opções base de anos

  const [prediction, setPrediction] = useState<ConstructorPrediction | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadingOptions, setLoadingOptions] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [noData, setNoData] = useState(false);

  // Parâmetros de previsão
  const [predictionParams, setPredictionParams] = useState({
    positions: true,
    points: true,
    wins: true,
    podiums: true,
    fastestLaps: true,
    pitStops: false,
    weather: false,
  });

  // Load available options on mount
  useEffect(() => {
    const loadOptions = async () => {
      try {
        setLoadingOptions(true);
        const [teamsRes, circuitsRes, yearsRes] = await Promise.all([
          f1Api.getActiveTeamsGrid(),  // Apenas equipes do grid atual (2025)
          f1Api.getAvailableCircuits(),
          f1Api.getAvailableYears()
        ]);

        // Map teams to dropdown options
        const teams = (teamsRes.teams || []).map((t: any) => ({
          value: t.name,
          label: t.name,
        }));
        setTeamOptions(teams);

        // Map circuits to dropdown options
        const circuits = (circuitsRes.circuits || []).map((c: any) => ({
          value: c.name,
          label: `${c.name} (${c.country})`,
        }));
        setCircuitOptions(circuits);

        // Map years to dropdown options - incluir anos futuros
        const currentYear = new Date().getFullYear();
        const historicalYears = yearsRes.years || [];
        const futureYears = [];

        // Adicionar anos futuros até 2030
        for (let year = currentYear; year <= 2030; year++) {
          if (!historicalYears.includes(year)) {
            futureYears.push(year);
          }
        }

        // Combinar anos históricos + futuros
        const allYears = [...historicalYears, ...futureYears].sort((a, b) => b - a);

        const years = allYears.map((y: number) => ({
          value: y.toString(),
          label: y >= currentYear ? `${y} (Previsão)` : y.toString(),
        }));
        setBaseYearOptions(years); // Salvar opções base
        setYearOptions(years); // Definir opções iniciais
      } catch (err: any) {
        console.error('Error loading options:', err);
      } finally {
        setLoadingOptions(false);
      }
    };

    loadOptions();
  }, []);

  // Efeito para filtrar anos quando o circuito mudar
  useEffect(() => {
    const updateYearOptions = async () => {
      if (!circuitName) {
        // Se nenhum circuito selecionado, mostrar todas as opções
        setYearOptions(baseYearOptions);
        return;
      }

      const currentYear = new Date().getFullYear();

      try {
        // Verificar se o circuito já teve corrida no ano atual
        const raceStatus = await f1Api.getCircuitRaceStatus(circuitName, currentYear);

        if (raceStatus.has_race) {
          // Se já teve corrida, filtrar o ano atual
          const filteredYears = baseYearOptions.filter(opt => parseInt(opt.value) > currentYear);
          setYearOptions(filteredYears);

          // Se o ano selecionado era o atual, trocar para o próximo ano
          if (parseInt(year) === currentYear) {
            setYear((currentYear + 1).toString());
          }
        } else {
          // Se não teve corrida, mostrar todas as opções
          setYearOptions(baseYearOptions);
        }
      } catch (err) {
        console.error('Error checking circuit race status:', err);
        // Em caso de erro, mostrar todas as opções
        setYearOptions(baseYearOptions);
      }
    };

    updateYearOptions();
  }, [circuitName, baseYearOptions]);

  const toggleParam = (param: keyof typeof predictionParams) => {
    setPredictionParams(prev => ({
      ...prev,
      [param]: !prev[param]
    }));
  };

  const loadPrediction = async () => {
    if (!teamName || !circuitName) {
      setError('Equipe e circuito são obrigatórios');
      return;
    }

    // Verificar se pelo menos um parâmetro está selecionado
    const hasSelectedParams = Object.values(predictionParams).some(v => v);
    if (!hasSelectedParams) {
      setError('Selecione pelo menos um parâmetro para a previsão');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setNoData(false);

      const data = await f1Api.getConstructorPrediction({
        team: teamName,
        circuit: circuitName,
        year,
        params: predictionParams
      });

      if (!data.prediction) {
        setNoData(true);
        setPrediction(null);
      } else {
        setPrediction(data);
        setNoData(false);
      }
    } catch (err: any) {
      setError(err.message || 'Erro ao carregar previsão');
      console.error('Error loading prediction:', err);
    } finally {
      setLoading(false);
    }
  };

  // Prepare data for charts with dynamic colors
  const probabilityData = prediction ? [
    { name: 'Vitória', value: prediction.prediction.probabilities.win, color: chartColors.accentRed },
    { name: 'Pódio', value: prediction.prediction.probabilities.podium - prediction.prediction.probabilities.win, color: chartColors.accentMagenta },
    { name: 'Sem Pódio', value: 100 - prediction.prediction.probabilities.podium, color: chartColors.gridColor }
  ].filter(d => d.value > 0) : [];

  const historyChartData = prediction?.history.map(h => ({
    year: h.year,
    points: h.totalPoints
  })) || [];

  if (loading) {
    return (
      <div className="predictions-page">
        <LoadingWithRetry
          message="Calculando previsão"
          hint="Analisando dados históricos..."
        />
      </div>
    );
  }

  return (
    <div className="predictions-page">
      <div className="predictions-header">
        <h1>🏎️ Previsão de Construtores</h1>
        <p className="predictions-subtitle">
          Análise estatística baseada em performance histórica da equipe no circuito
        </p>
      </div>

      {/* Input Form - Filtros Sequenciais */}
      <div className="filters-section">
        <h3 style={{ textAlign: 'center', marginBottom: '1rem', color: 'var(--text-primary)' }}>Configuração da Previsão</h3>
        <div className="filters-row">
          <FilterDropdown
            label="1️⃣ Equipe"
            value={teamName}
            options={teamOptions}
            onChange={setTeamName}
            placeholder="Escolha a equipe para análise"
            icon="🏎️"
            disabled={loadingOptions}
          />
          <FilterDropdown
            label="2️⃣ Circuito"
            value={circuitName}
            options={circuitOptions}
            onChange={setCircuitName}
            placeholder={teamName ? "Escolha o circuito" : "Selecione uma equipe primeiro"}
            icon="🏁"
            disabled={!teamName || loadingOptions}
          />
          <FilterDropdown
            label="3️⃣ Ano"
            value={year}
            options={yearOptions}
            onChange={setYear}
            placeholder="Ano para previsão"
            icon="📅"
            disabled={loadingOptions}
          />
        </div>
      </div>

      {/* Parâmetros de Previsão */}
      <div className="filters-section">
        <h3 style={{ textAlign: 'center', marginBottom: '1rem', color: 'var(--text-primary)' }}>Parâmetros para Análise</h3>
        <div style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: '1.5rem',
          justifyContent: 'center',
          alignItems: 'flex-start'
        }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={predictionParams.positions}
              onChange={() => toggleParam('positions')}
              style={{ cursor: 'pointer', width: '18px', height: '18px' }}
            />
            <span>📊 Posições Históricas</span>
          </label>
          <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={predictionParams.points}
              onChange={() => toggleParam('points')}
              style={{ cursor: 'pointer', width: '18px', height: '18px' }}
            />
            <span>⭐ Pontos Médios</span>
          </label>
          <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={predictionParams.wins}
              onChange={() => toggleParam('wins')}
              style={{ cursor: 'pointer', width: '18px', height: '18px' }}
            />
            <span>🏆 Vitórias</span>
          </label>
          <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={predictionParams.podiums}
              onChange={() => toggleParam('podiums')}
              style={{ cursor: 'pointer', width: '18px', height: '18px' }}
            />
            <span>🥇 Pódios</span>
          </label>
          <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={predictionParams.fastestLaps}
              onChange={() => toggleParam('fastestLaps')}
              style={{ cursor: 'pointer', width: '18px', height: '18px' }}
            />
            <span>⚡ Voltas Mais Rápidas</span>
          </label>
          <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={predictionParams.pitStops}
              onChange={() => toggleParam('pitStops')}
              style={{ cursor: 'pointer', width: '18px', height: '18px' }}
            />
            <span>⏱️ Pit Stops</span>
          </label>
          <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={predictionParams.weather}
              onChange={() => toggleParam('weather')}
              style={{ cursor: 'pointer', width: '18px', height: '18px' }}
            />
            <span>🌤️ Clima/Temperatura</span>
          </label>
        </div>
      </div>

      <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
        <button
          onClick={loadPrediction}
          className="predict-button"
          disabled={loadingOptions || !teamName || !circuitName}
        >
          🔮 Gerar Previsão
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="error-message">
          <p>{error}</p>
        </div>
      )}

      {/* No Data Message */}
      {noData && (
        <div className="no-data-message">
          <h3>📊 Sem Dados Históricos</h3>
          <p>Não há dados históricos suficientes para esta equipe neste circuito.</p>
          <p className="hint">Tente outra equipe ou circuito.</p>
        </div>
      )}

      {/* Prediction Results */}
      {prediction && !noData && (
        <div className="prediction-results">
          {/* Header Info */}
          <div className="result-header">
            <div className="team-info-card">
              <h2>{prediction.team.name}</h2>
              <h3>{prediction.circuit.name}</h3>
              <p>{prediction.circuit.location}, {prediction.circuit.country}</p>
            </div>
          </div>

          {/* Main Stats */}
          <div className="stats-grid">
            <div className="stat-card highlight">
              <h4>🎯 Posição Prevista (por piloto)</h4>
              <div className="stat-value">
                {prediction.prediction.predictedPositionRange.min} - {prediction.prediction.predictedPositionRange.max}
              </div>
              <div className="stat-range">
                Média histórica: {prediction.prediction.averagePosition?.toFixed(1)}º
              </div>
            </div>
            <div className="stat-card">
              <h4>📊 Pontos Médios por Corrida</h4>
              <div className="stat-value">{prediction.prediction.averagePointsPerRace?.toFixed(1)}</div>
              <div className="stat-range">
                Total: {prediction.statistics.totalPoints} pts
              </div>
            </div>
            <div className="stat-card">
              <h4>🏆 Vitórias</h4>
              <div className="stat-value">{prediction.statistics.wins}</div>
              <div className="stat-range">
                Em {prediction.statistics.totalRaces} corridas
              </div>
            </div>
            <div className="stat-card">
              <h4>🥇 Pódios</h4>
              <div className="stat-value">{prediction.statistics.podiums}</div>
              <div className="stat-range">
                {((prediction.statistics.podiums / (prediction.statistics.totalRaces * 2)) * 100).toFixed(0)}% das vagas
              </div>
            </div>
          </div>

          {/* Probabilities */}
          <div className="chart-section">
            <h3>Probabilidades de Resultado</h3>
            <div className="probability-charts">
              <div className="chart-container">
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={probabilityData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, value }: any) => `${name}: ${value.toFixed(1)}%`}
                      outerRadius={100}
                      dataKey="value"
                    >
                      {probabilityData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value: number) => `${value.toFixed(1)}%`} {...chartConfig.tooltip} />
                    <Legend {...chartConfig.legend} />
                  </PieChart>
                </ResponsiveContainer>
              </div>

              <div className="probability-bars">
                <div className="prob-bar-item">
                  <span className="prob-label">🏆 Chance de Vitória</span>
                  <div className="prob-bar">
                    <div
                      className="prob-fill gold"
                      style={{ width: `${prediction.prediction.probabilities.win}%` }}
                    />
                  </div>
                  <span className="prob-value">{prediction.prediction.probabilities.win.toFixed(1)}%</span>
                </div>
                <div className="prob-bar-item">
                  <span className="prob-label">🥇 Chance de Pódio Duplo</span>
                  <div className="prob-bar">
                    <div
                      className="prob-fill silver"
                      style={{ width: `${prediction.prediction.probabilities.podium}%` }}
                    />
                  </div>
                  <span className="prob-value">{prediction.prediction.probabilities.podium.toFixed(1)}%</span>
                </div>
              </div>
            </div>
          </div>

          {/* Historical Points Chart */}
          <div className="chart-section">
            <h3>Evolução de Pontos no Circuito</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={historyChartData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
                <CartesianGrid {...chartConfig.cartesianGrid} />
                <XAxis dataKey="year" {...chartConfig.xAxis} />
                <YAxis {...chartConfig.yAxis} label={{ value: 'Pontos', angle: -90, position: 'insideLeft', fill: chartColors.textSecondary }} />
                <Tooltip {...chartConfig.tooltip} />
                <Legend {...chartConfig.legend} />
                <Bar dataKey="points" fill={prediction.team.color || chartColors.accentRed} name="Pontos" {...chartConfig.bar} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Historical Results */}
          <div className="history-section">
            <h3>Histórico Detalhado Neste Circuito</h3>
            {prediction.history.map((yearData) => (
              <div key={yearData.year} className="year-results">
                <h4>
                  {yearData.year} - {yearData.totalPoints} pontos
                </h4>
                <div className="history-table-container">
                  <table className="history-table">
                    <thead>
                      <tr>
                        <th>Piloto</th>
                        <th>Posição</th>
                        <th>Pontos</th>
                      </tr>
                    </thead>
                    <tbody>
                      {yearData.results.map((result, idx) => (
                        <tr key={idx} className={result.position <= 3 ? 'podium-row' : ''}>
                          <td>{result.driver}</td>
                          <td className="position-cell">
                            {result.position}
                            {result.position === 1 && ' 🏆'}
                            {result.position === 2 && ' 🥈'}
                            {result.position === 3 && ' 🥉'}
                          </td>
                          <td>{result.points}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ))}
          </div>

          {/* Disclaimer */}
          <div className="disclaimer">
            <p>
              <strong>Nota:</strong> Esta previsão é baseada puramente em dados históricos e estatísticas.
              Fatores como mudanças de regulamento, atualizações dos carros, clima e estratégia de corrida
              não são considerados. Use apenas como referência.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
