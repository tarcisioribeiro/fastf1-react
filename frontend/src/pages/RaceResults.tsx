import { useState, useEffect } from 'react'
import { f1Api } from '../services/api'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorMessage from '../components/ErrorMessage'
import CustomSelect from '../components/CustomSelect'
import type { RaceResult, Race } from '../types'
import '../styles/RaceResults.css'

const RaceResults = () => {
  const [results, setResults] = useState<RaceResult[]>([])
  const [races, setRaces] = useState<Race[]>([])
  const [selectedRound, setSelectedRound] = useState<number | undefined>()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchRaces = async () => {
    try {
      const racesData = await f1Api.getRaces()
      setRaces(racesData)
    } catch (err) {
      console.error('Erro ao carregar corridas:', err)
    }
  }

  const fetchResults = async (round?: number) => {
    try {
      setLoading(true)
      setError(null)
      const resultsData = await f1Api.getRaceResults(2025, round)
      setResults(resultsData)
    } catch (err) {
      setError('Erro ao carregar resultados da corrida')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchRaces()
    fetchResults()
  }, [])

  const handleRaceChange = (round: number) => {
    setSelectedRound(round)
    fetchResults(round)
  }

  const getPodiumClass = (position: number): string => {
    switch (position) {
      case 1: return 'gold'
      case 2: return 'silver'
      case 3: return 'bronze'
      default: return ''
    }
  }

  return (
    <div className="race-results">
      <h2>Resultados das Corridas - 2025</h2>

      {races.length > 0 && (
        <div className="race-selector">
          <CustomSelect
            label="Selecione uma corrida"
            id="race-select"
            value={selectedRound || ''}
            onChange={(e) => handleRaceChange(Number(e.target.value))}
          >
            <option value="">Última corrida</option>
            {races.map((race) => (
              <option key={race.id} value={race.round}>
                Round {race.round} - {race.race_name} ({new Date(race.date).toLocaleDateString('pt-BR')})
              </option>
            ))}
          </CustomSelect>
        </div>
      )}

      {loading ? (
        <LoadingSpinner />
      ) : error ? (
        <ErrorMessage message={error} onRetry={() => fetchResults(selectedRound)} />
      ) : (
        <div className="card">
          <table className="results-table">
            <thead>
              <tr>
                <th>Pos</th>
                <th>Piloto</th>
                <th>Equipe</th>
                <th>Tempo</th>
                <th>Pontos</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {results.map((result) => (
                <tr key={result.id} className={getPodiumClass(result.position)}>
                  <td className="position">{result.position}</td>
                  <td className="driver-name">{result.driver_name}</td>
                  <td>{result.team}</td>
                  <td className="time">{result.time}</td>
                  <td className="points">{result.points}</td>
                  <td className={`status ${result.status.toLowerCase()}`}>
                    {result.status}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

export default RaceResults
