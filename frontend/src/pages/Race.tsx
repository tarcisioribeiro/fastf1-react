import { useEffect, useState } from 'react';
import { f1Api } from '../services/api';
import { SessionData } from '../types/f1';
import Table from '../components/Table';
import Podium from '../components/Podium';
import Card from '../components/Card';
import LoadingWithRetry from '../components/LoadingWithRetry';
import './Race.css';

export default function Race() {
  const [raceData, setRaceData] = useState<SessionData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dataAvailable, setDataAvailable] = useState(true);

  useEffect(() => {
    loadRace();
    // Só fazer polling se os dados estiverem disponíveis
    const interval = setInterval(() => {
      if (dataAvailable) {
        loadRace(false); // false = não mostrar loading em updates
      }
    }, 300000); // Atualizar a cada 5 minutos
    return () => clearInterval(interval);
  }, [dataAvailable]);

  const loadRace = async (showLoading = true) => {
    try {
      if (showLoading) {
        setLoading(true);
      }
      setError(null);
      const data = await f1Api.getLatestRace();
      setRaceData(data);
      setDataAvailable(true);
    } catch (err: any) {
      // Se for 404, dados ainda não foram populados
      if (err.response?.status === 404) {
        setError('Dados ainda não disponíveis. Aguardando coleta...');
        setDataAvailable(false);
      } else {
        setError(err.message || 'Erro ao carregar dados');
      }
      console.error('Erro ao carregar dados da corrida:', err);
    } finally {
      if (showLoading) {
        setLoading(false);
      }
    }
  };

  if (loading && !raceData) {
    return (
      <div className="race-page">
        <LoadingWithRetry
          message="Carregando dados da corrida"
          hint="Conectando à API FastF1 e buscando os resultados..."
        />
      </div>
    );
  }

  if (error || !raceData) {
    const isTimeout = error?.includes('timeout');
    return (
      <div className="race-page">
        <div className="error-container">
          <h2>⚠️ Erro ao carregar dados</h2>
          <p>{error || 'Nenhum dado disponível'}</p>
          {isTimeout && (
            <p className="error-hint">
              A API pode estar processando muitos dados. Tente novamente em alguns instantes.
            </p>
          )}
          <button onClick={loadRace} className="retry-button">
            Tentar Novamente
          </button>
        </div>
      </div>
    );
  }

  const { raceInfo, results } = raceData;
  const topThree = results.slice(0, 3);
  const columns = [
    { key: 'position', label: 'Pos.' },
    { key: 'driver', label: 'Piloto' },
    { key: 'team', label: 'Equipe' },
    { key: 'time', label: 'Tempo' },
    { key: 'points', label: 'Pontos' },
  ];

  // Formatar data
  const raceDate = new Date(raceInfo.date);
  const formattedDate = raceDate.toLocaleDateString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  });

  return (
    <div className="race-page">
      <div className="page-header">
        <h1>🏆 {raceInfo.eventName}</h1>
        <p className="subtitle">{raceInfo.location} • {formattedDate}</p>
        <p className="round-info">Rodada {raceInfo.round}</p>
      </div>

      {topThree.length === 3 && (
        <div className="podium-section">
          <h2>🏆 Pódio</h2>
          <Podium
            entries={topThree.map((result, index) => ({
              position: index + 1,
              name: result.driver,
              team: result.team,
              points: result.points,
            }))}
            title="Pódio"
          />
        </div>
      )}

      <div className="stats-cards">
        {topThree.map((result, index) => (
          <Card
            key={result.position}
            title={result.driver}
            subtitle={result.team}
            value={result.time}
            footer={`${result.points} pontos`}
            color={index === 0 ? 'gold' : index === 1 ? 'silver' : 'bronze'}
          />
        ))}
      </div>

      <div className="table-section">
        <h2>📊 Resultados Completos</h2>
        <Table
          data={results}
          columns={columns}
          highlightPositions={[1, 2, 3]}
        />
      </div>
    </div>
  );
}
