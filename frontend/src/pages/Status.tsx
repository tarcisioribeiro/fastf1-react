import { useEffect, useState } from 'react';
import { f1Api } from '../services/api';
import { useNotification } from '../contexts/NotificationContext';
import LoadingWithRetry from '../components/LoadingWithRetry';
import './Status.css';
import './HistoricalData.css';

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
  total_run_count?: number;
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

// Interfaces para TaskMonitor
interface CeleryTask {
  id: string;
  name: string;
  args: string;
  kwargs: any;
  worker: string;
  time_start?: number;
  acknowledged?: boolean;
  eta?: string;
  priority?: number;
}

interface WorkerInfo {
  name: string;
  status: string;
  pool: string;
  max_concurrency: number;
  total_tasks: any;
}

interface TasksData {
  timestamp: string;
  status: string;
  workers: WorkerInfo[];
  tasks: {
    active: CeleryTask[];
    scheduled: CeleryTask[];
    reserved: CeleryTask[];
  };
  stats: {
    total_active: number;
    total_scheduled: number;
    total_reserved: number;
    total_workers: number;
    workers_online: string[];
  };
  periodic_tasks?: PeriodicTask[];
  error?: string;
  message?: string;
}

// Historical Data Interfaces
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

// Data Audit Interfaces
interface DataAuditSuggestion {
  id: number;
  table_name: string;
  field_name: string;
  record_id: number;
  record_identifier: string;
  current_value: string | null;
  suggested_value: string;
  confidence_score: number;
  source_name: string;
  source_url: string;
  source_timestamp: string;
  applied: boolean;
  rejected: boolean;
  created_at: string;
}

interface DataAuditReport {
  id: number;
  execution_date: string;
  status: string;
  execution_time_seconds: number | null;
  total_tables_scanned: number;
  total_fields_scanned: number;
  total_empty_fields_found: number;
  total_suggestions_found: number;
  suggestions: DataAuditSuggestion[];
  suggestions_count: {
    total: number;
    pending: number;
    applied: number;
    rejected: number;
  };
}

