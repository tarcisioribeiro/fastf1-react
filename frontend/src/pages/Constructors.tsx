import { useEffect, useState } from 'react';
import { f1Api } from '../services/api';
import { Constructor } from '../types/f1';
import Table from '../components/Table';
import Podium from '../components/Podium';
import LoadingWithRetry from '../components/LoadingWithRetry';
import './Constructors.css';
import Icon from '../components/Icon';

export default function Constructors() {
  const [constructors, setConstructors] = useState<Constructor[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dataAvailable, setDataAvailable] = useState(true);

  useEffect(() => {
    loadConstructors();
    // Só fazer polling se os dados estiverem disponíveis
    const interval = setInterval(() => {
      if (dataAvailable) {
        loadConstructors(false); // false = não mostrar loading em updates
      }
    }, 60000); // Atualizar a cada minuto
    return () => clearInterval(interval);
  }, [dataAvailable]);

  const loadConstructors = async (showLoading = true) => {
    try {
      if (showLoading) {
        setLoading(true);
      }
      setError(null);
      const data = await f1Api.getConstructorStandings();
      setConstructors(data);
      setDataAvailable(true);
    } catch (err: any) {
      // Se for 404, dados ainda não foram populados
      if (err.response?.status === 404) {
        setError('Dados ainda não disponíveis. Aguardando coleta...');
        setDataAvailable(false);
      } else {
        setError(err.message || 'Erro ao carregar dados');
      }
      console.error('Erro ao carregar classificação de construtores:', err);
    } finally {
      if (showLoading) {
        setLoading(false);
      }
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
          <h2><Icon name="warning" size={16} /> Erro ao carregar dados</h2>
          <p>{error}</p>
          <button onClick={loadConstructors} className="retry-button" aria-label="Tentar carregar classificação de construtores novamente">
            Tentar Novamente
          </button>
        </div>
      </div>
    );
  }

  const seasonYear = constructors[0]?.season_year;
  const topThree = constructors.slice(0, 3);
  const columns = [
    { key: 'position', label: 'Posição' },
    { key: 'team', label: 'Equipe' },
    { key: 'points', label: 'Pontos' },
    { key: 'wins', label: 'Vitórias' },
    { key: 'podiums', label: 'Pódios' },
  ];

  return (
    <div className="constructors-page">
      <div className="page-header">
        <h1><Icon name="flag" size={16} /> Classificação de Construtores</h1>
        <p className="subtitle">Campeonato Mundial de Construtores{seasonYear ? ` ${seasonYear}` : ''}</p>
      </div>

      {topThree.length === 3 && (
        <div className="podium-section">
          <Podium
            entries={topThree.map((constructor, index) => ({
              position: index + 1,
              name: constructor.team,
              teamColor: constructor.teamColor,
              points: constructor.points,
              wins: constructor.wins,
            }))}
          />
        </div>
      )}

      <div className="table-section">
        <h2><Icon name="chart" size={16} /> Classificação Completa</h2>
        <Table
          data={constructors}
          columns={columns}
          showTeamColors={true}
          showPodiumHighlight={true}
        />
      </div>
    </div>
  );
}
