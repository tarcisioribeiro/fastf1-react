import { useState, useEffect } from 'react'
import { f1Api } from '../services/api'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorMessage from '../components/ErrorMessage'
import type { Driver, Constructor } from '../types'
import '../styles/Dashboard.css'

const Dashboard = () => {
  const [drivers, setDrivers] = useState<Driver[]>([])
  const [constructors, setConstructors] = useState<Constructor[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchData = async () => {
    try {
      setLoading(true)
      setError(null)
      const [driversData, constructorsData] = await Promise.all([
        f1Api.getDriverStandings(),
        f1Api.getConstructorStandings()
      ])
      setDrivers(driversData.slice(0, 5)) // Top 5
      setConstructors(constructorsData.slice(0, 5)) // Top 5
    } catch (err) {
      setError('Erro ao carregar dados do dashboard')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  if (loading) return <LoadingSpinner />
  if (error) return <ErrorMessage message={error} onRetry={fetchData} />

  const getPodiumClass = (position: number): string => {
    switch (position) {
      case 1: return 'gold'
      case 2: return 'silver'
      case 3: return 'bronze'
      default: return ''
    }
  }

  return (
    <div className="dashboard">
      <h2>Dashboard F1 - Temporada 2025</h2>

      <div className="dashboard-grid">
        <div className="card">
          <h3>Top 5 Pilotos</h3>
          <table className="standings-table">
            <thead>
              <tr>
                <th>Pos</th>
                <th>Piloto</th>
                <th>Equipe</th>
                <th>Pontos</th>
              </tr>
            </thead>
            <tbody>
              {drivers.map((driver) => (
                <tr key={driver.id} className={getPodiumClass(driver.position)}>
                  <td className="position">{driver.position}</td>
                  <td className="driver-name">{driver.driver_name}</td>
                  <td>{driver.team}</td>
                  <td className="points">{driver.points}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="card">
          <h3>Top 5 Construtores</h3>
          <table className="standings-table">
            <thead>
              <tr>
                <th>Pos</th>
                <th>Equipe</th>
                <th>Pontos</th>
              </tr>
            </thead>
            <tbody>
              {constructors.map((constructor) => (
                <tr key={constructor.id} className={getPodiumClass(constructor.position)}>
                  <td className="position">{constructor.position}</td>
                  <td className="team-name">{constructor.team_name}</td>
                  <td className="points">{constructor.points}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

export default Dashboard