export default function Status() {
  const [statusData, setStatusData] = useState<StatusData | null>(null);
  const [tasksData, setTasksData] = useState<TasksData | null>(null);
  const [historicalData, setHistoricalData] = useState<HistoricalDataResponse | null>(null);
  const [auditData, setAuditData] = useState<DataAuditReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [collecting, setCollecting] = useState(false);
  const notification = useNotification();

  useEffect(() => {
    loadData();
    // Auto-refresh a cada 5 segundos
    const interval = setInterval(() => {
      if (autoRefresh) {
        loadData(false);
      }
    }, 5000);
    return () => clearInterval(interval);
  }, [autoRefresh]);

  const loadData = async (showLoading = true) => {
    try {
      if (showLoading) {
        setLoading(true);
      }
      setError(null);

      // Carregar todos os endpoints em paralelo
      const [status, tasks, historical, audit] = await Promise.all([
        f1Api.getStatus(),
        f1Api.getTasksStatus(),
        f1Api.getHistoricalDataStatus(),
        f1Api.getLatestAuditReport().catch(() => null) // Não falhar se não houver relatórios
      ]);

      setStatusData(status);
      setTasksData(tasks);
      setHistoricalData(historical);
      setAuditData(audit);
    } catch (err: any) {
      setError(err.message || 'Erro ao carregar dados do sistema');
      console.error('Erro ao carregar dados:', err);
    } finally {
      if (showLoading) {
        setLoading(false);
      }
    }
  };

  // Funções auxiliares
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

  const formatTaskName = (name: string) => {
    const parts = name.split('.');
    return parts[parts.length - 1];
  };

  const formatTime = (timestamp?: number) => {
    if (!timestamp) return 'N/A';
    const date = new Date(timestamp * 1000);
    return date.toLocaleTimeString('pt-BR');
  };

  const getElapsedTime = (startTime?: number) => {
    if (!startTime) return 'N/A';
    const elapsed = Date.now() - (startTime * 1000);
    const seconds = Math.floor(elapsed / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);

    if (hours > 0) {
      return `${hours}h ${minutes % 60}m`;
    } else if (minutes > 0) {
      return `${minutes}m ${seconds % 60}s`;
    } else {
      return `${seconds}s`;
    }
  };

  const formatArgs = (args: string) => {
    try {
      const parsed = JSON.parse(args);
      if (Array.isArray(parsed) && parsed.length > 0) {
        return parsed.join(', ');
      }
      return args || '-';
    } catch {
      return args || '-';
    }
  };

  const triggerHistoricalCollection = async (year?: number) => {
    try {
      setCollecting(true);

      const params = year
        ? { year }
        : { start_year: 1950, end_year: 2017 };

      await f1Api.triggerHistoricalCollection(params);

      notification.success(
        'Coleta Iniciada',
        year
          ? `Coleta de dados históricos iniciada para o ano ${year}`
          : 'Coleta completa de dados históricos iniciada (1950-2017)',
        7000
      );

      // Recarregar dados após 5 segundos
      setTimeout(() => loadData(false), 5000);
    } catch (err: any) {
      notification.error(
        'Erro na Coleta',
        err.message || 'Erro desconhecido ao iniciar coleta de dados históricos',
        8000
      );
    } finally {
      setCollecting(false);
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
          <button onClick={() => loadData()} className="retry-button">
            Tentar Novamente
          </button>
        </div>
      </div>
    );
  }

  const { stats } = statusData;
  const lastUpdate = new Date(statusData.timestamp);

  return (
    <div className="status-page">
      {/* Header com controles */}
      <div className="page-header">
        <div>
          <h1>📊 Status do Sistema</h1>
          <p className="subtitle">Monitoramento em tempo real de dados e serviços</p>
        </div>
        <div className="header-controls">
          <label className="auto-refresh-control">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              aria-label="Auto-atualizar a cada 5 segundos"
            />
            Auto-atualizar (5s)
          </label>
          <button onClick={() => loadData()} className="refresh-button" aria-label="Atualizar dados do sistema manualmente">
            🔄 Atualizar
          </button>
        </div>
      </div>

      <p className="last-update">
        Última atualização: {lastUpdate.toLocaleTimeString('pt-BR')}
      </p>

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
            <div className="stat-label">Resultados de Qualificação</div>
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
            <div className="stat-label">Qualificações</div>
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
              <h3>⏱️ Qualificação</h3>
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

      {/* Workers Celery e Tarefas */}
      {tasksData && !tasksData.error && (
        <section className="status-section">
          <h2>⚙️ Workers e Tarefas Celery</h2>

          {/* Stats Cards */}
          <div className="stats-grid workers-stats">
            <div className="stat-card">
              <div className="stat-icon">👷</div>
              <div className="stat-content">
                <div className="stat-value">{tasksData.stats.total_workers}</div>
                <div className="stat-label">Workers Online</div>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon running">⚡</div>
              <div className="stat-content">
                <div className="stat-value">{tasksData.stats.total_active}</div>
                <div className="stat-label">Tarefas Ativas</div>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon queued">📋</div>
              <div className="stat-content">
                <div className="stat-value">{tasksData.stats.total_reserved}</div>
                <div className="stat-label">Na Fila</div>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon scheduled">⏰</div>
              <div className="stat-content">
                <div className="stat-value">{tasksData.stats.total_scheduled}</div>
                <div className="stat-label">Agendadas</div>
              </div>
            </div>
          </div>

          {/* Workers Info */}
          {tasksData.workers.length > 0 && (
            <div className="workers-grid">
              {tasksData.workers.map((worker) => (
                <div key={worker.name} className="worker-card">
                  <div className="worker-header">
                    <span className="worker-status online">● Online</span>
                    <h3>{worker.name}</h3>
                  </div>
                  <div className="worker-details">
                    <div className="worker-detail">
                      <strong>Pool:</strong> {worker.pool}
                    </div>
                    <div className="worker-detail">
                      <strong>Concorrência:</strong> {worker.max_concurrency}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Active Tasks */}
          {tasksData.tasks.active.length > 0 && (
            <>
              <h3 className="section-subtitle">
                Tarefas Ativas ({tasksData.stats.total_active})
                <span className="pulse-indicator"></span>
              </h3>
              <div className="tasks-table-container">
                <table className="tasks-table">
                  <thead>
                    <tr>
                      <th>Tarefa</th>
                      <th>Argumentos</th>
                      <th>Worker</th>
                      <th>Início</th>
                      <th>Tempo Decorrido</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {tasksData.tasks.active.map((task) => (
                      <tr key={task.id} className="task-row active">
                        <td>
                          <strong>{formatTaskName(task.name)}</strong>
                          <div className="task-id">{task.id.substring(0, 8)}...</div>
                        </td>
                        <td className="task-args">{formatArgs(task.args)}</td>
                        <td>{task.worker.split('@')[1] || task.worker}</td>
                        <td>{formatTime(task.time_start)}</td>
                        <td>{getElapsedTime(task.time_start)}</td>
                        <td>
                          <span className="task-badge running">⚡ Executando</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}

          {/* Reserved Tasks */}
          {tasksData.tasks.reserved.length > 0 && (
            <>
              <h3 className="section-subtitle">Tarefas na Fila ({tasksData.stats.total_reserved})</h3>
              <div className="tasks-table-container">
                <table className="tasks-table">
                  <thead>
                    <tr>
                      <th>Tarefa</th>
                      <th>Argumentos</th>
                      <th>Worker</th>
                      <th>Prioridade</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {tasksData.tasks.reserved.map((task) => (
                      <tr key={task.id} className="task-row reserved">
                        <td>
                          <strong>{formatTaskName(task.name)}</strong>
                          <div className="task-id">{task.id.substring(0, 8)}...</div>
                        </td>
                        <td className="task-args">{formatArgs(task.args)}</td>
                        <td>{task.worker.split('@')[1] || task.worker}</td>
                        <td>{task.priority || 0}</td>
                        <td>
                          <span className="task-badge queued">📋 Na Fila</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </section>
      )}

      {/* Tarefas Periódicas (Celery Beat) */}
      {tasksData?.periodic_tasks && tasksData.periodic_tasks.length > 0 && (
        <section className="status-section">
          <h2>⏰ Tarefas Periódicas</h2>
          <div className="tasks-table-container">
            <table className="tasks-table">
              <thead>
                <tr>
                  <th>Nome</th>
                  <th>Tarefa</th>
                  <th>Última Execução</th>
                  <th>Total de Execuções</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {tasksData.periodic_tasks.map((task, idx) => (
                  <tr key={idx} className="task-row periodic">
                    <td><strong>{task.name}</strong></td>
                    <td className="task-name">{formatTaskName(task.task)}</td>
                    <td>
                      {task.last_run_at
                        ? formatDate(task.last_run_at)
                        : 'Nunca executada'}
                    </td>
                    <td>{task.total_run_count || 0}</td>
                    <td>
                      <span className={`task-badge ${task.enabled ? 'enabled' : 'disabled'}`}>
                        {task.enabled ? '✓ Habilitada' : '✗ Desabilitada'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {/* Dados Históricos (Pré-2018) */}
      {historicalData && (
        <section className="status-section">
          <h2>📚 Dados Históricos F1 (Pré-2018)</h2>

          {/* Collection Status Banner */}
          {historicalData.health.collection_active && (
            <div className="collection-banner active">
              <span className="spinner"></span>
              <strong>Coleta histórica em andamento!</strong>
              <p>Dados de 1950-2017 estão sendo coletados.</p>
            </div>
          )}

          {historicalData.health.recent_errors > 0 && (
            <div className="collection-banner error">
              <strong>⚠️ {historicalData.health.recent_errors} erros recentes</strong>
              <p>Verifique os logs para mais detalhes.</p>
            </div>
          )}

          {/* Coverage Stats */}
          <div className="stats-grid workers-stats">
            <div className="stat-card">
              <div className="stat-icon">📅</div>
              <div className="stat-content">
                <div className="stat-value">
                  {historicalData.stats.coverage.first_year || 'N/A'} - {historicalData.stats.coverage.last_year || 'N/A'}
                </div>
                <div className="stat-label">Período</div>
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-icon">✅</div>
              <div className="stat-content">
                <div className="stat-value">{historicalData.stats.coverage.total_seasons}</div>
                <div className="stat-label">Temporadas com Dados</div>
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-icon">❌</div>
              <div className="stat-content">
                <div className="stat-value">{historicalData.stats.coverage.missing_seasons.length}</div>
                <div className="stat-label">Temporadas Faltando</div>
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-icon">🏁</div>
              <div className="stat-content">
                <div className="stat-value">{historicalData.stats.totals.events.toLocaleString('pt-BR')}</div>
                <div className="stat-label">Total de Eventos</div>
              </div>
            </div>
          </div>

          {/* Missing Seasons */}
          {historicalData.stats.coverage.missing_seasons.length > 0 && historicalData.stats.coverage.missing_seasons.length <= 20 && (
            <div className="missing-seasons">
              <h3 className="section-subtitle">Temporadas Faltando ({historicalData.stats.coverage.missing_seasons.length}):</h3>
              <div className="missing-years">
                {historicalData.stats.coverage.missing_seasons.map((year) => (
                  <button
                    key={year}
                    className="year-button"
                    onClick={() => triggerHistoricalCollection(year)}
                    disabled={collecting}
                  >
                    {year}
                  </button>
                ))}
              </div>
            </div>
          )}

          {historicalData.stats.coverage.missing_seasons.length > 20 && (
            <div className="actions-container" style={{ marginTop: '1.5rem' }}>
              <button
                onClick={() => triggerHistoricalCollection()}
                className="action-button"
                disabled={collecting}
              >
                {collecting ? '⏳ Coletando...' : '🚀 Iniciar Coleta Completa (1950-2017)'}
              </button>
              <p className="action-hint">
                Faltam {historicalData.stats.coverage.missing_seasons.length} temporadas.
                Clique para iniciar a coleta completa.
              </p>
            </div>
          )}
        </section>
      )}

      {/* Data Audit Reports */}
      {auditData && (
        <section className="status-section">
          <h2>🔍 Auditoria de Dados</h2>

          {/* Audit Stats */}
          <div className="stats-grid workers-stats">
            <div className="stat-card">
              <div className="stat-icon">📋</div>
              <div className="stat-content">
                <div className="stat-value">{auditData.total_tables_scanned}</div>
                <div className="stat-label">Tabelas Escaneadas</div>
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-icon warning">⚠️</div>
              <div className="stat-content">
                <div className="stat-value">{auditData.total_empty_fields_found}</div>
                <div className="stat-label">Campos Vazios</div>
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-icon info">💡</div>
              <div className="stat-content">
                <div className="stat-value">{auditData.total_suggestions_found}</div>
                <div className="stat-label">Sugestões Encontradas</div>
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-icon">⏱️</div>
              <div className="stat-content">
                <div className="stat-value">
                  {auditData.execution_time_seconds ? auditData.execution_time_seconds.toFixed(1) + 's' : 'N/A'}
                </div>
                <div className="stat-label">Tempo de Execução</div>
              </div>
            </div>
          </div>

          {/* Suggestions Summary */}
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-value">{auditData.suggestions_count.pending}</div>
              <div className="stat-label">Sugestões Pendentes</div>
            </div>
            <div className="stat-card success">
              <div className="stat-value">{auditData.suggestions_count.applied}</div>
              <div className="stat-label">Sugestões Aplicadas</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{auditData.suggestions_count.rejected}</div>
              <div className="stat-label">Sugestões Rejeitadas</div>
            </div>
          </div>

          {/* Suggestions Table */}
          {auditData.suggestions && auditData.suggestions.length > 0 && (
            <>
              <h3 className="section-subtitle">
                Sugestões Encontradas ({auditData.suggestions.length > 10 ? 'Primeiras 10 de ' : ''}{auditData.suggestions.length})
              </h3>
              <div className="tasks-table-container">
                <table className="tasks-table">
                  <thead>
                    <tr>
                      <th>Tabela</th>
                      <th>Campo</th>
                      <th>Registro</th>
                      <th>Valor Atual</th>
                      <th>Valor Sugerido</th>
                      <th>Fonte</th>
                      <th>Confiança</th>
                    </tr>
                  </thead>
                  <tbody>
                    {auditData.suggestions.slice(0, 10).map((suggestion) => (
                      <tr key={suggestion.id} className="task-row">
                        <td><strong>{suggestion.table_name}</strong></td>
                        <td>{suggestion.field_name}</td>
                        <td>{suggestion.record_identifier}</td>
                        <td className="task-args">
                          {suggestion.current_value || <em style={{color: 'var(--color-warning)'}}>vazio</em>}
                        </td>
                        <td className="task-args">
                          <strong>{suggestion.suggested_value}</strong>
                        </td>
                        <td>
                          <a
                            href={suggestion.source_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            style={{color: 'var(--color-link)', textDecoration: 'none'}}
                          >
                            {suggestion.source_name}
                          </a>
                        </td>
                        <td>
                          <span
                            className={`task-badge ${
                              suggestion.confidence_score >= 0.8 ? 'enabled' :
                              suggestion.confidence_score >= 0.5 ? 'queued' : 'disabled'
                            }`}
                          >
                            {(suggestion.confidence_score * 100).toFixed(0)}%
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}

          {/* Audit Info */}
          <div className="update-card" style={{marginTop: '1rem'}}>
            <p className="update-detail">
              <strong>Última Auditoria:</strong> {formatDate(auditData.execution_date)}
            </p>
            <p className="update-detail">
              <strong>Status:</strong> {auditData.status === 'completed' ? '✅ Concluído' : auditData.status}
            </p>
            <p className="update-detail" style={{fontSize: '0.9rem', color: 'var(--color-text-secondary)'}}>
              A auditoria executa automaticamente 1x por dia (01:00) e identifica campos vazios no banco de dados,
              buscando sugestões de preenchimento em fontes públicas como Wikipedia e Wikidata.
            </p>
          </div>
        </section>
      )}

      {/* Últimas Atualizações */}
      <section className="status-section">
        <h2>🔄 Últimas Atualizações (2018+)</h2>
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
              <h3>⏱️ Qualificação</h3>
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
    </div>
  );
}
