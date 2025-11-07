import { Link, useLocation } from 'react-router-dom';
import ThemeToggle from './ThemeToggle';
import './Navbar.css';

export default function Navbar() {
  const location = useLocation();

  const isActive = (path: string) => location.pathname === path;

  return (
    <nav className="navbar">
      <div className="navbar-container container">
        <Link to="/" className="navbar-logo">
          <span className="navbar-icon">🏎️</span>
          <span className="navbar-title">F1 Dashboard</span>
        </Link>

        <div className="navbar-right">
          <ul className="navbar-menu">
            <li>
              <Link
                to="/race"
                className={'navbar-link ' + (isActive('/race') ? 'active' : '')}
              >
                🏆 Última Corrida
              </Link>
            </li>
            <li>
              <Link
                to="/qualifying"
                className={'navbar-link ' + (isActive('/qualifying') ? 'active' : '')}
              >
                ⏱️ Última Qualificação
              </Link>
            </li>
            <li>
              <Link
                to="/drivers"
                className={'navbar-link ' + (isActive('/drivers') ? 'active' : '')}
              >
                👤 Pilotos
              </Link>
            </li>
            <li>
              <Link
                to="/constructors"
                className={'navbar-link ' + (isActive('/constructors') ? 'active' : '')}
              >
                🏁 Construtores
              </Link>
            </li>
            <li>
              <Link
                to="/status"
                className={'navbar-link ' + (isActive('/status') ? 'active' : '')}
              >
                📊 Status
              </Link>
            </li>
          </ul>

          <ThemeToggle />
        </div>
      </div>
    </nav>
  );
}
