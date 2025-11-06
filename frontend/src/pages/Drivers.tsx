import { useEffect, useState } from 'react';
import { f1Api } from '../services/api';
import { Driver } from '../types/f1';
import Table from '../components/Table';
import Podium from '../components/Podium';
import Card from '../components/Card';
import LoadingWithRetry from '../components/LoadingWithRetry';
import './Drivers.css';

export default function Drivers() {
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadDrivers();
    const interval = setInterval(loadDrivers, 60000); // Atualizar a cada minuto
    return () => clearInterval(interval);
  }, []);

  const loadDrivers = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await f1Api.getDriverStandings();
      setDrivers(data);
    } catch (err: any) {
      setError(err.message || 'Erro ao carregar dados');
      console.error('Erro ao carregar classificação de pilotos:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading && drivers.length === 0) {
    return (
      <div className="drivers-page">
        <LoadingWithRetry
          message="Carregando classificação dos pilotos"
          hint="Conectando à API FastF1 e buscando os dados..."
        />
      </div>
    );
  }

  if (error) {
    return (
      <div className="drivers-page">
        <div className="error-container">
          <h2>⚠️ Erro ao carregar dados</h2>
          <p>{error}</p>
          <button onClick={loadDrivers} className="retry-button">
            Tentar Novamente
          </button>
        </div>
      </div>
    );
  }

  const topThree = drivers.slice(0, 3);
  const columns = [
    { key: 'position', label: 'Pos.' },
    { key: 'name', label: 'Piloto' },
    { key: 'team', label: 'Equipe' },
    { key: 'points', label: 'Pontos' },
    { key: 'wins', label: 'Vitórias' },
  ];

  return (
    <div className="drivers-page">
      <div className="page-header">
        <h1>👤 Classificação de Pilotos</h1>
        <p className="subtitle">Campeonato Mundial de Pilotos 2025</p>
      </div>

      {topThree.length === 3 && (
        <div className="podium-section">
          <h2>🏆 Pódio do Campeonato</h2>
          <Podium
            first={{
              name: topThree[0].name,
              team: topThree[0].team,
              points: topThree[0].points,
            }}
            second={{
              name: topThree[1].name,
              team: topThree[1].team,
              points: topThree[1].points,
            }}
            third={{
              name: topThree[2].name,
              team: topThree[2].team,
              points: topThree[2].points,
            }}
          />
        </div>
      )}

      <div className="stats-cards">
        {topThree.map((driver, index) => (
          <Card
            key={driver.position}
            title={driver.name}
            subtitle={driver.team}
            value={`${driver.points} pts`}
            footer={`${driver.wins} vitórias`}
            color={index === 0 ? 'gold' : index === 1 ? 'silver' : 'bronze'}
          />
        ))}
      </div>

      <div className="table-section">
        <h2>📊 Classificação Completa</h2>
        <Table
          data={drivers}
          columns={columns}
          highlightPositions={[1, 2, 3]}
        />
      </div>
    </div>
  );
}
