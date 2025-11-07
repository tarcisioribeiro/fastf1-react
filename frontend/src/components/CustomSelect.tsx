import { SelectHTMLAttributes } from 'react';
import './CustomSelect.css';

interface CustomSelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
}

export default function CustomSelect({
  label,
  error,
  className = '',
  children,
  ...props
}: CustomSelectProps) {
  return (
    <div className={`custom-select-wrapper ${className}`}>
      {label && <label className="custom-select-label">{label}</label>}
      <div className="custom-select-container">
        <select className="custom-select" {...props}>
          {children}
        </select>
        <div className="custom-select-arrow">
          <svg
            width="12"
            height="12"
            viewBox="0 0 12 12"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              d="M2 4L6 8L10 4"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </div>
      </div>
      {error && <span className="custom-select-error">{error}</span>}
    </div>
  );
}
