/**
 * Container padronizado para agrupar filtros
 * Usa o estilo visual de AnalyticsPitStops
 */
import { ReactNode } from 'react';
import './FiltersContainer.css';

export interface FiltersContainerProps {
  children: ReactNode;
  title?: string;
}

export default function FiltersContainer({ children, title }: FiltersContainerProps) {
  return (
    <div className="filters-container">
      {title && <h3 className="filters-title">{title}</h3>}
      <div className="analytics-filters">
        {children}
      </div>
    </div>
  );
}
