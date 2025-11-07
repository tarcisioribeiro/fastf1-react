import { useEffect, useState, useMemo } from 'react';
import { f1Api } from '../services/api';
import './HistoryFilters.css';

interface HistoryFiltersProps {
  onFilterChange: (filters: {
    year: string;
    circuit: string;
    driver: string;
    team: string;
  }) => void;
}

interface Driver {
  code: string;
  full_name: string;
  number: number;
}

interface Team {
  name: string;
  color: string;
}

interface Circuit {
  name: string;
  location: string;
  country: string;
}

export default function HistoryFilters({ onFilterChange }: HistoryFiltersProps) {
  const [years, setYears] = useState<number[]>([]);
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [teams, setTeams] = useState<Team[]>([]);
  const [circuits, setCircuits] = useState<Circuit[]>([]);

  const [yearFilter, setYearFilter] = useState('');
  const [circuitFilter, setCircuitFilter] = useState('');
  const [driverFilter, setDriverFilter] = useState('');
  const [teamFilter, setTeamFilter] = useState('');

  useEffect(() => {
    loadFilterOptions();
  }, []);

  // Memoizar os filtros para evitar re-renders desnecessários
  const currentFilters = useMemo(() => ({
    year: yearFilter,
    circuit: circuitFilter,
    driver: driverFilter,
    team: teamFilter
  }), [yearFilter, circuitFilter, driverFilter, teamFilter]);

  useEffect(() => {
    onFilterChange(currentFilters);
  }, [currentFilters, onFilterChange]);

  const loadFilterOptions = async () => {
    try {
      const [yearsData, driversData, teamsData, circuitsData] = await Promise.all([
        f1Api.getAvailableYears(),
        f1Api.getAvailableDrivers(),
        f1Api.getAvailableTeams(),
        f1Api.getAvailableCircuits()
      ]);

      setYears(yearsData.years || []);
      setDrivers(driversData.drivers || []);
      setTeams(teamsData.teams || []);
      setCircuits(circuitsData.circuits || []);
    } catch (error) {
      console.error('Erro ao carregar opções de filtros:', error);
    }
  };

  const clearFilters = () => {
    setYearFilter('');
    setCircuitFilter('');
    setDriverFilter('');
    setTeamFilter('');
  };

  return (
    <div className="history-filters">
      <div className="filters-grid">
        <div className="filter-group">
          <label htmlFor="year-filter">Ano</label>
          <select
            id="year-filter"
            value={yearFilter}
            onChange={(e) => setYearFilter(e.target.value)}
            className="filter-select"
          >
            <option value="">Todos os anos</option>
            {years.map(year => (
              <option key={year} value={year}>{year}</option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label htmlFor="circuit-filter">Circuito</label>
          <select
            id="circuit-filter"
            value={circuitFilter}
            onChange={(e) => setCircuitFilter(e.target.value)}
            className="filter-select"
          >
            <option value="">Todos os circuitos</option>
            {circuits.map(circuit => (
              <option key={circuit.name} value={circuit.name}>
                {circuit.name}
              </option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label htmlFor="driver-filter">Piloto</label>
          <select
            id="driver-filter"
            value={driverFilter}
            onChange={(e) => setDriverFilter(e.target.value)}
            className="filter-select"
          >
            <option value="">Todos os pilotos</option>
            {drivers.map(driver => (
              <option key={driver.code} value={driver.code}>
                {driver.code} - {driver.full_name}
              </option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label htmlFor="team-filter">Equipe</label>
          <select
            id="team-filter"
            value={teamFilter}
            onChange={(e) => setTeamFilter(e.target.value)}
            className="filter-select"
          >
            <option value="">Todas as equipes</option>
            {teams.map(team => (
              <option key={team.name} value={team.name}>
                {team.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      <button onClick={clearFilters} className="clear-filters-btn">
        Limpar Filtros
      </button>
    </div>
  );
}
