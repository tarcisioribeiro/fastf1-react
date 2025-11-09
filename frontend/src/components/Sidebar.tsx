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

export default function Sidebar() {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const location = useLocation();

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
        { icon: '🔮', label: 'Previsão de Pilotos', path: '/predictions/driver' },
        { icon: '🏎️', label: 'Previsão de Equipes', path: '/predictions/constructor' },
      ]
    },
    {
      title: 'Sistema',
      items: [
        { icon: '⚙️', label: 'Status', path: '/status' },
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
          <span className="logo-icon">🏎️</span>
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
        {menuSections.map((section, sectionIndex) => (
          <div key={sectionIndex} className="menu-section">
            {!isCollapsed && <h3 className="section-title">{section.title}</h3>}
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
          </div>
        ))}
      </nav>
    </aside>
  );
}
