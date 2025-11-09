import { ReactNode } from 'react';
import './Tag.css';

interface TagProps {
  variant?: 'breaking' | 'magenta' | 'purple' | 'neutral' | 'success' | 'warning' | 'info';
  children: ReactNode;
  className?: string;
}

export default function Tag({ variant = 'neutral', children, className = '' }: TagProps) {
  return (
    <span className={`tag tag-${variant} ${className}`}>
      {children}
    </span>
  );
}
