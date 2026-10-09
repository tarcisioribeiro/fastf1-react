import { useEffect, useState } from 'react';
import { f1Api } from '../services/api';
import { useNotification } from '../contexts/NotificationContext';
import LoadingWithRetry from '../components/LoadingWithRetry';
import Button from '../components/Button';
import CollapsibleSection from '../components/CollapsibleSection';
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

// ML Models Interfaces
interface MLModelMetrics {
  train: {
    mae: number;
    rmse: number;
    r2: number;
  };
  test: {
    mae: number;
    rmse: number;
    r2: number;
  };
  samples: {
    train: number;
    test: number;
    total: number;
  };
}

interface MLModelMetadata {
  model_type: string;
  created_at: string;
  last_trained: string;
  training_samples: number;
  metrics: MLModelMetrics;
  year_range: string;
  last_saved: string;
}

interface MLModelInfo {
  type: string;
  trained: boolean;
  metadata: MLModelMetadata | null;
  file_size?: number;
  last_modified?: string;
}

interface MLModelsData {
  status: string;
  timestamp: string;
  models: {
    lap_time: MLModelInfo;
    position: MLModelInfo;
  };
}

export default function Status() {
  const [statusData, setStatusData] = useState<StatusData | null>(null);
  const [tasksData, setTasksData] = useState<TasksData | null>(null);
  const [auditData, setAuditData] = useState<DataAuditReport | null>(null);
  const [mlModelsData, setMlModelsData] = useState<MLModelsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [mlTraining, setMlTraining] = useState(false);
  const [mlTrainMode, setMlTrainMode] = useState<'incremental' | 'full'>('incremental');
  const [autoRefresh, setAutoRefresh] = useState(true);
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
      const [status, tasks, audit, mlModels] = await Promise.all([
        f1Api.getStatus(),
        f1Api.getTasksStatus(),
        f1Api.getLatestAuditReport().then(data => data?.empty ? null : data).catch(() => null), // Não falhar se não houver relatórios
        f1Api.getMlModelsStatus().catch(() => null) // Não falhar se não houver modelos
      ]);

      setStatusData(status);
      setTasksData(tasks);
      setAuditData(audit);
      setMlModelsData(mlModels);
    } catch (err: any) {
      setError(err.message || 'Erro ao carregar dados do sistema');
      console.error('Erro ao carregar dados:', err);
    } finally {
      if (showLoading) {
        setLoading(false);
      }
    }
  };

  const handleTrainModels = async () => {
    setMlTraining(true);
    try {
      const result = await f1Api.trainMlModels(mlTrainMode);
      notification.showSuccess(result.message || 'Treinamento iniciado com sucesso.');
    } catch (err: any) {
      notification.showError(err.response?.data?.error || err.message || 'Erro ao iniciar treinamento.');
    } finally {
      setMlTraining(false);
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
          <Button onClick={() => loadData()}>
            Tentar Novamente
          </Button>
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
          <Button onClick={() => loadData()} size="sm" aria-label="Atualizar dados do sistema manualmente">
            🔄 Atualizar
          </Button>
        </div>
      </div>

      <p className="last-update">
        Última atualização: {lastUpdate.toLocaleTimeString('pt-BR')}
      </p>

      {/* Database Statistics */}
      <CollapsibleSection as="section" className="status-section" title="💾 Banco de Dados">
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
      </CollapsibleSection>

      {/* Sessions Status */}
      <CollapsibleSection as="section" className="status-section" title="🏁 Status das Sessões">
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
      </CollapsibleSection>

      {/* Latest Updates */}
      <CollapsibleSection as="section" className="status-section" title="🔄 Últimas Atualizações">
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
      </CollapsibleSection>

      {/* Workers Celery e Tarefas */}
      {tasksData && !tasksData.error && (
        <CollapsibleSection as="section" className="status-section" title="⚙️ Workers e Tarefas Celery">
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
        </CollapsibleSection>
      )}

      {/* Tarefas Periódicas (Celery Beat) */}
      {tasksData?.periodic_tasks && tasksData.periodic_tasks.length > 0 && (
        <CollapsibleSection as="section" className="status-section" title="⏰ Tarefas Periódicas">
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
        </CollapsibleSection>
      )}

      {/* ML Models Section */}
      {mlModelsData && (
        <CollapsibleSection as="section" className="status-section" title="🤖 Modelos de Machine Learning">
          {/* Models Overview */}
          <div className="stats-grid workers-stats">
            {mlModelsData.models.lap_time.trained && (
              <>
                <div className="stat-card success">
                  <div className="stat-icon">✅</div>
                  <div className="stat-content">
                    <div className="stat-value">Lap Time</div>
                    <div className="stat-label">Modelo Treinado</div>
                  </div>
                </div>
              </>
            )}

            {mlModelsData.models.position.trained && (
              <>
                <div className="stat-card success">
                  <div className="stat-icon">✅</div>
                  <div className="stat-content">
                    <div className="stat-value">Position</div>
                    <div className="stat-label">Modelo Treinado</div>
                  </div>
                </div>
              </>
            )}

            {!mlModelsData.models.lap_time.trained && !mlModelsData.models.position.trained && (
              <div className="stat-card warning">
                <div className="stat-icon">⚠️</div>
                <div className="stat-content">
                  <div className="stat-value">Nenhum</div>
                  <div className="stat-label">Modelos Treinados</div>
                </div>
              </div>
            )}
          </div>

          {/* Lap Time Model */}
          {mlModelsData.models.lap_time.trained && mlModelsData.models.lap_time.metadata && (
            <div className="update-card" style={{marginTop: '1.5rem'}}>
              <h3>⚡ Lap Time Predictor</h3>
              <p className="update-detail">
                <strong>Tipo:</strong> Previsão de tempos de volta
              </p>
              <p className="update-detail">
                <strong>Algoritmo:</strong> Gradient Boosting Regressor
              </p>
              <p className="update-detail">
                <strong>Última atualização:</strong> {formatDate(mlModelsData.models.lap_time.metadata.last_trained)}
              </p>
              <p className="update-detail">
                <strong>Período de dados:</strong> {mlModelsData.models.lap_time.metadata.year_range}
              </p>
              <p className="update-detail">
                <strong>Amostras de treino:</strong> {mlModelsData.models.lap_time.metadata.training_samples.toLocaleString('pt-BR')}
              </p>

              <h4 style={{marginTop: '1rem', marginBottom: '0.5rem'}}>Métricas de Performance:</h4>
              <div className="stats-grid" style={{marginTop: '0.5rem'}}>
                <div className="stat-card">
                  <div className="stat-value">{mlModelsData.models.lap_time.metadata.metrics.test.mae.toFixed(3)}s</div>
                  <div className="stat-label">MAE (Teste)</div>
                </div>
                <div className="stat-card">
                  <div className="stat-value">{mlModelsData.models.lap_time.metadata.metrics.test.rmse.toFixed(3)}s</div>
                  <div className="stat-label">RMSE (Teste)</div>
                </div>
                <div className="stat-card success">
                  <div className="stat-value">{(mlModelsData.models.lap_time.metadata.metrics.test.r2 * 100).toFixed(2)}%</div>
                  <div className="stat-label">R² (Teste)</div>
                </div>
              </div>

              <p className="update-detail" style={{fontSize: '0.85rem', color: 'var(--color-text-secondary)', marginTop: '1rem'}}>
                <strong>Interpretação:</strong> MAE de ~{mlModelsData.models.lap_time.metadata.metrics.test.mae.toFixed(2)}s significa que o modelo erra em média {mlModelsData.models.lap_time.metadata.metrics.test.mae.toFixed(2)} segundos na previsão de tempos de volta. R² de {(mlModelsData.models.lap_time.metadata.metrics.test.r2 * 100).toFixed(1)}% indica excelente capacidade preditiva.
              </p>
            </div>
          )}

          {/* Position Model */}
          {mlModelsData.models.position.trained && mlModelsData.models.position.metadata && (
            <div className="update-card" style={{marginTop: '1.5rem'}}>
              <h3>🏆 Position Predictor</h3>
              <p className="update-detail">
                <strong>Tipo:</strong> Previsão de posições finais
              </p>
              <p className="update-detail">
                <strong>Algoritmo:</strong> Random Forest Regressor
              </p>
              <p className="update-detail">
                <strong>Última atualização:</strong> {formatDate(mlModelsData.models.position.metadata.last_trained)}
              </p>
              <p className="update-detail">
                <strong>Período de dados:</strong> {mlModelsData.models.position.metadata.year_range}
              </p>
              <p className="update-detail">
                <strong>Amostras de treino:</strong> {mlModelsData.models.position.metadata.training_samples.toLocaleString('pt-BR')}
              </p>

              <h4 style={{marginTop: '1rem', marginBottom: '0.5rem'}}>Métricas de Performance:</h4>
              <div className="stats-grid" style={{marginTop: '0.5rem'}}>
                <div className="stat-card">
                  <div className="stat-value">{mlModelsData.models.position.metadata.metrics.test.mae.toFixed(2)}</div>
                  <div className="stat-label">MAE (Teste)</div>
                </div>
                <div className="stat-card">
                  <div className="stat-value">{mlModelsData.models.position.metadata.metrics.test.rmse.toFixed(2)}</div>
                  <div className="stat-label">RMSE (Teste)</div>
                </div>
                <div className="stat-card success">
                  <div className="stat-value">{(mlModelsData.models.position.metadata.metrics.test.r2 * 100).toFixed(2)}%</div>
                  <div className="stat-label">R² (Teste)</div>
                </div>
              </div>

              <p className="update-detail" style={{fontSize: '0.85rem', color: 'var(--color-text-secondary)', marginTop: '1rem'}}>
                <strong>Interpretação:</strong> MAE de ~{mlModelsData.models.position.metadata.metrics.test.mae.toFixed(1)} posições significa que o modelo erra em média {mlModelsData.models.position.metadata.metrics.test.mae.toFixed(1)} posições na previsão final. R² de {(mlModelsData.models.position.metadata.metrics.test.r2 * 100).toFixed(1)}% indica boa capacidade preditiva.
              </p>
            </div>
          )}

          {/* Treinar Modelos */}
          <div className="update-card" style={{marginTop: '1.5rem'}}>
            <h3>🎯 Treinar Modelos</h3>
            <p className="update-detail" style={{marginBottom: '1rem'}}>
              Dispara o treinamento dos modelos via tarefa assíncrona (Celery). O processo ocorre em segundo plano.
            </p>
            <div style={{display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap'}}>
              <select
                value={mlTrainMode}
                onChange={e => setMlTrainMode(e.target.value as 'incremental' | 'full')}
                disabled={mlTraining}
                style={{
                  padding: '0.5rem 0.75rem',
                  borderRadius: '6px',
                  border: '1px solid var(--color-border)',
                  background: 'var(--color-bg-secondary)',
                  color: 'var(--color-text)',
                  fontSize: '0.9rem',
                  cursor: mlTraining ? 'not-allowed' : 'pointer',
                }}
              >
                <option value="incremental">Incremental — atualiza com novos dados</option>
                <option value="full">Completo — treina do zero</option>
              </select>
              <Button onClick={handleTrainModels} disabled={mlTraining} size="sm">
                {mlTraining ? '⏳ Enviando...' : '🚀 Iniciar Treinamento'}
              </Button>
            </div>
          </div>

          {/* Info sobre consolidação de equipes */}
          <div className="update-card" style={{marginTop: '1.5rem'}}>
            <h4>📊 Herança de Dados de Equipes</h4>
            <p className="update-detail">
              Os modelos foram treinados com dados consolidados considerando a herança histórica de equipes:
            </p>
            <ul style={{fontSize: '0.9rem', marginTop: '0.5rem', lineHeight: '1.8'}}>
              <li><strong>Mercedes:</strong> Herda dados de Tyrrell → BAR → Honda → Brawn GP</li>
              <li><strong>Red Bull Racing:</strong> Herda dados de Stewart → Jaguar</li>
              <li><strong>Alpine:</strong> Herda dados de Toleman → Benetton → Renault → Lotus</li>
              <li><strong>Aston Martin:</strong> Herda dados de Jordan → Midland → Spyker → Force India → Racing Point</li>
              <li><strong>Racing Bulls:</strong> Herda dados de Minardi → Toro Rosso → AlphaTauri → RB</li>
            </ul>
          </div>
        </CollapsibleSection>
      )}

      {/* Data Audit Reports */}
      {auditData && (
        <CollapsibleSection as="section" className="status-section" title="🔍 Auditoria de Dados">
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
        </CollapsibleSection>
      )}

      {/* Últimas Atualizações */}
      <CollapsibleSection as="section" className="status-section" title="🔄 Últimas Atualizações (2018+)">
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
      </CollapsibleSection>
    </div>
  );
}
