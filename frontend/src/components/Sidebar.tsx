import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import ThemeToggle from './ThemeToggle';
import './Sidebar.css';

interface MenuItem {
  icon: string;
  label: string;
  path: string;
}

interface MenuSection {
  title: string;
  items: MenuItem[];
}

const HIDDEN_SECTIONS_KEY = 'sidebar-hidden-sections';

function loadHiddenSections(): Record<string, boolean> {
  try {
    return JSON.parse(localStorage.getItem(HIDDEN_SECTIONS_KEY) || '{}');
  } catch {
    return {};
  }
}

export default function Sidebar() {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [hiddenSections, setHiddenSections] = useState<Record<string, boolean>>(loadHiddenSections);
  const location = useLocation();

  const toggleSection = (title: string) => {
    setHiddenSections((prev) => {
      const next = { ...prev, [title]: !prev[title] };
      localStorage.setItem(HIDDEN_SECTIONS_KEY, JSON.stringify(next));
      return next;
    });
  };

  const menuSections: MenuSection[] = [
    {
      title: 'Principal',
      items: [
        { icon: '🏠', label: 'Início', path: '/' },
      ]
    },
    {
      title: 'Resultados Recentes',
      items: [
        { icon: '🏁', label: 'Última Corrida', path: '/race' },
        { icon: '⏱️', label: 'Último Qualifying', path: '/qualifying' },
        { icon: '🚀', label: 'Última Sprint', path: '/sprint' },
      ]
    },
    {
      title: 'Classificações',
      items: [
        { icon: '🏆', label: 'Pilotos', path: '/drivers' },
        { icon: '🏁', label: 'Construtores', path: '/constructors' },
        { icon: '🏟️', label: 'Circuitos', path: '/circuits' },
      ]
    },
    {
      title: 'Histórico',
      items: [
        { icon: '📚', label: 'Todas as Corridas', path: '/history/races' },
        { icon: '⏱️', label: 'Todos os Qualifyings', path: '/history/qualifying' },
        { icon: '🚀', label: 'Todas as Sprints', path: '/history/sprints' },
        { icon: '🏆', label: 'Histórico de Equipes', path: '/history/teams' },
        { icon: '👤', label: 'Carreira de Pilotos', path: '/history/drivers' },
      ]
    },
    {
      title: 'Análises',
      items: [
        { icon: '📈', label: 'Evolução de Pontos', path: '/analytics/standings' },
        { icon: '🌤️', label: 'Dados Meteorológicos', path: '/analytics/weather' },
        { icon: '⛽', label: 'Análise de Pit Stops', path: '/analytics/pitstops' },
      ]
    },
    {
      title: 'Previsões',
      items: [
        { icon: '🔮', label: 'Posição - Pilotos', path: '/predictions/driver' },
        { icon: '🏎️', label: 'Posição - Equipes', path: '/predictions/constructor' },
        { icon: '🥇', label: 'Pole Position - Pilotos', path: '/predictions/pole-driver' },
        { icon: '🏆', label: 'Pole Position - Equipes', path: '/predictions/pole-constructor' },
      ]
    },
    {
      title: 'Sistema',
      items: [
        { icon: '⚙️', label: 'Status', path: '/status' },
        { icon: '⏰', label: 'Tarefas Periódicas', path: '/periodic-tasks' },
        { icon: '🔍', label: 'Auditoria de Dados', path: '/data-audit' },
      ]
    }
  ];

  const toggleSidebar = () => {
    setIsCollapsed(!isCollapsed);
  };

  return (
    <aside className={`sidebar ${isCollapsed ? 'collapsed' : ''}`}>
      {/* Header com Logo e Título */}
      <div className="sidebar-header">
        <Link to="/" className="sidebar-logo">
          <img className="logo-icon" src="/logo.png" alt="F1 Dashboard" />
          {!isCollapsed && <span className="logo-title">F1 Dashboard</span>}
        </Link>
        <div className="sidebar-header-actions">
          <ThemeToggle />
          <button
            className="sidebar-toggle"
            onClick={toggleSidebar}
            aria-label={isCollapsed ? 'Expandir menu' : 'Recolher menu'}
          >
            {isCollapsed ? '→' : '←'}
          </button>
        </div>
      </div>

      <nav className="sidebar-nav">
        {menuSections.map((section, sectionIndex) => {
          const isHidden = !isCollapsed && hiddenSections[section.title];
          return (
          <div key={sectionIndex} className="menu-section">
            {!isCollapsed && (
              <button
                type="button"
                className="section-title"
                onClick={() => toggleSection(section.title)}
                aria-expanded={!isHidden}
              >
                <span>{section.title}</span>
                <span className="section-toggle-icon">{isHidden ? '▸' : '▾'}</span>
              </button>
            )}
            {!isHidden && (
            <ul className="menu-items">
              {section.items.map((item, itemIndex) => (
                <li key={itemIndex}>
                  <Link
                    to={item.path}
                    className={`menu-item ${location.pathname === item.path ? 'active' : ''}`}
                    title={isCollapsed ? item.label : undefined}
                  >
                    <span className="menu-icon">{item.icon}</span>
                    {!isCollapsed && <span className="menu-label">{item.label}</span>}
                  </Link>
                </li>
              ))}
            </ul>
            )}
          </div>
          );
        })}
      </nav>
    </aside>
  );
}
