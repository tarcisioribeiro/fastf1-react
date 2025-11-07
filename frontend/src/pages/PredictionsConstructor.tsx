import { useState, useEffect } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts';
import { f1Api } from '../services/api';
import LoadingWithRetry from '../components/LoadingWithRetry';
import CustomSelect from '../components/CustomSelect';
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
  const [teamName, setTeamName] = useState('');
  const [circuitName, setCircuitName] = useState('');
  const [year, setYear] = useState(new Date().getFullYear().toString());

  const [availableTeams, setAvailableTeams] = useState<any[]>([]);
  const [availableCircuits, setAvailableCircuits] = useState<any[]>([]);
  const [availableYears, setAvailableYears] = useState<number[]>([]);

  const [prediction, setPrediction] = useState<ConstructorPrediction | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadingOptions, setLoadingOptions] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [noData, setNoData] = useState(false);

  // Load available options on mount
  useEffect(() => {
    const loadOptions = async () => {
      try {
        setLoadingOptions(true);
        const [teamsRes, circuitsRes, yearsRes] = await Promise.all([
          f1Api.getAvailableTeams(),
          f1Api.getAvailableCircuits(),
          f1Api.getAvailableYears()
        ]);

        setAvailableTeams(teamsRes.teams || []);
        setAvailableCircuits(circuitsRes.circuits || []);
        setAvailableYears(yearsRes.years || []);
      } catch (err: any) {
        console.error('Error loading options:', err);
      } finally {
        setLoadingOptions(false);
      }
    };

    loadOptions();
  }, []);

  const loadPrediction = async () => {
    if (!teamName || !circuitName) {
      setError('Equipe e circuito são obrigatórios');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setNoData(false);

      const data = await f1Api.getConstructorPrediction({
        team: teamName,
        circuit: circuitName,
        year
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

  // Prepare data for charts
  const probabilityData = prediction ? [
    { name: 'Vitória', value: prediction.prediction.probabilities.win, color: '#FFD700' },
    { name: 'Pódio', value: prediction.prediction.probabilities.podium - prediction.prediction.probabilities.win, color: '#C0C0C0' },
    { name: 'Sem Pódio', value: 100 - prediction.prediction.probabilities.podium, color: 'var(--surface-3)' }
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
        <h1>🏎️ Previsão para Construtores</h1>
        <p className="predictions-subtitle">
          Análise estatística baseada em performance histórica da equipe no circuito
        </p>
      </div>

      {/* Input Form */}
      <div className="prediction-form">
        <div className="form-group">
          <CustomSelect
            label="Equipe"
            value={teamName}
            onChange={(e) => setTeamName(e.target.value)}
            disabled={loadingOptions}
          >
            <option value="">Selecione uma equipe</option>
            {availableTeams.map(team => (
              <option key={team.name} value={team.name}>
                {team.name}
              </option>
            ))}
          </CustomSelect>
        </div>
        <div className="form-group">
          <CustomSelect
            label="Circuito"
            value={circuitName}
            onChange={(e) => setCircuitName(e.target.value)}
            disabled={loadingOptions}
          >
            <option value="">Selecione um circuito</option>
            {availableCircuits.map(circuit => (
              <option key={circuit.name} value={circuit.name}>
                {circuit.name} ({circuit.country})
              </option>
            ))}
          </CustomSelect>
        </div>
        <div className="form-group">
          <CustomSelect
            label="Ano"
            value={year}
            onChange={(e) => setYear(e.target.value)}
            disabled={loadingOptions}
          >
            {availableYears.map(y => (
              <option key={y} value={y}>
                {y}
              </option>
            ))}
          </CustomSelect>
        </div>
        <button
          onClick={loadPrediction}
          className="predict-button"
          disabled={loadingOptions || !teamName || !circuitName}
        >
          Gerar Previsão
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
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {probabilityData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value: number) => `${value.toFixed(1)}%`} />
                    <Legend />
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
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
                <XAxis dataKey="year" stroke="var(--text-secondary)" />
                <YAxis stroke="var(--text-secondary)" label={{ value: 'Pontos', angle: -90, position: 'insideLeft', fill: 'var(--text-secondary)' }} />
                <Tooltip
                  contentStyle={{
                    background: 'var(--surface-2)',
                    border: '1px solid var(--border-color)',
                    borderRadius: 'var(--radius-sm)'
                  }}
                />
                <Bar dataKey="points" fill={prediction.team.color} name="Pontos" />
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
