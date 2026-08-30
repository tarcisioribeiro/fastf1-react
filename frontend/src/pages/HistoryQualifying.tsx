import { useEffect, useState, useCallback } from 'react';
import { f1Api } from '../services/api';
import HistoryFilters from '../components/HistoryFilters';
import Table from '../components/Table';
import LoadingWithRetry from '../components/LoadingWithRetry';
import { formatDateBR } from '../utils/dateFormatter';
import './HistoryRaces.css'; // Reusing the same CSS
import Icon from '../components/Icon';

interface QualifyingResult {
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
  q1?: string;
  q2?: string;
  q3?: string;
}

interface HistoricalQualifying {
  sessionId: number;
  eventName: string;
  circuit: string;
  location: string;
  country: string;
  date: string;
  year: number;
  round: number;
  results: QualifyingResult[];
}

export default function HistoryQualifying() {
  const [qualifyings, setQualifyings] = useState<HistoricalQualifying[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filtering, setFiltering] = useState(false); // Estado de transição de filtro
  const [isInitialLoad, setIsInitialLoad] = useState(true); // Distinguir carregamento inicial

  // Paginação
  const [currentPage, setCurrentPage] = useState(1);
  const qualifyingsPerPage = 5; // Reduzido para melhor visualização

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

      const data = await f1Api.getQualifyingHistory(Object.keys(appliedFilters).length > 0 ? appliedFilters : undefined);
      setQualifyings(data.qualifyings || []);
      setCurrentPage(1); // Reset página ao filtrar
    } catch (err: any) {
      setError(err.message || 'Erro ao carregar histórico');
      console.error('Erro ao carregar histórico de qualifying:', err);
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
  const indexOfLastQualifying = currentPage * qualifyingsPerPage;
  const indexOfFirstQualifying = indexOfLastQualifying - qualifyingsPerPage;
  const currentQualifyings = qualifyings.slice(indexOfFirstQualifying, indexOfLastQualifying);
  const totalPages = Math.ceil(qualifyings.length / qualifyingsPerPage);

  // Mostrar loading completo APENAS no carregamento inicial
  if (loading && isInitialLoad) {
    return (
      <div className="history-page">
        <LoadingWithRetry
          message="Carregando histórico de qualificações"
          hint="Buscando todos os resultados disponíveis..."
        />
      </div>
    );
  }

  if (error) {
    return (
      <div className="history-page">
        <div className="error-container">
          <h2><Icon name="warning" size={16} /> Erro ao carregar histórico</h2>
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
        <h1><Icon name="timer" size={16} /> Histórico de Qualificações</h1>
        <p className="history-subtitle">
          Total: {qualifyings.length} {qualifyings.length === 1 ? 'qualificação' : 'qualificações'}
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

      {/* Lista de qualifyings */}
      <div className={`races-list ${filtering ? 'filtering' : ''}`}>
        {currentQualifyings.length === 0 ? (
          <div className="no-results">
            <p>Nenhuma qualificação encontrada com os filtros aplicados.</p>
          </div>
        ) : (
          currentQualifyings.map((qualifying) => {
            const polePosition = qualifying.results[0];

            // Formatar resultados para a tabela
            const formattedResults = qualifying.results.map(result => ({
              position: result.position,
              driverNumber: result.driver_number || result.driver?.number || '',
              driverCode: result.driver_code || result.driver?.code || '',
              driverName: result.driver || result.driver?.fullName || '',
              driverWithNumber: result.driver_number
                ? `${result.driver_number} ${result.driver}`
                : result.driver,
              team: result.team,
              teamColor: result.teamColor,
              q1: result.q1 || '-',
              q1Class: !result.q1 ? 'time-empty' : '',
              q2: result.q2 || '-',
              q2Class: !result.q2 ? 'time-empty' : '',
              q3: result.q3 || '-',
              q3Class: !result.q3 ? 'time-empty' : '',
            }));

            const columns = [
              { key: 'position', label: 'Pos.' },
              { key: 'driverWithNumber', label: 'Piloto' },
              { key: 'team', label: 'Equipe' },
              { key: 'q1', label: 'Q1' },
              { key: 'q2', label: 'Q2' },
              { key: 'q3', label: 'Q3' },
            ];

            return (
              <div key={qualifying.sessionId} className="race-card-modern">
                {/* Header da qualificação */}
                <div className="race-card-header">
                  <div className="race-title-section">
                    <h2>{qualifying.eventName} - Qualificação</h2>
                    <div className="race-metadata">
                      <span className="race-circuit"><Icon name="flag" size={16} /> {qualifying.circuit}</span>
                      <span className="race-location"><Icon name="pin" size={16} /> {qualifying.location}, {qualifying.country}</span>
                      <span className="race-date"><Icon name="calendar" size={16} /> {formatDateBR(qualifying.date)}</span>
                      <span className="race-round">Round {qualifying.round} • {qualifying.year}</span>
                    </div>
                  </div>
                </div>

                {/* Pole Position */}
                {polePosition && (
                  <div className="pole-position-section">
                    <h3><Icon name="flag" size={16} /> Pole Position</h3>
                    <div className="pole-card">
                      <div className="pole-icon"><Icon name="flag" size={16} /> </div>
                      <h3 className="pole-driver-name">
                        {polePosition.driver_number || polePosition.driver?.number || ''}{' '}
                        {polePosition.driver?.fullName || polePosition.driver || 'N/A'}
                      </h3>
                      <p className="pole-team" style={(polePosition.teamColor || polePosition.team?.color) ? {
                        borderLeft: `5px solid ${polePosition.teamColor || polePosition.team?.color}`,
                      } : undefined}>{polePosition.team?.name || polePosition.team || 'N/A'}</p>
                      <h3 className="pole-time">{polePosition.q3 || polePosition.q2 || polePosition.q1}</h3>
                    </div>
                  </div>
                )}

                {/* Tabela de resultados */}
                <div className="table-section">
                  <h3><Icon name="chart" size={16} /> Resultados Completos</h3>
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
            <Icon name="chevron-left" size={15} /> Anterior
          </button>
          <span className="pagination-info">
            Página {currentPage} de {totalPages}
          </span>
          <button
            onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
            disabled={currentPage === totalPages}
            className="pagination-btn"
          >
            Próxima <Icon name="chevron-right" size={15} />
          </button>
        </div>
      )}
    </div>
  );
}
