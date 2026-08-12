import React, { useState, useEffect } from 'react';
import { GitBranch, Layers, Award, Clock, ArrowRight, CheckCircle2, ShieldCheck, RefreshCw, BarChart2 } from 'lucide-react';
import { fetchExperiments, compareExperiments } from '../services/api';

export default function ExperimentsTab({ onNavigateToRegistry }) {
  const [experiments, setExperiments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedExp1, setSelectedExp1] = useState(null);
  const [selectedExp2, setSelectedExp2] = useState(null);
  const [comparison, setComparison] = useState(null);
  const [comparing, setComparing] = useState(false);

  const loadExperiments = async () => {
    setLoading(true);
    try {
      const data = await fetchExperiments();
      setExperiments(data);
      if (data && data.length >= 2) {
        setSelectedExp1(data[0].experiment_id);
        setSelectedExp2(data[1].experiment_id);
      } else if (data && data.length === 1) {
        setSelectedExp1(data[0].experiment_id);
      }
    } catch (err) {
      console.error('Failed to load experiments metadata:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadExperiments();
  }, []);

  const handleCompare = async () => {
    if (!selectedExp1 || !selectedExp2 || selectedExp1 === selectedExp2) return;
    setComparing(true);
    try {
      const res = await compareExperiments(selectedExp1, selectedExp2);
      setComparison(res);
    } catch (err) {
      console.error('Failed to compare experiments:', err);
    } finally {
      setComparing(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      
      {/* Header Banner & MLOps Lifecycle Flow */}
      <div className="glass-card">
        <div className="card-header">
          <span className="card-title">
            <GitBranch size={20} style={{ color: 'var(--primary-cyan)' }} /> MLOps Experiment Tracking & Lifecycle Management
          </span>
          <button onClick={loadExperiments} className="btn btn-secondary" style={{ fontSize: '0.8rem' }}>
            <RefreshCw size={14} /> Refresh Experiments
          </button>
        </div>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '1rem' }}>
          Every training run and evaluation benchmark is persisted as an immutable reproducible experiment, tracking full parameter configurations, loss curves, and evaluation metrics.
        </p>

        {/* Complete Lifecycle Traceability Flow */}
        <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '1.25rem', borderRadius: '12px', border: '1px solid #1e293b' }}>
          <div style={{ fontSize: '0.8rem', color: 'var(--primary-cyan)', fontWeight: 600, marginBottom: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Complete Traceable Lifecycle
          </div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.5rem' }}>
            <div style={{ textAlign: 'center', flex: 1, minWidth: '120px' }}>
              <div className="badge badge-violet" style={{ width: '100%', justifyContent: 'center', padding: '0.5rem' }}>1. Experiment</div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '0.3rem' }}>Hypothesis & Hyperparameters</div>
            </div>
            <ArrowRight size={16} style={{ color: 'var(--text-muted)' }} />
            <div style={{ textAlign: 'center', flex: 1, minWidth: '120px' }}>
              <div className="badge badge-cyan" style={{ width: '100%', justifyContent: 'center', padding: '0.5rem' }}>2. Training</div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '0.3rem' }}>PyTorch + PEFT LoRA (CUDA/MPS/CPU)</div>

            </div>
            <ArrowRight size={16} style={{ color: 'var(--text-muted)' }} />
            <div style={{ textAlign: 'center', flex: 1, minWidth: '120px' }}>
              <div className="badge badge-emerald" style={{ width: '100%', justifyContent: 'center', padding: '0.5rem' }}>3. Checkpoint</div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '0.3rem' }}>Safetensors Weight Artifacts</div>
            </div>
            <ArrowRight size={16} style={{ color: 'var(--text-muted)' }} />
            <div style={{ textAlign: 'center', flex: 1, minWidth: '120px' }}>
              <div className="badge badge-amber" style={{ width: '100%', justifyContent: 'center', padding: '0.5rem' }}>4. Evaluation</div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '0.3rem' }}>AST EM & Result Set EX</div>
            </div>
            <ArrowRight size={16} style={{ color: 'var(--text-muted)' }} />
            <div style={{ textAlign: 'center', flex: 1, minWidth: '120px' }}>
              <div className="badge badge-emerald" style={{ width: '100%', justifyContent: 'center', padding: '0.5rem' }}>5. Deployment</div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '0.3rem' }}>Zero-Downtime Serving Traffic</div>
            </div>
          </div>
        </div>
      </div>

      {/* Side-by-Side Comparison Controls */}
      <div className="glass-card">
        <div className="card-header">
          <span className="card-title"><BarChart2 size={18} /> Side-by-Side Experiment Comparison</span>
          <button
            onClick={handleCompare}
            disabled={!selectedExp1 || !selectedExp2 || selectedExp1 === selectedExp2 || comparing}
            className="btn btn-primary"
            style={{ fontSize: '0.8rem' }}
          >
            {comparing ? 'Comparing...' : 'Compare Selected Experiments'}
          </button>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginTop: '0.5rem' }}>
          <div>
            <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.3rem' }}>Baseline Experiment 1:</label>
            <select
              value={selectedExp1 || ''}
              onChange={(e) => setSelectedExp1(e.target.value)}
              className="select-input"
              style={{ width: '100%' }}
            >
              {experiments.map((exp) => (
                <option key={exp.experiment_id} value={exp.experiment_id}>
                  {exp.experiment_id} ({exp.checkpoint_id})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.3rem' }}>Comparison Experiment 2:</label>
            <select
              value={selectedExp2 || ''}
              onChange={(e) => setSelectedExp2(e.target.value)}
              className="select-input"
              style={{ width: '100%' }}
            >
              {experiments.map((exp) => (
                <option key={exp.experiment_id} value={exp.experiment_id}>
                  {exp.experiment_id} ({exp.checkpoint_id})
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Comparison Differential Card */}
        {comparison && (
          <div style={{ marginTop: '1.25rem', background: 'rgba(15, 23, 42, 0.7)', padding: '1.25rem', borderRadius: '12px', border: '1px solid #00f2fe' }}>
            <h4 style={{ fontSize: '1rem', marginBottom: '1rem', color: '#00f2fe' }}>
              Comparison Results: {comparison.exp1.experiment_id} ──► {comparison.exp2.experiment_id}
            </h4>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem' }}>
              <div style={{ background: 'rgba(30, 41, 59, 0.6)', padding: '0.75rem', borderRadius: '8px' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Exact Match (EM)</div>
                <div style={{ fontSize: '1.2rem', fontWeight: 700, color: comparison.diff_exact_match_acc >= 0 ? '#10b981' : '#f43f5e' }}>
                  {(comparison.exp2.exact_match_acc * 100).toFixed(0)}% vs {(comparison.exp1.exact_match_acc * 100).toFixed(0)}%
                </div>
                <div style={{ fontSize: '0.8rem', color: comparison.diff_exact_match_acc >= 0 ? '#10b981' : '#f43f5e' }}>
                  {comparison.diff_exact_match_acc >= 0 ? '+' : ''}{(comparison.diff_exact_match_acc * 100).toFixed(1)}% Lift
                </div>
              </div>

              <div style={{ background: 'rgba(30, 41, 59, 0.6)', padding: '0.75rem', borderRadius: '8px' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Execution Acc (EX)</div>
                <div style={{ fontSize: '1.2rem', fontWeight: 700, color: comparison.diff_execution_acc >= 0 ? '#00f2fe' : '#f43f5e' }}>
                  {(comparison.exp2.execution_acc * 100).toFixed(0)}% vs {(comparison.exp1.execution_acc * 100).toFixed(0)}%
                </div>
                <div style={{ fontSize: '0.8rem', color: comparison.diff_execution_acc >= 0 ? '#00f2fe' : '#f43f5e' }}>
                  {comparison.diff_execution_acc >= 0 ? '+' : ''}{(comparison.diff_execution_acc * 100).toFixed(1)}% Lift
                </div>
              </div>

              <div style={{ background: 'rgba(30, 41, 59, 0.6)', padding: '0.75rem', borderRadius: '8px' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>P95 Latency</div>
                <div style={{ fontSize: '1.2rem', fontWeight: 700, color: comparison.diff_p95_latency_ms <= 0 ? '#10b981' : '#f43f5e' }}>
                  {comparison.exp2.p95_latency_ms}ms vs {comparison.exp1.p95_latency_ms}ms
                </div>
                <div style={{ fontSize: '0.8rem', color: comparison.diff_p95_latency_ms <= 0 ? '#10b981' : '#f43f5e' }}>
                  {comparison.diff_p95_latency_ms <= 0 ? '' : '+'}{comparison.diff_p95_latency_ms} ms
                </div>
              </div>

              <div style={{ background: 'rgba(30, 41, 59, 0.6)', padding: '0.75rem', borderRadius: '8px' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Validation Loss</div>
                <div style={{ fontSize: '1.2rem', fontWeight: 700, color: comparison.diff_final_val_loss <= 0 ? '#10b981' : '#f43f5e' }}>
                  {comparison.exp2.final_val_loss} vs {comparison.exp1.final_val_loss}
                </div>
                <div style={{ fontSize: '0.8rem', color: comparison.diff_final_val_loss <= 0 ? '#10b981' : '#f43f5e' }}>
                  {comparison.diff_final_val_loss <= 0 ? '' : '+'}{comparison.diff_final_val_loss}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Persistent Experiment History Table */}
      <div className="glass-card">
        <div className="card-header">
          <span className="card-title">Persistent Experiment History Log</span>
        </div>

        {loading ? (
          <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>Loading experiment history...</div>
        ) : (
          <div className="data-table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Experiment ID</th>
                  <th>Checkpoint ID</th>
                  <th>Base Model</th>
                  <th>LoRA r/α</th>
                  <th>Val Loss</th>
                  <th>EM Acc</th>
                  <th>EX Acc</th>
                  <th>P95 Latency</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {experiments.map((exp) => (
                  <tr key={exp.experiment_id}>
                    <td style={{ fontFamily: 'var(--font-mono)', color: '#00f2fe', fontWeight: 600 }}>{exp.experiment_id}</td>
                    <td style={{ fontFamily: 'var(--font-mono)', color: '#e2e8f0', fontSize: '0.8rem' }}>{exp.checkpoint_id}</td>
                    <td style={{ fontSize: '0.8rem' }}>{exp.base_model}</td>
                    <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>r={exp.lora_r}, α={exp.lora_alpha}</td>
                    <td style={{ fontFamily: 'var(--font-mono)', color: '#f59e0b' }}>{exp.final_val_loss}</td>
                    <td>
                      <span className="badge badge-emerald">{(exp.exact_match_acc * 100).toFixed(0)}%</span>
                    </td>
                    <td>
                      <span className="badge badge-cyan">{(exp.execution_acc * 100).toFixed(0)}%</span>
                    </td>
                    <td style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{exp.p95_latency_ms} ms</td>
                    <td>
                      {exp.is_deployed ? (
                        <span className="badge badge-emerald">ACTIVE DEPLOYED</span>
                      ) : (
                        <span className="badge badge-violet">{exp.deployment_status || 'READY'}</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

    </div>
  );
}
