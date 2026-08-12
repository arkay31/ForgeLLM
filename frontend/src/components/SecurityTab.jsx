import React, { useState } from 'react';
import { ShieldCheck, Key, Copy, Check, Lock, Terminal } from 'lucide-react';
import { API_BASE_URL } from '../services/api';

export default function SecurityTab() {
  const [copiedCurl, setCopiedCurl] = useState(false);
  const [copiedPython, setCopiedPython] = useState(false);
  const apiKey = 'forge-secret-key-2026-prod';

  const baseUrl = API_BASE_URL.replace(/\/api\/v1\/?$/, '');
  const docsUrl = `${baseUrl}/docs`;
  const generateUrl = `${API_BASE_URL}/serve/generate`;

  const curlSnippet = `curl -X POST "${generateUrl}" \\
  -H "Content-Type: application/json" \\
  -H "X-API-Key: ${apiKey}" \\
  -d '{
    "prompt": "Find top 5 customers by total spending in Canada",
    "model_version": "active",
    "execute_sql": true,
    "schema_context": {
      "db_id": "ecommerce_store",
      "ddl": "CREATE TABLE customers (customer_id INT, first_name TEXT, country TEXT);"
    }
  }'`;

  const pythonSnippet = `import requests

url = "${generateUrl}"
headers = {
    "Content-Type": "application/json",
    "X-API-Key": "${apiKey}"
}
payload = {
    "prompt": "List all departments with average salary above $150k",
    "model_version": "active",
    "execute_sql": True
}

response = requests.post(url, json=payload, headers=headers)
print("Generated SQL:", response.json()["formatted_sql"])
print("Execution Result:", response.json()["execution_result"])`;

  const copyToClipboard = (text, setCopied) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="page-view">
      <div style={{ marginBottom: '1.5rem' }}>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 800 }}>API Security, Rate Limiting & Developer Docs</h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
          Production authentication middleware, sliding window rate limiters, and SDK integration code snippets.
        </p>
      </div>

      <div className="grid-2">
        {/* Security Settings Card */}
        <div className="glass-card">
          <div className="card-header">
            <span className="card-title"><Key size={18} /> API Key Management</span>
            <span className="badge badge-emerald">Enforced</span>
          </div>

          <div className="form-group">
            <label className="form-label">Active Master Admin API Key</label>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <input type="text" className="form-input" value={apiKey} readOnly style={{ fontFamily: 'var(--font-mono)' }} />
              <button
                onClick={() => copyToClipboard(apiKey, () => {})}
                className="btn btn-secondary"
              >
                Copy Key
              </button>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginTop: '1rem' }}>
            <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '0.85rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Rate Limit Policy</div>
              <strong style={{ fontSize: '1.1rem', color: '#00f2fe' }}>60 requests/min</strong>
            </div>

            <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '0.85rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>CORS Policy</div>
              <strong style={{ fontSize: '1.1rem', color: '#10b981' }}>Allowed Origins [*]</strong>
            </div>
          </div>
        </div>

        {/* OpenAPI / Swagger Link */}
        <div className="glass-card">
          <div className="card-header">
            <span className="card-title"><Terminal size={18} /> Interactive OpenAPI Documentation</span>
            <span className="badge badge-violet">Swagger UI</span>
          </div>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '1rem' }}>
            Explore full OpenAPI specification, schema definitions, and interactive request sandbox via FastAPI Swagger docs.
          </p>
          <a
            href={docsUrl}
            target="_blank"
            rel="noreferrer"

            className="btn btn-primary"
            style={{ textDecoration: 'none', display: 'inline-flex' }}
          >
            Launch Interactive OpenAPI Swagger UI (/docs)
          </a>
        </div>
      </div>

      {/* Code Snippets */}
      <div className="grid-2">
        <div className="glass-card">
          <div className="card-header">
            <span className="card-title">cURL API Integration</span>
            <button
              onClick={() => copyToClipboard(curlSnippet, setCopiedCurl)}
              className="btn btn-secondary"
              style={{ fontSize: '0.75rem' }}
            >
              {copiedCurl ? <Check size={14} /> : <Copy size={14} />}
              {copiedCurl ? 'Copied!' : 'Copy cURL'}
            </button>
          </div>
          <pre className="sql-box" style={{ color: '#00f2fe', fontSize: '0.75rem' }}>{curlSnippet}</pre>
        </div>

        <div className="glass-card">
          <div className="card-header">
            <span className="card-title">Python requests Integration</span>
            <button
              onClick={() => copyToClipboard(pythonSnippet, setCopiedPython)}
              className="btn btn-secondary"
              style={{ fontSize: '0.75rem' }}
            >
              {copiedPython ? <Check size={14} /> : <Copy size={14} />}
              {copiedPython ? 'Copied!' : 'Copy Python'}
            </button>
          </div>
          <pre className="sql-box" style={{ color: '#38bdf8', fontSize: '0.75rem' }}>{pythonSnippet}</pre>
        </div>
      </div>
    </div>
  );
}
