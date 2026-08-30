import { SelectHTMLAttributes, ReactNode } from 'react';
import Icon, { type IconName } from './Icon';
import './Select.css';

export interface SelectOption {
  value: string | number;
  label: string;
}

interface SelectProps extends Omit<SelectHTMLAttributes<HTMLSelectElement>, 'onChange'> {
  label?: string;
  icon?: IconName;
  options?: SelectOption[];
  placeholder?: string;
  error?: string;
  onChange?: (value: string) => void;
  children?: ReactNode;
}

export default function Select({
  label,
  icon,
  options,
  placeholder,
  error,
  onChange,
  className = '',
  children,
  ...rest
}: SelectProps) {
  return (
    <div className={`field ${className}`.trim()}>
      {label && (
        <label className="field-label">
          {icon && <Icon name={icon} size={15} />}
          {label}
        </label>
      )}
      <select
        className="select-field"
        onChange={(e) => onChange?.(e.target.value)}
        {...rest}
      >
        {placeholder && <option value="">{placeholder}</option>}
        {options
          ? options.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))
          : children}
      </select>
      {error && <span className="field-error">{error}</span>}
    </div>
  );
}
