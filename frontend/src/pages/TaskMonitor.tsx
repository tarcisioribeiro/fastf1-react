import { useEffect, useState } from 'react';
import { f1Api } from '../services/api';
import LoadingWithRetry from '../components/LoadingWithRetry';
import './TaskMonitor.css';

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
  periodic_tasks?: any[];
  error?: string;
  message?: string;
}

export default function TaskMonitor() {
  const [tasksData, setTasksData] = useState<TasksData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  useEffect(() => {
    loadTasks();

    // Auto-refresh a cada 5 segundos se habilitado
    const interval = setInterval(() => {
      if (autoRefresh) {
        loadTasks(false);
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [autoRefresh]);

  const loadTasks = async (showLoading = true) => {
    try {
      if (showLoading) {
        setLoading(true);
      }
      setError(null);

      const data = await f1Api.getTasksStatus();
      setTasksData(data);
      setLastUpdate(new Date());
    } catch (err: any) {
      console.error('Error loading tasks:', err);
      setError(err.response?.data?.error || 'Erro ao carregar status das tarefas');
    } finally {
      if (showLoading) {
        setLoading(false);
      }
    }
  };

  const formatTaskName = (name: string) => {
    // Remove prefixo do módulo
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

  if (loading) {
    return <LoadingWithRetry onRetry={() => loadTasks()} />;
  }

  if (error) {
    return (
      <div className="container">
        <div className="error-container">
          <div className="error-icon">⚠️</div>
          <h2>Erro ao carregar dados</h2>
          <p>{error}</p>
          <button onClick={() => loadTasks()} className="retry-button">
            Tentar Novamente
          </button>
        </div>
      </div>
    );
  }

  if (!tasksData) {
    return null;
  }

  return (
    <div className="container task-monitor">
      <div className="task-monitor-header">
        <div>
          <h1>Monitor de Tarefas Celery</h1>
          <p className="subtitle">
            Monitoramento em tempo real de tarefas de coleta de dados F1
          </p>
        </div>

        <div className="header-actions">
          <div className="auto-refresh-toggle">
            <label>
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
              />
              Auto-atualizar (5s)
            </label>
          </div>
          <button onClick={() => loadTasks()} className="refresh-button">
            🔄 Atualizar
          </button>
        </div>
      </div>

      {lastUpdate && (
        <div className="last-update">
          Última atualização: {lastUpdate.toLocaleTimeString('pt-BR')}
        </div>
      )}

      {tasksData.error ? (
        <div className="error-banner">
          <strong>⚠️ {tasksData.message}</strong>
          <p>{tasksData.error}</p>
        </div>
      ) : (
        <>
          {/* Workers Status */}
          <section className="stats-grid">
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
          </section>

          {/* Workers Info */}
          {tasksData.workers.length > 0 && (
            <section className="workers-section">
              <h2>Workers</h2>
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
            </section>
          )}

          {/* Active Tasks */}
          <section className="tasks-section">
            <h2>
              Tarefas Ativas ({tasksData.stats.total_active})
              {tasksData.stats.total_active > 0 && (
                <span className="pulse-indicator"></span>
              )}
            </h2>
            {tasksData.tasks.active.length === 0 ? (
              <div className="empty-state">
                <p>Nenhuma tarefa em execução no momento</p>
              </div>
            ) : (
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
                          <span className="task-status running">
                            ⚡ Executando
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          {/* Reserved Tasks (Queue) */}
          <section className="tasks-section">
            <h2>Tarefas na Fila ({tasksData.stats.total_reserved})</h2>
            {tasksData.tasks.reserved.length === 0 ? (
              <div className="empty-state">
                <p>Nenhuma tarefa na fila</p>
              </div>
            ) : (
              <div className="tasks-table-container">
                <table className="tasks-table">
                  <thead>
                    <tr>
                      <th>Tarefa</th>
                      <th>Argumentos</th>
                      <th>Worker Atribuído</th>
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
                          <span className="task-status queued">
                            📋 Na Fila
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          {/* Scheduled Tasks */}
          {tasksData.stats.total_scheduled > 0 && (
            <section className="tasks-section">
              <h2>Tarefas Agendadas ({tasksData.stats.total_scheduled})</h2>
              <div className="tasks-table-container">
                <table className="tasks-table">
                  <thead>
                    <tr>
                      <th>Tarefa</th>
                      <th>Argumentos</th>
                      <th>Worker</th>
                      <th>ETA</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {tasksData.tasks.scheduled.map((task) => (
                      <tr key={task.id} className="task-row scheduled">
                        <td>
                          <strong>{formatTaskName(task.name)}</strong>
                          <div className="task-id">{task.id?.substring(0, 8)}...</div>
                        </td>
                        <td className="task-args">{formatArgs(task.args)}</td>
                        <td>{task.worker.split('@')[1] || task.worker}</td>
                        <td>{task.eta || 'N/A'}</td>
                        <td>
                          <span className="task-status scheduled">
                            ⏰ Agendada
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}

          {/* Periodic Tasks */}
          {tasksData.periodic_tasks && tasksData.periodic_tasks.length > 0 && (
            <section className="tasks-section">
              <h2>Tarefas Periódicas</h2>
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
                        <td>{formatTaskName(task.task)}</td>
                        <td>
                          {task.last_run_at
                            ? new Date(task.last_run_at).toLocaleString('pt-BR')
                            : 'Nunca executada'}
                        </td>
                        <td>{task.total_run_count || 0}</td>
                        <td>
                          <span className={`task-status ${task.enabled ? 'enabled' : 'disabled'}`}>
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
        </>
      )}
    </div>
  );
}
