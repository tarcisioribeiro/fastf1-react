import { useState, useEffect } from 'react';
import axios from 'axios';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';
import { Circuit } from '../types/f1';
import '../styles/Circuits.css';

// Criar instância do axios para esta página
const API_URL = import.meta.env.MODE === 'development' ? '/api' : (import.meta.env.VITE_API_URL || '/api');
const api = axios.create({
  baseURL: API_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

interface CircuitsPageProps {}

const Circuits: React.FC<CircuitsPageProps> = () => {
  const [circuits, setCircuits] = useState<Circuit[]>([]);
  const [filteredCircuits, setFilteredCircuits] = useState<Circuit[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCountry, setSelectedCountry] = useState('all');
  const [sortBy, setSortBy] = useState<'name' | 'country' | 'year'>('name');

  useEffect(() => {
    fetchCircuits();
  }, []);

  useEffect(() => {
    filterAndSortCircuits();
  }, [circuits, searchTerm, selectedCountry, sortBy]);

  const fetchCircuits = async () => {
    try {
      setLoading(true);
      const response = await api.get('/circuits/');
      // A API retorna um objeto paginado: { count, next, previous, results }
      setCircuits(response.data.results || response.data);
      setError(null);
    } catch (err: any) {
      console.error('Error fetching circuits:', err);
      setError(err.response?.data?.error || 'Falha ao carregar dados dos circuitos');
    } finally {
      setLoading(false);
    }
  };

  const filterAndSortCircuits = () => {
    let filtered = [...circuits];

    // Filtrar por busca
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      filtered = filtered.filter(circuit =>
        circuit.name.toLowerCase().includes(term) ||
        circuit.location.toLowerCase().includes(term) ||
        circuit.country.toLowerCase().includes(term)
      );
    }

    // Filtrar por país
    if (selectedCountry !== 'all') {
      filtered = filtered.filter(circuit => circuit.country === selectedCountry);
    }

    // Ordenar
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'name':
          return a.name.localeCompare(b.name);
        case 'country':
          return a.country.localeCompare(b.country);
        case 'year':
          return (b.first_grand_prix || 0) - (a.first_grand_prix || 0);
        default:
          return 0;
      }
    });

    setFilteredCircuits(filtered);
  };

  const getUniqueCountries = () => {
    const countries = Array.from(new Set(circuits.map(c => c.country))).sort();
    return countries;
  };

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorMessage message={error} />;

  return (
    <div className="circuits-page">
      <div className="circuits-header">
        <h1>Circuitos de Fórmula 1</h1>
        <p className="circuits-subtitle">
          Explore todos os {circuits.length} circuitos que já receberam um Grande Prêmio de F1
        </p>
      </div>

      <div className="circuits-filters">
        <div className="filter-group">
          <input
            type="text"
            placeholder="Buscar por nome, localização ou país..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="search-input"
          />
        </div>

        <div className="filter-group">
          <label htmlFor="country-filter">País:</label>
          <select
            id="country-filter"
            value={selectedCountry}
            onChange={(e) => setSelectedCountry(e.target.value)}
            className="country-select"
          >
            <option value="all">Todos os países ({circuits.length})</option>
            {getUniqueCountries().map(country => (
              <option key={country} value={country}>
                {country}
              </option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label htmlFor="sort-by">Ordenar por:</label>
          <select
            id="sort-by"
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as 'name' | 'country' | 'year')}
            className="sort-select"
          >
            <option value="name">Nome</option>
            <option value="country">País</option>
            <option value="year">Ano (primeiro GP)</option>
          </select>
        </div>
      </div>

      <div className="circuits-count">
        Exibindo {filteredCircuits.length} de {circuits.length} circuitos
      </div>

      <div className="circuits-grid">
        {filteredCircuits.map(circuit => (
          <div key={circuit.id} className="circuit-card">
            <div className="circuit-card-header">
              <h2>{circuit.name}</h2>
              <span className="circuit-location">
                {circuit.location}, {circuit.country}
              </span>
            </div>

            <div className="circuit-layout">
              {circuit.svg_url_black ? (
                <img
                  src={circuit.svg_url_black}
                  alt={`${circuit.name} track layout`}
                  className="circuit-svg"
                  loading="lazy"
                />
              ) : (
                <div className="circuit-no-layout">
                  <span>Traçado não disponível</span>
                </div>
              )}
            </div>

            <div className="circuit-info">
              {circuit.length_km && (
                <div className="info-item">
                  <span className="info-label">Comprimento:</span>
                  <span className="info-value">{circuit.length_km.toFixed(3)} km</span>
                </div>
              )}

              {circuit.number_of_corners && (
                <div className="info-item">
                  <span className="info-label">Curvas:</span>
                  <span className="info-value">{circuit.number_of_corners}</span>
                </div>
              )}

              {circuit.number_of_laps && (
                <div className="info-item">
                  <span className="info-label">Voltas (corrida):</span>
                  <span className="info-value">{circuit.number_of_laps}</span>
                </div>
              )}

              {circuit.race_distance_km && (
                <div className="info-item">
                  <span className="info-label">Distância da corrida:</span>
                  <span className="info-value">{circuit.race_distance_km.toFixed(1)} km</span>
                </div>
              )}

              {circuit.direction && (
                <div className="info-item">
                  <span className="info-label">Direção:</span>
                  <span className="info-value">
                    {circuit.direction === 'clockwise' ? 'Horário' : 'Anti-horário'}
                  </span>
                </div>
              )}

              {circuit.circuit_type && (
                <div className="info-item">
                  <span className="info-label">Tipo:</span>
                  <span className="info-value">{circuit.circuit_type}</span>
                </div>
              )}
            </div>

            {circuit.lap_record_formatted && (
              <div className="circuit-record">
                <div className="record-title">Recorde da pista</div>
                <div className="record-time">{circuit.lap_record_formatted}</div>
                {circuit.lap_record_driver && (
                  <div className="record-driver">
                    {circuit.lap_record_driver}
                    {circuit.lap_record_year && ` (${circuit.lap_record_year})`}
                  </div>
                )}
              </div>
            )}

            <div className="circuit-history-section">
              {circuit.first_grand_prix && (
                <div className="history-item">
                  <span className="history-label">Primeiro GP:</span>
                  <span className="history-value">{circuit.first_grand_prix}</span>
                </div>
              )}

              {circuit.total_races_held && (
                <div className="history-item">
                  <span className="history-label">Total de corridas:</span>
                  <span className="history-value">{circuit.total_races_held}</span>
                </div>
              )}
            </div>

            {circuit.description && (
              <div className="circuit-description">
                <h3>Descrição</h3>
                <p>{circuit.description}</p>
              </div>
            )}

            {circuit.history && circuit.history !== circuit.description && (
              <div className="circuit-history">
                <h3>História</h3>
                <p>{circuit.history}</p>
              </div>
            )}

            {(circuit.latitude && circuit.longitude) && (
              <div className="circuit-coordinates">
                <span>📍 {circuit.latitude.toFixed(6)}, {circuit.longitude.toFixed(6)}</span>
              </div>
            )}
          </div>
        ))}
      </div>

      {filteredCircuits.length === 0 && (
        <div className="no-results">
          <p>Nenhum circuito encontrado com os filtros aplicados.</p>
        </div>
      )}
    </div>
  );
};

export default Circuits;
