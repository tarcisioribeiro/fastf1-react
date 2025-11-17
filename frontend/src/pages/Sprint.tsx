import { useEffect, useState } from 'react';
import { f1Api } from '../services/api';
import { SprintData } from '../types/f1';
import Table from '../components/Table';
import Podium from '../components/Podium';
import LoadingWithRetry from '../components/LoadingWithRetry';
import { formatDateBR } from '../utils/dateFormatter';
import { translateDriverStatus } from '../utils/translations';
import { formatDriverName, formatTeamName, formatTime as formatTimeUtil, formatStatusDisplay } from '../utils/formatters';
import './Race.css'; // Reusing Race styles

export default function Sprint() {
  const [sprintData, setSprintData] = useState<SprintData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dataAvailable, setDataAvailable] = useState(true);

  useEffect(() => {
    loadSprint();
    // Só fazer polling se os dados estiverem disponíveis
    const interval = setInterval(() => {
      if (dataAvailable) {
        loadSprint(false); // false = não mostrar loading em updates
      }
    }, 300000); // Atualizar a cada 5 minutos
    return () => clearInterval(interval);
  }, [dataAvailable]);

  const loadSprint = async (showLoading = true) => {
    try {
      if (showLoading) {
        setLoading(true);
      }
      setError(null);
      const data = await f1Api.getLatestSprint();
      setSprintData(data);
      setDataAvailable(true);
    } catch (err: any) {
      // Se for 404, dados ainda não foram populados
      if (err.response?.status === 404) {
        setError('Dados ainda não disponíveis. Aguardando coleta...');
        setDataAvailable(false);
      } else {
        setError(err.message || 'Erro ao carregar dados');
      }
      console.error('Erro ao carregar dados do sprint:', err);
    } finally {
      if (showLoading) {
        setLoading(false);
      }
    }
  };

  if (loading && !sprintData) {
    return (
      <div className="race-page">
        <LoadingWithRetry
          message="Carregando dados do sprint"
          hint="Conectando à API FastF1 e buscando os resultados..."
        />
      </div>
    );
  }

  if (error || !sprintData) {
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
          <button onClick={() => loadSprint()} className="retry-button">
            Tentar Novamente
          </button>
        </div>
      </div>
    );
  }

  const { raceInfo, results } = sprintData;
  const topThree = results.slice(0, 3);

  // Adicionar campo de número do piloto formatado para exibição
  const formattedResults = results.map(result => {
    const translatedStatus = translateDriverStatus(result.status || 'Finished');
    const statusDisplay = formatStatusDisplay(result.status || 'Finished', translatedStatus);

    return {
      position: result.position,
      driverNumber: result.driver_number,
      driverCode: result.driver_code,
      driverName: result.driver_name || result.driver,
      driverWithNumber: formatDriverName(result),
      team: formatTeamName(result),
      teamColor: result.team_color || result.teamColor,
      time: formatTimeUtil(result.time),
      points: result.points,
      status: statusDisplay.display,
      statusClass: statusDisplay.className,
    };
  });

  const columns = [
    { key: 'position', label: 'Posição' },
    { key: 'driverWithNumber', label: 'Piloto' },
    { key: 'team', label: 'Equipe' },
    { key: 'time', label: 'Tempo' },
    { key: 'points', label: 'Pontos' },
    { key: 'status', label: 'Status' },
  ];

  return (
    <div className="race-page">
      <div className="page-header">
        <h1>🚀 {raceInfo.eventName} - Sprint</h1>
        <p className="subtitle">{raceInfo.location} • {formatDateBR(raceInfo.date)}</p>
        <p className="round-info">Rodada {raceInfo.round}</p>
      </div>

      {topThree.length === 3 && (
        <Podium
          title="🏆 Top 3"
          entries={topThree.map((result, index) => ({
            position: index + 1,
            name: result.driver_name || result.driver,
            driverNumber: result.driver_number,
            team: result.team_name || result.team,
            teamColor: result.team_color || result.teamColor,
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
