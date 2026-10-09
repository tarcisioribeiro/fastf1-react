import { useState, ReactNode } from 'react';
import './CollapsibleSection.css';

interface CollapsibleSectionProps {
  title: ReactNode;
  children: ReactNode;
  defaultOpen?: boolean;
  className?: string;
  as?: 'div' | 'section';
}

export default function CollapsibleSection({
  title,
  children,
  defaultOpen = true,
  className = '',
  as = 'div',
}: CollapsibleSectionProps) {
  const [open, setOpen] = useState(defaultOpen);
  const Wrapper = as;

  return (
    <Wrapper className={`collapsible-section ${className}`}>
      <button
        type="button"
        className="collapsible-header"
        onClick={() => setOpen(!open)}
        aria-expanded={open}
      >
        <span className="collapsible-title">{title}</span>
        <span className={`collapsible-icon ${open ? '' : 'is-collapsed'}`}>▾</span>
      </button>
      <div className={`collapsible-content ${open ? '' : 'is-collapsed'}`}>
        {children}
      </div>
    </Wrapper>
  );
}
