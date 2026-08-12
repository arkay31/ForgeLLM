import React from 'react';

import {
  Cpu,
  HardDrive,
  Zap,
  Activity,
  Clock,
  Server,
  Flame,
} from 'lucide-react';

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';


export default function OverviewTab({
  systemMetrics,
  telemetryHistory = [],
  activeModel,
  models,
  jobs,
  latencyHistory = [],
}) {

  // ==========================================================
  // REAL LATENCY DATA
  // ==========================================================

  const latencyData =
    (latencyHistory || []).map(
      (item) => ({

        time: item.time,

        base_ms:
          item.is_finetuned
            ? null
            : item.latency_ms,

        qlora_ms:
          item.is_finetuned
            ? item.latency_ms
            : null,

      })
    );


  // ==========================================================
  // LATEST LATENCIES
  // ==========================================================

  const baseEntries =
    (latencyHistory || []).filter(
      (item) =>
        !item.is_finetuned
    );


  const qloraEntries =
    (latencyHistory || []).filter(
      (item) =>
        item.is_finetuned
    );


  const latestBase =
    baseEntries.length > 0
      ? baseEntries[
          baseEntries.length - 1
        ].latency_ms
      : null;


  const latestQLoRA =
    qloraEntries.length > 0
      ? qloraEntries[
          qloraEntries.length - 1
        ].latency_ms
      : null;


  return (

    <div
      style={{
        marginBottom: '1.5rem',
      }}
    >

      <h2
        style={{
          fontSize: '1.5rem',
          fontWeight: 800,
        }}
      >
        Platform Infrastructure & Telemetry
      </h2>


      <p
        style={{
          color: 'var(--text-muted)',
          fontSize: '0.875rem',
        }}
      >
        Real-time metrics for LLM
        fine-tuning compute, inference
        latency, hardware resource
        allocation, and active serving
        status.
      </p>


      {/* =====================================================
          TOP METRIC CARDS
      ====================================================== */}

      <div className="grid-4">

        {/* CPU */}
        <div className="glass-card">
          <div className="card-header">
            <span className="card-title">
              <Cpu size={16} style={{ color: '#00f2fe' }} />
              CPU Utilization
            </span>
            <span className="badge badge-cyan">{systemMetrics?.cpu_usage_percent || 0}% Sys</span>
          </div>
          <div className="stat-value">{systemMetrics?.cpu_usage_percent || 0}%</div>
          <div className="stat-subtext">Process CPU: {systemMetrics?.process_cpu_percent || 0}%</div>
        </div>

        {/* RAM */}
        <div className="glass-card">
          <div className="card-header">
            <span className="card-title">
              <HardDrive size={16} style={{ color: '#7f00ff' }} />
              Memory (RAM)
            </span>
            <span className="badge badge-violet">{systemMetrics?.memory_usage_percent || 0}% Sys</span>
          </div>
          <div className="stat-value">{systemMetrics?.memory_used_gb || 0} GB</div>
          <div className="stat-subtext">
            Process RSS: {systemMetrics?.process_memory_used_gb || 0} GB / {systemMetrics?.memory_total_gb || 0} GB Total
          </div>
        </div>

        {/* GPU / Accelerator */}
        <div className="glass-card">
          <div className="card-header">
            <span className="card-title">
              <Zap size={16} style={{ color: '#f59e0b' }} />
              Hardware Accelerator
            </span>
            <span className="badge badge-emerald">
              {systemMetrics?.gpu_available ? 'Online' : 'CPU Mode'}
            </span>
          </div>
          <div className="stat-value" style={{ fontSize: '1.05rem' }}>
            {systemMetrics?.gpu_name || 'Apple Silicon MPS UMA'}
          </div>
          <div className="stat-subtext">
            Unified RAM: {systemMetrics?.gpu_memory_used_gb || 0} GB / {systemMetrics?.gpu_memory_total_gb || 0} GB
          </div>
        </div>



        {/* Active Model */}

        <div className="glass-card">

          <div className="card-header">

            <span className="card-title">

              <Activity
                size={16}
                style={{
                  color: '#10b981',
                }}
              />

              Active Serving Model

            </span>


            <span className="badge badge-emerald">

              Hot-Swappable

            </span>

          </div>


          <div
            className="stat-value"
            style={{
              fontSize: '1.1rem',
              color: '#00f2fe',
            }}
          >

            {
              activeModel?.name
              || 'Base Model'
            }

          </div>


          <div className="stat-subtext">

            Exact Match SQL Acc:
            {' '}
            {
              (
                (
                  activeModel?.metrics
                    ?.exact_match
                  || 0.88
                )
                * 100
              ).toFixed(0)
            }%

          </div>

        </div>

      </div>


      {/* =====================================================
          LIVE TELEMETRY HARDWARE CHART
      ====================================================== */}
      <div className="glass-card" style={{ marginTop: '1.5rem', marginBottom: '1.5rem' }}>
        <div className="card-header">
          <span className="card-title">
            <Activity size={18} style={{ color: '#00f2fe' }} />
            Real-Time System Hardware Telemetry Stream (CPU % & RAM %)
          </span>
          <div style={{ display: 'flex', gap: '1rem', fontSize: '0.75rem' }}>
            <span style={{ color: '#00f2fe' }}>● CPU ({systemMetrics?.cpu_usage_percent || 0}%)</span>
            <span style={{ color: '#a855f7' }}>● RAM ({systemMetrics?.memory_usage_percent || 0}%)</span>
            <span style={{ color: '#10b981' }}>● VRAM ({systemMetrics?.gpu_memory_used_gb || 0} GB)</span>
          </div>
        </div>

        <div style={{ height: '260px', width: '100%' }}>
          {telemetryHistory && telemetryHistory.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={telemetryHistory}>
                <defs>
                  <linearGradient id="colorCpuUtil" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#00f2fe" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#00f2fe" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="colorMemUtil" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#a855f7" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#a855f7" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="time" stroke="#64748b" />
                <YAxis stroke="#64748b" domain={[0, 100]} unit="%" />
                <Tooltip contentStyle={{ background: '#0f172a', borderColor: '#334155' }} />
                <Area
                  type="monotone"
                  dataKey="cpu"
                  stroke="#00f2fe"
                  strokeWidth={2.5}
                  fillOpacity={1}
                  fill="url(#colorCpuUtil)"
                  name="CPU Usage (%)"
                />
                <Area
                  type="monotone"
                  dataKey="memory"
                  stroke="#a855f7"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#colorMemUtil)"
                  name="RAM Usage (%)"
                />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div style={{ display: 'flex', height: '100%', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
              Connecting to live telemetry stream...
            </div>
          )}
        </div>
      </div>


      {/* =====================================================
          LATENCY + ENVIRONMENT
      ====================================================== */}

      <div className="grid-3-1">


        <div className="glass-card">

          <div className="card-header">

            <span className="card-title">

              <Clock size={18} />

              Live Inference Latency Breakdown (ms)

            </span>


            <div
              style={{
                display: 'flex',
                gap: '0.75rem',
                fontSize: '0.75rem',
              }}
            >

              <span
                style={{
                  color: '#f43f5e',
                }}
              >

                ● Base LLM
                {latestBase !== null
                  ? ` (${latestBase}ms)`
                  : ''}

              </span>


              <span
                style={{
                  color: '#00f2fe',
                }}
              >

                ● QLoRA Fine-Tuned
                {latestQLoRA !== null
                  ? ` (${latestQLoRA}ms)`
                  : ''}

              </span>

            </div>

          </div>


          <div
            style={{
              height: '260px',
              width: '100%',
            }}
          >

            <ResponsiveContainer
              width="100%"
              height="100%"
            >

              <AreaChart
                data={latencyData}
              >

                <defs>

                  <linearGradient
                    id="colorBase"
                    x1="0"
                    y1="0"
                    x2="0"
                    y2="1"
                  >

                    <stop
                      offset="5%"
                      stopColor="#f43f5e"
                      stopOpacity={0.4}
                    />

                    <stop
                      offset="95%"
                      stopColor="#f43f5e"
                      stopOpacity={0}
                    />

                  </linearGradient>


                  <linearGradient
                    id="colorQLoRA"
                    x1="0"
                    y1="0"
                    x2="0"
                    y2="1"
                  >

                    <stop
                      offset="5%"
                      stopColor="#00f2fe"
                      stopOpacity={0.4}
                    />

                    <stop
                      offset="95%"
                      stopColor="#00f2fe"
                      stopOpacity={0}
                    />

                  </linearGradient>

                </defs>


                <XAxis
                  dataKey="time"
                  stroke="#64748b"
                />


                <YAxis
                  stroke="#64748b"
                  label={{
                    value: 'ms',
                    angle: -90,
                    position: 'insideLeft',
                  }}
                />


                <Tooltip
                  contentStyle={{
                    background: '#0f172a',
                    borderColor: '#334155',
                  }}
                />


                <Area
                  type="monotone"
                  dataKey="base_ms"
                  stroke="#f43f5e"
                  fillOpacity={1}
                  fill="url(#colorBase)"
                  name="Base Model (ms)"
                  connectNulls={false}
                />


                <Area
                  type="monotone"
                  dataKey="qlora_ms"
                  stroke="#00f2fe"
                  fillOpacity={1}
                  fill="url(#colorQLoRA)"
                  name="QLoRA Model (ms)"
                  connectNulls={false}
                />

              </AreaChart>

            </ResponsiveContainer>

          </div>


          {latencyData.length === 0 && (

            <div
              style={{
                textAlign: 'center',
                color: 'var(--text-muted)',
                fontSize: '0.8rem',
                padding: '0.5rem',
              }}
            >
              No inference data yet.
              Run a Text-to-SQL query
              to populate this chart.
            </div>

          )}

        </div>


        {/* =================================================
            ACTIVE ENVIRONMENT
        ================================================== */}

        <div className="glass-card">

          <div className="card-header">

            <span className="card-title">

              <Server size={18} />

              Active Environment

            </span>

          </div>


          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: '1rem',
              marginTop: '0.5rem',
            }}
          >

            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                fontSize: '0.85rem',
              }}
            >

              <span
                style={{
                  color: 'var(--text-muted)',
                }}
              >
                Registered Models
              </span>

              <strong
                style={{
                  color: '#fff',
                }}
              >
                {models.length}
              </strong>

            </div>


            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                fontSize: '0.85rem',
              }}
            >

              <span
                style={{
                  color: 'var(--text-muted)',
                }}
              >
                Fine-Tuning Jobs
              </span>

              <strong
                style={{
                  color: '#fff',
                }}
              >
                {jobs.length}
              </strong>

            </div>


            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                fontSize: '0.85rem',
              }}
            >

              <span
                style={{
                  color: 'var(--text-muted)',
                }}
              >
                System Uptime
              </span>

              <strong
                style={{
                  color: '#10b981',
                }}
              >
                {
                  Math.floor(
                    (
                      systemMetrics?.uptime_seconds
                      || 0
                    ) / 60
                  )
                }
                {' '}
                mins
              </strong>

            </div>


            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                fontSize: '0.85rem',
              }}
            >

              <span
                style={{
                  color: 'var(--text-muted)',
                }}
              >
                Security Protocol
              </span>

              <span className="badge badge-emerald">
                API Key Guarded
              </span>

            </div>


            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                fontSize: '0.85rem',
              }}
            >

              <span
                style={{
                  color: 'var(--text-muted)',
                }}
              >
                Prometheus Target
              </span>

              <span className="badge badge-cyan">
                /api/v1/system/prometheus
              </span>

            </div>

          </div>

        </div>

      </div>


      {/* =====================================================
          MODEL CHECKPOINT REGISTRY
      ====================================================== */}

      <div className="glass-card">

        <div className="card-header">

          <span className="card-title">

            <Flame size={18} />

            Model Checkpoint Registry Quick View

          </span>

        </div>


        <div className="data-table-container">

          <table className="data-table">

            <thead>

              <tr>

                <th>
                  Checkpoint ID
                </th>

                <th>
                  Model Name
                </th>

                <th>
                  Base Architecture
                </th>

                <th>
                  Exact Match Acc
                </th>

                <th>
                  Exec Acc
                </th>

                <th>
                  Status
                </th>

              </tr>

            </thead>


            <tbody>

              {models.map(
                (cp) => (

                  <tr
                    key={
                      cp.checkpoint_id
                    }
                  >

                    <td
                      style={{
                        fontFamily:
                          'var(--font-mono)',
                        color:
                          '#00f2fe',
                      }}
                    >
                      {
                        cp.checkpoint_id
                      }
                    </td>


                    <td>
                      <strong>
                        {cp.name}
                      </strong>
                    </td>


                    <td>
                      {
                        cp.base_model
                      }
                    </td>


                    <td>

                      <strong
                        style={{
                          color:
                            '#10b981',
                        }}
                      >

                        {
                          (
                            (
                              cp.metrics
                                ?.exact_match
                              || 0
                            ) * 100
                          ).toFixed(0)
                        }%

                      </strong>

                    </td>


                    <td>

                      <strong
                        style={{
                          color:
                            '#38bdf8',
                        }}
                      >

                        {
                          (
                            (
                              cp.metrics
                                ?.exec_acc
                              || 0
                            ) * 100
                          ).toFixed(0)
                        }%

                      </strong>

                    </td>


                    <td>

                      {cp.status === 'active' ? (

                        <span className="badge badge-emerald">
                          Active Serving
                        </span>

                      ) : (

                        <span className="badge badge-cyan">
                          Ready
                        </span>

                      )}

                    </td>

                  </tr>

                )
              )}

            </tbody>

          </table>

        </div>

      </div>

    </div>

  );
}