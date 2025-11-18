import { useState, useEffect } from 'react';
import { DataAuditSuggestion, SuggestionsByTable } from '../types';
import f1Api from '../services/api';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';
import { useNotification } from '../contexts/NotificationContext';
import './DataAudit.css';

interface EditModalData {
  id: number;
  currentValue: string;
  suggestedValue: string;
  tableName: string;
  fieldName: string;
  recordIdentifier: string;
}

export default function DataAudit() {
  const [suggestions, setSuggestions] = useState<DataAuditSuggestion[]>([]);
  const [filteredSuggestions, setFilteredSuggestions] = useState<DataAuditSuggestion[]>([]);
  const [tableStats, setTableStats] = useState<SuggestionsByTable[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedSuggestions, setSelectedSuggestions] = useState<Set<number>>(new Set());
  const [showEditModal, setShowEditModal] = useState(false);
  const [editModalData, setEditModalData] = useState<EditModalData | null>(null);
  const [editedValue, setEditedValue] = useState('');
  const [processingIds, setProcessingIds] = useState<Set<number>>(new Set());
  const { success, error: showError, warning } = useNotification();

  // Filtros
  const [selectedTable, setSelectedTable] = useState<string>('');
  const [selectedField, setSelectedField] = useState<string>('');
  const [minConfidence, setMinConfidence] = useState<number>(0);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [showApplied, setShowApplied] = useState(false);
  const [showRejected, setShowRejected] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    applyFilters();
  }, [suggestions, selectedTable, selectedField, minConfidence, searchQuery, showApplied, showRejected]);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [suggestionsData, statsData] = await Promise.all([
        f1Api.getPendingDataAuditSuggestions(),
        f1Api.getSuggestionsByTable(),
      ]);

      setSuggestions(suggestionsData.results || suggestionsData);
      setTableStats(statsData);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Erro ao carregar sugestões');
      console.error('Erro ao carregar dados de auditoria:', err);
    } finally {
      setLoading(false);
    }
  };

  const applyFilters = () => {
    let filtered = [...suggestions];

    // Filtrar por tabela
    if (selectedTable) {
      filtered = filtered.filter(s => s.table_name === selectedTable);
    }

    // Filtrar por campo
    if (selectedField) {
      filtered = filtered.filter(s => s.field_name === selectedField);
    }

    // Filtrar por confiança mínima
    if (minConfidence > 0) {
      filtered = filtered.filter(s => s.confidence_score >= minConfidence);
    }

    // Filtrar por busca
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(s =>
        s.record_identifier.toLowerCase().includes(query) ||
        s.table_name.toLowerCase().includes(query) ||
        s.field_name.toLowerCase().includes(query) ||
        s.suggested_value.toLowerCase().includes(query)
      );
    }

    // Mostrar aplicadas/rejeitadas
    if (!showApplied) {
      filtered = filtered.filter(s => !s.applied);
    }
    if (!showRejected) {
      filtered = filtered.filter(s => !s.rejected);
    }

    setFilteredSuggestions(filtered);
  };

  const handleApplySuggestion = async (id: number) => {
    try {
      setProcessingIds(prev => new Set(prev).add(id));

      await f1Api.applySuggestion(id);

      success('Sucesso', 'Sugestão aplicada com sucesso!');

      // Remover da lista
      setSuggestions(prev => prev.filter(s => s.id !== id));
      setSelectedSuggestions(prev => {
        const newSet = new Set(prev);
        newSet.delete(id);
        return newSet;
      });
    } catch (err: any) {
      const errorMsg = err.response?.data?.error || 'Erro ao aplicar sugestão';
      showError('Erro', errorMsg);
      console.error('Erro ao aplicar sugestão:', err);
    } finally {
      setProcessingIds(prev => {
        const newSet = new Set(prev);
        newSet.delete(id);
        return newSet;
      });
    }
  };

  const handleRejectSuggestion = async (id: number, reason?: string) => {
    try {
      setProcessingIds(prev => new Set(prev).add(id));

      await f1Api.rejectSuggestion(id, reason);

      success('Sucesso', 'Sugestão rejeitada');

      // Remover da lista
      setSuggestions(prev => prev.filter(s => s.id !== id));
      setSelectedSuggestions(prev => {
        const newSet = new Set(prev);
        newSet.delete(id);
        return newSet;
      });
    } catch (err: any) {
      const errorMsg = err.response?.data?.error || 'Erro ao rejeitar sugestão';
      showError("Erro", errorMsg);
      console.error('Erro ao rejeitar sugestão:', err);
    } finally {
      setProcessingIds(prev => {
        const newSet = new Set(prev);
        newSet.delete(id);
        return newSet;
      });
    }
  };

  const handleEditSuggestion = (suggestion: DataAuditSuggestion) => {
    setEditModalData({
      id: suggestion.id,
      currentValue: suggestion.current_value || '',
      suggestedValue: suggestion.suggested_value,
      tableName: suggestion.table_name,
      fieldName: suggestion.field_name,
      recordIdentifier: suggestion.record_identifier,
    });
    setEditedValue(suggestion.suggested_value);
    setShowEditModal(true);
  };

  const handleSaveEdit = async () => {
    if (!editModalData) return;

    try {
      await f1Api.updateSuggestion(editModalData.id, editedValue);

      success('Sucesso', 'Valor atualizado com sucesso!');

      // Atualizar na lista
      setSuggestions(prev =>
        prev.map(s => s.id === editModalData.id ? { ...s, suggested_value: editedValue } : s)
      );

      setShowEditModal(false);
      setEditModalData(null);
    } catch (err: any) {
      const errorMsg = err.response?.data?.error || 'Erro ao atualizar sugestão';
      showError("Erro", errorMsg);
      console.error('Erro ao atualizar sugestão:', err);
    }
  };

  const handleBulkApply = async () => {
    if (selectedSuggestions.size === 0) {
      warning('Atenção', 'Selecione pelo menos uma sugestão');
      return;
    }

    try {
      setLoading(true);

      const result = await f1Api.bulkApplySuggestions(Array.from(selectedSuggestions));

      const { success: successList, failed: failedList } = result.results;

      if (successList.length > 0) {
        success("Sucesso", `${successList.length} sugestões aplicadas com sucesso!`);
      }

      if (failedList.length > 0) {
        showError("Erro", `${failedList.length} sugestões falharam`);
      }

      // Atualizar lista
      await fetchData();
      setSelectedSuggestions(new Set());
    } catch (err: any) {
      const errorMsg = err.response?.data?.error || 'Erro ao aplicar sugestões em lote';
      showError("Erro", errorMsg);
      console.error('Erro ao aplicar sugestões em lote:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleBulkReject = async () => {
    if (selectedSuggestions.size === 0) {
      warning('Atenção', 'Selecione pelo menos uma sugestão');
      return;
    }

    try {
      setLoading(true);

      await f1Api.bulkRejectSuggestions(Array.from(selectedSuggestions));

      success("Sucesso", `${selectedSuggestions.size} sugestões rejeitadas`);

      // Atualizar lista
      await fetchData();
      setSelectedSuggestions(new Set());
    } catch (err: any) {
      const errorMsg = err.response?.data?.error || 'Erro ao rejeitar sugestões em lote';
      showError("Erro", errorMsg);
      console.error('Erro ao rejeitar sugestões em lote:', err);
    } finally {
      setLoading(false);
    }
  };

  const toggleSelection = (id: number) => {
    setSelectedSuggestions(prev => {
      const newSet = new Set(prev);
      if (newSet.has(id)) {
        newSet.delete(id);
      } else {
        newSet.add(id);
      }
      return newSet;
    });
  };

  const toggleSelectAll = () => {
    if (selectedSuggestions.size === filteredSuggestions.length) {
      setSelectedSuggestions(new Set());
    } else {
      setSelectedSuggestions(new Set(filteredSuggestions.map(s => s.id)));
    }
  };

  const getConfidenceBadgeClass = (score: number): string => {
    if (score >= 0.9) return 'confidence-badge confidence-high';
    if (score >= 0.7) return 'confidence-badge confidence-medium';
    return 'confidence-badge confidence-low';
  };

  const getConfidenceLabel = (score: number): string => {
    if (score >= 0.9) return 'Alta';
    if (score >= 0.7) return 'Média';
    return 'Baixa';
  };

  // Obter valores únicos para filtros
  const uniqueTables = Array.from(new Set(suggestions.map(s => s.table_name))).sort();
  const uniqueFields = Array.from(new Set(
    suggestions
      .filter(s => !selectedTable || s.table_name === selectedTable)
      .map(s => s.field_name)
  )).sort();

  if (loading && suggestions.length === 0) {
    return (
      <div className="data-audit-container">
        <h1>Auditoria de Dados</h1>
        <LoadingSpinner />
      </div>
    );
  }

  if (error) {
    return (
      <div className="data-audit-container">
        <h1>Auditoria de Dados</h1>
        <ErrorMessage message={error} />
      </div>
    );
  }

  return (
    <div className="data-audit-container">
      <div className="data-audit-header">
        <h1>Auditoria de Dados</h1>
        <p className="subtitle">
          Gerencie sugestões de preenchimento de dados faltantes
        </p>
      </div>

      {/* Estatísticas por Tabela */}
      {tableStats.length > 0 && (
        <div className="table-stats">
          <h3>Estatísticas por Tabela</h3>
          <div className="stats-grid">
            {tableStats.map(stat => (
              <div key={stat.table_name} className="stat-card">
                <h4>{stat.table_name}</h4>
                <div className="stat-numbers">
                  <span className="stat-item">
                    <strong>{stat.pending}</strong> pendentes
                  </span>
                  <span className="stat-item">
                    <strong>{stat.applied}</strong> aplicadas
                  </span>
                  <span className="stat-item">
                    <strong>{stat.rejected}</strong> rejeitadas
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Filtros */}
      <div className="filters-section">
        <div className="filters-row">
          <div className="filter-group">
            <label>Tabela:</label>
            <select
              value={selectedTable}
              onChange={(e) => setSelectedTable(e.target.value)}
            >
              <option value="">Todas</option>
              {uniqueTables.map(table => (
                <option key={table} value={table}>{table}</option>
              ))}
            </select>
          </div>

          <div className="filter-group">
            <label>Campo:</label>
            <select
              value={selectedField}
              onChange={(e) => setSelectedField(e.target.value)}
            >
              <option value="">Todos</option>
              {uniqueFields.map(field => (
                <option key={field} value={field}>{field}</option>
              ))}
            </select>
          </div>

          <div className="filter-group">
            <label>Confiança Mínima:</label>
            <select
              value={minConfidence}
              onChange={(e) => setMinConfidence(Number(e.target.value))}
            >
              <option value="0">Qualquer</option>
              <option value="0.7">Média (≥70%)</option>
              <option value="0.9">Alta (≥90%)</option>
            </select>
          </div>

          <div className="filter-group">
            <label>Buscar:</label>
            <input
              type="text"
              placeholder="Buscar..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
        </div>

        <div className="filters-row">
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={showApplied}
              onChange={(e) => setShowApplied(e.target.checked)}
            />
            Mostrar aplicadas
          </label>

          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={showRejected}
              onChange={(e) => setShowRejected(e.target.checked)}
            />
            Mostrar rejeitadas
          </label>
        </div>
      </div>

      {/* Ações em Lote */}
      {selectedSuggestions.size > 0 && (
        <div className="bulk-actions">
          <span className="selection-count">
            {selectedSuggestions.size} selecionada(s)
          </span>
          <button
            onClick={handleBulkApply}
            className="btn btn-success"
            disabled={loading}
          >
            ✓ Aplicar Selecionadas
          </button>
          <button
            onClick={handleBulkReject}
            className="btn btn-danger"
            disabled={loading}
          >
            ✕ Rejeitar Selecionadas
          </button>
        </div>
      )}

      {/* Lista de Sugestões */}
      {filteredSuggestions.length === 0 ? (
        <div className="no-suggestions">
          <p>Nenhuma sugestão encontrada com os filtros aplicados.</p>
        </div>
      ) : (
        <div className="suggestions-list">
          <div className="suggestions-header">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={selectedSuggestions.size === filteredSuggestions.length}
                onChange={toggleSelectAll}
              />
              Selecionar todas ({filteredSuggestions.length})
            </label>
          </div>

          {filteredSuggestions.map(suggestion => (
            <div
              key={suggestion.id}
              className={`suggestion-card ${suggestion.applied ? 'applied' : ''} ${suggestion.rejected ? 'rejected' : ''}`}
            >
              <div className="suggestion-checkbox">
                <input
                  type="checkbox"
                  checked={selectedSuggestions.has(suggestion.id)}
                  onChange={() => toggleSelection(suggestion.id)}
                  disabled={suggestion.applied || suggestion.rejected || processingIds.has(suggestion.id)}
                />
              </div>

              <div className="suggestion-content">
                <div className="suggestion-header-info">
                  <h3>{suggestion.record_identifier}</h3>
                  <span className={getConfidenceBadgeClass(suggestion.confidence_score)}>
                    {getConfidenceLabel(suggestion.confidence_score)} ({(suggestion.confidence_score * 100).toFixed(0)}%)
                  </span>
                </div>

                <div className="suggestion-details">
                  <div className="detail-row">
                    <strong>Tabela:</strong> {suggestion.table_name}
                  </div>
                  <div className="detail-row">
                    <strong>Campo:</strong> {suggestion.field_name}
                  </div>
                  <div className="detail-row">
                    <strong>Valor Atual:</strong>
                    <span className="value-display empty">
                      {suggestion.current_value || '(vazio)'}
                    </span>
                  </div>
                  <div className="detail-row">
                    <strong>Valor Sugerido:</strong>
                    <span className="value-display suggested">
                      {suggestion.suggested_value}
                    </span>
                  </div>
                  <div className="detail-row">
                    <strong>Fonte:</strong>
                    <a
                      href={suggestion.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="source-link"
                    >
                      {suggestion.source_name} ↗
                    </a>
                  </div>
                </div>

                {!suggestion.applied && !suggestion.rejected && (
                  <div className="suggestion-actions">
                    <button
                      onClick={() => handleApplySuggestion(suggestion.id)}
                      className="btn btn-success btn-sm"
                      disabled={processingIds.has(suggestion.id)}
                    >
                      {processingIds.has(suggestion.id) ? 'Aplicando...' : '✓ Aceitar'}
                    </button>
                    <button
                      onClick={() => handleEditSuggestion(suggestion)}
                      className="btn btn-primary btn-sm"
                      disabled={processingIds.has(suggestion.id)}
                    >
                      ✏️ Editar
                    </button>
                    <button
                      onClick={() => handleRejectSuggestion(suggestion.id)}
                      className="btn btn-danger btn-sm"
                      disabled={processingIds.has(suggestion.id)}
                    >
                      {processingIds.has(suggestion.id) ? 'Rejeitando...' : '✕ Rejeitar'}
                    </button>
                  </div>
                )}

                {suggestion.applied && (
                  <div className="status-badge applied-badge">
                    ✓ Aplicada em {new Date(suggestion.applied_at!).toLocaleString('pt-BR')}
                  </div>
                )}

                {suggestion.rejected && (
                  <div className="status-badge rejected-badge">
                    ✕ Rejeitada
                    {suggestion.rejection_reason && ` - ${suggestion.rejection_reason}`}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modal de Edição */}
      {showEditModal && editModalData && (
        <div className="modal-overlay" onClick={() => setShowEditModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Editar Valor Sugerido</h2>
              <button className="modal-close" onClick={() => setShowEditModal(false)}>
                ✕
              </button>
            </div>

            <div className="modal-body">
              <div className="modal-info">
                <p><strong>Registro:</strong> {editModalData.recordIdentifier}</p>
                <p><strong>Tabela:</strong> {editModalData.tableName}</p>
                <p><strong>Campo:</strong> {editModalData.fieldName}</p>
                <p>
                  <strong>Valor Atual:</strong>
                  <span className="value-display empty">
                    {editModalData.currentValue || '(vazio)'}
                  </span>
                </p>
              </div>

              <div className="form-group">
                <label>Novo Valor:</label>
                <input
                  type="text"
                  value={editedValue}
                  onChange={(e) => setEditedValue(e.target.value)}
                  className="form-input"
                  autoFocus
                />
              </div>
            </div>

            <div className="modal-footer">
              <button
                onClick={() => setShowEditModal(false)}
                className="btn btn-secondary"
              >
                Cancelar
              </button>
              <button
                onClick={handleSaveEdit}
                className="btn btn-primary"
                disabled={!editedValue.trim()}
              >
                Salvar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
