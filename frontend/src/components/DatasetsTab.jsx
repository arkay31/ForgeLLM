import React, { useState, useEffect } from 'react';
import { Database, CheckCircle2, Code2, AlertTriangle, Search, Play, FileJson, Cpu } from 'lucide-react';
import { fetchDatasets, fetchDatasetSamples, validateSQL, prepareDataset } from '../services/api';

export default function DatasetsTab() {
  const [datasets, setDatasets] = useState([]);
  const [selectedDataset, setSelectedDataset] = useState('spider_sample.json');
  const [samples, setSamples] = useState([]);
  
  // Interactive SQL Validator
  const [testSql, setTestSql] = useState('SELECT T1.name, SUM(T2.total) FROM singers AS T1 JOIN concerts AS T2 ON T1.id = T2.singer_id GROUP BY T1.name HAVING SUM(T2.total) > 100;');
  const [validationRes, setValidationRes] = useState(null);

  // Data Pipeline Trigger State
  const [formatType, setFormatType] = useState('gemma');
  const [isPreparing, setIsPreparing] = useState(false);
  const [pipelineReport, setPipelineReport] = useState(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const res = await fetchDatasets();
      setDatasets(res.datasets || []);
      const sRes = await fetchDatasetSamples('spider_sample.json');
      setSamples(sRes || []);
    } catch (err) {
      console.error(err);
    }
  };

  const handleDatasetSelect = async (name) => {
    setSelectedDataset(name);
    try {
      const sRes = await fetchDatasetSamples(name);
      setSamples(sRes || []);
    } catch (err) {
      console.error(err);
    }
  };

  const handleValidateSql = async () => {
    try {
      const res = await validateSQL(testSql);
      setValidationRes(res);
    } catch (err) {
      alert('Validation error: ' + err.message);
    }
  };

  const handleRunPipeline = async () => {
    setIsPreparing(true);
    setPipelineReport(null);
    try {
      const res = await prepareDataset('spider', formatType);
      setPipelineReport(res);
      alert('✅ Data pipeline execution completed! JSONL datasets generated & validated.');
      loadData();
    } catch (err) {
      alert('Pipeline execution failed: ' + err.message);
    } finally {
      setIsPreparing(false);
    }
  };

  return (
    <div className="page-view">
      <div style={{ marginBottom: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 800 }}>Dataset & SQL Pipeline Manager</h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
            Data cleaning, deduplication, train/val/test splitting, JSONL instruction formatting, and token length validation.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <select className="form-select" value={formatType} onChange={(e) => setFormatType(e.target.value)} style={{ padding: '0.55rem' }}>
            <option value="gemma">Format: Gemma</option>
            <option value="alpaca">Format: Alpaca</option>
            <option value="chatml">Format: ChatML</option>
            <option value="llama3">Format: Llama-3</option>
          </select>
          <button
            onClick={handleRunPipeline}
            disabled={isPreparing}
            className="btn btn-primary"
            style={{ padding: '0.65rem 1.2rem' }}
          >
            <Play size={16} />
            {isPreparing ? 'Processing Data Pipeline...' : 'Run Pipeline & Export JSONL'}
          </button>
        </div>
      </div>

      {/* Validation Report Banner if Pipeline executed */}
      {pipelineReport && (
        <div className="glass-card" style={{ marginBottom: '1.5rem', borderColor: 'var(--primary-cyan)' }}>
          <div className="card-header">
            <span className="card-title" style={{ color: '#00f2fe' }}><CheckCircle2 size={18} /> Data Pipeline Validation Report</span>
            <span className="badge badge-emerald">Dataset: {pipelineReport.dataset} ({pipelineReport.format})</span>
          </div>

          <div className="grid-4" style={{ marginBottom: '0.5rem' }}>
            <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '0.75rem', borderRadius: '8px' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Train Split</div>
              <strong style={{ fontSize: '1.2rem', color: '#00f2fe' }}>{pipelineReport.splits?.train} records</strong>
            </div>
            <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '0.75rem', borderRadius: '8px' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>SQL AST Validity</div>
              <strong style={{ fontSize: '1.2rem', color: '#10b981' }}>{pipelineReport.validation_report?.syntax_checks?.validity_percentage}%</strong>
            </div>
            <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '0.75rem', borderRadius: '8px' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Prompt Tokens (P50/P95)</div>
              <strong style={{ fontSize: '1.2rem', color: '#f59e0b' }}>
                {pipelineReport.validation_report?.token_length_distribution?.prompt_tokens?.p50} / {pipelineReport.validation_report?.token_length_distribution?.prompt_tokens?.p95}
              </strong>
            </div>
            <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '0.75rem', borderRadius: '8px' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Completion Tokens (P50/P95)</div>
              <strong style={{ fontSize: '1.2rem', color: '#38bdf8' }}>
                {pipelineReport.validation_report?.token_length_distribution?.completion_tokens?.p50} / {pipelineReport.validation_report?.token_length_distribution?.completion_tokens?.p95}
              </strong>
            </div>
          </div>
        </div>
      )}

      <div className="grid-2">
        {/* Dataset Browser */}
        <div className="glass-card">
          <div className="card-header">
            <span className="card-title"><Database size={18} /> Available Training Corpora</span>
            <span className="badge badge-cyan">{datasets.length} Datasets</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginBottom: '1rem' }}>
            {datasets.map((ds) => (
              <div
                key={ds.dataset_name}
                onClick={() => handleDatasetSelect(ds.dataset_name)}
                style={{
                  background: selectedDataset === ds.dataset_name ? 'rgba(0, 242, 254, 0.1)' : 'rgba(255, 255, 255, 0.03)',
                  border: `1px solid ${selectedDataset === ds.dataset_name ? 'var(--primary-cyan)' : 'var(--border-color)'}`,
                  padding: '0.85rem',
                  borderRadius: '10px',
                  cursor: 'pointer',
                  display: 'flex',
                  justify: 'space-between',
                  alignItems: 'center',
                }}
              >
                <div>
                  <strong style={{ color: '#fff', fontSize: '0.9rem' }}>{ds.dataset_name}</strong>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                    {ds.total_pairs} Prompt-SQL Pairs | Domains: {ds.domains?.join(', ')}
                  </div>
                </div>
                <span className="badge badge-violet">Loaded</span>
              </div>
            ))}
          </div>
        </div>

        {/* Interactive SQL Validator */}
        <div className="glass-card">
          <div className="card-header">
            <span className="card-title"><Code2 size={18} /> Interactive SQL Linter & AST Validator</span>
            <span className="badge badge-emerald">sqlglot Engine</span>
          </div>

          <div className="form-group">
            <label className="form-label">Input SQL to Lint & Parse AST</label>
            <textarea
              rows={4}
              className="form-textarea"
              value={testSql}
              onChange={(e) => setTestSql(e.target.value)}
              style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem' }}
            />
          </div>

          <button onClick={handleValidateSql} className="btn btn-primary" style={{ width: '100%', padding: '0.65rem' }}>
            Lint & Validate SQL Syntax
          </button>

          {validationRes && (
            <div style={{ marginTop: '1rem' }}>
              {validationRes.valid ? (
                <div style={{ background: 'rgba(16, 185, 129, 0.1)', border: '1px solid rgba(16, 185, 129, 0.3)', padding: '0.75rem', borderRadius: '8px', color: '#10b981', fontSize: '0.85rem' }}>
                  <div style={{ fontWeight: 700, marginBottom: '0.4rem' }}>✓ Valid SQL Syntax</div>
                  <div>Tables Referenced: <code>{validationRes.tables_referenced.join(', ') || 'None'}</code></div>
                </div>
              ) : (
                <div style={{ background: 'rgba(244, 63, 94, 0.1)', border: '1px solid rgba(244, 63, 94, 0.3)', padding: '0.75rem', borderRadius: '8px', color: '#f43f5e', fontSize: '0.85rem' }}>
                  ❌ Syntax Error: {validationRes.syntax_error}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Dataset Samples Inspection */}
      <div className="glass-card">
        <div className="card-header">
          <span className="card-title">Training Pair Inspection ({selectedDataset})</span>
        </div>
        <div className="data-table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Database</th>
                <th>Instruction Question</th>
                <th>Target SQL Output</th>
              </tr>
            </thead>
            <tbody>
              {samples.slice(0, 5).map((s) => (
                <tr key={s.id}>
                  <td style={{ fontFamily: 'var(--font-mono)', color: '#00f2fe' }}>{s.id}</td>
                  <td><span className="badge badge-cyan">{s.db_id || 'default'}</span></td>
                  <td style={{ maxWidth: '300px' }}>{s.instruction}</td>
                  <td style={{ fontFamily: 'var(--font-mono)', color: '#38bdf8', fontSize: '0.8rem' }}>{s.output}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
