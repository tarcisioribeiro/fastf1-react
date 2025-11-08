import { useEffect, useState } from 'react';
import { f1Api } from '../services/api';
import LoadingWithRetry from '../components/LoadingWithRetry';
import FilterDropdown, { DropdownOption } from '../components/FilterDropdown';
import FiltersContainer from '../components/FiltersContainer';
import Table from '../components/Table';
import './DriverCareer.css';

interface DriverInfo {
  code: string;
  full_name: string;
  number: number;
  nationality: string;
  date_of_birth: string | null;
}

interface CareerTotals {
  total_races: number;
  total_wins: number;
  total_podiums: number;
  total_points: number;
  total_dnfs: number;
  total_fastest_laps: number;
  championships: number;
  best_championship_position: number | null;
  seasons: number;
}

interface SeasonCareer {
  year: number;
  team: string;
  canonical_team: string;
  team_color: string;
  final_position: number | null;
  final_points: number;
  wins: number;
  podiums: number;
  races?: number;
  dnfs?: number;
  fastest_laps?: number;
}

interface TeamCareer {
  canonical_team: string;
  team_color: string;
  years: number[];
  total_races: number;
  total_wins: number;
  total_podiums: number;
  total_points: number;
  best_championship_position: number | null;
}

interface DriverCareerResponse {
  status: string;
  driver: DriverInfo;
  career_totals: CareerTotals;
  career_by_season: SeasonCareer[];
  career_by_team: TeamCareer[];
}

