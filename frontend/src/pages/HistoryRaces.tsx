import { useEffect, useState, useCallback } from 'react';
import { f1Api } from '../services/api';
import HistoryFilters from '../components/HistoryFilters';
import Table from '../components/Table';
import Podium from '../components/Podium';
import LoadingWithRetry from '../components/LoadingWithRetry';
import { formatDateBR } from '../utils/dateFormatter';
import { translateDriverStatus } from '../utils/translations';
import { formatTime as formatTimeUtil, formatStatusDisplay } from '../utils/formatters';
import './HistoryRaces.css';

interface RaceResult {
  position: number;
  driver: {
    code: string;
    fullName: string;
    number: string;
  };
  team: {
    name: string;
    color: string;
  };
  points: number;
  status: string;
  time?: string;
  fastestLap?: boolean;
}

interface HistoricalRace {
  sessionId: number;
  eventName: string;
  circuit: string;
  location: string;
  country: string;
  date: string;
  year: number;
  round: number;
  results: RaceResult[];
}

export default function HistoryRaces() {
  const [races, setRaces] = useState<HistoricalRace[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filtering, setFiltering] = useState(false); // Estado de transição de filtro
  const [isInitialLoad, setIsInitialLoad] = useState(true); // Distinguir carregamento inicial

  // Paginação
  const [currentPage, setCurrentPage] = useState(1);
  const racesPerPage = 5; // Reduzido para melhor visualização

  // Filtros
  const [filters, setFilters] = useState({
    year: '',
    circuit: '',
    driver: '',
    team: ''
  });

  const loadHistory = async (appliedFilters: any, isInitial: boolean = false) => {
    try {
      // Apenas mostrar loading completo no carregamento inicial
      // Durante filtragens, usar apenas o indicador 'filtering'
      if (isInitial) {
        setLoading(true);
      }
      setError(null);

      const data = await f1Api.getRaceHistory(Object.keys(appliedFilters).length > 0 ? appliedFilters : undefined);
      setRaces(data.races || []);
      setCurrentPage(1); // Reset página ao filtrar
    } catch (err: any) {
      setError(err.message || 'Erro ao carregar histórico');
      console.error('Erro ao carregar histórico de corridas:', err);
    } finally {
      if (isInitial) {
        setLoading(false);
        setIsInitialLoad(false);
      }
      setFiltering(false);
    }
  };

  // Debounce effect para aplicar filtros com delay suave
  useEffect(() => {
    setFiltering(true);
    const debounceTimer = setTimeout(() => {
      // Criar objeto de filtros apenas com valores preenchidos
      const appliedFilters: any = {};
      if (filters.year) appliedFilters.year = filters.year;
      if (filters.circuit) appliedFilters.circuit = filters.circuit;
      if (filters.driver) appliedFilters.driver = filters.driver;
      if (filters.team) appliedFilters.team = filters.team;

      // Passar isInitialLoad para distinguir carregamento inicial de filtragens
      loadHistory(appliedFilters, isInitialLoad);
    }, 500); // 500ms de delay para fluidez

    return () => {
      clearTimeout(debounceTimer);
    };
  }, [filters.year, filters.circuit, filters.driver, filters.team, isInitialLoad]);

  // Callback estável para mudança de filtros
  const handleFilterChange = useCallback((newFilters: typeof filters) => {
    setFilters(newFilters);
  }, []);

  // Paginação
  const indexOfLastRace = currentPage * racesPerPage;
  const indexOfFirstRace = indexOfLastRace - racesPerPage;
  const currentRaces = races.slice(indexOfFirstRace, indexOfLastRace);
  const totalPages = Math.ceil(races.length / racesPerPage);

  // Mostrar loading completo APENAS no carregamento inicial
  if (loading && isInitialLoad) {
    return (
      <div className="history-page">
        <LoadingWithRetry
          message="Carregando histórico de corridas"
          hint="Buscando todos os resultados disponíveis..."
        />
      </div>
    );
  }

  if (error) {
    return (
      <div className="history-page">
        <div className="error-container">
          <h2>⚠️ Erro ao carregar histórico</h2>
          <p>{error}</p>
          <button onClick={() => {
            const appliedFilters: any = {};
            if (filters.year) appliedFilters.year = filters.year;
            if (filters.circuit) appliedFilters.circuit = filters.circuit;
            if (filters.driver) appliedFilters.driver = filters.driver;
            if (filters.team) appliedFilters.team = filters.team;
            loadHistory(appliedFilters, false);
          }} className="retry-button">
            Tentar Novamente
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="history-page">
      <div className="history-header">
        <h1>📚 Histórico de Corridas</h1>
        <p className="history-subtitle">
          Total: {races.length} {races.length === 1 ? 'corrida' : 'corridas'}
        </p>
      </div>

      <HistoryFilters onFilterChange={handleFilterChange} />

      {/* Indicador de filtragem */}
      {filtering && !loading && (
        <div className="filtering-indicator">
          <div className="filtering-spinner"></div>
          <span>Aplicando filtros...</span>
        </div>
      )}

      {/* Lista de corridas */}
      <div className={`races-list ${filtering ? 'filtering' : ''}`}>
        {currentRaces.length === 0 ? (
          <div className="no-results">
            <p>Nenhuma corrida encontrada com os filtros aplicados.</p>
          </div>
        ) : (
          currentRaces.map((race) => {
            const topThree = race.results.slice(0, 3);

            // Formatar resultados para a tabela
            const formattedResults = race.results.map(result => {
              const translatedStatus = translateDriverStatus(result.status);
              const statusDisplay = formatStatusDisplay(result.status, translatedStatus);

              return {
                position: result.position,
                driverNumber: result.driver_number || result.driver?.number || '',
                driverCode: result.driver_code || result.driver?.code || '',
                driverName: result.driver || result.driver?.fullName || '',
                driverWithNumber: result.driver_number
                  ? `${result.driver_number} ${result.driver}`
                  : result.driver,
                team: result.team,
                teamColor: result.teamColor,
                time: formatTimeUtil(result.time),
                points: result.points,
                status: statusDisplay.display,
                statusClass: statusDisplay.className,
                fastestLap: result.fastestLap
              };
            });

            const columns = [
              { key: 'position', label: 'Pos.' },
              { key: 'driverWithNumber', label: 'Piloto' },
              { key: 'team', label: 'Equipe' },
              { key: 'time', label: 'Tempo' },
              { key: 'points', label: 'Pontos' },
              { key: 'status', label: 'Status' },
            ];

            return (
              <div key={race.sessionId} className="race-card-modern">
                {/* Header da corrida */}
                <div className="race-card-header">
                  <div className="race-title-section">
                    <h2>{race.eventName}</h2>
                    <div className="race-metadata">
                      <span className="race-circuit">🏁 {race.circuit}</span>
                      <span className="race-location">📍 {race.location}, {race.country}</span>
                      <span className="race-date">📅 {formatDateBR(race.date)}</span>
                      <span className="race-round">Round {race.round} • {race.year}</span>
                    </div>
                  </div>
                </div>

                {/* Pódio */}
                {topThree.length === 3 && (
                  <Podium
                    title="🏆 Pódio"
                    entries={topThree.map((result, index) => ({
                      position: index + 1,
                      name: result.driver?.fullName || result.driver || 'N/A',
                      driverNumber: result.driver_number || (result.driver?.number ? parseInt(result.driver.number) : undefined),
                      team: result.team?.name || result.team || 'N/A',
                      teamColor: result.teamColor || result.team?.color,
                      points: result.points,
                    }))}
                  />
                )}

                {/* Tabela de resultados */}
                <div className="table-section">
                  <h3>📊 Resultados Completos</h3>
                  <Table
                    data={formattedResults}
                    columns={columns}
                    showTeamColors={true}
                  />
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Paginação */}
      {totalPages > 1 && (
        <div className="pagination">
          <button
            onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
            disabled={currentPage === 1}
            className="pagination-btn"
          >
            ← Anterior
          </button>
          <span className="pagination-info">
            Página {currentPage} de {totalPages}
          </span>
          <button
            onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
            disabled={currentPage === totalPages}
            className="pagination-btn"
          >
            Próxima →
          </button>
        </div>
      )}
    </div>
  );
}
