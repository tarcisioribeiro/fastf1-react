import { useState, useEffect } from 'react';
import { f1Api } from '../services/api';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';
import Card from '../components/Card';
import '../styles/PredictionsPole.css';

interface DriverPrediction {
  driver: {
    code: string;
    fullName: string;
  };
  poleProbability: number;
}

interface TeamPrediction {
  team: {
    id: number;
    name: string;
    color: string;
  };
  poleProbability: number;
  bestDriver: {
    code: string;
    fullName: string;
  };
  drivers: DriverPrediction[];
}

interface PoleData {
  circuit: {
    id: number;
    name: string;
    location: string;
    country: string;
  };
  year: number;
  predictions: TeamPrediction[];
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

function PredictionsPoleConstructor() {
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

        const result = await f1Api.getPolePredictionConstructor(params);
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
        <h1>Previsão de Pole Position - Equipes</h1>
        <LoadingSpinner message="Carregando previsões de pole position..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="predictions-page">
        <h1>Previsão de Pole Position - Equipes</h1>
        <ErrorMessage message={error} />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="predictions-page">
        <h1>Previsão de Pole Position - Equipes</h1>
        <p>Nenhum dado disponível.</p>
      </div>
    );
  }

  return (
    <div className="predictions-page">
      <div className="page-header">
        <h1>Previsão de Pole Position - Equipes</h1>
        <p className="page-subtitle">
          Probabilidades de pole position por equipe (melhor piloto)
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
            <Card key={pred.team.id} className="team-prediction-card">
              <div className="prediction-header">
                <div className="position-badge" style={{ backgroundColor: getProbabilityColor(pred.poleProbability) }}>
                  #{index + 1}
                </div>
                <div className="team-info">
                  <h3 style={{ color: pred.team.color }}>
                    {pred.team.name}
                  </h3>
                  <p className="best-driver">
                    Melhor: {pred.bestDriver.fullName} ({pred.bestDriver.code})
                  </p>
                </div>
              </div>

              <div className="probability-section">
                <div className="probability-main">
                  <span className="probability-value">{pred.poleProbability.toFixed(1)}%</span>
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

              {/* Comparação de pilotos */}
              {pred.drivers.length > 0 && (
                <div className="drivers-comparison">
                  <h4>Pilotos da Equipe:</h4>
                  <div className="drivers-list">
                    {pred.drivers.map((driver) => (
                      <div key={driver.driver.code} className="driver-item">
                        <span className="driver-code-small">{driver.driver.code}</span>
                        <div className="mini-bar">
                          <div
                            className="mini-bar-fill"
                            style={{
                              width: `${driver.poleProbability}%`,
                              backgroundColor: pred.team.color
                            }}
                          />
                        </div>
                        <span className="driver-probability">{driver.poleProbability.toFixed(1)}%</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </Card>
          ))}
        </div>
      )}

      {/* Top 3 Equipes */}
      {data.predictions.length >= 3 && (
        <Card className="top-3-card">
          <h2>Top 3 Equipes com Maior Chance de Pole</h2>
          <div className="podium">
            {data.predictions.slice(0, 3).map((pred, index) => (
              <div key={pred.team.id} className={`podium-position podium-${index + 1}`}>
                <div className="podium-trophy">
                  {index === 0 && '🥇'}
                  {index === 1 && '🥈'}
                  {index === 2 && '🥉'}
                </div>
                <div className="podium-team" style={{ color: pred.team.color }}>
                  {pred.team.name}
                </div>
                <div className="podium-probability">{pred.poleProbability.toFixed(1)}%</div>
                <div className="podium-driver-small">{pred.bestDriver.code}</div>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}

export default PredictionsPoleConstructor;
