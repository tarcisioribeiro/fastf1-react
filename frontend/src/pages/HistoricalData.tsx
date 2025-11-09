import { useEffect, useState } from 'react';
import { f1Api } from '../services/api';
import LoadingWithRetry from '../components/LoadingWithRetry';
import './HistoricalData.css';

interface YearData {
  year: number;
  events: number;
  race_results: number;
  qualifying_results: number;
  driver_standings: number;
  constructor_standings: number;
  pit_stops: number;
  is_complete: boolean;
}

interface HistoricalStats {
  coverage: {
    first_year: number | null;
    last_year: number | null;
    total_seasons: number;
    seasons_with_data: number[];
    missing_seasons: number[];
  };
  totals: {
    seasons: number;
    events: number;
    race_results: number;
    qualifying_results: number;
    driver_standings: number;
    constructor_standings: number;
    pit_stops: number;
  };
  by_year: YearData[];
  collection_logs: any[];
}

interface HistoricalDataResponse {
  status: string;
  timestamp: string;
  stats: HistoricalStats;
  health: {
    recent_errors: number;
    recent_warnings: number;
    collection_active: boolean;
  };
}

export default function HistoricalData() {
  const [data, setData] = useState<HistoricalDataResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [collecting, setCollecting] = useState(false);

  useEffect(() => {
    loadData();

    const interval = setInterval(() => {
      if (autoRefresh) {
        loadData(false);
      }
    }, 10000); // Atualiza a cada 10 segundos

    return () => clearInterval(interval);
  }, [autoRefresh]);

  const loadData = async (showLoading = true) => {
    try {
      if (showLoading) {
        setLoading(true);
      }
      setError(null);

      const result = await f1Api.getHistoricalDataStatus();
      setData(result);
    } catch (err: any) {
      setError(err.message || 'Erro ao carregar dados históricos');
      console.error('Erro ao carregar dados históricos:', err);
    } finally {
      if (showLoading) {
        setLoading(false);
      }
    }
  };

  const triggerCollection = async (year?: number) => {
    try {
      setCollecting(true);

      const params = year
        ? { year }
        : { start_year: 1950, end_year: 2017 };

      await f1Api.triggerHistoricalCollection(params);

      alert(year
        ? `Coleta iniciada para o ano ${year}`
        : 'Coleta completa iniciada (1950-2017)');

      // Recarregar dados após 5 segundos
      setTimeout(() => loadData(), 5000);
    } catch (err: any) {
      alert('Erro ao iniciar coleta: ' + (err.message || 'Erro desconhecido'));
    } finally {
      setCollecting(false);
    }
  };

  if (loading && !data) {
    return (
      <div className="historical-data-page">
        <LoadingWithRetry
          message="Carregando dados históricos"
          hint="Consultando dados pré-2018..."
        />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="historical-data-page">
        <div className="error-container">
          <h2>⚠️ Erro ao carregar dados</h2>
          <p>{error || 'Nenhum dado disponível'}</p>
          <button onClick={() => loadData()} className="retry-button">
            Tentar Novamente
          </button>
        </div>
      </div>
    );
  }

  const { stats, health } = data;
  const lastUpdate = new Date(data.timestamp);

  return (
    <div className="historical-data-page">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1>📚 Dados Históricos F1 (Pré-2018)</h1>
          <p className="subtitle">
            Estatísticas e dados completos de 1950 a 2017
          </p>
        </div>
        <div className="header-controls">
          <label className="auto-refresh-control">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
            />
            Auto-atualizar (10s)
          </label>
          <button onClick={() => loadData()} className="refresh-button">
            🔄 Atualizar
          </button>
        </div>
      </div>

      <p className="last-update">
        Última atualização: {lastUpdate.toLocaleTimeString('pt-BR')}
      </p>

      {/* Collection Status Banner */}
      {health.collection_active && (
        <div className="collection-banner active">
          <span className="spinner"></span>
          <strong>Coleta em andamento!</strong>
          <p>Dados históricos estão sendo coletados em tempo real.</p>
        </div>
      )}

      {health.recent_errors > 0 && (
        <div className="collection-banner error">
          <strong>⚠️ {health.recent_errors} erros recentes</strong>
          <p>Verifique os logs abaixo para mais detalhes.</p>
        </div>
      )}

      {/* Coverage Summary */}
      <section className="historical-section">
        <h2>📊 Cobertura de Dados</h2>

        <div className="coverage-stats">
          <div className="coverage-card">
            <div className="coverage-icon">📅</div>
            <div className="coverage-content">
              <div className="coverage-value">
                {stats.coverage.first_year || 'N/A'} - {stats.coverage.last_year || 'N/A'}
              </div>
              <div className="coverage-label">Período</div>
            </div>
          </div>

          <div className="coverage-card">
            <div className="coverage-icon">✅</div>
            <div className="coverage-content">
              <div className="coverage-value">{stats.coverage.total_seasons}</div>
              <div className="coverage-label">Temporadas com Dados</div>
            </div>
          </div>

          <div className="coverage-card">
            <div className="coverage-icon">❌</div>
            <div className="coverage-content">
              <div className="coverage-value">{stats.coverage.missing_seasons.length}</div>
              <div className="coverage-label">Temporadas Faltando</div>
            </div>
          </div>

          <div className="coverage-card">
            <div className="coverage-icon">🏁</div>
            <div className="coverage-content">
              <div className="coverage-value">{stats.totals.events}</div>
              <div className="coverage-label">Total de Eventos</div>
            </div>
          </div>
        </div>

        {stats.coverage.missing_seasons.length > 0 && (
          <div className="missing-seasons">
            <h3>Temporadas Faltando:</h3>
            <div className="missing-years">
              {stats.coverage.missing_seasons.map((year) => (
                <button
                  key={year}
                  className="year-button"
                  onClick={() => triggerCollection(year)}
                  disabled={collecting}
                >
                  {year}
                </button>
              ))}
            </div>
          </div>
        )}
      </section>

      {/* Totals */}
      <section className="historical-section">
        <h2>📈 Estatísticas Totais</h2>
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-value">{stats.totals.race_results.toLocaleString('pt-BR')}</div>
            <div className="stat-label">Resultados de Corrida</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{stats.totals.qualifying_results.toLocaleString('pt-BR')}</div>
            <div className="stat-label">Resultados de Qualifying</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{stats.totals.driver_standings.toLocaleString('pt-BR')}</div>
            <div className="stat-label">Classificações de Pilotos</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{stats.totals.constructor_standings.toLocaleString('pt-BR')}</div>
            <div className="stat-label">Classificações de Equipes</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{stats.totals.pit_stops.toLocaleString('pt-BR')}</div>
            <div className="stat-label">Pit Stops</div>
          </div>
        </div>
      </section>

      {/* By Year */}
      <section className="historical-section">
        <h2>📅 Dados por Ano</h2>
        <div className="years-table-container">
          <table className="years-table">
            <thead>
              <tr>
                <th>Ano</th>
                <th>Eventos</th>
                <th>Resultados</th>
                <th>Qualifyings</th>
                <th>Standings</th>
                <th>Pit Stops</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {stats.by_year.slice().reverse().map((yearData) => (
                <tr key={yearData.year} className={yearData.is_complete ? 'complete' : 'incomplete'}>
                  <td><strong>{yearData.year}</strong></td>
                  <td>{yearData.events}</td>
                  <td>{yearData.race_results}</td>
                  <td>{yearData.qualifying_results}</td>
                  <td>{yearData.driver_standings}</td>
                  <td>{yearData.pit_stops}</td>
                  <td>
                    {yearData.is_complete ? (
                      <span className="status-badge complete">✓ Completo</span>
                    ) : (
                      <span className="status-badge incomplete">⚠️ Incompleto</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Collection Logs */}
      {stats.collection_logs.length > 0 && (
        <section className="historical-section">
          <h2>📝 Logs Recentes (Últimas 24h)</h2>
          <div className="logs-container">
            {stats.collection_logs.map((log, index) => (
              <div key={index} className={`log-entry log-${log.level.toLowerCase()}`}>
                <span className="log-timestamp">
                  {new Date(log.timestamp).toLocaleString('pt-BR')}
                </span>
                <span className="log-level">[{log.level}]</span>
                <span className="log-task">{log.task_name}</span>
                <span className="log-message">{log.message}</span>
                {log.year && <span className="log-year">Ano: {log.year}</span>}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Collection Actions */}
      <section className="historical-section">
        <h2>⚙️ Ações de Coleta</h2>
        <div className="actions-container">
          <button
            onClick={() => triggerCollection()}
            className="action-button primary"
            disabled={collecting}
          >
            {collecting ? '⏳ Coletando...' : '🚀 Iniciar Coleta Completa (1950-2017)'}
          </button>
          <p className="action-hint">
            Esta ação iniciará a coleta de dados históricos para todos os anos de 1950 a 2017.
            O processo pode levar várias horas.
          </p>
        </div>
      </section>
    </div>
  );
}
