import { useEffect, useState } from 'react';
import { f1Api } from '../services/api';
import LoadingWithRetry from '../components/LoadingWithRetry';
import './Status.css';

interface DatabaseStats {
  seasons: number;
  events: number;
  sessions: number;
  drivers: number;
  teams: number;
  circuits: number;
  race_results: number;
  qualifying_results: number;
  sprint_results: number;
  driver_standings: number;
  constructor_standings: number;
  lap_times: number;
  tyre_strategies: number;
  pit_stops: number;
  weather_data: number;
}

interface SessionsByType {
  races: number;
  qualifying: number;
  sprints: number;
}

interface SessionsStatus {
  complete: number;
  incomplete: number;
  data_collected: number;
}

interface LatestUpdate {
  event_name: string;
  round: number;
  session_date: string;
  collection_date: string | null;
}

interface CeleryInfo {
  active_tasks?: any;
  scheduled_tasks?: any;
  workers_online?: string[];
  error?: string;
  message?: string;
}

interface PeriodicTask {
  name: string;
  task: string;
  enabled: boolean;
  last_run_at: string | null;
}

interface CeleryBeatInfo {
  periodic_tasks?: PeriodicTask[];
  error?: string;
  message?: string;
}

interface StatusData {
  status: string;
  timestamp: string;
  stats: {
    database: DatabaseStats;
    sessions_by_type: SessionsByType;
    sessions_status: SessionsStatus;
    latest_updates: {
      race?: LatestUpdate;
      qualifying?: LatestUpdate;
      sprint?: LatestUpdate;
    };
    celery: CeleryInfo;
    celery_beat: CeleryBeatInfo;
  };
}

