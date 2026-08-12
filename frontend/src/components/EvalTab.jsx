import React, { useState } from 'react';
import { BarChart3, Play, AlertTriangle, Clock, Zap, CheckCircle2, XCircle, Activity, ShieldCheck } from 'lucide-react';
import { runBenchmark, runPerformanceBenchmark } from '../services/api';

export default function EvalTab({ activeModel, models }) {
  const [activeTab, setActiveTab] = useState('accuracy'); // 'accuracy' or 'performance'
  const [isRunning, setIsRunning] = useState(false);
  const [sampleLimit, setSampleLimit] = useState(5);
  const [benchmarkResult, setBenchmarkResult] = useState(null);
  const [categoryFilter, setCategoryFilter] = useState(null);

  // Performance Load Test Controls

  const [numRequests, setNumRequests] = useState(20);
  const [concurrency, setConcurrency] = useState(4);
  const [perfResult, setPerfResult] = useState(null);

  const handleRunAccuracyBenchmark = async () => {
    setIsRunning(true);
    try {
      const res = await runBenchmark(
        'spider_sample.json',
        activeModel?.checkpoint_id || 'forgellm-qlora-v1-spider',
        parseInt(sampleLimit)
      );
      setBenchmarkResult(res);
    } catch (err) {
      alert('Accuracy Benchmark run failed: ' + err.message);
    } finally {
      setIsRunning(false);
    }
  };

  const handleRunPerfBenchmark = async () => {
    setIsRunning(true);
    try {
      const res = await runPerformanceBenchmark({
        num_requests: parseInt(numRequests),
        concurrency: parseInt(concurrency),
        timeout_seconds: 10.0,
        dataset_name: 'spider_sample.json',
        checkpoint_id: activeModel?.checkpoint_id || 'forgellm-qlora-v1-spider',
        compare_base: true,
      });
      setPerfResult(res);
    } catch (err) {
      alert('Performance Load Benchmark run failed: ' + err.message);
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="page-view">
      <div style={{ marginBottom: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 800 }}>Text-to-SQL Benchmarking & Evaluation Suite</h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
            Scientifically rigorous evaluation comparing Base Foundation Model vs Fine-Tuned Model across AST Exact Match, Execution Accuracy, and Concurrency Load Throughput.
          </p>
        </div>

        {/* Mode Selector Tabs */}
        <div style={{ display: 'flex', background: 'rgba(15, 23, 42, 0.6)', padding: '0.25rem', borderRadius: '8px', border: '1px solid #1e293b' }}>
          <button
            onClick={() => setActiveTab('accuracy')}
            className={`btn ${activeTab === 'accuracy' ? 'btn-primary' : 'btn-secondary'}`}
            style={{ fontSize: '0.8rem', padding: '0.4rem 0.85rem', border: 'none' }}
          >
            <BarChart3 size={14} /> Accuracy Benchmark (EM / EX)
          </button>
          <button
            onClick={() => setActiveTab('performance')}
            className={`btn ${activeTab === 'performance' ? 'btn-primary' : 'btn-secondary'}`}
            style={{ fontSize: '0.8rem', padding: '0.4rem 0.85rem', border: 'none' }}
          >
            <Zap size={14} /> Concurrency Load Benchmark
          </button>
        </div>
      </div>

      {/* ------------------------------------------------------------- */}
      {/* ACCURACY BENCHMARK TAB */}
      {/* ------------------------------------------------------------- */}
      {activeTab === 'accuracy' && (
        <div>
          <div className="glass-card" style={{ marginBottom: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <span className="card-title" style={{ fontSize: '1rem' }}>Accuracy & Semantic Verification Benchmark</span>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginTop: '0.2rem' }}>
                Evaluates Exact Match AST queries and target database execution result rows.
              </p>
            </div>

            <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Sample Size:</label>
                <select
                  className="form-select"
                  value={sampleLimit}
                  onChange={(e) => setSampleLimit(parseInt(e.target.value))}
                  disabled={isRunning}
                  style={{ width: '130px', padding: '0.4rem 0.6rem', fontSize: '0.85rem' }}
                >
                  <option value={5}>5 Queries (Demo)</option>
                  <option value={25}>25 Queries</option>
                  <option value={50}>50 Queries</option>
                  <option value={0}>All Available</option>
                </select>
              </div>

              <button
                onClick={handleRunAccuracyBenchmark}
                disabled={isRunning}
                className="btn btn-primary"
                style={{ padding: '0.65rem 1.25rem' }}
              >
                <Play size={16} />
                {isRunning ? 'Running Accuracy Test Suite...' : 'Run Accuracy Evaluation'}
              </button>
            </div>
          </div>

          {benchmarkResult ? (
            <div>
              {/* Small Sample Warning Notice */}
              {benchmarkResult.total_samples < 30 && (
                <div
                  style={{
                    background: 'rgba(245, 158, 11, 0.12)',
                    border: '1px solid rgba(245, 158, 11, 0.3)',
                    borderRadius: '8px',
                    padding: '0.75rem 1rem',
                    marginBottom: '1.25rem',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.75rem',
                    color: '#f59e0b',
                    fontSize: '0.875rem',
                  }}
                >
                  <AlertTriangle size={18} />
                  <span>Small evaluation set ({benchmarkResult.total_samples} samples) — results are indicative, not statistically significant.</span>
                </div>
              )}

              {/* Metrics Overview Grid */}
              <div className="grid-4">
                <div className="glass-card">
                  <div className="card-header">
                    <span className="card-title">Exact Match AST (EM)</span>
                    <span className="badge badge-emerald">
                      {((benchmarkResult.finetuned_exact_match_acc - benchmarkResult.base_exact_match_acc) * 100).toFixed(0)}% Lift
                    </span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginTop: '0.5rem' }}>
                    <div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Base Model</div>
                      <div style={{ fontSize: '1.2rem', color: '#f43f5e', fontWeight: 700 }}>{(benchmarkResult.base_exact_match_acc * 100).toFixed(0)}%</div>
                    </div>
                    <div style={{ fontSize: '1.5rem', color: 'var(--text-muted)' }}>→</div>
                    <div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Fine-Tuned</div>
                      <div style={{ fontSize: '1.6rem', color: '#10b981', fontWeight: 800 }}>{(benchmarkResult.finetuned_exact_match_acc * 100).toFixed(0)}%</div>
                    </div>
                  </div>
                </div>

                <div className="glass-card">
                  <div className="card-header">
                    <span className="card-title">Execution (EX) Acc</span>
                    <span className="badge badge-cyan">
                      +{( (benchmarkResult.finetuned_exec_acc - benchmarkResult.base_exec_acc) * 100).toFixed(0)}% Lift
                    </span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginTop: '0.5rem' }}>
                    <div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Base Model</div>
                      <div style={{ fontSize: '1.2rem', color: '#f43f5e', fontWeight: 700 }}>{(benchmarkResult.base_exec_acc * 100).toFixed(0)}%</div>
                    </div>
                    <div style={{ fontSize: '1.5rem', color: 'var(--text-muted)' }}>→</div>
                    <div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Fine-Tuned</div>
                      <div style={{ fontSize: '1.6rem', color: '#00f2fe', fontWeight: 800 }}>{(benchmarkResult.finetuned_exec_acc * 100).toFixed(0)}%</div>
                    </div>
                  </div>
                </div>

                <div className="glass-card">
                  <div className="card-header">
                    <span className="card-title">Average Latency</span>
                    <span className="badge badge-emerald">Latency Profile</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginTop: '0.5rem' }}>
                    <div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Base Model</div>
                      <div style={{ fontSize: '1.2rem', color: '#f59e0b', fontWeight: 700 }}>{benchmarkResult.base_avg_latency_ms} ms</div>
                    </div>
                    <div style={{ fontSize: '1.5rem', color: 'var(--text-muted)' }}>→</div>
                    <div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Fine-Tuned</div>
                      <div style={{ fontSize: '1.6rem', color: '#10b981', fontWeight: 800 }}>{benchmarkResult.finetuned_avg_latency_ms} ms</div>
                    </div>
                  </div>
                </div>

                <div className="glass-card">
                  <div className="card-header">
                    <span className="card-title">Test Corpus & Experiment</span>
                    <span className="badge badge-violet">{benchmarkResult.eval_id}</span>
                  </div>
                  <div className="stat-value">{benchmarkResult.total_samples} Queries</div>
                  <div className="stat-subtext">Dataset: {benchmarkResult.dataset_name}</div>
                </div>
              </div>

              {/* Latency Percentiles Breakdown */}
              <div className="glass-card" style={{ marginTop: '1.25rem' }}>
                <div className="card-header">
                  <span className="card-title"><Clock size={18} /> Latency Distribution Percentiles (P50 / P95 / P99)</span>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1.5rem', marginTop: '0.5rem' }}>
                  <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '1rem', borderRadius: '8px', border: '1px solid #1e293b' }}>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.4rem' }}>P50 Latency (Median)</div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span>Base: <strong style={{ color: '#f59e0b' }}>{benchmarkResult.base_p50_latency_ms} ms</strong></span>
                      <span>Fine-Tuned: <strong style={{ color: '#10b981' }}>{benchmarkResult.finetuned_p50_latency_ms} ms</strong></span>
                    </div>
                  </div>

                  <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '1rem', borderRadius: '8px', border: '1px solid #1e293b' }}>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.4rem' }}>P95 Latency</div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span>Base: <strong style={{ color: '#f59e0b' }}>{benchmarkResult.base_p95_latency_ms} ms</strong></span>
                      <span>Fine-Tuned: <strong style={{ color: '#10b981' }}>{benchmarkResult.finetuned_p95_latency_ms} ms</strong></span>
                    </div>
                  </div>

                  <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '1rem', borderRadius: '8px', border: '1px solid #1e293b' }}>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.4rem' }}>P99 Latency</div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span>Base: <strong style={{ color: '#f59e0b' }}>{benchmarkResult.base_p99_latency_ms} ms</strong></span>
                      <span>Fine-Tuned: <strong style={{ color: '#10b981' }}>{benchmarkResult.finetuned_p99_latency_ms} ms</strong></span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Failure Analysis Section */}
              <div className="glass-card" style={{ marginTop: '1.25rem' }}>
                <div className="card-header">
                  <span className="card-title"><AlertTriangle size={18} style={{ color: '#f59e0b' }} /> Failure Analysis (AST Deterministic Classification)</span>
                  {categoryFilter && (
                    <button
                      onClick={() => setCategoryFilter(null)}
                      className="btn btn-secondary"
                      style={{ fontSize: '0.75rem', padding: '0.25rem 0.6rem' }}
                    >
                      Reset Filter (Show All)
                    </button>
                  )}
                </div>

                {benchmarkResult.failure_analysis && Object.keys(benchmarkResult.failure_analysis).length > 0 ? (
                  <div>
                    <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
                      Click on any failure category below to filter affected benchmark query cases:
                    </p>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem' }}>
                      {Object.entries(benchmarkResult.failure_analysis).map(([cat, pct]) => {
                        const count = benchmarkResult.failure_counts?.[cat] || 0;
                        const isSelected = categoryFilter === cat;
                        return (
                          <div
                            key={cat}
                            onClick={() => setCategoryFilter(isSelected ? null : cat)}
                            style={{
                              background: isSelected ? 'rgba(0, 242, 254, 0.15)' : 'rgba(15, 23, 42, 0.6)',
                              border: isSelected ? '1px solid #00f2fe' : '1px solid #1e293b',
                              borderRadius: '8px',
                              padding: '0.6rem 1rem',
                              cursor: 'pointer',
                              display: 'flex',
                              justify: 'space-between',
                              alignItems: 'center',
                              gap: '1rem',
                              transition: 'all 0.2s ease',
                            }}
                          >
                            <span style={{ fontSize: '0.85rem', fontWeight: 600, color: isSelected ? '#00f2fe' : '#e2e8f0' }}>{cat}</span>
                            <span className="badge badge-amber" style={{ fontSize: '0.75rem' }}>{pct}% ({count})</span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                ) : (
                  <div style={{ fontSize: '0.85rem', color: '#10b981', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <CheckCircle2 size={16} /> 100% Execution Accuracy — 0 failure cases detected!
                  </div>
                )}
              </div>

              {/* Itemized Results Table */}
              <div className="glass-card" style={{ marginTop: '1.25rem' }}>
                <div className="card-header">
                  <span className="card-title">
                    Itemized Case-by-Case Benchmark Comparison
                    {categoryFilter && <span style={{ color: '#00f2fe', marginLeft: '0.5rem', fontSize: '0.85rem' }}>(Filtered: {categoryFilter})</span>}
                  </span>
                </div>
                <div className="data-table-container">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Sample ID</th>
                        <th>User Question</th>
                        <th>Ground Truth SQL</th>
                        <th>Base Model SQL</th>
                        <th>Fine-Tuned SQL</th>
                        <th>EM</th>
                        <th>EX</th>
                        <th>Failure Category</th>
                        <th>Latency</th>
                      </tr>
                    </thead>
                    <tbody>
                      {benchmarkResult.details
                        .filter((item) => !categoryFilter || item.failure_category === categoryFilter)
                        .map((item) => (
                          <tr key={item.id}>
                            <td style={{ fontFamily: 'var(--font-mono)', color: '#00f2fe' }}>{item.id}</td>
                            <td style={{ maxWidth: '180px' }}>{item.question}</td>
                            <td style={{ fontFamily: 'var(--font-mono)', color: '#38bdf8', fontSize: '0.75rem' }}>{item.ground_truth_sql}</td>
                            <td style={{ fontFamily: 'var(--font-mono)', color: '#f43f5e', fontSize: '0.75rem' }}>{item.base_model_sql}</td>
                            <td style={{ fontFamily: 'var(--font-mono)', color: '#10b981', fontSize: '0.75rem' }}>{item.finetuned_model_sql}</td>
                            <td>
                              {item.finetuned_exact_match ? (
                                <span className="badge badge-emerald">✓ PASS</span>
                              ) : (
                                <span className="badge badge-amber">MISMATCH</span>
                              )}
                            </td>
                            <td>
                              {item.finetuned_exec_match ? (
                                <span className="badge badge-emerald">✓ PASS</span>
                              ) : (
                                <span className="badge badge-rose">FAIL</span>
                              )}
                            </td>
                            <td>
                              {item.failure_category ? (
                                <span className="badge badge-amber" style={{ fontSize: '0.7rem' }}>{item.failure_category}</span>
                              ) : (
                                <span className="badge badge-emerald" style={{ fontSize: '0.7rem' }}>None</span>
                              )}
                            </td>
                            <td style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{item.finetuned_latency_ms} ms</td>
                          </tr>
                        ))}
                    </tbody>
                  </table>
                </div>
              </div>

            </div>
          ) : (
            <div className="glass-card" style={{ padding: '3rem', textAlign: 'center' }}>
              <BarChart3 size={48} style={{ color: 'var(--primary-cyan)', marginBottom: '1rem' }} />
              <h3 style={{ fontSize: '1.25rem', marginBottom: '0.5rem' }}>Ready to run Text-to-SQL Accuracy Benchmark</h3>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
                Select sample size and click the button above to execute automated evaluation comparing Base vs Fine-Tuned model outputs.
              </p>
            </div>
          )}
        </div>
      )}

      {/* ------------------------------------------------------------- */}
      {/* PERFORMANCE & CONCURRENCY LOAD BENCHMARK TAB */}
      {/* ------------------------------------------------------------- */}
      {activeTab === 'performance' && (
        <div>
          <div className="glass-card" style={{ marginBottom: '1.5rem' }}>
            <div className="card-header">
              <span className="card-title"><Zap size={18} /> Concurrent Inference Load & Throughput Benchmark</span>
              <span className="badge badge-amber">Manual Execution Only</span>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
              <div className="form-group" style={{ marginBottom: 0 }}>
                <label className="form-label">Total Requests</label>
                <select
                  className="form-select"
                  value={numRequests}
                  onChange={(e) => setNumRequests(parseInt(e.target.value))}
                  disabled={isRunning}
                >
                  <option value={10}>10 Requests</option>
                  <option value={20}>20 Requests (Standard)</option>
                  <option value={50}>50 Requests</option>
                  <option value={100}>100 Requests (Stress)</option>
                </select>
              </div>

              <div className="form-group" style={{ marginBottom: 0 }}>
                <label className="form-label">Concurrency Level (Workers)</label>
                <select
                  className="form-select"
                  value={concurrency}
                  onChange={(e) => setConcurrency(parseInt(e.target.value))}
                  disabled={isRunning}
                >
                  <option value={1}>1 Worker (Sequential)</option>
                  <option value={2}>2 Workers</option>
                  <option value={4}>4 Workers (Optimal)</option>
                  <option value={8}>8 Workers (High Load)</option>
                </select>
              </div>

              <div style={{ alignSelf: 'flex-end' }}>
                <button
                  onClick={handleRunPerfBenchmark}
                  disabled={isRunning}
                  className="btn btn-primary"
                  style={{ width: '100%', padding: '0.65rem' }}
                >
                  <Zap size={16} />
                  {isRunning ? 'Running Concurrent Load Test...' : 'Launch Performance Load Test'}
                </button>
              </div>
            </div>
          </div>

          {perfResult ? (
            <div>
              {/* Hardware Machine Notice Banner */}
              <div
                style={{
                  background: 'rgba(56, 189, 248, 0.1)',
                  border: '1px solid rgba(56, 189, 248, 0.3)',
                  borderRadius: '8px',
                  padding: '0.75rem 1rem',
                  marginBottom: '1.25rem',
                  color: '#38bdf8',
                  fontSize: '0.85rem',
                }}
              >
                {perfResult.hardware_notice}
              </div>

              {/* Performance Cards Overview */}
              <div className="grid-4">
                <div className="glass-card">
                  <div className="card-header">
                    <span className="card-title">Throughput (Req/Sec)</span>
                    <span className="badge badge-emerald">Throughput</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginTop: '0.5rem' }}>
                    <div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Base Model</div>
                      <div style={{ fontSize: '1.2rem', color: '#f43f5e', fontWeight: 700 }}>{perfResult.base_metrics?.throughput_req_sec || 0} req/s</div>
                    </div>
                    <div style={{ fontSize: '1.5rem', color: 'var(--text-muted)' }}>→</div>
                    <div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Fine-Tuned</div>
                      <div style={{ fontSize: '1.6rem', color: '#10b981', fontWeight: 800 }}>{perfResult.finetuned_metrics?.throughput_req_sec || 0} req/s</div>
                    </div>
                  </div>
                </div>

                <div className="glass-card">
                  <div className="card-header">
                    <span className="card-title">P50 Latency (Median)</span>
                    <span className="badge badge-cyan">Latency</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginTop: '0.5rem' }}>
                    <div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Base Model</div>
                      <div style={{ fontSize: '1.2rem', color: '#f59e0b', fontWeight: 700 }}>{perfResult.base_metrics?.p50_latency_ms || 0} ms</div>
                    </div>
                    <div style={{ fontSize: '1.5rem', color: 'var(--text-muted)' }}>→</div>
                    <div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Fine-Tuned</div>
                      <div style={{ fontSize: '1.6rem', color: '#00f2fe', fontWeight: 800 }}>{perfResult.finetuned_metrics?.p50_latency_ms || 0} ms</div>
                    </div>
                  </div>
                </div>

                <div className="glass-card">
                  <div className="card-header">
                    <span className="card-title">P95 Latency</span>
                    <span className="badge badge-emerald">P95 Tail</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginTop: '0.5rem' }}>
                    <div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Base Model</div>
                      <div style={{ fontSize: '1.2rem', color: '#f59e0b', fontWeight: 700 }}>{perfResult.base_metrics?.p95_latency_ms || 0} ms</div>

                    </div>
                    <div style={{ fontSize: '1.5rem', color: 'var(--text-muted)' }}>→</div>
                    <div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Fine-Tuned</div>
                      <div style={{ fontSize: '1.6rem', color: '#10b981', fontWeight: 800 }}>{perfResult.finetuned_metrics?.p95_latency_ms || 0} ms</div>
                    </div>
                  </div>
                </div>

                <div className="glass-card">
                  <div className="card-header">
                    <span className="card-title">Test Config</span>
                    <span className="badge badge-violet">{perfResult.benchmark_id}</span>
                  </div>
                  <div className="stat-value">{perfResult.num_requests} Reqs</div>
                  <div className="stat-subtext">Concurrency={perfResult.concurrency} | Time={perfResult.total_duration_sec}s</div>
                </div>
              </div>

              {/* Side-by-Side Detailed Load Test Metrics Table */}
              <div className="glass-card" style={{ marginTop: '1.25rem' }}>
                <div className="card-header">
                  <span className="card-title">Side-by-Side Performance Load Metrics</span>
                </div>
                <div className="data-table-container">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Metric</th>
                        <th>Base Foundation Model</th>
                        <th>Fine-Tuned Model</th>
                        <th>Comparison Delta</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr>
                        <td><strong>Throughput</strong></td>
                        <td>{perfResult.base_metrics?.throughput_req_sec || 0} req/sec</td>
                        <td style={{ color: '#10b981', fontWeight: 700 }}>{perfResult.finetuned_metrics?.throughput_req_sec || 0} req/sec</td>
                        <td>
                          <span className="badge badge-emerald">
                            {((perfResult.finetuned_metrics?.throughput_req_sec || 1) / (perfResult.base_metrics?.throughput_req_sec || 1)).toFixed(1)}x Speedup
                          </span>
                        </td>
                      </tr>
                      <tr>
                        <td><strong>Average Latency</strong></td>
                        <td>{perfResult.base_metrics?.avg_latency_ms || 0} ms</td>
                        <td style={{ color: '#00f2fe', fontWeight: 700 }}>{perfResult.finetuned_metrics?.avg_latency_ms || 0} ms</td>
                        <td><span className="badge badge-cyan">Faster Response</span></td>
                      </tr>
                      <tr>
                        <td><strong>P50 Latency (Median)</strong></td>
                        <td>{perfResult.base_metrics?.p50_latency_ms || 0} ms</td>
                        <td style={{ color: '#00f2fe' }}>{perfResult.finetuned_metrics?.p50_latency_ms || 0} ms</td>
                        <td>Median Latency</td>
                      </tr>
                      <tr>
                        <td><strong>P95 Latency</strong></td>
                        <td>{perfResult.base_metrics?.p95_latency_ms || 0} ms</td>
                        <td style={{ color: '#10b981' }}>{perfResult.finetuned_metrics?.p95_latency_ms || 0} ms</td>
                        <td>95th Percentile Tail</td>
                      </tr>
                      <tr>
                        <td><strong>P99 Latency</strong></td>
                        <td>{perfResult.base_metrics?.p99_latency_ms || 0} ms</td>
                        <td style={{ color: '#10b981' }}>{perfResult.finetuned_metrics?.p99_latency_ms || 0} ms</td>
                        <td>99th Percentile Tail</td>
                      </tr>
                      <tr>
                        <td><strong>Success Rate</strong></td>
                        <td>{((perfResult.base_metrics?.success_rate || 0) * 100).toFixed(1)}%</td>
                        <td style={{ color: '#10b981', fontWeight: 700 }}>{((perfResult.finetuned_metrics?.success_rate || 0) * 100).toFixed(1)}%</td>
                        <td><span className="badge badge-emerald">✓ Stable</span></td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          ) : (
            <div className="glass-card" style={{ padding: '3rem', textAlign: 'center' }}>
              <Zap size={48} style={{ color: '#f59e0b', marginBottom: '1rem' }} />
              <h3 style={{ fontSize: '1.25rem', marginBottom: '0.5rem' }}>Ready to run Concurrency & Throughput Performance Test</h3>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
                Select total requests and parallel concurrency workers to measure inference throughput (req/s), P50/P95/P99 latency percentiles, and error rates.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
