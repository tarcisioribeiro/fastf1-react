import { useEffect, useState } from 'react';
import { f1Api } from '../services/api';
import { QualifyingData } from '../types/f1';
import Table from '../components/Table';
import LoadingWithRetry from '../components/LoadingWithRetry';
import './Qualifying.css';

export default function Qualifying() {
  const [qualifyingData, setQualifyingData] = useState<QualifyingData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dataAvailable, setDataAvailable] = useState(true);

  useEffect(() => {
    loadQualifying();
    // Só fazer polling se os dados estiverem disponíveis
    const interval = setInterval(() => {
      if (dataAvailable) {
        loadQualifying(false); // false = não mostrar loading em updates
      }
    }, 300000); // Atualizar a cada 5 minutos
    return () => clearInterval(interval);
  }, [dataAvailable]);

  const loadQualifying = async (showLoading = true) => {
    try {
      if (showLoading) {
        setLoading(true);
      }
      setError(null);
      const data = await f1Api.getLatestQualifying();
      setQualifyingData(data);
      setDataAvailable(true);
    } catch (err: any) {
      // Se for 404, dados ainda não foram populados
      if (err.response?.status === 404) {
        setError('Dados ainda não disponíveis. Aguardando coleta...');
        setDataAvailable(false);
      } else {
        setError(err.message || 'Erro ao carregar dados');
      }
      console.error('Erro ao carregar dados da qualificação:', err);
    } finally {
      if (showLoading) {
        setLoading(false);
      }
    }
  };

  if (loading && !qualifyingData) {
    return (
      <div className="qualifying-page">
        <LoadingWithRetry
          message="Carregando dados da qualificação"
          hint="Conectando à API FastF1 e buscando os tempos..."
        />
      </div>
    );
  }

  if (error || !qualifyingData) {
    const isTimeout = error?.includes('timeout');
    return (
      <div className="qualifying-page">
        <div className="error-container">
          <h2>⚠️ Erro ao carregar dados</h2>
          <p>{error || 'Nenhum dado disponível'}</p>
          {isTimeout && (
            <p className="error-hint">
              A API pode estar processando muitos dados. Tente novamente em alguns instantes.
            </p>
          )}
          <button onClick={loadQualifying} className="retry-button">
            Tentar Novamente
          </button>
        </div>
      </div>
    );
  }

  const { raceInfo, results } = qualifyingData;
  const polePosition = results[0];

  // Adicionar campo de número do piloto formatado para exibição
  const formattedResults = results.map(result => ({
    ...result,
    driverWithNumber: result.driver_number ? `${result.driver_number} ${result.driver}` : result.driver,
  }));

  const columns = [
    { key: 'position', label: 'Pos.' },
    { key: 'driverWithNumber', label: 'Piloto' },
    { key: 'team', label: 'Equipe' },
    { key: 'q1', label: 'Q1' },
    { key: 'q2', label: 'Q2' },
    { key: 'q3', label: 'Q3' },
  ];

  // Formatar data
  const qualifyingDate = new Date(raceInfo.date);
  const formattedDate = qualifyingDate.toLocaleDateString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  });

  return (
    <div className="qualifying-page">
      <div className="page-header">
        <h1>⏱️ {raceInfo.eventName}</h1>
        <p className="subtitle">{raceInfo.location} • {formattedDate}</p>
        <p className="round-info">Qualificação - Rodada {raceInfo.round}</p>
      </div>

      {polePosition && (
        <div className="pole-position-section">
          <h2>🏁 Pole Position</h2>
          <div className="pole-card">
            <div className="pole-icon">🏁</div>
            <h3>{polePosition.driver_number ? `${polePosition.driver_number} ` : ''}{polePosition.driver}</h3>
            <p className="pole-team" style={polePosition.teamColor ? {
              borderLeft: `4px solid ${polePosition.teamColor}`,
              paddingLeft: '8px'
            } : undefined}>{polePosition.team}</p>
            <p className="pole-time">{polePosition.q3 || polePosition.q2 || polePosition.q1}</p>
          </div>
        </div>
      )}

      <div className="table-section">
        <h2>📊 Resultados Completos</h2>
        <Table
          data={formattedResults}
          columns={columns}
          showTeamColors={true}
        />
      </div>
    </div>
  );
}
