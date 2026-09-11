/**
 * Componente de dropdown padronizado para filtros
 * Usa o estilo de fonte de AnalyticsPitStops e visual aprimorado
 */
import './FilterDropdown.css';

export interface DropdownOption {
  value: string | number;
  label: string;
}

export interface FilterDropdownProps {
  label: string;
  value: string | number;
  options: DropdownOption[];
  onChange: (value: string) => void;
  placeholder?: string;
  icon?: string;
  disabled?: boolean;
}

export default function FilterDropdown({
  label,
  value,
  options,
  onChange,
  placeholder = 'Selecione...',
  icon,
  disabled = false,
}: FilterDropdownProps) {
  return (
    <div className="filter-group">
      <label className="filter-label">
        {icon && <span className="filter-icon">{icon}</span>}
        {label}
      </label>
      <select
        className="filter-input filter-dropdown"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
      >
        {placeholder && (
          <option value="">
            {placeholder}
          </option>
        )}
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  );
}
