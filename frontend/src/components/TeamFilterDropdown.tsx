import { useState, useEffect, useRef } from 'react';
import { f1Api } from '../services/api';
import './TeamFilterDropdown.css';

interface TeamOption {
  id: number;
  current_name: string;
  color: string;
  operation_line_id: number;
  succession_line: Array<{
    name: string;
    years_active: string;
    is_current: boolean;
    status: string;
  }>;
}

interface TeamFilterDropdownProps {
  value: string;
  onChange: (value: string) => void;
  label?: string;
  icon?: string;
  placeholder?: string;
  disabled?: boolean;
  showHistoricalToggle?: boolean;
}

export default function TeamFilterDropdown({
  value,
  onChange,
  label = 'Equipe',
  icon = '🏎️',
  placeholder = 'Selecione uma equipe',
  disabled = false,
  showHistoricalToggle = false,
}: TeamFilterDropdownProps) {
  const [teams, setTeams] = useState<TeamOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [showTooltip, setShowTooltip] = useState(false);
  const [tooltipTeam, setTooltipTeam] = useState<TeamOption | null>(null);
  const [tooltipPosition, setTooltipPosition] = useState({ x: 0, y: 0 });
  const [includeHistorical, setIncludeHistorical] = useState(false);
  const tooltipRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadTeams();
  }, []);

  const loadTeams = async () => {
    try {
      setLoading(true);
      const data = await f1Api.getTeamsForFilters();
      setTeams(data);
    } catch (error) {
      console.error('Erro ao carregar equipes:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleMouseEnter = (team: TeamOption, event: React.MouseEvent) => {
    // Apenas mostrar tooltip se houver linha de sucessão com múltiplas entradas
    if (team.succession_line.length > 1) {
      const rect = (event.currentTarget as HTMLElement).getBoundingClientRect();
      setTooltipPosition({
        x: rect.left + rect.width / 2,
        y: rect.top - 10,
      });
      setTooltipTeam(team);
      setShowTooltip(true);
    }
  };

  const handleMouseLeave = () => {
    setShowTooltip(false);
    setTooltipTeam(null);
  };

  const renderSuccessionLine = () => {
    if (!tooltipTeam) return null;

    // Ordenar por anos (mais antigo primeiro)
    const sorted = [...tooltipTeam.succession_line].sort((a, b) => {
      const yearA = parseInt(a.years_active.split('-')[0]);
      const yearB = parseInt(b.years_active.split('-')[0]);
      return yearA - yearB;
    });

    return (
      <div className="succession-list">
        {sorted.map((item, index) => (
          <div
            key={index}
            className={`succession-item ${item.is_current ? 'current' : ''}`}
          >
            <span className="succession-name">{item.name}</span>
            <span className="succession-years">{item.years_active}</span>
            {index < sorted.length - 1 && (
              <span className="succession-arrow">→</span>
            )}
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="team-filter-dropdown">
      {label && (
        <label className="filter-label">
          {icon && <span className="filter-icon">{icon}</span>}
          {label}
        </label>
      )}

      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled || loading}
        className="filter-select"
      >
        <option value="">{loading ? 'Carregando...' : placeholder}</option>
        {teams.map((team) => (
          <option
            key={team.id}
            value={team.current_name}
            onMouseEnter={(e) => handleMouseEnter(team, e as any)}
            onMouseLeave={handleMouseLeave}
          >
            {team.current_name}
          </option>
        ))}
      </select>

      {showHistoricalToggle && (
        <div className="historical-toggle">
          <label className="toggle-label">
            <input
              type="checkbox"
              checked={includeHistorical}
              onChange={(e) => setIncludeHistorical(e.target.checked)}
              disabled={disabled}
            />
            <span>Incluir equipes históricas</span>
          </label>
        </div>
      )}

      {showTooltip && tooltipTeam && (
        <div
          ref={tooltipRef}
          className="team-tooltip"
          style={{
            left: `${tooltipPosition.x}px`,
            top: `${tooltipPosition.y}px`,
          }}
        >
          <div className="tooltip-header">
            <strong>{tooltipTeam.current_name}</strong>
            <span className="tooltip-subtitle">Linha de Sucessão</span>
          </div>
          {renderSuccessionLine()}
          <div className="tooltip-footer">
            <small>
              {tooltipTeam.succession_line.length} identidade(s) histórica(s)
            </small>
          </div>
        </div>
      )}
    </div>
  );
}
