import React, { useState, useEffect, useCallback } from 'react';
import './App.css';

import Sidebar from './components/Sidebar';
import Header from './components/Header';
import OverviewTab from './components/OverviewTab';
import FineTuneTab from './components/FineTuneTab';
import PlaygroundTab from './components/PlaygroundTab';
import RegistryTab from './components/RegistryTab';
import DatasetsTab from './components/DatasetsTab';
import EvalTab from './components/EvalTab';
import SecurityTab from './components/SecurityTab';
import ExperimentsTab from './components/ExperimentsTab';



import {
  fetchSystemMetrics,
  fetchSystemHistory,
  fetchLatencyHistory,
  fetchModels,
  fetchActiveModel,
  fetchTrainingJobs,
} from './services/api';

export default function App() {
  const [activeTab, setActiveTab] = useState('overview');
  const [systemMetrics, setSystemMetrics] = useState(null);
  const [telemetryHistory, setTelemetryHistory] = useState([]);
  const [latencyHistory, setLatencyHistory] = useState([]);
  const [lastUpdated, setLastUpdated] = useState('');
  const [models, setModels] = useState([]);
  const [activeModel, setActiveModel] = useState(null);
  const [jobs, setJobs] = useState([]);

  // Fast live polling for real-time telemetry (CPU/Memory/GPU/Latency)
  const pollTelemetry = useCallback(async () => {
    try {
      const [mRes, hRes, lRes] = await Promise.allSettled([
        fetchSystemMetrics(),
        fetchSystemHistory(),
        fetchLatencyHistory(),
      ]);

      if (mRes.status === 'fulfilled' && mRes.value) {
        const metrics = mRes.value;
        setSystemMetrics(metrics);
        const timestamp = metrics.timestamp || new Date().toLocaleTimeString();
        setLastUpdated(timestamp);

        // If backend returned history, map it directly; otherwise push to rolling history
        if (hRes.status === 'fulfilled' && Array.isArray(hRes.value) && hRes.value.length > 0) {
          const formattedHistory = hRes.value.map((pt) => ({
            time: pt.time,
            cpu: pt.cpu_usage_percent || 0,
            memory: pt.memory_usage_percent || 0,
            gpu_mem: pt.gpu_memory_used_gb || 0,
          }));
          setTelemetryHistory(formattedHistory);
        } else {
          setTelemetryHistory((prev) => {
            const next = [
              ...prev,
              {
                time: timestamp,
                cpu: metrics.cpu_usage_percent || 0,
                memory: metrics.memory_usage_percent || 0,
                gpu_mem: metrics.gpu_memory_used_gb || 0,
              },
            ];
            return next.slice(-30);
          });
        }
      }

      if (lRes.status === 'fulfilled' && Array.isArray(lRes.value)) {
        setLatencyHistory(lRes.value);
      }
    } catch (err) {
      console.error('Error polling live telemetry:', err);
    }
  }, []);

  const loadData = async () => {
    await pollTelemetry();
    try {
      const [modelsRes, activeRes, jobsRes] = await Promise.allSettled([
        fetchModels(),
        fetchActiveModel(),
        fetchTrainingJobs(),
      ]);

      if (modelsRes.status === 'fulfilled') setModels(modelsRes.value);
      if (activeRes.status === 'fulfilled') setActiveModel(activeRes.value);
      if (jobsRes.status === 'fulfilled') setJobs(jobsRes.value);
    } catch (err) {
      console.error('Error fetching models/jobs data:', err);
    }
  };

  useEffect(() => {
    loadData();

    // Refresh CPU/Memory/GPU telemetry every 2 seconds (2000ms)
    const interval = setInterval(pollTelemetry, 2000);
    return () => clearInterval(interval);
  }, [pollTelemetry]);

  return (
    <div className="app-container">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} activeModel={activeModel} />
      
      <main className="main-content">
        <Header systemMetrics={systemMetrics} activeModel={activeModel} lastUpdated={lastUpdated} onRefresh={loadData} />
        
        {activeTab === 'overview' && (
          <OverviewTab
            systemMetrics={systemMetrics}
            telemetryHistory={telemetryHistory}
            latencyHistory={latencyHistory}
            activeModel={activeModel}
            models={models}
            jobs={jobs}
          />
        )}
        {activeTab === 'finetune' && (
          <FineTuneTab onJobStarted={loadData} />
        )}
        {activeTab === 'playground' && (
          <PlaygroundTab activeModel={activeModel} models={models} />
        )}
        {activeTab === 'registry' && (
          <RegistryTab models={models} activeModel={activeModel} onModelsUpdated={loadData} />
        )}
        {activeTab === 'experiments' && (
          <ExperimentsTab onNavigateToRegistry={() => setActiveTab('registry')} />
        )}
        {activeTab === 'datasets' && (
          <DatasetsTab />
        )}
        {activeTab === 'eval' && (
          <EvalTab activeModel={activeModel} models={models} />
        )}
        {activeTab === 'security' && (
          <SecurityTab />
        )}
      </main>
    </div>
  );
}

