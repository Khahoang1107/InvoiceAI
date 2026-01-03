# Integration & Admin Dashboard Guide

## 📊 Accessing Your Benchmarks & Metrics

### Quick Access URLs

Once your server is running on `http://localhost:8000`:

#### NER Benchmarks
```
Latest benchmark:
http://localhost:8000/api/admin/benchmarks/ner/latest

All benchmarks:
http://localhost:8000/api/admin/benchmarks/ner/all

Comparison (improvements):
http://localhost:8000/api/admin/benchmarks/ner/comparison

Formatted report:
http://localhost:8000/api/admin/benchmarks/ner/report

Entity performance:
http://localhost:8000/api/admin/benchmarks/ner/entity-summary
```

#### System Metrics
```
Last 24h metrics:
http://localhost:8000/api/admin/metrics/summary?hours=24

Performance by tool:
http://localhost:8000/api/admin/metrics/performance

Export to CSV:
http://localhost:8000/api/admin/metrics/export (POST)
```

## 🎯 Use Cases

### Use Case 1: Check System Health

```bash
# Get last 24 hours metrics
curl http://localhost:8000/api/admin/metrics/summary?hours=24

# Response example:
{
  "status": "ok",
  "data": {
    "retrieval_metrics": {
      "total_retrievals": 1250,
      "avg_score": 0.87,
      "precision_at_k": {...}
    },
    "function_calling": {
      "total_calls": 2341,
      "success_rate": 98.5,
      "avg_execution_time": 0.45
    },
    "response_quality": {
      "avg_tokens": 245,
      "avg_latency": 1.24,
      "intent_confidence": 0.94
    }
  }
}
```

### Use Case 2: Monitor NER Model Performance

```bash
# Get latest NER benchmark
curl http://localhost:8000/api/admin/benchmarks/ner/latest

# Response:
{
  "status": "ok",
  "data": {
    "model_name": "Invoice NER v1",
    "version": "1.0",
    "overall_metrics": {
      "precision": 93.9,
      "recall": 92.7,
      "f1": 93.3
    },
    "entities": {
      "Mã hóa đơn": {"precision": 92.5, "recall": 91.0, "f1": 91.7},
      "Ngày phát hành": {"precision": 94.0, "recall": 93.2, "f1": 93.6},
      "Tổng tiền": {"precision": 95.1, "recall": 94.0, "f1": 94.5}
    }
  }
}
```

### Use Case 3: Track Model Improvements

```bash
# Get comparison across all versions
curl http://localhost:8000/api/admin/benchmarks/ner/comparison

# Shows improvement from v1.0 to v2.0, v2.0 to v3.0, etc.
# Useful for validating that new models are better
```

### Use Case 4: Identify Weak Entities

```bash
# Get per-entity analysis
curl http://localhost:8000/api/admin/benchmarks/ner/entity-summary

# Shows which entity types need improvement
# Example: Mã hóa đơn has lower F1 than Tổng tiền
```

## 🖥️ Admin Dashboard Implementation

### Minimal Python Admin Dashboard

Create `backend/admin_dashboard.py`:

