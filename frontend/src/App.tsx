import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Standings from './pages/Standings'
import RaceResults from './pages/RaceResults'
import './styles/App.css'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="standings" element={<Standings />} />
        <Route path="race-results" element={<RaceResults />} />
      </Route>
    </Routes>
  )
}

export default App