export default function DriverCareer() {
  const [driverOptions, setDriverOptions] = useState<DropdownOption[]>([]);
  const [selectedDriver, setSelectedDriver] = useState<string>('');
  const [driverData, setDriverData] = useState<DriverCareerResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadingDrivers, setLoadingDrivers] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'season' | 'team'>('season');

  useEffect(() => {
    loadDrivers();
  }, []);

  const loadDrivers = async () => {
    try {
      setLoadingDrivers(true);
      const data = await f1Api.getAvailableDrivers();
      const options = data.drivers.map((driver: any) => ({
        value: driver.code,
        label: `${driver.code} - ${driver.full_name}`,
      }));
      setDriverOptions(options);
      setLoadingDrivers(false);
    } catch (err: any) {
      setError('Erro ao carregar pilotos disponíveis');
      setLoadingDrivers(false);
      console.error('Erro ao carregar pilotos:', err);
    }
  };

  const loadDriverCareer = async () => {
    if (!selectedDriver) return;

    try {
      setLoading(true);
      setError(null);

      const url = `/api/history/driver/?driver=${encodeURIComponent(selectedDriver)}`;

      const response = await fetch(url);

      // Verificar se a resposta está OK
      if (!response.ok) {
        throw new Error(`Erro HTTP: ${response.status}`);
      }

      const text = await response.text();

      // Verificar se há conteúdo antes de parsear
      if (!text || text.trim() === '') {
        throw new Error('Resposta vazia do servidor');
      }

      const data = JSON.parse(text);

      if (data.status === 'success') {
        setDriverData(data);
      } else {
        setError(data.error || 'Erro ao carregar carreira');
      }
    } catch (err: any) {
      console.error('Erro ao carregar carreira:', err);
      setError(err.message || 'Erro ao carregar carreira do piloto');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedDriver) {
      loadDriverCareer();
    }
  }, [selectedDriver]);

  if (loadingDrivers) {
    return (
      <div className="driver-career-page">
        <LoadingWithRetry message="Carregando pilotos disponíveis" />
      </div>
    );
  }

  const seasonColumns = [
    { key: 'year', label: 'Ano' },
    { key: 'team', label: 'Equipe' },
    { key: 'final_position', label: 'Posição Final' },
    { key: 'final_points', label: 'Pontos' },
    { key: 'wins', label: 'Vitórias' },
    { key: 'podiums', label: 'Pódios' },
    { key: 'races', label: 'Corridas' },
  ];

  const teamColumns = [
    { key: 'canonical_team', label: 'Equipe' },
    { key: 'years_display', label: 'Anos' },
    { key: 'total_races', label: 'Corridas' },
    { key: 'total_wins', label: 'Vitórias' },
    { key: 'total_podiums', label: 'Pódios' },
    { key: 'total_points', label: 'Pontos' },
    { key: 'best_championship_position', label: 'Melhor Posição' },
  ];

  const teamDataFormatted = driverData?.career_by_team.map(team => ({
    ...team,
    years_display: team.years.length > 1
      ? `${Math.min(...team.years)} - ${Math.max(...team.years)}`
      : team.years[0].toString(),
  }));

  return (
    <div className="driver-career-page">
      <div className="page-header">
        <h1>👤 Carreira dos Pilotos</h1>
        <p className="subtitle">Visualize a trajetória completa de um piloto pelas equipes</p>
      </div>

      <FiltersContainer title="Filtros de Carreira">
        <FilterDropdown
          label="👤 Piloto"
          value={selectedDriver}
          options={driverOptions}
          onChange={setSelectedDriver}
          placeholder="Selecione um piloto para ver toda a carreira"
          icon="👤"
          disabled={loadingDrivers}
        />
      </FiltersContainer>

      {loading && (
        <LoadingWithRetry message="Carregando carreira do piloto" />
      )}

      {error && (
        <div className="error-container">
          <h2>⚠️ Erro</h2>
          <p>{error}</p>
          <button onClick={loadDriverCareer} className="retry-button">
            Tentar Novamente
          </button>
        </div>
      )}

      {driverData && !loading && (
        <>
          <div className="driver-info-card">
            <div className="driver-info-header">
              <div className="driver-number-badge">
                {driverData.driver.number}
              </div>
              <div>
                <h2>{driverData.driver.full_name}</h2>
                <p className="driver-subtitle">
                  {driverData.driver.code} • {driverData.driver.nationality}
                  {driverData.driver.date_of_birth &&
                    ` • ${new Date(driverData.driver.date_of_birth).toLocaleDateString('pt-BR')}`
                  }
                </p>
              </div>
            </div>

            <div className="career-totals">
              <div className="total-item highlight">
                <span className="total-label">Campeonatos:</span>
                <span className="total-value">{driverData.career_totals.championships}</span>
              </div>
              <div className="total-item">
                <span className="total-label">Temporadas:</span>
                <span className="total-value">{driverData.career_totals.seasons}</span>
              </div>
              <div className="total-item">
                <span className="total-label">Corridas:</span>
                <span className="total-value">{driverData.career_totals.total_races}</span>
              </div>
              <div className="total-item">
                <span className="total-label">Vitórias:</span>
                <span className="total-value">{driverData.career_totals.total_wins}</span>
              </div>
              <div className="total-item">
                <span className="total-label">Pódios:</span>
                <span className="total-value">{driverData.career_totals.total_podiums}</span>
              </div>
              <div className="total-item">
                <span className="total-label">Pontos Totais:</span>
                <span className="total-value">{driverData.career_totals.total_points.toFixed(1)}</span>
              </div>
              <div className="total-item">
                <span className="total-label">Voltas Rápidas:</span>
                <span className="total-value">{driverData.career_totals.total_fastest_laps}</span>
              </div>
              <div className="total-item">
                <span className="total-label">Melhor Posição:</span>
                <span className="total-value">
                  {driverData.career_totals.best_championship_position
                    ? `P${driverData.career_totals.best_championship_position}`
                    : 'N/A'}
                </span>
              </div>
            </div>
          </div>

          <div className="view-mode-selector">
            <button
              className={`view-button ${viewMode === 'season' ? 'active' : ''}`}
              onClick={() => setViewMode('season')}
            >
              📅 Por Temporada
            </button>
            <button
              className={`view-button ${viewMode === 'team' ? 'active' : ''}`}
              onClick={() => setViewMode('team')}
            >
              🏁 Por Equipe
            </button>
          </div>

          <div className="career-table-container">
            {viewMode === 'season' ? (
              <>
                <h3>Carreira por Temporada</h3>
                <Table
                  data={driverData.career_by_season}
                  columns={seasonColumns}
                  highlightPositions={[1, 2, 3]}
                  positionKey="final_position"
                />
              </>
            ) : (
              <>
                <h3>Carreira por Equipe (Consolidado)</h3>
                <Table
                  data={teamDataFormatted || []}
                  columns={teamColumns}
                  highlightPositions={[1, 2, 3]}
                  positionKey="best_championship_position"
                />
              </>
            )}
          </div>
        </>
      )}

      {!selectedDriver && !loading && (
        <div className="empty-state">
          <p>Selecione um piloto para visualizar sua carreira</p>
        </div>
      )}
    </div>
  );
}
