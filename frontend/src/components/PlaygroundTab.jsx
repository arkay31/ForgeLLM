import React, { useState } from 'react';
import { Terminal, Play, Sparkles, Database, CheckCircle2, AlertCircle, ArrowRightLeft, ShieldCheck, ShieldAlert } from 'lucide-react';
import { generateSQL } from '../services/api';

export default function PlaygroundTab({ activeModel, models }) {
  const [selectedDb, setSelectedDb] = useState('ecommerce_store');
  const [prompt, setPrompt] = useState('Find top 5 customers by total spending in Canada or Germany');
  const [modelVersion, setModelVersion] = useState('active');
  const [compareMode, setCompareMode] = useState(true);
  
  const [isLoading, setIsLoading] = useState(false);
  const [primaryResult, setPrimaryResult] = useState(null);
  const [comparisonResult, setComparisonResult] = useState(null);

  const sampleQuestions = [
    { label: 'E-Commerce Top Customers', db: 'ecommerce_store', q: 'Find top 5 customers by total spending in Canada or Germany' },
    { label: 'Concert Singers (>2020)', db: 'concert_singer', q: 'Find the names, country, and age of all singers who have sung in concerts after 2020' },
    { label: 'HR Average Salary by Dept', db: 'hr_analytics', q: 'List all departments with total number of employees and average salary' },
    { label: 'Top Rated Products', db: 'ecommerce_store', q: 'Show products with average review rating greater than 4.0' },
  ];

  const ddlMap = {
    ecommerce_store: `CREATE TABLE customers (customer_id INT PRIMARY KEY, first_name TEXT, last_name TEXT, email TEXT, country TEXT, created_at TIMESTAMP);\nCREATE TABLE products (product_id INT PRIMARY KEY, name TEXT, category TEXT, price DECIMAL, stock_quantity INT);\nCREATE TABLE orders (order_id INT PRIMARY KEY, customer_id INT, order_date DATE, total_amount DECIMAL, status TEXT);\nCREATE TABLE order_items (item_id INT PRIMARY KEY, order_id INT, product_id INT, quantity INT, unit_price DECIMAL);\nCREATE TABLE reviews (review_id INT PRIMARY KEY, product_id INT, customer_id INT, rating INT, comment TEXT, review_date DATE);`,
    hr_analytics: `CREATE TABLE departments (dept_id INT PRIMARY KEY, dept_name TEXT, location TEXT, budget DECIMAL);\nCREATE TABLE employees (emp_id INT PRIMARY KEY, first_name TEXT, last_name TEXT, email TEXT, role TEXT, dept_id INT, hire_date DATE);\nCREATE TABLE salaries (salary_id INT PRIMARY KEY, emp_id INT, base_salary DECIMAL, bonus DECIMAL, effective_date DATE);\nCREATE TABLE performance_reviews (review_id INT PRIMARY KEY, emp_id INT, review_year INT, rating INT, notes TEXT);`,
    concert_singer: `CREATE TABLE singer (singer_id INT PRIMARY KEY, name TEXT, country TEXT, song_name TEXT, song_release_year TEXT, age INT, is_male BOOLEAN);\nCREATE TABLE concert (concert_id INT PRIMARY KEY, concert_name TEXT, theme TEXT, stadium_id INT, year INT);`,
    finance_bank: `CREATE TABLE accounts (account_id INT PRIMARY KEY, customer_id INT, account_type TEXT, balance DECIMAL);\nCREATE TABLE transactions (tx_id INT PRIMARY KEY, account_id INT, tx_date DATE, amount DECIMAL, tx_type TEXT);`
  };

  const handleGenerate = async () => {
    setIsLoading(true);
    setPrimaryResult(null);
    setComparisonResult(null);

    const schemaCtx = {
      db_id: selectedDb,
      ddl: ddlMap[selectedDb] || ddlMap['ecommerce_store'],
    };

    try {
      const req1 = {
        prompt,
        model_version: modelVersion,
        schema_context: schemaCtx,
        execute_sql: true,
      };
      const res1 = await generateSQL(req1);
      setPrimaryResult(res1);

      if (compareMode) {
        const req2 = {
          prompt,
          model_version: modelVersion === 'base' ? 'active' : 'base',
          schema_context: schemaCtx,
          execute_sql: true,
        };
        const res2 = await generateSQL(req2);
        setComparisonResult(res2);
      }
    } catch (err) {
      alert('Inference error: ' + err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="page-view">
      <div style={{ marginBottom: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 800 }}>Text-to-SQL Playground & Inference Studio</h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
            Translate natural language questions to SQL, validate AST safety, and execute live against in-memory target databases.
          </p>
        </div>
        <button
          onClick={() => setCompareMode(!compareMode)}
          className={`btn ${compareMode ? 'btn-primary' : 'btn-secondary'}`}
        >
          <ArrowRightLeft size={16} />
          {compareMode ? 'Comparison Mode: ON' : 'Comparison Mode: OFF'}
        </button>
      </div>

      {/* Preset Pickers */}
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
        <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)', alignSelf: 'center', marginRight: '0.5rem' }}>Presets:</span>
        {sampleQuestions.map((sq, idx) => (
          <button
            key={idx}
            onClick={() => {
              setSelectedDb(sq.db);
              setPrompt(sq.q);
            }}
            className="btn btn-secondary"
            style={{ fontSize: '0.75rem', padding: '0.35rem 0.65rem' }}
          >
            {sq.label}
          </button>
        ))}
      </div>

      {/* Input Form */}
      <div className="glass-card" style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
          <div className="form-group" style={{ marginBottom: 0 }}>
            <label className="form-label">User Natural Language Query</label>
            <input
              type="text"
              className="form-input"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="e.g. Find all customers who spent more than $1000..."
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label">Target DB Schema</label>
              <select className="form-select" value={selectedDb} onChange={(e) => setSelectedDb(e.target.value)}>
                <option value="ecommerce_store">E-Commerce Store</option>
                <option value="hr_analytics">HR Analytics</option>
                <option value="concert_singer">Concert Singers</option>
                <option value="finance_bank">Finance & Banking</option>
              </select>
            </div>

            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label">Serving Model</label>
              <select className="form-select" value={modelVersion} onChange={(e) => setModelVersion(e.target.value)}>
                <option value="active">Active ({activeModel?.name || 'QLoRA'})</option>
                <option value="base">Base Model (Un-tuned)</option>
                {models.map((m) => (
                  <option key={m.checkpoint_id} value={m.checkpoint_id}>{m.name}</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        <button
          onClick={handleGenerate}
          disabled={isLoading}
          className="btn btn-primary"
          style={{ width: '100%', padding: '0.75rem' }}
        >
          <Sparkles size={16} />
          {isLoading ? 'Validating AST Safety & Generating SQL...' : 'Generate SQL Query & Execute Live'}
        </button>
      </div>

      {/* Output Panel / Comparison Side-by-Side */}
      {primaryResult && (
        <div className={compareMode && comparisonResult ? 'grid-2' : ''}>
          {/* Primary Model Result */}
          <div className="glass-card">
            <div className="card-header">
              <span className="card-title" style={{ color: '#00f2fe' }}>
                <CheckCircle2 size={18} /> {primaryResult.model_used}
              </span>
              <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                {primaryResult.safety_result ? (
                  primaryResult.safety_result.allowed ? (
                    <span className="badge badge-emerald" style={{ display: 'flex', gap: '0.25rem', alignItems: 'center' }}>
                      <ShieldCheck size={12} /> SQL Safety: PASSED
                    </span>
                  ) : (
                    <span className="badge badge-rose" style={{ display: 'flex', gap: '0.25rem', alignItems: 'center' }}>
                      <ShieldAlert size={12} /> SQL Safety: BLOCKED
                    </span>
                  )
                ) : null}
                <span className="badge badge-cyan">{primaryResult.latency_ms} ms</span>
              </div>
            </div>

            <div style={{ marginBottom: '1rem' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.35rem' }}>GENERATED SQL QUERY</div>
              <pre className="sql-box">{primaryResult.formatted_sql}</pre>
            </div>

            {/* SQLite Execution Preview */}
            {primaryResult.execution_result && (
              <div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.35rem', display: 'flex', justifyContent: 'space-between' }}>
                  <span>SQLITE LIVE EXECUTION RESULT</span>
                  <span style={{ color: primaryResult.execution_result.error ? '#f43f5e' : '#10b981' }}>
                    {primaryResult.execution_result.row_count} rows returned ({primaryResult.execution_result.execution_time_ms} ms)
                  </span>
                </div>

                {primaryResult.execution_result.error ? (
                  <div style={{ background: 'rgba(244, 63, 94, 0.1)', border: '1px solid rgba(244, 63, 94, 0.3)', padding: '0.75rem', borderRadius: '8px', color: '#f43f5e', fontSize: '0.85rem' }}>
                    {primaryResult.execution_result.error}
                  </div>
                ) : (
                  <div className="data-table-container">
                    <table className="data-table">
                      <thead>
                        <tr>
                          {primaryResult.execution_result.columns.map((col, idx) => (
                            <th key={idx}>{col}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {primaryResult.execution_result.rows.map((row, rIdx) => (
                          <tr key={rIdx}>
                            {row.map((cell, cIdx) => (
                              <td key={cIdx}>{cell}</td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Comparison Model Result */}
          {compareMode && comparisonResult && (
            <div className="glass-card" style={{ borderColor: 'rgba(244, 63, 94, 0.3)' }}>
              <div className="card-header">
                <span className="card-title" style={{ color: '#f43f5e' }}>
                  <AlertCircle size={18} /> {comparisonResult.model_used}
                </span>
                <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                  {comparisonResult.safety_result ? (
                    comparisonResult.safety_result.allowed ? (
                      <span className="badge badge-emerald" style={{ display: 'flex', gap: '0.25rem', alignItems: 'center' }}>
                        <ShieldCheck size={12} /> SQL Safety: PASSED
                      </span>
                    ) : (
                      <span className="badge badge-rose" style={{ display: 'flex', gap: '0.25rem', alignItems: 'center' }}>
                        <ShieldAlert size={12} /> SQL Safety: BLOCKED
                      </span>
                    )
                  ) : null}
                  <span className="badge badge-amber">{comparisonResult.latency_ms} ms</span>
                </div>
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.35rem' }}>BASE MODEL UN-TUNED SQL OUTPUT</div>
                <pre className="sql-box" style={{ color: '#f43f5e' }}>{comparisonResult.formatted_sql}</pre>
              </div>

              {comparisonResult.execution_result && (
                <div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.35rem', display: 'flex', justifyContent: 'space-between' }}>
                    <span>BASE MODEL EXECUTION RESULT</span>
                    <span>{comparisonResult.execution_result.row_count} rows</span>
                  </div>

                  {comparisonResult.execution_result.error ? (
                    <div style={{ background: 'rgba(244, 63, 94, 0.1)', border: '1px solid rgba(244, 63, 94, 0.3)', padding: '0.75rem', borderRadius: '8px', color: '#f43f5e', fontSize: '0.85rem' }}>
                      {comparisonResult.execution_result.error}
                    </div>
                  ) : (
                    <div className="data-table-container">
                      <table className="data-table">
                        <thead>
                          <tr>
                            {comparisonResult.execution_result.columns.map((col, idx) => (
                              <th key={idx}>{col}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {comparisonResult.execution_result.rows.map((row, rIdx) => (
                            <tr key={rIdx}>
                              {row.map((cell, cIdx) => (
                                <td key={cIdx}>{cell}</td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
