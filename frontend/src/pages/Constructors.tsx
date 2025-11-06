import { useEffect, useState } from 'react';
import { f1Api } from '../services/api';
import { Constructor } from '../types/f1';
import Table from '../components/Table';
import Podium from '../components/Podium';
import Card from '../components/Card';
import LoadingWithRetry from '../components/LoadingWithRetry';
import './Constructors.css';

export default function Constructors() {
  const [constructors, setConstructors] = useState<Constructor[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadConstructors();
    const interval = setInterval(loadConstructors, 60000); // Atualizar a cada minuto
    return () => clearInterval(interval);
  }, []);

  const loadConstructors = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await f1Api.getConstructorStandings();
      setConstructors(data);
    } catch (err: any) {
      setError(err.message || 'Erro ao carregar dados');
      console.error('Erro ao carregar classificação de construtores:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading && constructors.length === 0) {
    return (
      <div className="constructors-page">
        <LoadingWithRetry
          message="Carregando classificação dos construtores"
          hint="Conectando à API FastF1 e buscando os dados..."
        />
      </div>
    );
  }

  if (error) {
    return (
      <div className="constructors-page">
        <div className="error-container">
          <h2>⚠️ Erro ao carregar dados</h2>
          <p>{error}</p>
          <button onClick={loadConstructors} className="retry-button">
            Tentar Novamente
          </button>
        </div>
      </div>
    );
  }

  const topThree = constructors.slice(0, 3);
  const columns = [
    { key: 'position', label: 'Pos.' },
    { key: 'team', label: 'Equipe' },
    { key: 'points', label: 'Pontos' },
    { key: 'wins', label: 'Vitórias' },
  ];

  return (
    <div className="constructors-page">
      <div className="page-header">
        <h1>🏁 Classificação de Construtores</h1>
        <p className="subtitle">Campeonato Mundial de Construtores 2025</p>
      </div>

      {topThree.length === 3 && (
        <div className="podium-section">
          <h2>🏆 Pódio do Campeonato</h2>
          <Podium
            first={{
              name: topThree[0].team,
              points: topThree[0].points,
              wins: topThree[0].wins,
            }}
            second={{
              name: topThree[1].team,
              points: topThree[1].points,
              wins: topThree[1].wins,
            }}
            third={{
              name: topThree[2].team,
              points: topThree[2].points,
              wins: topThree[2].wins,
            }}
          />
        </div>
      )}

      <div className="stats-cards">
        {topThree.map((constructor, index) => (
          <Card
            key={constructor.position}
            title={constructor.team}
            value={`${constructor.points} pts`}
            footer={`${constructor.wins} vitórias`}
            color={index === 0 ? 'gold' : index === 1 ? 'silver' : 'bronze'}
          />
        ))}
      </div>

      <div className="table-section">
        <h2>📊 Classificação Completa</h2>
        <Table
          data={constructors}
          columns={columns}
          highlightPositions={[1, 2, 3]}
        />
      </div>
    </div>
  );
}