```python
"""Simple admin dashboard server"""
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
import json
from services.metrics_service import MetricsService
from services.ner_benchmark_service import NERBenchmarkService

app = FastAPI(title="InvoiceAI Admin Dashboard")

metrics_service = MetricsService()
ner_service = NERBenchmarkService()

@app.get("/")
async def dashboard():
    """Main dashboard page"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>InvoiceAI Admin Dashboard</title>
        <style>
            body { font-family: Arial; margin: 20px; background: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; }
            .card { background: white; padding: 20px; margin: 10px 0; border-radius: 8px; }
            .metric { display: inline-block; margin: 10px 20px; }
            .metric-value { font-size: 24px; font-weight: bold; color: #2c3e50; }
            .metric-label { color: #7f8c8d; font-size: 12px; }
            .good { color: #27ae60; }
            .warning { color: #e67e22; }
            .danger { color: #e74c3c; }
            table { width: 100%; border-collapse: collapse; }
            th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
            th { background: #34495e; color: white; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 InvoiceAI Admin Dashboard</h1>
            
            <div class="card">
                <h2>🔴 System Metrics (Last 24h)</h2>
                <div id="metrics-container">Loading...</div>
            </div>
            
            <div class="card">
                <h2>🤖 NER Model Performance</h2>
                <div id="ner-container">Loading...</div>
            </div>
        </div>
        
        <script>
        // Load metrics
        fetch('/api/admin/metrics/summary?hours=24')
            .then(r => r.json())
            .then(data => {
                const m = data.data;
                document.getElementById('metrics-container').innerHTML = `
                    <div class="metric">
                        <div class="metric-value good">${m.function_calling?.success_rate?.toFixed(1)}%</div>
                        <div class="metric-label">Function Success Rate</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">${m.response_quality?.avg_latency?.toFixed(2)}s</div>
                        <div class="metric-label">Avg Latency</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">${m.retrieval_metrics?.avg_score?.toFixed(2)}</div>
                        <div class="metric-label">Retrieval Score</div>
                    </div>
                `;
            });
        
        // Load NER benchmark
        fetch('/api/admin/benchmarks/ner/latest')
            .then(r => r.json())
            .then(data => {
                const b = data.data;
                const overall = b.overall_metrics;
                let entityHtml = '<table><tr><th>Entity</th><th>Precision</th><th>Recall</th><th>F1</th></tr>';
                for (const [entity, metrics] of Object.entries(b.entities)) {
                    entityHtml += `
                        <tr>
                            <td>${entity}</td>
                            <td>${metrics.precision.toFixed(1)}%</td>
                            <td>${metrics.recall.toFixed(1)}%</td>
                            <td>${metrics.f1.toFixed(1)}%</td>
                        </tr>
                    `;
                }
                entityHtml += '</table>';
                
                document.getElementById('ner-container').innerHTML = `
                    <p><strong>Model:</strong> ${b.model_name} v${b.version}</p>
                    <div class="metric">
                        <div class="metric-value good">${overall.f1.toFixed(1)}%</div>
                        <div class="metric-label">Overall F1-Score</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">${overall.precision.toFixed(1)}%</div>
                        <div class="metric-label">Precision</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">${overall.recall.toFixed(1)}%</div>
                        <div class="metric-label">Recall</div>
                    </div>
                    <h3>Entity Performance</h3>
                    ${entityHtml}
                `;
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(html)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
```

Run:
```bash
python backend/admin_dashboard.py
```

Access: `http://localhost:8001`

### Using Existing Admin Routes

Your admin API routes are already available in `main.py`:

```python
from backend.routers import admin

app.include_router(admin.router)
```

This makes all endpoints available:
- `/api/admin/metrics/*`
- `/api/admin/benchmarks/ner/*`

## 📱 Frontend Integration (React)

### Add Dashboard Component

Create `frontend/src/pages/AdminDashboard.tsx`:

```typescript
import React, { useEffect, useState } from 'react';
import axios from 'axios';

interface MetricsData {
  function_calling?: {
    success_rate: number;
  };
  response_quality?: {
    avg_latency: number;
  };
  retrieval_metrics?: {
    avg_score: number;
  };
}

interface NERBenchmark {
  model_name: string;
  version: string;
  overall_metrics: {
    precision: number;
    recall: number;
    f1: number;
  };
  entities: Record<string, {
    precision: number;
    recall: number;
    f1: number;
  }>;
}

export const AdminDashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<MetricsData | null>(null);
  const [nerBench, setNerBench] = useState<NERBenchmark | null>(null);

  useEffect(() => {
    // Load metrics
    axios.get('/api/admin/metrics/summary?hours=24')
      .then(res => setMetrics(res.data.data))
      .catch(console.error);

    // Load NER benchmark
    axios.get('/api/admin/benchmarks/ner/latest')
      .then(res => setNerBench(res.data.data))
      .catch(console.error);
  }, []);

  return (
    <div className="admin-dashboard">
      <h1>📊 Admin Dashboard</h1>

      {metrics && (
        <div className="metrics-card">
          <h2>System Metrics (24h)</h2>
          <div className="metric-grid">
            <MetricBox 
              label="Function Success Rate"
              value={`${metrics.function_calling?.success_rate?.toFixed(1)}%`}
            />
            <MetricBox 
              label="Avg Response Time"
              value={`${metrics.response_quality?.avg_latency?.toFixed(2)}s`}
            />
            <MetricBox 
              label="Retrieval Score"
              value={metrics.retrieval_metrics?.avg_score?.toFixed(2)}
            />
          </div>
        </div>
      )}

      {nerBench && (
        <div className="ner-card">
          <h2>🤖 NER Model: {nerBench.model_name} v{nerBench.version}</h2>
          <div className="metric-grid">
            <MetricBox 
              label="F1-Score"
              value={`${nerBench.overall_metrics.f1.toFixed(1)}%`}
              className="good"
            />
            <MetricBox 
              label="Precision"
              value={`${nerBench.overall_metrics.precision.toFixed(1)}%`}
            />
            <MetricBox 
              label="Recall"
              value={`${nerBench.overall_metrics.recall.toFixed(1)}%`}
            />
          </div>

          <h3>Entity Performance</h3>
          <table className="entity-table">
            <thead>
              <tr>
                <th>Entity Type</th>
                <th>Precision</th>
                <th>Recall</th>
                <th>F1-Score</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(nerBench.entities).map(([entity, metrics]) => (
                <tr key={entity}>
                  <td>{entity}</td>
                  <td>{metrics.precision.toFixed(1)}%</td>
                  <td>{metrics.recall.toFixed(1)}%</td>
                  <td>{metrics.f1.toFixed(1)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

interface MetricBoxProps {
  label: string;
  value: string | number;
  className?: string;
}

const MetricBox: React.FC<MetricBoxProps> = ({ label, value, className }) => (
  <div className={`metric-box ${className || ''}`}>
    <div className="metric-value">{value}</div>
    <div className="metric-label">{label}</div>
  </div>
);
```

