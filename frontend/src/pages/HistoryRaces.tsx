import { useEffect, useState } from 'react';
import { f1Api } from '../services/api';
import LoadingWithRetry from '../components/LoadingWithRetry';
import { formatDateBR } from '../utils/dateFormatter';
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
  const [filteredRaces, setFilteredRaces] = useState<HistoricalRace[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filtros
  const [yearFilter, setYearFilter] = useState('');
  const [circuitFilter, setCircuitFilter] = useState('');
  const [driverFilter, setDriverFilter] = useState('');
  const [teamFilter, setTeamFilter] = useState('');

  // Paginação
  const [currentPage, setCurrentPage] = useState(1);
  const racesPerPage = 10;

  // Expandir/colapsar resultados
  const [expandedRaces, setExpandedRaces] = useState<Set<number>>(new Set());

  useEffect(() => {
    loadHistory();
  }, []);

  useEffect(() => {
    applyFilters();
  }, [yearFilter, circuitFilter, driverFilter, teamFilter, races]);

  const loadHistory = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await f1Api.getRaceHistory({
        year: yearFilter || undefined,
        circuit: circuitFilter || undefined,
        driver: driverFilter || undefined,
        team: teamFilter || undefined
      });
      setRaces(data.races || []);
    } catch (err: any) {
      setError(err.message || 'Erro ao carregar histórico');
      console.error('Erro ao carregar histórico de corridas:', err);
    } finally {
      setLoading(false);
    }
  };

  const applyFilters = () => {
    let filtered = [...races];

    if (yearFilter) {
      filtered = filtered.filter(race => race.year.toString() === yearFilter);
    }
    if (circuitFilter) {
      filtered = filtered.filter(race =>
        race.circuit.toLowerCase().includes(circuitFilter.toLowerCase())
      );
    }
    if (driverFilter) {
      filtered = filtered.filter(race =>
        race.results.some(result =>
          result.driver.code.toLowerCase().includes(driverFilter.toLowerCase()) ||
          result.driver.fullName.toLowerCase().includes(driverFilter.toLowerCase())
        )
      );
    }
    if (teamFilter) {
      filtered = filtered.filter(race =>
        race.results.some(result =>
          result.team.name.toLowerCase().includes(teamFilter.toLowerCase())
        )
      );
    }

    setFilteredRaces(filtered);
    setCurrentPage(1); // Reset para primeira página ao filtrar
  };

  const toggleRaceExpanded = (sessionId: number) => {
    setExpandedRaces(prev => {
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
  const indexOfLastRace = currentPage * racesPerPage;
  const indexOfFirstRace = indexOfLastRace - racesPerPage;
  const currentRaces = filteredRaces.slice(indexOfFirstRace, indexOfLastRace);
  const totalPages = Math.ceil(filteredRaces.length / racesPerPage);

  const formatTime = (time?: string) => {
    if (!time) return '-';
    // Se já está formatado (tem +), retorna direto
    if (time.includes('+')) return time;
    // Caso contrário, formata o tempo
    return time;
  };

  if (loading) {
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
        <h1>📚 Histórico de Corridas</h1>
        <p className="history-subtitle">
          Total: {filteredRaces.length} {filteredRaces.length === 1 ? 'corrida' : 'corridas'}
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

      {/* Lista de corridas */}
      <div className="races-list">
        {currentRaces.length === 0 ? (
          <div className="no-results">
            <p>Nenhuma corrida encontrada com os filtros aplicados.</p>
          </div>
        ) : (
          currentRaces.map((race) => (
            <div key={race.sessionId} className="race-card">
              <div
                className="race-header"
                onClick={() => toggleRaceExpanded(race.sessionId)}
              >
                <div className="race-info">
                  <h3>{race.eventName}</h3>
                  <div className="race-details">
                    <span className="race-circuit">🏁 {race.circuit}</span>
                    <span className="race-location">📍 {race.location}, {race.country}</span>
                    <span className="race-date">📅 {formatDateBR(race.date)}</span>
                    <span className="race-round">Round {race.round} • {race.year}</span>
                  </div>
                </div>
                <div className="expand-icon">
                  {expandedRaces.has(race.sessionId) ? '▼' : '▶'}
                </div>
              </div>

              {expandedRaces.has(race.sessionId) && (
                <div className="race-results">
                  <table className="results-table">
                    <thead>
                      <tr>
                        <th>Pos</th>
                        <th>Piloto</th>
                        <th>Equipe</th>
                        <th>Tempo</th>
                        <th>Pontos</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {race.results.map((result) => (
                        <tr
                          key={`${race.sessionId}-${result.position}`}
                          className={result.position <= 3 ? `podium-${result.position}` : ''}
                        >
                          <td className="position-cell">
                            {result.position}
                            {result.position === 1 && ' 🏆'}
                            {result.position === 2 && ' 🥈'}
                            {result.position === 3 && ' 🥉'}
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
                          <td className="time-cell">
                            {formatTime(result.time)}
                            {result.fastestLap && ' 💨'}
                          </td>
                          <td className="points-cell">{result.points}</td>
                          <td className="status-cell">{result.status}</td>
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
