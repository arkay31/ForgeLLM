import React from 'react';
import { LayoutDashboard, Flame, Terminal, Layers, Database, BarChart3, ShieldCheck, GitBranch } from 'lucide-react';

export default function Sidebar({ activeTab, setActiveTab, activeModel }) {
  const menuItems = [
    { id: 'overview', label: 'System Telemetry', icon: LayoutDashboard },
    { id: 'finetune', label: 'QLoRA Fine-Tuning', icon: Flame },
    { id: 'playground', label: 'Text-to-SQL Studio', icon: Terminal },
    { id: 'registry', label: 'Model Registry', icon: Layers },
    { id: 'experiments', label: 'MLOps Experiments', icon: GitBranch },
    { id: 'datasets', label: 'Dataset Manager', icon: Database },
    { id: 'eval', label: 'Evaluation Suite', icon: BarChart3 },
    { id: 'security', label: 'Security & API Keys', icon: ShieldCheck },
  ];


  return (
    <aside className="sidebar">
      <div className="brand-logo">
        <div className="brand-logo-icon">
          <Flame size={22} />
        </div>
        <div>
          <div className="brand-title">ForgeLLM</div>
          <span className="brand-tag">v1.0 Production</span>
        </div>
      </div>

      <nav className="nav-menu">
        {menuItems.map((item) => {
          const Icon = item.icon;
          return (
            <div
              key={item.id}
              className={`nav-item ${activeTab === item.id ? 'active' : ''}`}
              onClick={() => setActiveTab(item.id)}
            >
              <Icon size={18} />
              <span>{item.label}</span>
            </div>
          );
        })}
      </nav>

      <div className="sidebar-footer">
        <div className="active-model-badge">
          <div>
            <div className="model-badge-title">ACTIVE SERVING MODEL</div>
            <div className="model-badge-name">{activeModel?.name || 'Base Qwen-1.5B'}</div>
          </div>
          <span className="badge badge-emerald">Live</span>
        </div>
      </div>
    </aside>
  );
}
