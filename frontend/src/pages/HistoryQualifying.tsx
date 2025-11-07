import { useEffect, useState } from 'react';
import { f1Api } from '../services/api';
import LoadingWithRetry from '../components/LoadingWithRetry';
import './HistoryRaces.css'; // Reusing the same CSS

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
  const [filteredQualifyings, setFilteredQualifyings] = useState<HistoricalQualifying[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filtros
  const [yearFilter, setYearFilter] = useState('');
  const [circuitFilter, setCircuitFilter] = useState('');
  const [driverFilter, setDriverFilter] = useState('');
  const [teamFilter, setTeamFilter] = useState('');

  // Paginação
  const [currentPage, setCurrentPage] = useState(1);
  const qualifyingsPerPage = 10;

  // Expandir/colapsar resultados
  const [expandedQualifyings, setExpandedQualifyings] = useState<Set<number>>(new Set());

  useEffect(() => {
    loadHistory();
  }, []);

  useEffect(() => {
    applyFilters();
  }, [yearFilter, circuitFilter, driverFilter, teamFilter, qualifyings]);

  const loadHistory = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await f1Api.getQualifyingHistory({
        year: yearFilter || undefined,
        circuit: circuitFilter || undefined,
        driver: driverFilter || undefined,
        team: teamFilter || undefined
      });
      setQualifyings(data.qualifyings || []);
    } catch (err: any) {
      setError(err.message || 'Erro ao carregar histórico');
      console.error('Erro ao carregar histórico de qualifying:', err);
    } finally {
      setLoading(false);
    }
  };

  const applyFilters = () => {
    let filtered = [...qualifyings];

    if (yearFilter) {
      filtered = filtered.filter(q => q.year.toString() === yearFilter);
    }
    if (circuitFilter) {
      filtered = filtered.filter(q =>
        q.circuit.toLowerCase().includes(circuitFilter.toLowerCase())
      );
    }
    if (driverFilter) {
      filtered = filtered.filter(q =>
        q.results.some(result =>
          result.driver.code.toLowerCase().includes(driverFilter.toLowerCase()) ||
          result.driver.fullName.toLowerCase().includes(driverFilter.toLowerCase())
        )
      );
    }
    if (teamFilter) {
      filtered = filtered.filter(q =>
        q.results.some(result =>
          result.team.name.toLowerCase().includes(teamFilter.toLowerCase())
        )
      );
    }

    setFilteredQualifyings(filtered);
    setCurrentPage(1);
  };

  const toggleQualifyingExpanded = (sessionId: number) => {
    setExpandedQualifyings(prev => {
      const newSet = new Set(prev);
      if (newSet.has(sessionId)) {
        newSet.delete(sessionId);
      } else {
        newSet.add(sessionId);
      }
      return newSet;
    });
  };

  const clearFilters = () => {
    setYearFilter('');
    setCircuitFilter('');
    setDriverFilter('');
    setTeamFilter('');
  };

  // Paginação
  const indexOfLastQualifying = currentPage * qualifyingsPerPage;
  const indexOfFirstQualifying = indexOfLastQualifying - qualifyingsPerPage;
  const currentQualifyings = filteredQualifyings.slice(indexOfFirstQualifying, indexOfLastQualifying);
  const totalPages = Math.ceil(filteredQualifyings.length / qualifyingsPerPage);

  const formatTime = (time?: string) => {
    if (!time) return '-';
    return time;
  };

  if (loading) {
    return (
      <div className="history-page">
        <LoadingWithRetry
          message="Carregando histórico de qualifying"
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
          <button onClick={loadHistory} className="retry-button">
            Tentar Novamente
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="history-page">
      <div className="history-header">
        <h1>⏱️ Histórico de Qualifying</h1>
        <p className="history-subtitle">
          Total: {filteredQualifyings.length} {filteredQualifyings.length === 1 ? 'qualifying' : 'qualifyings'}
        </p>
      </div>

      {/* Filtros */}
      <div className="filters-container">
        <div className="filter-group">
          <label>Ano</label>
          <input
            type="text"
            placeholder="Ex: 2024"
            value={yearFilter}
            onChange={(e) => setYearFilter(e.target.value)}
            className="filter-input"
          />
        </div>
        <div className="filter-group">
          <label>Circuito</label>
          <input
            type="text"
            placeholder="Ex: Monza"
            value={circuitFilter}
            onChange={(e) => setCircuitFilter(e.target.value)}
            className="filter-input"
          />
        </div>
        <div className="filter-group">
          <label>Piloto</label>
          <input
            type="text"
            placeholder="Ex: VER"
            value={driverFilter}
            onChange={(e) => setDriverFilter(e.target.value)}
            className="filter-input"
          />
        </div>
        <div className="filter-group">
          <label>Equipe</label>
          <input
            type="text"
            placeholder="Ex: Red Bull"
            value={teamFilter}
            onChange={(e) => setTeamFilter(e.target.value)}
            className="filter-input"
          />
        </div>
        <button onClick={clearFilters} className="clear-filters-btn">
          Limpar Filtros
        </button>
      </div>

      {/* Lista de qualifyings */}
      <div className="races-list">
        {currentQualifyings.length === 0 ? (
          <div className="no-results">
            <p>Nenhum qualifying encontrado com os filtros aplicados.</p>
          </div>
        ) : (
          currentQualifyings.map((qualifying) => (
            <div key={qualifying.sessionId} className="race-card">
              <div
                className="race-header"
                onClick={() => toggleQualifyingExpanded(qualifying.sessionId)}
              >
                <div className="race-info">
                  <h3>{qualifying.eventName}</h3>
                  <div className="race-details">
                    <span className="race-circuit">🏁 {qualifying.circuit}</span>
                    <span className="race-location">📍 {qualifying.location}, {qualifying.country}</span>
                    <span className="race-date">📅 {new Date(qualifying.date).toLocaleDateString('pt-BR')}</span>
                    <span className="race-round">Round {qualifying.round} • {qualifying.year}</span>
                  </div>
                </div>
                <div className="expand-icon">
                  {expandedQualifyings.has(qualifying.sessionId) ? '▼' : '▶'}
                </div>
              </div>

              {expandedQualifyings.has(qualifying.sessionId) && (
                <div className="race-results">
                  <table className="results-table">
                    <thead>
                      <tr>
                        <th>Pos</th>
                        <th>Piloto</th>
                        <th>Equipe</th>
                        <th>Q1</th>
                        <th>Q2</th>
                        <th>Q3</th>
                      </tr>
                    </thead>
                    <tbody>
                      {qualifying.results.map((result) => (
                        <tr
                          key={`${qualifying.sessionId}-${result.position}`}
                          className={result.position === 1 ? 'podium-1' : ''}
                        >
                          <td className="position-cell">
                            {result.position}
                            {result.position === 1 && ' 🏁'}
                          </td>
                          <td>
                            <div className="driver-info">
                              <span className="driver-code">{result.driver.code}</span>
                              <span className="driver-name">{result.driver.fullName}</span>
                            </div>
                          </td>
                          <td>
                            <div
                              className="team-badge"
                              style={{ borderLeft: `4px solid ${result.team.color}` }}
                            >
                              {result.team.name}
                            </div>
                          </td>
                          <td className="time-cell">{formatTime(result.q1)}</td>
                          <td className="time-cell">{formatTime(result.q2)}</td>
                          <td className="time-cell">{formatTime(result.q3)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          ))
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
