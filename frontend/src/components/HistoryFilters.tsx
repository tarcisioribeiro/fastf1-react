import { useEffect, useState, useMemo } from 'react';
import { f1Api } from '../services/api';
import FilterDropdown, { DropdownOption } from './FilterDropdown';
import FiltersContainer from './FiltersContainer';
import './HistoryFilters.css';

interface HistoryFiltersProps {
  onFilterChange: (filters: {
    year: string;
    circuit: string;
    driver: string;
    team: string;
  }) => void;
}

export default function HistoryFilters({ onFilterChange }: HistoryFiltersProps) {
  // Filtros primários (sempre disponíveis)
  const [yearOptions, setYearOptions] = useState<DropdownOption[]>([]);

  // Filtros secundários (dependem do ano)
  const [gpOptions, setGpOptions] = useState<DropdownOption[]>([]);
  const [driverOptions, setDriverOptions] = useState<DropdownOption[]>([]);
  const [teamOptions, setTeamOptions] = useState<DropdownOption[]>([]);

  // Estados dos filtros
  const [yearFilter, setYearFilter] = useState('');
  const [circuitFilter, setCircuitFilter] = useState('');
  const [driverFilter, setDriverFilter] = useState('');
  const [teamFilter, setTeamFilter] = useState('');

  const [loadingOptions, setLoadingOptions] = useState(true);
  const [loadingDependentOptions, setLoadingDependentOptions] = useState(false);

  // Carregar anos (filtro primário) no mount
  useEffect(() => {
    loadYearOptions();
  }, []);

  // Carregar opções dependentes quando o ano mudar
  useEffect(() => {
    if (yearFilter) {
      loadDependentOptions(yearFilter);
    } else {
      // Se não há ano selecionado, limpar opções dependentes
      setGpOptions([]);
      setDriverOptions([]);
      setTeamOptions([]);
    }
  }, [yearFilter]);

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

  const loadYearOptions = async () => {
    try {
      setLoadingOptions(true);
      const yearsData = await f1Api.getAvailableYears();

      // Map years to dropdown options
      const years = (yearsData.years || []).map((y: number) => ({
        value: y.toString(),
        label: y.toString(),
      }));
      setYearOptions(years);
    } catch (error) {
      console.error('Erro ao carregar anos:', error);
    } finally {
      setLoadingOptions(false);
    }
  };

  const loadDependentOptions = async (year: string) => {
    try {
      setLoadingDependentOptions(true);

      // Resetar filtros dependentes quando ano mudar
      setCircuitFilter('');
      setDriverFilter('');
      setTeamFilter('');

      // Carregar opções filtradas por ano
      const [gpsData, driversData, teamsData] = await Promise.all([
        f1Api.getGrandsPrix(year),
        f1Api.getDriversByYear(year),
        f1Api.getTeamsByYear(year)
      ]);

      // Map GPs to dropdown options (SEM índice)
      const gps = (gpsData || []).map((gp: any) => ({
        value: gp.round.toString(),
        label: gp.name, // Apenas o nome, sem o índice
      }));
      setGpOptions(gps);

      // Map drivers to dropdown options
      const drivers = (driversData || []).map((d: any) => ({
        value: d.code,
        label: `${d.code} - ${d.fullName}`,
      }));
      setDriverOptions(drivers);

      // Map teams to dropdown options
      const teams = (teamsData || []).map((t: any) => ({
        value: t.name,
        label: t.name,
      }));
      setTeamOptions(teams);
    } catch (error) {
      console.error('Erro ao carregar opções dependentes:', error);
    } finally {
      setLoadingDependentOptions(false);
    }
  };

  const clearFilters = () => {
    setYearFilter('');
    setCircuitFilter('');
    setDriverFilter('');
    setTeamFilter('');
  };

  return (
    <>
      <FiltersContainer title="Filtros de Histórico">
        <FilterDropdown
          label="1️⃣ Ano"
          value={yearFilter}
          options={yearOptions}
          onChange={setYearFilter}
          placeholder="Selecione o ano"
          icon="📅"
          disabled={loadingOptions}
        />
        <FilterDropdown
          label="2️⃣ GP"
          value={circuitFilter}
          options={gpOptions}
          onChange={setCircuitFilter}
          placeholder={yearFilter ? "Todos os GPs" : "Selecione um ano primeiro"}
          icon="🏁"
          disabled={!yearFilter || loadingDependentOptions}
        />
        <FilterDropdown
          label="3️⃣ Piloto"
          value={driverFilter}
          options={driverOptions}
          onChange={setDriverFilter}
          placeholder={yearFilter ? "Todos os pilotos" : "Selecione um ano primeiro"}
          icon="👤"
          disabled={!yearFilter || loadingDependentOptions}
        />
        <FilterDropdown
          label="4️⃣ Equipe"
          value={teamFilter}
          options={teamOptions}
          onChange={setTeamFilter}
          placeholder={yearFilter ? "Todas as equipes" : "Selecione um ano primeiro"}
          icon="🏎️"
          disabled={!yearFilter || loadingDependentOptions}
        />
      </FiltersContainer>

      <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
        <button onClick={clearFilters} className="clear-filters-btn">
          Limpar Filtros
        </button>
      </div>
    </>
  );
}
