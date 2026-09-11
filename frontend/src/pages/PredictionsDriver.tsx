import { useState, useEffect } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import { f1Api } from '../services/api';
import LoadingWithRetry from '../components/LoadingWithRetry';
import FilterDropdown, { DropdownOption } from '../components/FilterDropdown';
import PredictionExplanation from '../components/PredictionExplanation';
import AppliedFactorsPanel, { AppliedFactor } from '../components/AppliedFactorsPanel';
import { useChartTheme, useChartConfig } from '../hooks/useChartTheme';
import '../components/FiltersContainer.css';
import './Predictions.css';

interface DriverPrediction {
  driver: {
    code: string;
    fullName: string;
    number: string;
  };
  circuit: {
    name: string;
    location: string;
    country: string;
  };
  prediction: {
    averagePosition: number;
    averagePoints: number;
    predictedPosition: number | null;
    predictedPositionRange: {
      min: number | null;
      max: number | null;
    };
    probabilities: {
      win: number;
      podium: number;
      points: number;
    };
    appliedFactors?: AppliedFactor[];
  };
  statistics: {
    totalRaces: number;
    wins: number;
    podiums: number;
    pointsFinishes: number;
  };
  history: Array<{
    year: number;
    position: number;
    points: number;
    team: string;
  }>;
}

