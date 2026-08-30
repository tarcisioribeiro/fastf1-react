/**
 * Dropdown de filtro padronizado — usa o componente Select do design system.
 */
import Select from './Select';
import type { IconName } from './Icon';
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
  icon?: IconName;
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
    <Select
      className="filter-group"
      label={label}
      icon={icon}
      value={value}
      options={options}
      onChange={onChange}
      placeholder={placeholder}
      disabled={disabled}
    />
  );
}
