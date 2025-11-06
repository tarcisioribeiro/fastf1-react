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

  useEffect(() => {
    loadRace();
    const interval = setInterval(loadRace, 300000); // Atualizar a cada 5 minutos
    return () => clearInterval(interval);
  }, []);

  const loadRace = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await f1Api.getLatestRace();
      setRaceData(data);
    } catch (err: any) {
      setError(err.message || 'Erro ao carregar dados');
      console.error('Erro ao carregar dados da corrida:', err);
    } finally {
      setLoading(false);
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
            first={{
              name: topThree[0].driver,
              team: topThree[0].team,
              points: topThree[0].points,
            }}
            second={{
              name: topThree[1].driver,
              team: topThree[1].team,
              points: topThree[1].points,
            }}
            third={{
              name: topThree[2].driver,
              team: topThree[2].team,
              points: topThree[2].points,
            }}
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
