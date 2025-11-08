import { useEffect, useState } from 'react';
import { f1Api } from '../services/api';
import LoadingWithRetry from '../components/LoadingWithRetry';
import FilterDropdown, { DropdownOption } from '../components/FilterDropdown';
import FiltersContainer from '../components/FiltersContainer';
import Table from '../components/Table';
import './TeamHistory.css';

interface TeamHistoryData {
  canonical_name: string;
  current_name: string;
  color: string;
  historical_names: string[];
}

interface SeasonHistory {
  year: number;
  team_name: string;
  final_position: number | null;
  final_points: number;
  wins: number;
  podiums: number;
  best_result?: number;
  evolution: {
    round: number;
    event_name: string;
    position: number;
    points: number;
    wins: number;
    podiums: number;
  }[];
}

interface TeamHistoryResponse {
  status: string;
  team: TeamHistoryData;
  history: SeasonHistory[];
}

export default function TeamHistory() {
  const [teamOptions, setTeamOptions] = useState<DropdownOption[]>([]);
  const [selectedTeam, setSelectedTeam] = useState<string>('');
  const [teamData, setTeamData] = useState<TeamHistoryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadingTeams, setLoadingTeams] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadTeams();
  }, []);

  const loadTeams = async () => {
    try {
      setLoadingTeams(true);
      const data = await f1Api.getAvailableTeams();
      const options = data.teams.map((team: any) => ({
        value: team.name,
        label: team.name,
      }));
      setTeamOptions(options);
      setLoadingTeams(false);
    } catch (err: any) {
      setError('Erro ao carregar equipes disponíveis');
      setLoadingTeams(false);
      console.error('Erro ao carregar equipes:', err);
    }
  };

  const loadTeamHistory = async () => {
    if (!selectedTeam) return;

    try {
      setLoading(true);
      setError(null);

      const url = `/api/history/team/?team=${encodeURIComponent(selectedTeam)}`;

      const response = await fetch(url);
      const data = await response.json();

      if (data.status === 'success') {
        setTeamData(data);
      } else {
        setError(data.error || 'Erro ao carregar histórico');
      }
    } catch (err: any) {
      setError(err.message || 'Erro ao carregar histórico da equipe');
      console.error('Erro ao carregar histórico:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedTeam) {
      loadTeamHistory();
    }
  }, [selectedTeam]);

  if (loadingTeams) {
    return (
      <div className="team-history-page">
        <LoadingWithRetry message="Carregando equipes disponíveis" />
      </div>
    );
  }

  const columns = [
    { key: 'year', label: 'Ano' },
    { key: 'team_name', label: 'Nome da Equipe' },
    { key: 'final_position', label: 'Posição Final' },
    { key: 'final_points', label: 'Pontos' },
    { key: 'wins', label: 'Vitórias' },
    { key: 'podiums', label: 'Pódios' },
  ];

  const totals = teamData?.history.reduce(
    (acc, season) => ({
      total_points: acc.total_points + season.final_points,
      total_wins: acc.total_wins + season.wins,
      total_podiums: acc.total_podiums + season.podiums,
      championships: acc.championships + (season.final_position === 1 ? 1 : 0),
    }),
    { total_points: 0, total_wins: 0, total_podiums: 0, championships: 0 }
  );

  return (
    <div className="team-history-page">
      <div className="page-header">
        <h1>🏆 Histórico de Equipes</h1>
        <p className="subtitle">Visualize o histórico completo de uma equipe (consolidado)</p>
      </div>

      <FiltersContainer title="Selecione a Equipe">
        <FilterDropdown
          label="Equipe"
          value={selectedTeam}
          options={teamOptions}
          onChange={setSelectedTeam}
          placeholder="Selecione uma equipe"
          icon="🏎️"
          disabled={loadingTeams}
        />
      </FiltersContainer>

      {loading && (
        <LoadingWithRetry message="Carregando histórico da equipe" />
      )}

      {error && (
        <div className="error-container">
          <h2>⚠️ Erro</h2>
          <p>{error}</p>
          <button onClick={loadTeamHistory} className="retry-button">
            Tentar Novamente
          </button>
        </div>
      )}

      {teamData && !loading && (
        <>
          <div className="team-info-card">
            <div className="team-info-header">
              <div
                className="team-color-indicator"
                style={{ backgroundColor: teamData.team.color }}
              ></div>
              <div>
                <h2>{teamData.team.canonical_name}</h2>
                <p className="team-subtitle">Nome Atual: {teamData.team.current_name}</p>
                <p className="historical-names">
                  Nomes Históricos: {teamData.team.historical_names.join(', ')}
                </p>
              </div>
            </div>

            {totals && (
              <div className="team-totals">
                <div className="total-item">
                  <span className="total-label">Campeonatos:</span>
                  <span className="total-value">{totals.championships}</span>
                </div>
                <div className="total-item">
                  <span className="total-label">Pontos Totais:</span>
                  <span className="total-value">{totals.total_points.toFixed(1)}</span>
                </div>
                <div className="total-item">
                  <span className="total-label">Vitórias:</span>
                  <span className="total-value">{totals.total_wins}</span>
                </div>
                <div className="total-item">
                  <span className="total-label">Pódios:</span>
                  <span className="total-value">{totals.total_podiums}</span>
                </div>
                <div className="total-item">
                  <span className="total-label">Temporadas:</span>
                  <span className="total-value">{teamData.history.length}</span>
                </div>
              </div>
            )}
          </div>

          <div className="history-table-container">
            <h3>Histórico por Temporada</h3>
            <Table
              data={teamData.history}
              columns={columns}
              highlightPositions={[1, 2, 3]}
              positionKey="final_position"
            />
          </div>
        </>
      )}

      {!selectedTeam && !loading && (
        <div className="empty-state">
          <p>Selecione uma equipe para visualizar seu histórico</p>
        </div>
      )}
    </div>
  );
}
