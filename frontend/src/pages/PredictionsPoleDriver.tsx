import { useState, useEffect } from 'react';
import { f1Api } from '../services/api';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';
import Card from '../components/Card';
import '../styles/PredictionsPole.css';
import Icon from '../components/Icon';

interface DriverPrediction {
  driver: {
    id: number;
    code: string;
    fullName: string;
    number: number;
  };
  team: {
    name: string;
    color: string;
  };
  poleProbability: number;
  confidence: string;
  recentForm: {
    avgQualifyingPosition: number;
    polesRecent: number;
    frontRowRecent: number;
  };
  circuitHistory: {
    avgQualifyingPosition: number;
    polesAtCircuit: number;
  };
}

interface PoleData {
  circuit: {
    id: number;
    name: string;
    location: string;
    country: string;
  };
  year: number;
  predictions: DriverPrediction[];
  modelInfo: any;
}

interface PoleTimePrediction {
  predicted_time_seconds: number;
  predicted_time_formatted: string;
  confidence: string;
  historical_avg: number | null;
  historical_min: number | null;
  historical_max: number | null;
  num_historical_samples: number;
  circuit: {
    id: number;
    name: string;
    length_km: number;
    corners: number;
  };
}

function PredictionsPoleDriver() {
  const [data, setData] = useState<PoleData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [circuits, setCircuits] = useState<any[]>([]);
  const [selectedCircuit, setSelectedCircuit] = useState<number | undefined>();
  const [selectedYear, setSelectedYear] = useState<number>(new Date().getFullYear());
  const [poleTimePrediction, setPoleTimePrediction] = useState<PoleTimePrediction | null>(null);

  // Carregar circuitos
  useEffect(() => {
    const loadCircuits = async () => {
      try {
        const response = await f1Api.getAvailableCircuits();
        // A API retorna { status: 'success', circuits: [...] }
        setCircuits(Array.isArray(response?.circuits) ? response.circuits : []);
      } catch (err) {
        console.error('Erro ao carregar circuitos:', err);
        setCircuits([]); // Garantir que seja um array vazio em caso de erro
      }
    };
    loadCircuits();
  }, []);

  // Carregar previsões
  useEffect(() => {
    const loadPredictions = async () => {
      try {
        setLoading(true);
        setError(null);

        const params: any = {
          year: selectedYear
        };

        if (selectedCircuit) {
          params.circuit_id = selectedCircuit;
        }

        const result = await f1Api.getPolePredictionDriver(params);
        setData(result);

        // Carregar previsão de tempo da pole se temos o circuito
        if (result?.circuit?.id) {
          try {
            const timePrediction = await f1Api.getPoleTimePrediction({
              circuit_id: result.circuit.id,
              year: selectedYear
            });
            if (timePrediction?.prediction) {
              setPoleTimePrediction(timePrediction.prediction);
            }
          } catch (timeErr) {
            console.warn('Não foi possível carregar previsão de tempo:', timeErr);
            setPoleTimePrediction(null);
          }
        }
      } catch (err: any) {
        console.error('Erro ao carregar previsões:', err);
        setError(err.response?.data?.error || err.message || 'Erro ao carregar previsões');
      } finally {
        setLoading(false);
      }
    };

    loadPredictions();
  }, [selectedCircuit, selectedYear]);

  const getConfidenceClass = (confidence: string) => {
    switch (confidence) {
      case 'high': return 'confidence-high';
      case 'medium': return 'confidence-medium';
      case 'low': return 'confidence-low';
      default: return '';
    }
  };

  const getProbabilityColor = (probability: number) => {
    if (probability >= 70) return '#ffd700'; // Gold
    if (probability >= 50) return '#c0c0c0'; // Silver
    if (probability >= 30) return '#cd7f32'; // Bronze
    return '#ddd';
  };

  if (loading) {
    return (
      <div className="predictions-page">
        <h1>Previsão de Pole Position - Pilotos</h1>
        <LoadingSpinner message="Carregando previsões de pole position..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="predictions-page">
        <h1>Previsão de Pole Position - Pilotos</h1>
        <ErrorMessage message={error} />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="predictions-page">
        <h1>Previsão de Pole Position - Pilotos</h1>
        <p>Nenhum dado disponível.</p>
      </div>
    );
  }

  return (
    <div className="predictions-page">
      <div className="page-header">
        <h1>Previsão de Pole Position - Pilotos</h1>
        <p className="page-subtitle">
          Probabilidades de pole position usando Machine Learning (XGBoost)
        </p>
      </div>

      {/* Filtros */}
      <Card className="filters-card">
        <div className="filters-grid">
          <div className="filter-group">
            <label htmlFor="circuit-select">Circuito:</label>
            <select
              id="circuit-select"
              value={selectedCircuit || ''}
              onChange={(e) => setSelectedCircuit(e.target.value ? parseInt(e.target.value) : undefined)}
            >
              <option value="">Próxima corrida</option>
              {circuits.map((circuit) => (
                <option key={circuit.id} value={circuit.id}>
                  {circuit.name} ({circuit.location})
                </option>
              ))}
            </select>
          </div>

          <div className="filter-group">
            <label htmlFor="year-select">Ano:</label>
            <select
              id="year-select"
              value={selectedYear}
              onChange={(e) => setSelectedYear(parseInt(e.target.value))}
            >
              <option value="2025">2025</option>
              <option value="2026">2026</option>
              <option value="2027">2027</option>
              <option value="2028">2028</option>
              <option value="2029">2029</option>
              <option value="2030">2030</option>
            </select>
          </div>
        </div>
      </Card>

      {/* Informações do Circuito */}
      <Card className="circuit-info-card">
        <h2>{data.circuit.name}</h2>
        <p className="circuit-location">
          {data.circuit.location}, {data.circuit.country}
        </p>

        {/* Tempo de Pole Previsto */}
        {poleTimePrediction && (
          <div className="pole-time-prediction">
            <h3>Tempo de Pole Previsto</h3>
            <div className="pole-time-value">
              {poleTimePrediction.predicted_time_formatted}
            </div>
            {data.predictions.length > 0 && (
              <div className="pole-favorite-driver">
                <span className="driver-name">{data.predictions[0].driver.fullName}</span>
                <span className="team-name" style={{ color: data.predictions[0].team.color }}>
                  {data.predictions[0].team.name}
                </span>
              </div>
            )}
            <span className={`confidence-badge ${getConfidenceClass(poleTimePrediction.confidence)}`}>
              {poleTimePrediction.confidence === 'high' ? 'Alta' : poleTimePrediction.confidence === 'medium' ? 'Média' : 'Baixa'} confiança
            </span>
            {poleTimePrediction.historical_avg && (
              <p className="historical-info">
                Histórico: {(poleTimePrediction.historical_min! / 60).toFixed(0)}:{(poleTimePrediction.historical_min! % 60).toFixed(3).padStart(6, '0')} - {(poleTimePrediction.historical_max! / 60).toFixed(0)}:{(poleTimePrediction.historical_max! % 60).toFixed(3).padStart(6, '0')}
                ({poleTimePrediction.num_historical_samples} amostras)
              </p>
            )}
          </div>
        )}

        <p className="model-info">
          Modelo treinado com {data.modelInfo?.training_samples?.toLocaleString()} amostras
          (Accuracy: {(data.modelInfo?.metrics?.test?.accuracy * 100).toFixed(1)}%)
        </p>
      </Card>

      {/* Lista de Previsões */}
      {data.predictions.length === 0 ? (
        <Card>
          <p>Nenhuma previsão disponível para este circuito/ano.</p>
        </Card>
      ) : (
        <div className="predictions-grid">
          {data.predictions.map((pred, index) => (
            <Card key={pred.driver.id} className="driver-prediction-card">
              <div className="prediction-header">
                <div className="position-badge" style={{ backgroundColor: getProbabilityColor(pred.poleProbability) }}>
                  #{index + 1}
                </div>
                <div className="driver-info">
                  <h3>
                    <span className="driver-code">{pred.driver.code}</span>
                    {pred.driver.fullName}
                  </h3>
                  <p className="team-name" style={{ color: pred.team.color }}>
                    {pred.team.name}
                  </p>
                </div>
              </div>

              <div className="probability-section">
                <div className="probability-main">
                  <span className="probability-value">{pred.poleProbability.toFixed(1)}%</span>
                  <span className={`confidence-badge ${getConfidenceClass(pred.confidence)}`}>
                    {pred.confidence === 'high' ? 'Alta' : pred.confidence === 'medium' ? 'Média' : 'Baixa'} confiança
                  </span>
                </div>

                <div className="probability-bar">
                  <div
                    className="probability-fill"
                    style={{
                      width: `${pred.poleProbability}%`,
                      backgroundColor: getProbabilityColor(pred.poleProbability)
                    }}
                  />
                </div>
              </div>

              <div className="stats-grid">
                <div className="stat-box">
                  <span className="stat-label">Forma Recente</span>
                  <span className="stat-value">P{pred.recentForm.avgQualifyingPosition.toFixed(1)}</span>
                  <span className="stat-detail">
                    {pred.recentForm.polesRecent} poles, {pred.recentForm.frontRowRecent} 1ª fila
                  </span>
                </div>

                <div className="stat-box">
                  <span className="stat-label">Neste Circuito</span>
                  <span className="stat-value">P{pred.circuitHistory.avgQualifyingPosition.toFixed(1)}</span>
                  <span className="stat-detail">
                    {pred.circuitHistory.polesAtCircuit} pole{pred.circuitHistory.polesAtCircuit !== 1 ? 's' : ''}
                  </span>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Top 3 Favoritos */}
      {data.predictions.length >= 3 && (
        <Card className="top-3-card">
          <h2>Top 3 Favoritos para Pole Position</h2>
          <div className="podium">
            {data.predictions.slice(0, 3).map((pred, index) => (
              <div key={pred.driver.id} className={`podium-position podium-${index + 1}`}>
                <div className="podium-trophy">
                  {index === 0 && <Icon name="medal" size={14} color="var(--gold)" />}
                  {index === 1 && <Icon name="medal" size={14} color="var(--silver)" />}
                  {index === 2 && <Icon name="medal" size={14} color="var(--bronze)" />}
                </div>
                <div className="podium-driver">{pred.driver.code}</div>
                <div className="podium-probability">{pred.poleProbability.toFixed(1)}%</div>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}

export default PredictionsPoleDriver;