export default function PredictionsDriver() {
  const chartColors = useChartTheme();
  const chartConfig = useChartConfig();

  const [driverCode, setDriverCode] = useState('');
  const [circuitName, setCircuitName] = useState('');
  const [year, setYear] = useState(new Date().getFullYear().toString());

  const [driverOptions, setDriverOptions] = useState<DropdownOption[]>([]);
  const [circuitOptions, setCircuitOptions] = useState<DropdownOption[]>([]);
  const [yearOptions, setYearOptions] = useState<DropdownOption[]>([]);
  const [baseYearOptions, setBaseYearOptions] = useState<DropdownOption[]>([]); // Opções base de anos

  const [prediction, setPrediction] = useState<DriverPrediction | null>(null);
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
    weather: true,
    // Fatores contextuais
    regulationChanges: false,
    carUpgrades: false,
    strategy: false,
    currentForm: true,
  });

  // Load available options on mount
  useEffect(() => {
    const loadOptions = async () => {
      try {
        setLoadingOptions(true);
        const [driversRes, circuitsRes, yearsRes] = await Promise.all([
          f1Api.getActiveDriversGrid(),  // Apenas pilotos do grid atual (2025)
          f1Api.getAvailableCircuits(),
          f1Api.getAvailableYears()
        ]);

        // Map drivers to dropdown options
        const drivers = (driversRes.drivers || []).map((d: any) => ({
          value: d.code,
          label: `${d.code} - ${d.full_name}`,
        }));
        setDriverOptions(drivers);

        // Map circuits to dropdown options
        const circuits = (circuitsRes.circuits || []).map((c: any) => ({
          value: c.name,
          label: `${c.name} (${c.country})`,
        }));
        setCircuitOptions(circuits);

        // Map years to dropdown options - apenas anos de 2025 em diante
        const predictionYears = [2025, 2026, 2027, 2028, 2029, 2030];

        const years = predictionYears.map((y: number) => ({
          value: y.toString(),
          label: `${y} (Previsão)`,
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
    if (!driverCode || !circuitName) {
      setError('Piloto e circuito são obrigatórios');
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

      const data = await f1Api.getDriverPrediction({
        driver: driverCode,
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

  // Prepare data for pie charts with dynamic colors
  const probabilityData = prediction ? [
    { name: 'Vitória', value: prediction.prediction.probabilities.win, color: '#FFD700' },
    { name: 'Pódio', value: prediction.prediction.probabilities.podium - prediction.prediction.probabilities.win, color: '#C0C0C0' },
    { name: 'Pontos', value: prediction.prediction.probabilities.points - prediction.prediction.probabilities.podium, color: '#CD7F32' },
    { name: 'Sem Pontos', value: 100 - prediction.prediction.probabilities.points, color: chartColors.borderColor }
  ].filter(d => d.value > 0) : [];

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
        <h1>🔮 Previsão de Pilotos</h1>
        <p className="predictions-subtitle">
          Análise estatística baseada em performance histórica no circuito
        </p>
      </div>

      {/* Input Form - Filtros Sequenciais */}
      <div className="filters-section">
        <h3 style={{ textAlign: 'center', marginBottom: '1rem', color: 'var(--text-primary)' }}>Configuração da Previsão</h3>
        <div className="filters-row">
          <FilterDropdown
            label="1️⃣ Piloto"
            value={driverCode}
            options={driverOptions}
            onChange={setDriverCode}
            placeholder="Escolha o piloto para análise"
            icon="🏎️"
            disabled={loadingOptions}
          />
          <FilterDropdown
            label="2️⃣ Circuito"
            value={circuitName}
            options={circuitOptions}
            onChange={setCircuitName}
            placeholder={driverCode ? "Escolha o circuito" : "Selecione um piloto primeiro"}
            icon="🏁"
            disabled={!driverCode || loadingOptions}
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

        <h3 style={{ textAlign: 'center', margin: '1.5rem 0 1rem', color: 'var(--text-primary)' }}>Fatores Contextuais</h3>
        <div style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: '1.5rem',
          justifyContent: 'center',
          alignItems: 'flex-start'
        }}>
          {([
            ['regulationChanges', '🚩', 'Mudanças de Regulamento'],
            ['carUpgrades', '🔧', 'Atualizações de Carro'],
            ['strategy', '⏱️', 'Estratégia'],
            ['currentForm', '📈', 'Forma Atual'],
          ] as const).map(([key, icon, label]) => (
            <label key={key} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={predictionParams[key]}
                onChange={() => toggleParam(key)}
                style={{ cursor: 'pointer', width: '18px', height: '18px' }}
              />
              <span>{icon} {label}</span>
            </label>
          ))}
        </div>
      </div>

      <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
        <button
          onClick={loadPrediction}
          className="predict-button"
          disabled={loadingOptions || !driverCode || !circuitName}
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
          <p>Não há dados históricos suficientes para este piloto neste circuito.</p>
          <p className="hint">Tente outro piloto ou circuito.</p>
        </div>
      )}

      {/* Prediction Results */}
      {prediction && !noData && (
        <div className="prediction-results">
          {/* Header Info */}
          <div className="result-header">
            <div className="driver-info-card">
              <h2>{prediction.driver.fullName} (#{prediction.driver.number})</h2>
              <h3>{prediction.circuit.name}</h3>
              <p>{prediction.circuit.location}, {prediction.circuit.country}</p>
            </div>
          </div>

          {/* Main Stats */}
          <div className="stats-grid">
            <div className="stat-card highlight">
              <h4>🎯 Posição Prevista</h4>
              <div className="stat-value">
                {prediction.prediction.predictedPosition != null
                  ? `${prediction.prediction.predictedPosition}º`
                  : '—'}
              </div>
              <div className="stat-range">
                {prediction.prediction.predictedPositionRange.min != null &&
                 prediction.prediction.predictedPositionRange.max != null && (
                  <>Faixa provável: {prediction.prediction.predictedPositionRange.min}º–{prediction.prediction.predictedPositionRange.max}º<br /></>
                )}
                Média histórica: {prediction.prediction.averagePosition?.toFixed(1)}º
              </div>
            </div>
            <div className="stat-card">
              <h4>📊 Pontos Médios</h4>
              <div className="stat-value">{prediction.prediction.averagePoints?.toFixed(1)}</div>
              <div className="stat-range">
                Por corrida neste circuito
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
                Taxa: {((prediction.statistics.podiums / prediction.statistics.totalRaces) * 100).toFixed(0)}%
              </div>
            </div>
          </div>

          {/* Probabilities Chart */}
          <div className="chart-section">
            <h3>Probabilidades de Resultado</h3>
            <div className="probability-charts">
              <div className="chart-container">
                <div className="donut-wrap">
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={probabilityData}
                        cx="50%"
                        cy="50%"
                        innerRadius={78}
                        outerRadius={112}
                        paddingAngle={3}
                        cornerRadius={8}
                        stroke="none"
                        dataKey="value"
                      >
                        {probabilityData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip formatter={(value: number) => `${value.toFixed(1)}%`} {...chartConfig.tooltip} />
                    </PieChart>
                  </ResponsiveContainer>
                  <div className="donut-center">
                    <span className="donut-center-value">
                      {prediction.prediction.probabilities.points.toFixed(1)}%
                    </span>
                    <span className="donut-center-label">Chance de Pontos</span>
                  </div>
                </div>
              </div>

              <div className="probability-bars">
                <div className="prob-bar-item">
                  <div className="prob-bar-header">
                    <span className="prob-label">
                      <span className="prob-icon gold">🏆</span>
                      Chance de Vitória
                    </span>
                    <span className="prob-value gold">{prediction.prediction.probabilities.win.toFixed(1)}%</span>
                  </div>
                  <div className="prob-bar">
                    <div
                      className="prob-fill gold"
                      style={{ width: `${Math.max(prediction.prediction.probabilities.win, 2)}%` }}
                    />
                  </div>
                </div>
                <div className="prob-bar-item">
                  <div className="prob-bar-header">
                    <span className="prob-label">
                      <span className="prob-icon silver">🥇</span>
                      Chance de Pódio
                    </span>
                    <span className="prob-value silver">{prediction.prediction.probabilities.podium.toFixed(1)}%</span>
                  </div>
                  <div className="prob-bar">
                    <div
                      className="prob-fill silver"
                      style={{ width: `${Math.max(prediction.prediction.probabilities.podium, 2)}%` }}
                    />
                  </div>
                </div>
                <div className="prob-bar-item">
                  <div className="prob-bar-header">
                    <span className="prob-label">
                      <span className="prob-icon bronze">📊</span>
                      Chance de Pontos
                    </span>
                    <span className="prob-value bronze">{prediction.prediction.probabilities.points.toFixed(1)}%</span>
                  </div>
                  <div className="prob-bar">
                    <div
                      className="prob-fill bronze"
                      style={{ width: `${Math.max(prediction.prediction.probabilities.points, 2)}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Prediction Explanation */}
          <PredictionExplanation
            predictionType="driver"
            selectedDriver={prediction.driver.fullName}
            selectedCircuit={prediction.circuit.name}
            historyData={prediction.history}
            prediction={prediction.prediction}
          />

          {prediction.prediction.appliedFactors && (
            <AppliedFactorsPanel factors={prediction.prediction.appliedFactors} />
          )}

          {/* Historical Results */}
          <div className="history-section">
            <h3>Histórico Neste Circuito</h3>
            <div className="history-table-container">
              <table className="history-table">
                <thead>
                  <tr>
                    <th>Ano</th>
                    <th>Posição</th>
                    <th>Pontos</th>
                    <th>Equipe</th>
                  </tr>
                </thead>
                <tbody>
                  {prediction.history.map((item, idx) => (
                    <tr key={idx} className={item.position <= 3 ? 'podium-row' : ''}>
                      <td>{item.year}</td>
                      <td className="position-cell">
                        {item.position}
                        {item.position === 1 && ' 🏆'}
                        {item.position === 2 && ' 🥈'}
                        {item.position === 3 && ' 🥉'}
                      </td>
                      <td>{item.points}</td>
                      <td>{item.team}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Disclaimer */}
          <div className="disclaimer">
            <p>
              <strong>Nota:</strong> A previsão combina o histórico do piloto no circuito com os
              fatores contextuais selecionados (mudanças de regulamento, atualizações de carro,
              clima, estratégia e forma atual). Estimativas de regulamento e evolução de carro usam
              histórico curado e indicadores de ritmo — não dados oficiais de desenvolvimento.
              Use apenas como referência.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
