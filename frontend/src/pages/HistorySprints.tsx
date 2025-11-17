import { useEffect, useState, useCallback } from 'react';
import { f1Api } from '../services/api';
import HistoryFilters from '../components/HistoryFilters';
import Table from '../components/Table';
import Podium from '../components/Podium';
import LoadingWithRetry from '../components/LoadingWithRetry';
import { formatDateBR } from '../utils/dateFormatter';
import { translateDriverStatus } from '../utils/translations';
import { formatTime as formatTimeUtil, formatStatusDisplay } from '../utils/formatters';
import './HistoryRaces.css'; // Reusing the same CSS

interface SprintResult {
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

interface HistoricalSprint {
  sessionId: number;
  eventName: string;
  circuit: string;
  location: string;
  country: string;
  date: string;
  year: number;
  round: number;
  results: SprintResult[];
}

export default function HistorySprints() {
  const [sprints, setSprints] = useState<HistoricalSprint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filtering, setFiltering] = useState(false); // Estado de transição de filtro
  const [isInitialLoad, setIsInitialLoad] = useState(true); // Distinguir carregamento inicial

  // Paginação
  const [currentPage, setCurrentPage] = useState(1);
  const sprintsPerPage = 5; // Reduzido para melhor visualização

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

      const data = await f1Api.getSprintHistory(Object.keys(appliedFilters).length > 0 ? appliedFilters : undefined);
      setSprints(data.sprints || []);
      setCurrentPage(1); // Reset página ao filtrar
    } catch (err: any) {
      setError(err.message || 'Erro ao carregar histórico');
      console.error('Erro ao carregar histórico de sprints:', err);
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
  const indexOfLastSprint = currentPage * sprintsPerPage;
  const indexOfFirstSprint = indexOfLastSprint - sprintsPerPage;
  const currentSprints = sprints.slice(indexOfFirstSprint, indexOfLastSprint);
  const totalPages = Math.ceil(sprints.length / sprintsPerPage);

  // Mostrar loading completo APENAS no carregamento inicial
  if (loading && isInitialLoad) {
    return (
      <div className="history-page">
        <LoadingWithRetry
          message="Carregando histórico de sprints"
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
        <h1>🚀 Histórico de Sprints</h1>
        <p className="history-subtitle">
          Total: {sprints.length} {sprints.length === 1 ? 'sprint' : 'sprints'}
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

      {/* Lista de sprints */}
      <div className={`races-list ${filtering ? 'filtering' : ''}`}>
        {currentSprints.length === 0 ? (
          <div className="no-results">
            <p>Nenhum sprint encontrado com os filtros aplicados.</p>
          </div>
        ) : (
          currentSprints.map((sprint) => {
            const topThree = sprint.results.slice(0, 3);

            // Formatar resultados para a tabela
            const formattedResults = sprint.results.map(result => {
              const translatedStatus = translateDriverStatus(result.status);
              const statusDisplay = formatStatusDisplay(result.status, translatedStatus);

              return {
                position: result.position,
                driverNumber: result.driver_number || result.driver?.number || '',
                driverCode: result.driver_code || result.driver?.code || '',
                driverName: result.driver_name || result.driver?.fullName || '',
                driverWithNumber: result.driver_number
                  ? `${result.driver_number} ${result.driver_name || result.driver}`
                  : result.driver_name || result.driver,
                team: result.team_name || result.team,
                teamColor: result.team_color || result.teamColor,
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
              <div key={sprint.sessionId} className="race-card-modern">
                {/* Header do sprint */}
                <div className="race-card-header">
                  <div className="race-title-section">
                    <h2>{sprint.eventName} - Sprint</h2>
                    <div className="race-metadata">
                      <span className="race-circuit">🏁 {sprint.circuit}</span>
                      <span className="race-location">📍 {sprint.location}, {sprint.country}</span>
                      <span className="race-date">📅 {formatDateBR(sprint.date)}</span>
                      <span className="race-round">Round {sprint.round} • {sprint.year}</span>
                    </div>
                  </div>
                </div>

                {/* Top 3 */}
                {topThree.length === 3 && (
                  <Podium
                    title="🏆 Top 3"
                    entries={topThree.map((result, index) => ({
                      position: index + 1,
                      name: result.driver_name || result.driver?.fullName || result.driver || 'N/A',
                      driverNumber: result.driver_number || (result.driver?.number ? parseInt(result.driver.number) : undefined),
                      team: result.team_name || result.team?.name || result.team || 'N/A',
                      teamColor: result.team_color || result.teamColor || result.team?.color,
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
