import { useEffect, useState } from 'react';
import { f1Api } from '../services/api';
import { Driver } from '../types/f1';
import Table from '../components/Table';
import Podium from '../components/Podium';
import LoadingWithRetry from '../components/LoadingWithRetry';
import './Drivers.css';

export default function Drivers() {
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dataAvailable, setDataAvailable] = useState(true);

  useEffect(() => {
    loadDrivers();
    // Só fazer polling se os dados estiverem disponíveis
    const interval = setInterval(() => {
      if (dataAvailable) {
        loadDrivers(false); // false = não mostrar loading em updates
      }
    }, 60000); // Atualizar a cada minuto
    return () => clearInterval(interval);
  }, [dataAvailable]);

  const loadDrivers = async (showLoading = true) => {
    try {
      if (showLoading) {
        setLoading(true);
      }
      setError(null);
      const data = await f1Api.getDriverStandings();
      setDrivers(data);
      setDataAvailable(true);
    } catch (err: any) {
      // Se for 404, dados ainda não foram populados
      if (err.response?.status === 404) {
        setError('Dados ainda não disponíveis. Aguardando coleta...');
        setDataAvailable(false);
      } else {
        setError(err.message || 'Erro ao carregar dados');
      }
      console.error('Erro ao carregar classificação de pilotos:', err);
    } finally {
      if (showLoading) {
        setLoading(false);
      }
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

  // Adicionar campo de número do piloto formatado para exibição
  const formattedDrivers = drivers.map(driver => ({
    ...driver,
    nameWithNumber: driver.driver_number ? `${driver.driver_number} ${driver.name}` : driver.name,
  }));

  const columns = [
    { key: 'position', label: 'Pos.' },
    { key: 'nameWithNumber', label: 'Piloto' },
    { key: 'team', label: 'Equipe' },
    { key: 'points', label: 'Pontos' },
    { key: 'wins', label: 'Vitórias' },
    { key: 'podiums', label: 'Pódios' },
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
            entries={topThree.map((driver, index) => ({
              position: index + 1,
              name: driver.name,
              driverNumber: driver.driver_number,
              team: driver.team,
              teamColor: driver.teamColor,
              points: driver.points,
              wins: driver.wins,
            }))}
            title="Pódio do Campeonato"
          />
        </div>
      )}

      <div className="table-section">
        <h2>📊 Classificação Completa</h2>
        <Table
          data={formattedDrivers}
          columns={columns}
          showTeamColors={true}
        />
      </div>
    </div>
  );
}
