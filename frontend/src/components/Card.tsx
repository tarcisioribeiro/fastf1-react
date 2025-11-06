import { ReactNode } from 'react';
import './Card.css';

interface CardProps {
  children: ReactNode;
  className?: string;
  variant?: 'default' | 'gold' | 'silver' | 'bronze';
}

export default function Card({ children, className = '', variant = 'default' }: CardProps) {
  return (
    <div className={`card card-${variant} ${className}`}>
      {children}
    </div>
  );
}
