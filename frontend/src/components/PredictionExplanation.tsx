import { useState } from 'react';
import './PredictionExplanation.css';
import Icon from './Icon';

interface PredictionExplanationProps {
  predictionType: 'driver' | 'constructor' | 'pole-driver' | 'pole-constructor';
  selectedDriver?: string;
  selectedTeam?: string;
  selectedCircuit?: string;
  historyData?: Array<{
    year: number;
    position?: number;
    points?: number;
    team?: string;
    time?: string;
  }>;
  prediction?: {
    averagePosition?: number;
    averagePoints?: number;
    predictedPositionRange?: { min: number; max: number };
    probabilities?: {
      win: number;
      podium: number;
      points: number;
      pole?: number;
    };
  };
}

export default function PredictionExplanation({
  predictionType,
  selectedDriver,
  selectedTeam,
  selectedCircuit,
  historyData = [],
  prediction
}: PredictionExplanationProps) {
  const [expanded, setExpanded] = useState(false);

  // Calcular estatísticas dinâmicas dos dados históricos
  const stats = {
    totalRaces: historyData.length,
    avgPosition: historyData.length > 0
      ? historyData.reduce((sum, h) => sum + (h.position || 0), 0) / historyData.length
      : 0,
    avgPoints: historyData.length > 0
      ? historyData.reduce((sum, h) => sum + (h.points || 0), 0) / historyData.length
      : 0,
    wins: historyData.filter(h => h.position === 1).length,
    podiums: historyData.filter(h => h.position && h.position <= 3).length,
    poles: historyData.filter(h => h.position === 1).length, // Simplificado
  };

  // Determinar título e descrição baseado no tipo
  const getTitleAndDescription = () => {
    switch (predictionType) {
      case 'driver':
        return {
          title: 'Previsão de Desempenho de Piloto',
          description: 'Análise estatística baseada no histórico do piloto neste circuito'
        };
      case 'constructor':
        return {
          title: 'Previsão de Desempenho de Equipe',
          description: 'Análise estatística baseada no histórico da equipe neste circuito'
        };
      case 'pole-driver':
        return {
          title: 'Previsão de Pole Position - Piloto',
          description: 'Probabilidade de conquistar a pole position baseada em desempenho histórico'
        };
      case 'pole-constructor':
        return {
          title: 'Previsão de Pole Position - Equipe',
          description: 'Probabilidade de conquistar a pole position baseada em desempenho histórico'
        };
    }
  };

  const { title, description } = getTitleAndDescription();

  return (
    <div className="prediction-explanation">
      <div className="explanation-header" onClick={() => setExpanded(!expanded)}>
        <h3>
          <Icon name="book" size={16} /> {expanded ? 'Como funciona esta previsão?' : 'Clique para entender o cálculo'}
        </h3>
        <span className="expand-icon">
          <Icon name={expanded ? 'chevron-down' : 'chevron-right'} size={16} />
        </span>
      </div>

      {expanded && (
        <div className="explanation-content">
          <div className="explanation-intro">
            <h4>{title}</h4>
            <p>{description}</p>
          </div>

          {/* Seção 1: Dados de Entrada */}
          <div className="explanation-section">
            <h4><Icon name="chart" size={16} /> Passo 1: Dados de Entrada</h4>
            <div className="data-input-cards">
              {selectedDriver && (
                <div className="input-card">
                  <div className="input-label">Piloto Selecionado</div>
                  <div className="input-value">{selectedDriver}</div>
                </div>
              )}
              {selectedTeam && (
                <div className="input-card">
                  <div className="input-label">Equipe Selecionada</div>
                  <div className="input-value">{selectedTeam}</div>
                </div>
              )}
              {selectedCircuit && (
                <div className="input-card">
                  <div className="input-label">Circuito Selecionado</div>
                  <div className="input-value">{selectedCircuit}</div>
                </div>
              )}
              <div className="input-card highlight">
                <div className="input-label">Corridas Analisadas</div>
                <div className="input-value">{stats.totalRaces}</div>
              </div>
            </div>
          </div>

          {/* Seção 2: Cálculo de Estatísticas */}
          {historyData.length > 0 && (
            <div className="explanation-section">
              <h4><Icon name="calculator" size={16} /> Passo 2: Cálculo de Estatísticas Históricas</h4>
              <div className="calculation-steps">
                <div className="calc-step">
                  <div className="calc-formula">
                    <strong>Posição Média =</strong> (Soma de todas as posições) ÷ (Total de corridas)
                  </div>
                  <div className="calc-example">
                    <span className="example-label">Exemplo com seus dados:</span>
                    <div className="example-breakdown">
                      <span>Posições: {historyData.slice(0, 5).map(h => h.position).join(' + ')} {historyData.length > 5 && '...'}</span>
                      <span className="arrow">→</span>
                      <span>Total: {historyData.reduce((sum, h) => sum + (h.position || 0), 0)}</span>
                      <span className="arrow">÷</span>
                      <span>{stats.totalRaces} corridas</span>
                      <span className="arrow">=</span>
                      <span className="result">{stats.avgPosition.toFixed(2)}ª posição</span>
                    </div>
                  </div>
                </div>

                <div className="calc-step">
                  <div className="calc-formula">
                    <strong>Pontos Médios =</strong> (Soma de todos os pontos) ÷ (Total de corridas)
                  </div>
                  <div className="calc-example">
                    <span className="example-label">Exemplo com seus dados:</span>
                    <div className="example-breakdown">
                      <span>Pontos: {historyData.slice(0, 5).map(h => h.points).join(' + ')} {historyData.length > 5 && '...'}</span>
                      <span className="arrow">→</span>
                      <span>Total: {historyData.reduce((sum, h) => sum + (h.points || 0), 0)}</span>
                      <span className="arrow">÷</span>
                      <span>{stats.totalRaces} corridas</span>
                      <span className="arrow">=</span>
                      <span className="result">{stats.avgPoints.toFixed(2)} pontos</span>
                    </div>
                  </div>
                </div>

                <div className="calc-step">
                  <div className="calc-formula">
                    <strong>Contadores:</strong> Vitórias, Pódios, Pontos
                  </div>
                  <div className="calc-example">
                    <div className="counters-grid">
                      <div className="counter-box">
                        <span className="counter-value">{stats.wins}</span>
                        <span className="counter-label">Vitórias (P1)</span>
                      </div>
                      <div className="counter-box">
                        <span className="counter-value">{stats.podiums}</span>
                        <span className="counter-label">Pódios (P1-P3)</span>
                      </div>
                      <div className="counter-box">
                        <span className="counter-value">{historyData.filter(h => (h.points || 0) > 0).length}</span>
                        <span className="counter-label">Pontuações</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Seção 3: Cálculo de Probabilidades */}
          {prediction?.probabilities && historyData.length > 0 && (
            <div className="explanation-section">
              <h4><Icon name="trending-up" size={16} /> Passo 3: Cálculo de Probabilidades</h4>
              <div className="calculation-steps">
                <div className="calc-step">
                  <div className="calc-formula">
                    <strong>Probabilidade de Vitória =</strong> (Número de vitórias) ÷ (Total de corridas) × 100%
                  </div>
                  <div className="calc-example">
                    <div className="example-breakdown">
                      <span>{stats.wins} vitórias</span>
                      <span className="arrow">÷</span>
                      <span>{stats.totalRaces} corridas</span>
                      <span className="arrow">×</span>
                      <span>100%</span>
                      <span className="arrow">=</span>
                      <span className="result">{prediction.probabilities.win.toFixed(1)}%</span>
                    </div>
                  </div>
                </div>

                <div className="calc-step">
                  <div className="calc-formula">
                    <strong>Probabilidade de Pódio =</strong> (Número de pódios) ÷ (Total de corridas) × 100%
                  </div>
                  <div className="calc-example">
                    <div className="example-breakdown">
                      <span>{stats.podiums} pódios</span>
                      <span className="arrow">÷</span>
                      <span>{stats.totalRaces} corridas</span>
                      <span className="arrow">×</span>
                      <span>100%</span>
                      <span className="arrow">=</span>
                      <span className="result">{prediction.probabilities.podium.toFixed(1)}%</span>
                    </div>
                  </div>
                </div>

                <div className="calc-step">
                  <div className="calc-formula">
                    <strong>Probabilidade de Pontos =</strong> (Corridas com pontos) ÷ (Total de corridas) × 100%
                  </div>
                  <div className="calc-example">
                    <div className="example-breakdown">
                      <span>{historyData.filter(h => (h.points || 0) > 0).length} pontuações</span>
                      <span className="arrow">÷</span>
                      <span>{stats.totalRaces} corridas</span>
                      <span className="arrow">×</span>
                      <span>100%</span>
                      <span className="arrow">=</span>
                      <span className="result">{prediction.probabilities.points.toFixed(1)}%</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Seção 4: Resultado Final */}
          {prediction && (
            <div className="explanation-section final-result">
              <h4><Icon name="target" size={16} /> Passo 4: Resultado Final da Previsão</h4>
              <div className="result-summary">
                {prediction.predictedPositionRange && (
                  <div className="result-item">
                    <span className="result-label">Posição Prevista:</span>
                    <span className="result-value highlight">
                      {prediction.predictedPositionRange.min}ª - {prediction.predictedPositionRange.max}ª
                    </span>
                  </div>
                )}
                {prediction.averagePosition && (
                  <div className="result-item">
                    <span className="result-label">Posição Média Histórica:</span>
                    <span className="result-value">{prediction.averagePosition.toFixed(2)}ª</span>
                  </div>
                )}
                {prediction.averagePoints !== undefined && (
                  <div className="result-item">
                    <span className="result-label">Pontos Médios:</span>
                    <span className="result-value">{prediction.averagePoints.toFixed(2)}</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Disclaimer */}
          <div className="explanation-disclaimer">
            <h4><Icon name="warning" size={16} /> Importante</h4>
            <ul>
              <li>Esta previsão é <strong>100% baseada em dados históricos</strong> do piloto/equipe neste circuito específico</li>
              <li>Não considera fatores como: mudanças de regulamento, atualizações de carro, clima, estratégia, ou forma atual</li>
              <li>Quanto <strong>mais corridas no histórico</strong>, mais confiável é a previsão</li>
              <li>Use apenas como <strong>referência estatística</strong>, não como garantia de resultado</li>
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}
