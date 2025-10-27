import { Outlet, Link, useLocation } from 'react-router-dom'
import '../styles/Layout.css'

const Layout = () => {
  const location = useLocation()

  const isActive = (path: string) => {
    return location.pathname === path ? 'active' : ''
  }

  return (
    <div className="layout">
      <header className="header">
        <div className="header-content">
          <h1 className="logo">FastF1 Dashboard</h1>
          <nav className="nav">
            <Link to="/" className={`nav-link ${isActive('/')}`}>
              Dashboard
            </Link>
            <Link to="/standings" className={`nav-link ${isActive('/standings')}`}>
              Classificação
            </Link>
            <Link to="/race-results" className={`nav-link ${isActive('/race-results')}`}>
              Resultados
            </Link>
          </nav>
        </div>
      </header>
      <main className="main">
        <Outlet />
      </main>
      <footer className="footer">
        <p>FastF1 Dashboard - Temporada 2025</p>
      </footer>
    </div>
  )
}

export default Layout
