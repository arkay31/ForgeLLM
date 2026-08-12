import React, { useState, useEffect } from 'react';
import { Layers, Zap, Download, Trash2, CheckCircle2, RefreshCw, RotateCcw, Clock, AlertTriangle, ShieldCheck } from 'lucide-react';
import { hotSwapModel, deleteCheckpoint, rollbackModel, fetchDeploymentHistory } from '../services/api';

export default function RegistryTab({ models, activeModel, onModelsUpdated }) {
  const [selectedCp, setSelectedCp] = useState(null);
  const [deploymentHistory, setDeploymentHistory] = useState([]);
  const [isRollbacking, setIsRollbacking] = useState(false);

  const loadHistory = async () => {
    try {
      const history = await fetchDeploymentHistory();
      setDeploymentHistory(history);
    } catch (err) {
      console.error('Failed to load deployment history:', err);
    }
  };

  useEffect(() => {
    loadHistory();
  }, [models, activeModel]);

  const handleHotSwap = async (checkpoint_id) => {
    try {
      await hotSwapModel(checkpoint_id);
      alert(`🚀 Model checkpoint '${checkpoint_id}' successfully deployed as active serving model!`);
      if (onModelsUpdated) onModelsUpdated();
      loadHistory();
    } catch (err) {
      alert('Deployment failed: ' + err.message);
    }
  };

  const handleRollback = async () => {
    if (!window.confirm('⚠️ Are you sure you want to ROLLBACK production serving traffic to the previous active model checkpoint?')) return;
    setIsRollbacking(true);
    try {
      const res = await rollbackModel();
      alert(`🔄 ${res.message}`);
      if (onModelsUpdated) onModelsUpdated();
      loadHistory();
    } catch (err) {
      alert('Rollback failed: ' + err.message);
    } finally {
      setIsRollbacking(false);
    }
  };

  const handleDelete = async (checkpoint_id) => {
    if (checkpoint_id === activeModel?.checkpoint_id) {
      alert('⛔ Action Blocked: Cannot delete or archive the currently active model. Please deploy another model first.');
      return;
    }
    if (!window.confirm(`Are you sure you want to delete checkpoint '${checkpoint_id}'?`)) return;
    try {
      await deleteCheckpoint(checkpoint_id);
      alert('Checkpoint deleted successfully.');
      if (onModelsUpdated) onModelsUpdated();
    } catch (err) {
      alert('Delete failed: ' + err.message);
    }
  };

  const getStatusBadge = (status, isActive) => {
    if (isActive || status === 'ACTIVE') {
      return <span className="badge badge-emerald"><CheckCircle2 size={12} /> ACTIVE SERVED</span>;
    }
    if (status === 'READY') {
      return <span className="badge badge-cyan">READY</span>;
    }
    if (status === 'REGISTERED') {
      return <span className="badge badge-violet">REGISTERED</span>;
    }
    if (status === 'FAILED') {
      return <span className="badge badge-rose">FAILED</span>;
    }
    return <span className="badge badge-amber">{status || 'ARCHIVED'}</span>;
  };

  return (
    <div className="page-view">
      <div style={{ marginBottom: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 800 }}>Model Registry & Lifecycle Studio</h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
            Manage fine-tuned LoRA adapters, version history, audit logs, and zero-downtime deployment rollbacks.
          </p>
        </div>

        <button
          onClick={handleRollback}
          disabled={isRollbacking}
          className="btn btn-secondary"
          style={{ borderColor: 'rgba(245, 158, 11, 0.4)', color: '#f59e0b', padding: '0.65rem 1.25rem' }}
        >
          <RotateCcw size={16} />
          {isRollbacking ? 'Rolling back...' : 'Rollback to Previous Model'}
        </button>
      </div>

      {/* Checkpoint Table */}
      <div className="glass-card" style={{ marginBottom: '1.5rem' }}>
        <div className="card-header">
          <span className="card-title"><Layers size={18} /> Registered Checkpoint Lifecycle</span>
          <span className="badge badge-cyan">{models.length} Versions</span>
        </div>

        <div className="data-table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Checkpoint ID</th>
                <th>Name</th>
                <th>Version</th>
                <th>Base LLM</th>
                <th>Exact Match</th>
                <th>Exec Acc</th>
                <th>Size</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {models.map((cp) => {
                const isActive = cp.status === 'ACTIVE' || cp.checkpoint_id === activeModel?.checkpoint_id;
                return (
                  <tr key={cp.checkpoint_id}>
                    <td style={{ fontFamily: 'var(--font-mono)', color: '#00f2fe' }}>{cp.checkpoint_id}</td>
                    <td><strong>{cp.name}</strong></td>
                    <td><span className="badge badge-violet" style={{ fontSize: '0.7rem' }}>{cp.version || 'v1.0.0'}</span></td>
                    <td>{cp.base_model}</td>
                    <td><strong style={{ color: '#10b981' }}>{((cp.metrics?.exact_match || 0) * 100).toFixed(0)}%</strong></td>
                    <td><strong style={{ color: '#38bdf8' }}>{((cp.metrics?.exec_acc || 0) * 100).toFixed(0)}%</strong></td>
                    <td>{cp.size_mb} MB</td>
                    <td>{getStatusBadge(cp.status, isActive)}</td>
                    <td>
                      <div style={{ display: 'flex', gap: '0.5rem' }}>
                        {!isActive && (
                          <button
                            onClick={() => handleHotSwap(cp.checkpoint_id)}
                            className="btn btn-primary"
                            style={{ fontSize: '0.75rem', padding: '0.3rem 0.6rem' }}
                            title="Deploy Checkpoint to Production"
                          >
                            <Zap size={14} /> Deploy
                          </button>
                        )}
                        <button
                          onClick={() => setSelectedCp(cp)}
                          className="btn btn-secondary"
                          style={{ fontSize: '0.75rem', padding: '0.3rem 0.6rem' }}
                          title="Inspect Metadata"
                        >
                          Details
                        </button>
                        {cp.checkpoint_id !== 'base-model' && (
                          <button
                            onClick={() => handleDelete(cp.checkpoint_id)}
                            disabled={isActive}
                            className={`btn ${isActive ? 'btn-secondary' : 'btn-danger'}`}
                            style={{ fontSize: '0.75rem', padding: '0.3rem 0.5rem', opacity: isActive ? 0.4 : 1, cursor: isActive ? 'not-allowed' : 'pointer' }}
                            title={isActive ? 'Active model cannot be deleted' : 'Delete Checkpoint'}
                          >
                            <Trash2 size={14} />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Deployment & Rollback Audit History Table */}
      <div className="glass-card" style={{ marginBottom: '1.5rem' }}>
        <div className="card-header">
          <span className="card-title"><Clock size={18} /> Deployment & Rollback Audit History</span>
          <span className="badge badge-emerald">{deploymentHistory.length} Events Logged</span>
        </div>

        <div className="data-table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Event ID</th>
                <th>Action</th>
                <th>Target Model</th>
                <th>Checkpoint ID</th>
                <th>Previous Model</th>
                <th>Timestamp</th>
              </tr>
            </thead>
            <tbody>
              {deploymentHistory.map((dep) => (
                <tr key={dep.event_id}>
                  <td style={{ fontFamily: 'var(--font-mono)', color: '#38bdf8', fontSize: '0.75rem' }}>{dep.event_id}</td>
                  <td>
                    {dep.action === 'rollback' ? (
                      <span className="badge badge-amber" style={{ display: 'flex', gap: '0.25rem', alignItems: 'center', width: 'fit-content' }}>
                        <RotateCcw size={12} /> ROLLBACK
                      </span>
                    ) : (
                      <span className="badge badge-emerald" style={{ display: 'flex', gap: '0.25rem', alignItems: 'center', width: 'fit-content' }}>
                        <Zap size={12} /> DEPLOY
                      </span>
                    )}
                  </td>
                  <td><strong>{dep.model_name}</strong></td>
                  <td style={{ fontFamily: 'var(--font-mono)', color: '#00f2fe', fontSize: '0.75rem' }}>{dep.checkpoint_id}</td>
                  <td style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', fontSize: '0.75rem' }}>{dep.previous_checkpoint_id || 'N/A'}</td>
                  <td style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{dep.timestamp}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Checkpoint Details Drawer */}
      {selectedCp && (
        <div className="glass-card">
          <div className="card-header">
            <span className="card-title">Checkpoint Details: {selectedCp.name} ({selectedCp.version})</span>
            <button onClick={() => setSelectedCp(null)} className="btn btn-secondary" style={{ fontSize: '0.75rem' }}>Close</button>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', fontSize: '0.85rem' }}>
            <div>
              <p><strong>Path:</strong> <code style={{ color: '#38bdf8' }}>{selectedCp.path}</code></p>
              <p><strong>Created At:</strong> {selectedCp.created_at}</p>
              <p><strong>Deployed At:</strong> {selectedCp.deployed_at || 'N/A'}</p>
              <p><strong>Dataset Used:</strong> {selectedCp.dataset_name || selectedCp.dataset_used}</p>
            </div>
            <div>
              <p><strong>Hyperparameters:</strong></p>
              <pre className="sql-box" style={{ marginTop: '0.4rem', fontSize: '0.75rem' }}>
                {JSON.stringify(selectedCp.hyperparameters, null, 2)}
              </pre>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
