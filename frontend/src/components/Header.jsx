import React from 'react';
import { Cpu, Zap, Shield, HardDrive, RefreshCw } from 'lucide-react';

export default function Header({ systemMetrics, activeModel, lastUpdated, onRefresh }) {
  return (
    <header className="top-header">
      <div className="header-title-container">
        <h2 className="header-page-title">ForgeLLM Control Plane</h2>
        <span className="badge badge-cyan">Production Node #1</span>
      </div>

      <div className="header-stats-group">
        <div className="status-pill">
          <div className="pulse-dot"></div>
          <span>Live Poll: <strong style={{ color: '#10b981' }}>{lastUpdated || 'Connecting...'}</strong></span>
        </div>

        <div className="status-pill">
          <Cpu size={14} className="text-cyan" />
          <span>CPU: <strong>{systemMetrics?.cpu_usage_percent || 0}%</strong></span>
        </div>

        <div className="status-pill">
          <HardDrive size={14} className="text-violet" />
          <span>Compute: <strong>{systemMetrics?.gpu_name || (systemMetrics?.gpu_available ? 'GPU Accelerator' : 'CPU Execution Engine')}</strong></span>
        </div>


        <div className="status-pill">
          <Zap size={14} className="text-amber" />
          <span>Active Served Model: <strong style={{ color: '#00f2fe' }}>{activeModel?.name || 'Loading...'}</strong></span>
        </div>

        <button onClick={onRefresh} className="btn btn-secondary" style={{ padding: '0.4rem 0.6rem' }} title="Refresh Telemetry">
          <RefreshCw size={14} />
        </button>
      </div>
    </header>
  );
}

