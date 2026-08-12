import React, { useState, useEffect } from 'react';
import { Flame, Play, Square, Settings, LineChart, Terminal as TerminalIcon, CheckCircle2 } from 'lucide-react';
import { LineChart as RechartsLine, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { triggerFineTuneJob, apiClient, API_BASE_URL } from '../services/api';

export default function FineTuneTab({ onJobStarted }) {
  const [jobName, setJobName] = useState('qlora-spider-sql-run-1');
  const [baseModel, setBaseModel] = useState('google/gemma-2b-it');
  const [datasetName, setDatasetName] = useState('spider_sample.json');
  
  // QLoRA Hyperparameters
  const [rank, setRank] = useState(16);
  const [alpha, setAlpha] = useState(32);
  const [lr, setLr] = useState(0.0002);
  const [epochs, setEpochs] = useState(3);
  const [batchSize, setBatchSize] = useState(4);
  const [quantBits, setQuantBits] = useState(4);

  const [activeJob, setActiveJob] = useState(null);
  const [telemetryHistory, setTelemetryHistory] = useState([]);
  const [logs, setLogs] = useState([]);
  const [isTraining, setIsTraining] = useState(false);

  // Subscribe to SSE telemetry stream
  useEffect(() => {
    const eventSource = new EventSource(`${API_BASE_URL}/finetune/stream`);


    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'telemetry') {
          setIsTraining(true);
          setTelemetryHistory((prev) => [
            ...prev,
            {
              step: data.step,
              epoch: data.epoch,
              train_loss: data.train_loss,
              val_loss: data.val_loss,
              perplexity: data.perplexity,
            },
          ]);
          setActiveJob((prev) => ({
            ...prev,
            current_step: data.step,
            total_steps: data.total_steps,
            train_loss: data.train_loss,
            val_loss: data.val_loss,
            perplexity: data.perplexity,
            tokens_per_second: data.tokens_per_second,
            eta_seconds: data.eta_seconds,
          }));
        } else if (data.type === 'log') {
          setLogs((prev) => [...prev, data.text]);
        } else if (data.type === 'job_complete') {
          setIsTraining(false);
          setLogs((prev) => [...prev, '🎉 QLoRA Fine-Tuning Job Completed Successfully! Model checkpoint saved and registered.']);
          if (onJobStarted) onJobStarted();
        }
      } catch (err) {
        console.error('SSE Error:', err);
      }
    };

    return () => {
      eventSource.close();
    };
  }, [onJobStarted]);

  const handleStartTraining = async () => {
    setTelemetryHistory([]);
    setLogs(['🚀 Initializing QLoRA Fine-Tuning Job...']);
    setIsTraining(true);

    const req = {
      job_name: jobName,
      base_model: baseModel,
      dataset_name: datasetName,
      hyperparameters: {
        r: parseInt(rank),
        lora_alpha: parseInt(alpha),
        lora_dropout: 0.05,
        target_modules: ['q_proj', 'v_proj', 'k_proj', 'o_proj'],
        learning_rate: parseFloat(lr),
        batch_size: parseInt(batchSize),
        gradient_accumulation_steps: 4,
        num_epochs: parseInt(epochs),
        quantization_bits: parseInt(quantBits),
      },
    };

    try {
      const res = await triggerFineTuneJob(req);
      setActiveJob(res);
    } catch (err) {
      alert('Failed to launch training job: ' + err.message);
      setIsTraining(false);
    }
  };

  return (
    <div className="page-view">
      <div style={{ marginBottom: '1.5rem' }}>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 800 }}>QLoRA Fine-Tuning Studio</h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
          Parameter-Efficient Fine-Tuning (PEFT) engine utilizing 4-bit NormalFloat (NF4) quantization and low-rank LoRA adapters.
        </p>
      </div>

      <div className="grid-2">
        {/* Hyperparameter Controls */}
        <div className="glass-card">
          <div className="card-header">
            <span className="card-title"><Settings size={18} /> Training Job Configuration</span>
            <span className="badge badge-violet">QLoRA Standard</span>
          </div>

          <div className="form-group">
            <label className="form-label">Job Name</label>
            <input type="text" className="form-input" value={jobName} onChange={(e) => setJobName(e.target.value)} />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div className="form-group">
              <label className="form-label">Base Model</label>
              <select className="form-select" value={baseModel} onChange={(e) => setBaseModel(e.target.value)}>
                <option value="google/gemma-2b-it">Google Gemma-2B-Instruct</option>
                <option value="Qwen/Qwen2.5-Coder-1.5B-Instruct">Qwen-2.5-Coder-1.5B-Instruct</option>
                <option value="mistralai/Mistral-7B-Instruct-v0.2">Mistral-7B-Instruct-v0.2</option>
                <option value="TinyLlama/TinyLlama-1.1B-Chat-v1.0">TinyLlama-1.1B-Chat</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Dataset</label>
              <select className="form-select" value={datasetName} onChange={(e) => setDatasetName(e.target.value)}>
                <option value="spider_sample.json">Spider Text-to-SQL Benchmark</option>
                <option value="ecommerce_sample.json">E-Commerce Schema SQL Pairs</option>
                <option value="hr_analytics.json">HR Analytics SQL Pairs</option>
              </select>
            </div>
          </div>

          {/* Hyperparameter Sliders */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginTop: '0.5rem' }}>
            <div className="form-group">
              <label className="form-label">LoRA Rank (r): <strong>{rank}</strong></label>
              <input type="range" className="range-slider" min="4" max="64" step="4" value={rank} onChange={(e) => setRank(e.target.value)} />
            </div>

            <div className="form-group">
              <label className="form-label">LoRA Alpha (α): <strong>{alpha}</strong></label>
              <input type="range" className="range-slider" min="8" max="128" step="8" value={alpha} onChange={(e) => setAlpha(e.target.value)} />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div className="form-group">
              <label className="form-label">Learning Rate: <strong>{lr}</strong></label>
              <input type="number" step="0.00005" className="form-input" value={lr} onChange={(e) => setLr(e.target.value)} />
            </div>

            <div className="form-group">
              <label className="form-label">Training Epochs: <strong>{epochs}</strong></label>
              <input type="range" className="range-slider" min="1" max="10" value={epochs} onChange={(e) => setEpochs(e.target.value)} />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div className="form-group">
              <label className="form-label">Batch Size</label>
              <select className="form-select" value={batchSize} onChange={(e) => setBatchSize(e.target.value)}>
                <option value="2">2 (Low Memory)</option>
                <option value="4">4 (Optimal)</option>
                <option value="8">8 (High Throughput)</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Quantization</label>
              <select className="form-select" value={quantBits} onChange={(e) => setQuantBits(e.target.value)}>
                <option value="4">4-bit QLoRA (NF4)</option>
                <option value="8">8-bit LoRA (Int8)</option>
                <option value="16">16-bit Full LoRA (FP16)</option>
              </select>
            </div>
          </div>

          <div style={{ marginTop: '1.25rem' }}>
            <button
              onClick={handleStartTraining}
              disabled={isTraining}
              className="btn btn-primary"
              style={{ width: '100%', padding: '0.8rem' }}
            >
              {isTraining ? <Square size={16} /> : <Play size={16} />}
              {isTraining ? 'Training In Progress...' : 'Launch QLoRA Training Run'}
            </button>
          </div>
        </div>

        {/* Live Loss Curves Graph */}
        <div className="glass-card">
          <div className="card-header">
            <span className="card-title"><LineChart size={18} /> Live Loss & Perplexity Convergence</span>
            <div style={{ display: 'flex', gap: '0.75rem', fontSize: '0.75rem' }}>
              <span style={{ color: '#00f2fe' }}>● Train Loss ({activeJob?.train_loss || '0.00'})</span>
              <span style={{ color: '#f59e0b' }}>● Val Loss ({activeJob?.val_loss || '0.00'})</span>
            </div>
          </div>

          <div style={{ height: '320px', width: '100%' }}>
            {telemetryHistory.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <RechartsLine data={telemetryHistory}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="step" stroke="#64748b" label={{ value: 'Steps', position: 'insideBottom', offset: -5 }} />
                  <YAxis stroke="#64748b" />
                  <Tooltip contentStyle={{ background: '#0f172a', borderColor: '#334155' }} />
                  <Line type="monotone" dataKey="train_loss" stroke="#00f2fe" strokeWidth={2.5} dot={false} name="Train Loss" />
                  <Line type="monotone" dataKey="val_loss" stroke="#f59e0b" strokeWidth={2} dot={false} name="Val Loss" />
                </RechartsLine>
              </ResponsiveContainer>
            ) : (
              <div style={{ display: 'flex', height: '100%', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
                Click "Launch QLoRA Training Run" to begin streaming live loss convergence telemetry.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Terminal Output Log Window */}
      <div className="glass-card">
        <div className="card-header">
          <span className="card-title"><TerminalIcon size={18} /> Live SSE Training Logs & Output Stream</span>
          <span className="badge badge-emerald">Streaming Active</span>
        </div>
        <div className="terminal-window">
          {logs.map((log, idx) => (
            <div key={idx}>{log}</div>
          ))}
        </div>
      </div>
    </div>
  );
}
