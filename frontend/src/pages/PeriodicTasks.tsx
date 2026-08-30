import { useEffect, useState } from 'react';
import { f1Api } from '../services/api';
import { PeriodicTask, CrontabSchedule } from '../types';
import { useNotification } from '../contexts/NotificationContext';
import LoadingWithRetry from '../components/LoadingWithRetry';
import './PeriodicTasks.css';
import Icon from '../components/Icon';

interface EditingTask extends Partial<PeriodicTask> {
  crontab_minute?: string;
  crontab_hour?: string;
  crontab_day_of_month?: string;
  crontab_month_of_year?: string;
  crontab_day_of_week?: string;
}

export default function PeriodicTasks() {
  const [tasks, setTasks] = useState<PeriodicTask[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingTask, setEditingTask] = useState<EditingTask | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [crontabExplanation, setCrontabExplanation] = useState('');
  const { success, error: errorNotification } = useNotification();

  useEffect(() => {
    loadTasks();
  }, []);

  const loadTasks = async () => {
    try {
      setLoading(true);
      const data = await f1Api.getPeriodicTasks();
      // A API retorna um objeto paginado com results
      const tasksArray = data.results || data;
      setTasks(Array.isArray(tasksArray) ? tasksArray : []);
    } catch (err: any) {
      console.error('Erro ao carregar tarefas:', err);
      errorNotification('Erro', 'Erro ao carregar tarefas periódicas');
    } finally {
      setLoading(false);
    }
  };

  const handleToggleTask = async (taskId: number) => {
    try {
      await f1Api.togglePeriodicTask(taskId);
      success('Sucesso', 'Status da tarefa alterado com sucesso');
      loadTasks();
    } catch (err: any) {
      console.error('Erro ao alterar status da tarefa:', err);
      errorNotification('Erro', 'Erro ao alterar status da tarefa');
    }
  };

  const handleDeleteTask = async (taskId: number, taskName: string) => {
    if (!confirm(`Tem certeza que deseja excluir a tarefa "${taskName}"?`)) {
      return;
    }

    try {
      await f1Api.deletePeriodicTask(taskId);
      success('Sucesso', 'Tarefa excluída com sucesso');
      loadTasks();
    } catch (err: any) {
      console.error('Erro ao excluir tarefa:', err);
      errorNotification('Erro', 'Erro ao excluir tarefa');
    }
  };

  const handleEditTask = (task: PeriodicTask) => {
    const editData: EditingTask = {
      ...task,
      crontab_minute: task.crontab?.minute || '*',
      crontab_hour: task.crontab?.hour || '*',
      crontab_day_of_month: task.crontab?.day_of_month || '*',
      crontab_month_of_year: task.crontab?.month_of_year || '*',
      crontab_day_of_week: task.crontab?.day_of_week || '*',
    };
    setEditingTask(editData);
    updateCrontabExplanation(editData);
  };

  const updateCrontabExplanation = async (task: EditingTask) => {
    const crontabStr = `${task.crontab_minute} ${task.crontab_hour} ${task.crontab_day_of_month} ${task.crontab_month_of_year} ${task.crontab_day_of_week}`;
    try {
      const result = await f1Api.explainCrontab(crontabStr);
      setCrontabExplanation(result.explanation);
    } catch (error) {
      setCrontabExplanation('Formato de crontab inválido');
    }
  };

  const handleCrontabChange = (field: keyof EditingTask, value: string) => {
    if (!editingTask) return;

    const updated = { ...editingTask, [field]: value };
    setEditingTask(updated);
    updateCrontabExplanation(updated);
  };

  const handleSaveTask = async () => {
    if (!editingTask || !editingTask.id) return;

    try {
      // Criar crontab schedule primeiro
      const crontabData = {
        minute: editingTask.crontab_minute || '*',
        hour: editingTask.crontab_hour || '*',
        day_of_month: editingTask.crontab_day_of_month || '*',
        month_of_year: editingTask.crontab_month_of_year || '*',
        day_of_week: editingTask.crontab_day_of_week || '*',
        timezone: 'America/Sao_Paulo',
      };

      const crontabSchedule = await f1Api.createCrontabSchedule(crontabData);

      // Atualizar tarefa com novo crontab
      await f1Api.updatePeriodicTask(editingTask.id, {
        name: editingTask.name,
        description: editingTask.description,
        crontab_id: crontabSchedule.id,
        interval_id: null,
        enabled: editingTask.enabled,
      });

      success('Sucesso', 'Tarefa atualizada com sucesso');
      setEditingTask(null);
      loadTasks();
    } catch (err: any) {
      console.error('Erro ao salvar tarefa:', err);
      errorNotification('Erro', 'Erro ao salvar tarefa');
    }
  };

  const formatLastRun = (lastRunAt: string | null) => {
    if (!lastRunAt) return 'Nunca executada';
    return new Date(lastRunAt).toLocaleString('pt-BR');
  };

  const formatTaskName = (taskName: string) => {
    // Remove prefixo do módulo para exibição
    const parts = taskName.split('.');
    return parts[parts.length - 1];
  };

  if (loading) {
    return <LoadingWithRetry onRetry={loadTasks} />;
  }

  return (
    <div className="container periodic-tasks">
      <div className="page-header">
        <div>
          <h1>Tarefas Periódicas</h1>
          <p className="subtitle">
            Gerencie as tarefas agendadas do Celery Beat
          </p>
        </div>
        <button onClick={() => setShowCreateForm(true)} className="btn-primary">
          <Icon name="plus" size={16} /> Nova Tarefa
        </button>
      </div>

      {/* Lista de Tarefas */}
      <div className="tasks-grid">
        {tasks.map((task) => (
          <div key={task.id} className={`task-card ${!task.enabled ? 'disabled' : ''}`}>
            <div className="task-card-header">
              <div className="task-info">
                <h3>{task.name}</h3>
                <span className="task-name">{formatTaskName(task.task)}</span>
              </div>
              <div className="task-actions">
                <button
                  onClick={() => handleToggleTask(task.id)}
                  className={`toggle-btn ${task.enabled ? 'enabled' : 'disabled'}`}
                  title={task.enabled ? 'Desativar' : 'Ativar'}
                >
                  {task.enabled ? '' : ''}
                </button>
              </div>
            </div>

            <div className="task-card-body">
              {task.description && (
                <p className="task-description">{task.description}</p>
              )}

              <div className="task-schedule">
                <div className="schedule-info">
                  <strong>Agendamento:</strong>
                  <span className="schedule-text">{task.schedule_display}</span>
                </div>

                {task.crontab && (
                  <div className="crontab-display">
                    <code>
                      {task.crontab.minute} {task.crontab.hour}{' '}
                      {task.crontab.day_of_month} {task.crontab.month_of_year}{' '}
                      {task.crontab.day_of_week}
                    </code>
                  </div>
                )}
              </div>

              <div className="task-stats">
                <div className="stat">
                  <span className="stat-label">Última Execução:</span>
                  <span className="stat-value">{formatLastRun(task.last_run_at)}</span>
                </div>
                <div className="stat">
                  <span className="stat-label">Total de Execuções:</span>
                  <span className="stat-value">{task.total_run_count}</span>
                </div>
              </div>
            </div>

            <div className="task-card-footer">
              <button
                onClick={() => handleEditTask(task)}
                className="btn-secondary btn-sm"
              >
                <Icon name="edit" size={16} /> Editar
              </button>
              <button
                onClick={() => handleDeleteTask(task.id, task.name)}
                className="btn-danger btn-sm"
              >
                <Icon name="trash" size={16} /> Excluir
              </button>
            </div>
          </div>
        ))}
      </div>

      {tasks.length === 0 && (
        <div className="empty-state">
          <p>Nenhuma tarefa periódica configurada.</p>
        </div>
      )}

      {/* Modal de Edição */}
      {editingTask && (
        <div className="modal-overlay" onClick={() => setEditingTask(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Editar Tarefa</h2>
              <button onClick={() => setEditingTask(null)} className="close-btn">
                <Icon name="x" size={16} /> 
              </button>
            </div>

            <div className="modal-body">
              <div className="form-group">
                <label>Nome da Tarefa</label>
                <input
                  type="text"
                  value={editingTask.name || ''}
                  onChange={(e) =>
                    setEditingTask({ ...editingTask, name: e.target.value })
                  }
                  className="form-input"
                />
              </div>

              <div className="form-group">
                <label>Descrição</label>
                <textarea
                  value={editingTask.description || ''}
                  onChange={(e) =>
                    setEditingTask({ ...editingTask, description: e.target.value })
                  }
                  className="form-input"
                  rows={3}
                />
              </div>

              <div className="form-group">
                <label>Agendamento Crontab</label>
                <div className="crontab-inputs">
                  <div className="crontab-field">
                    <label>Minuto</label>
                    <input
                      type="text"
                      value={editingTask.crontab_minute || '*'}
                      onChange={(e) =>
                        handleCrontabChange('crontab_minute', e.target.value)
                      }
                      className="form-input"
                      placeholder="*"
                    />
                  </div>
                  <div className="crontab-field">
                    <label>Hora</label>
                    <input
                      type="text"
                      value={editingTask.crontab_hour || '*'}
                      onChange={(e) =>
                        handleCrontabChange('crontab_hour', e.target.value)
                      }
                      className="form-input"
                      placeholder="*"
                    />
                  </div>
                  <div className="crontab-field">
                    <label>Dia do Mês</label>
                    <input
                      type="text"
                      value={editingTask.crontab_day_of_month || '*'}
                      onChange={(e) =>
                        handleCrontabChange('crontab_day_of_month', e.target.value)
                      }
                      className="form-input"
                      placeholder="*"
                    />
                  </div>
                  <div className="crontab-field">
                    <label>Mês</label>
                    <input
                      type="text"
                      value={editingTask.crontab_month_of_year || '*'}
                      onChange={(e) =>
                        handleCrontabChange('crontab_month_of_year', e.target.value)
                      }
                      className="form-input"
                      placeholder="*"
                    />
                  </div>
                  <div className="crontab-field">
                    <label>Dia da Semana</label>
                    <input
                      type="text"
                      value={editingTask.crontab_day_of_week || '*'}
                      onChange={(e) =>
                        handleCrontabChange('crontab_day_of_week', e.target.value)
                      }
                      className="form-input"
                      placeholder="*"
                    />
                  </div>
                </div>

                {crontabExplanation && (
                  <div className="crontab-explanation">
                    <strong>Significado:</strong> {crontabExplanation}
                  </div>
                )}

                <div className="crontab-help">
                  <small>
                    Use * para "qualquer", números específicos, ou */N para intervalos.
                    <br />
                    Exemplo: "0 */6 * * *" = A cada 6 horas
                  </small>
                </div>
              </div>
            </div>

            <div className="modal-footer">
              <button onClick={() => setEditingTask(null)} className="btn-secondary">
                Cancelar
              </button>
              <button onClick={handleSaveTask} className="btn-primary">
                Salvar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