export default function Status() {
  const [statusData, setStatusData] = useState<StatusData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadStatus();
    // Auto-refresh a cada 10 segundos
    const interval = setInterval(() => {
      loadStatus(false);
    }, 10000);
    return () => clearInterval(interval);
  }, []);

  const loadStatus = async (showLoading = true) => {
    try {
      if (showLoading) {
        setLoading(true);
      }
      setError(null);
      const data = await f1Api.getStatus();
      setStatusData(data);
    } catch (err: any) {
      setError(err.message || 'Erro ao carregar status');
      console.error('Erro ao carregar status:', err);
    } finally {
      if (showLoading) {
        setLoading(false);
      }
    }
  };

  if (loading && !statusData) {
    return (
      <div className="status-page">
        <LoadingWithRetry
          message="Carregando status do sistema"
          hint="Consultando banco de dados e serviços..."
        />
      </div>
    );
  }

  if (error || !statusData) {
    return (
      <div className="status-page">
        <div className="error-container">
          <h2>⚠️ Erro ao carregar status</h2>
          <p>{error || 'Nenhum dado disponível'}</p>
          <button onClick={() => loadStatus()} className="retry-button">
            Tentar Novamente
          </button>
        </div>
      </div>
    );
  }

  const { stats } = statusData;
  const lastUpdate = new Date(statusData.timestamp);

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="status-page">
      <div className="page-header">
        <h1>📊 Status do Sistema</h1>
        <p className="subtitle">Monitoramento de dados e serviços</p>
        <p className="last-update">
          Última atualização: {lastUpdate.toLocaleTimeString('pt-BR')}
        </p>
      </div>

      {/* Database Statistics */}
      <section className="status-section">
        <h2>💾 Banco de Dados</h2>
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-value">{stats.database.seasons}</div>
            <div className="stat-label">Temporadas</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{stats.database.events}</div>
            <div className="stat-label">Eventos</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{stats.database.sessions}</div>
            <div className="stat-label">Sessões</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{stats.database.drivers}</div>
            <div className="stat-label">Pilotos</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{stats.database.teams}</div>
            <div className="stat-label">Equipes</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{stats.database.circuits}</div>
            <div className="stat-label">Circuitos</div>
          </div>
        </div>

        <h3>Resultados</h3>
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-value">{stats.database.race_results}</div>
            <div className="stat-label">Resultados de Corrida</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{stats.database.qualifying_results}</div>
            <div className="stat-label">Resultados de Qualifying</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{stats.database.sprint_results}</div>
            <div className="stat-label">Resultados de Sprint</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{stats.database.driver_standings}</div>
            <div className="stat-label">Classificação de Pilotos</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{stats.database.constructor_standings}</div>
            <div className="stat-label">Classificação de Construtores</div>
          </div>
        </div>

        <h3>Dados Detalhados</h3>
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-value">{stats.database.lap_times}</div>
            <div className="stat-label">Tempos de Volta</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{stats.database.pit_stops}</div>
            <div className="stat-label">Pit Stops</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{stats.database.weather_data}</div>
            <div className="stat-label">Dados Meteorológicos</div>
          </div>
        </div>
      </section>

      {/* Sessions Status */}
      <section className="status-section">
        <h2>🏁 Status das Sessões</h2>
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-value">{stats.sessions_by_type.races}</div>
            <div className="stat-label">Corridas</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{stats.sessions_by_type.qualifying}</div>
            <div className="stat-label">Qualifyings</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{stats.sessions_by_type.sprints}</div>
            <div className="stat-label">Sprints</div>
          </div>
        </div>

        <div className="stats-grid">
          <div className="stat-card success">
            <div className="stat-value">{stats.sessions_status.complete}</div>
            <div className="stat-label">Sessões Completas</div>
          </div>
          <div className="stat-card warning">
            <div className="stat-value">{stats.sessions_status.incomplete}</div>
            <div className="stat-label">Sessões Futuras</div>
          </div>
          <div className="stat-card info">
            <div className="stat-value">{stats.sessions_status.data_collected}</div>
            <div className="stat-label">Com Dados Coletados</div>
          </div>
        </div>
      </section>

      {/* Latest Updates */}
      <section className="status-section">
        <h2>🔄 Últimas Atualizações</h2>
        <div className="updates-grid">
          {stats.latest_updates.race && (
            <div className="update-card">
              <h3>🏆 Corrida</h3>
              <p className="update-event">{stats.latest_updates.race.event_name}</p>
              <p className="update-detail">Round {stats.latest_updates.race.round}</p>
              <p className="update-detail">
                Sessão: {formatDate(stats.latest_updates.race.session_date)}
              </p>
              {stats.latest_updates.race.collection_date && (
                <p className="update-detail">
                  Coletado: {formatDate(stats.latest_updates.race.collection_date)}
                </p>
              )}
            </div>
          )}

          {stats.latest_updates.qualifying && (
            <div className="update-card">
              <h3>⏱️ Qualifying</h3>
              <p className="update-event">{stats.latest_updates.qualifying.event_name}</p>
              <p className="update-detail">Round {stats.latest_updates.qualifying.round}</p>
              <p className="update-detail">
                Sessão: {formatDate(stats.latest_updates.qualifying.session_date)}
              </p>
              {stats.latest_updates.qualifying.collection_date && (
                <p className="update-detail">
                  Coletado: {formatDate(stats.latest_updates.qualifying.collection_date)}
                </p>
              )}
            </div>
          )}

          {stats.latest_updates.sprint && (
            <div className="update-card">
              <h3>🚀 Sprint</h3>
              <p className="update-event">{stats.latest_updates.sprint.event_name}</p>
              <p className="update-detail">Round {stats.latest_updates.sprint.round}</p>
              <p className="update-detail">
                Sessão: {formatDate(stats.latest_updates.sprint.session_date)}
              </p>
              {stats.latest_updates.sprint.collection_date && (
                <p className="update-detail">
                  Coletado: {formatDate(stats.latest_updates.sprint.collection_date)}
                </p>
              )}
            </div>
          )}
        </div>
      </section>

      {/* Celery Workers */}
      <section className="status-section">
        <h2>⚙️ Workers Celery</h2>
        {stats.celery.error ? (
          <div className="error-box">
            <p>❌ {stats.celery.message}</p>
            <p className="error-detail">{stats.celery.error}</p>
          </div>
        ) : (
          <div>
            <div className="workers-status">
              <h3>Workers Online: {stats.celery.workers_online?.length || 0}</h3>
              {stats.celery.workers_online && stats.celery.workers_online.length > 0 ? (
                <ul className="workers-list">
                  {stats.celery.workers_online.map((worker) => (
                    <li key={worker} className="worker-item">
                      ✅ {worker}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="warning-text">⚠️ Nenhum worker online</p>
              )}
            </div>
          </div>
        )}
      </section>

      {/* Celery Beat Tasks */}
      <section className="status-section">
        <h2>⏰ Tarefas Agendadas (Celery Beat)</h2>
        {stats.celery_beat.error ? (
          <div className="error-box">
            <p>❌ {stats.celery_beat.message}</p>
            <p className="error-detail">{stats.celery_beat.error}</p>
          </div>
        ) : (
          <div className="tasks-list">
            {stats.celery_beat.periodic_tasks && stats.celery_beat.periodic_tasks.length > 0 ? (
              stats.celery_beat.periodic_tasks.map((task) => (
                <div key={task.name} className="task-card">
                  <div className="task-header">
                    <h3>{task.name}</h3>
                    <span className={`task-status ${task.enabled ? 'enabled' : 'disabled'}`}>
                      {task.enabled ? '✅ Ativo' : '❌ Inativo'}
                    </span>
                  </div>
                  <p className="task-name">{task.task}</p>
                  {task.last_run_at ? (
                    <p className="task-detail">
                      Última execução: {formatDate(task.last_run_at)}
                    </p>
                  ) : (
                    <p className="task-detail">Nunca executado</p>
                  )}
                </div>
              ))
            ) : (
              <p className="warning-text">⚠️ Nenhuma tarefa agendada encontrada</p>
            )}
          </div>
        )}
      </section>

      <div className="refresh-info">
        <p>🔄 Esta página é atualizada automaticamente a cada 10 segundos</p>
      </div>
    </div>
  );
}
