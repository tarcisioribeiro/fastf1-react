import { useEffect, useState } from 'react';
import { f1Api } from '../services/api';
import { SessionData } from '../types/f1';
import Table from '../components/Table';
import Podium from '../components/Podium';
import LoadingWithRetry from '../components/LoadingWithRetry';
import Button from '../components/Button';
import { formatDateBR } from '../utils/dateFormatter';
import { translateDriverStatus } from '../utils/translations';
import { formatDriverName, formatTime as formatTimeUtil, formatStatusDisplay } from '../utils/formatters';
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
          <Button onClick={loadRace} aria-label="Tentar carregar dados da corrida novamente">
            Tentar Novamente
          </Button>
        </div>
      </div>
    );
  }

  const { raceInfo, results } = raceData;
  const topThree = results.slice(0, 3);

  // Adicionar campo de número do piloto formatado para exibição
  const formattedResults = results.map(result => {
    const translatedStatus = translateDriverStatus(result.status || 'Unknown');
    const statusDisplay = formatStatusDisplay(result.status || 'Unknown', translatedStatus);

    return {
      ...result,
      driverWithNumber: formatDriverName(result),
      translatedStatus: statusDisplay.display,
      translatedStatusClass: statusDisplay.className,
      time: formatTimeUtil(result.time),
    };
  });

  const columns = [
    { key: 'position', label: 'Posição' },
    { key: 'driverWithNumber', label: 'Piloto' },
    { key: 'team', label: 'Equipe' },
    { key: 'time', label: 'Tempo' },
    { key: 'points', label: 'Pontos' },
    { key: 'translatedStatus', label: 'Status' },
  ];

  return (
    <div className="race-page">
      <div className="page-header">
        <h1>🏆 {raceInfo.eventName}</h1>
        <p className="subtitle">{raceInfo.location} • {formatDateBR(raceInfo.date)}</p>
        <p className="round-info">Rodada {raceInfo.round}</p>
      </div>

      {topThree.length === 3 && (
        <Podium
          title="🏆 Pódio"
          entries={topThree.map((result, index) => ({
            position: index + 1,
            name: result.driver,
            driverNumber: result.driver_number,
            team: result.team,
            teamColor: result.teamColor,
            points: result.points,
          }))}
        />
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