## 🔗 Integration Checklist

- ✅ NER Benchmark Service created
- ✅ NER API endpoints added to admin router
- ✅ Benchmark data saved and accessible
- ✅ Metrics system integrated into ChatService
- ✅ Metrics API endpoints available
- 🔄 Admin dashboard (optional, examples provided)
- 🔄 Frontend integration (examples provided)

## 📈 Data Flow Diagram

```
┌────────────────┐
│  User Chat     │
└────────┬───────┘
         │
         ↓
┌────────────────────────────┐
│  ChatService               │
│  - send_message()          │
│  - _call_groq_with_context │
└────────┬────────────────────┘
         │
         ↓ (Real-time)
┌────────────────────────────┐
│  MetricsService            │
│  - log_retrieval_metrics   │
│  - log_function_calling    │
│  - log_response_quality    │
└────────┬────────────────────┘
         │
         ↓
┌────────────────────────────┐
│  logs/metrics.jsonl        │
│  (Auto-appended)           │
└────────────────────────────┘

         ↓ (On-demand)
┌────────────────────────────┐
│  AdminAPI.metrics_summary  │
│  .metrics_performance      │
│  .metrics_export           │
└────────────────────────────┘

────────────────────────────────────────

NER Model Training Cycle:

┌────────────────┐
│ Train Model    │
└────────┬───────┘
         │
         ↓
┌────────────────────────────┐
│ Evaluate on Test Set       │
└────────┬────────────────────┘
         │
         ↓
┌────────────────────────────┐
│ NERBenchmarkService        │
│ .save_ner_benchmark()      │
└────────┬────────────────────┘
         │
         ↓
┌────────────────────────────────┐
│ logs/benchmarks/ner_*..jsonl   │
│ (Benchmark history)            │
└────────┬───────────────────────┘
         │
         ↓ (On-demand)
┌────────────────────────────┐
│ AdminAPI.benchmarks/ner/*  │
│ - latest                   │
│ - all                      │
│ - comparison               │
│ - report                   │
│ - entity-summary           │
└────────────────────────────┘
```

## 🎯 Recommended Monitoring Setup

### Weekly Metrics Review

```python
# Check system health
curl http://localhost:8000/api/admin/metrics/summary?hours=168

# Check NER baseline
curl http://localhost:8000/api/admin/benchmarks/ner/latest

# Export for analysis
curl -X POST http://localhost:8000/api/admin/metrics/export
# Saves to logs/metrics_export.csv
```

### After New Model Training

```python
# Save new benchmark
python -c "
from backend.services.ner_benchmark_service import NERBenchmarkService
service = NERBenchmarkService()
service.save_ner_benchmark(
    model_name='Invoice NER v2',
    version='2.0',
    entities={...},
    overall_metrics={...},
    notes='Improved with additional training'
)
"

# View comparison
curl http://localhost:8000/api/admin/benchmarks/ner/comparison

# Check improvement %
curl http://localhost:8000/api/admin/benchmarks/ner/report
```

---

**System Ready**: All monitoring and benchmarking endpoints are functional
**Next Step**: Choose dashboard implementation (Python Flask, React, or custom)
