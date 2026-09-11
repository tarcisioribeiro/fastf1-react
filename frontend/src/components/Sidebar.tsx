import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import ThemeToggle from './ThemeToggle';
import Icon, { type IconName } from './Icon';
import './Sidebar.css';

interface MenuItem {
  icon: IconName;
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
        { icon: 'home', label: 'Início', path: '/' },
      ]
    },
    {
      title: 'Resultados Recentes',
      items: [
        { icon: 'flag', label: 'Última Corrida', path: '/race' },
        { icon: 'timer', label: 'Último Qualifying', path: '/qualifying' },
        { icon: 'rocket', label: 'Última Sprint', path: '/sprint' },
      ]
    },
    {
      title: 'Classificações',
      items: [
        { icon: 'trophy', label: 'Pilotos', path: '/drivers' },
        { icon: 'users', label: 'Construtores', path: '/constructors' },
        { icon: 'circuit', label: 'Circuitos', path: '/circuits' },
      ]
    },
    {
      title: 'Histórico',
      items: [
        { icon: 'flag', label: 'Todas as Corridas', path: '/history/races' },
        { icon: 'timer', label: 'Todos os Qualifyings', path: '/history/qualifying' },
        { icon: 'rocket', label: 'Todas as Sprints', path: '/history/sprints' },
        { icon: 'users', label: 'Histórico de Equipes', path: '/history/teams' },
        { icon: 'user', label: 'Carreira de Pilotos', path: '/history/drivers' },
      ]
    },
    {
      title: 'Análises',
      items: [
        { icon: 'trending-up', label: 'Evolução de Pontos', path: '/analytics/standings' },
        { icon: 'weather', label: 'Dados Meteorológicos', path: '/analytics/weather' },
        { icon: 'fuel', label: 'Análise de Pit Stops', path: '/analytics/pitstops' },
      ]
    },
    {
      title: 'Previsões',
      items: [
        { icon: 'crystal', label: 'Posição - Pilotos', path: '/predictions/driver' },
        { icon: 'car', label: 'Posição - Equipes', path: '/predictions/constructor' },
        { icon: 'medal', label: 'Pole Position - Pilotos', path: '/predictions/pole-driver' },
        { icon: 'trophy', label: 'Pole Position - Equipes', path: '/predictions/pole-constructor' },
      ]
    },
    {
      title: 'Sistema',
      items: [
        { icon: 'settings', label: 'Status', path: '/status' },
        { icon: 'alarm', label: 'Tarefas Periódicas', path: '/periodic-tasks' },
        { icon: 'search', label: 'Auditoria de Dados', path: '/data-audit' },
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
            <Icon name={isCollapsed ? 'chevron-right' : 'chevron-left'} size={16} />
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
                <Icon name={isHidden ? 'chevron-right' : 'chevron-down'} size={14} />
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
                    <span className="menu-icon"><Icon name={item.icon} size={18} /></span>
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
