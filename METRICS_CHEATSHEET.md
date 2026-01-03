# ⚡ METRICS CHEAT SHEET

Quick reference for metrics system

---

## 🚀 Quick Start (30 seconds)

```bash
# 1. Start backend
python backend/main_refactored.py

# 2. Send chat
curl -X POST "http://localhost:8000/api/chat" \
  -d '{"message":"hôm nay có mấy hóa đơn"}'

# 3. View metrics
curl "http://localhost:8000/api/admin/metrics/summary?hours=24" | jq
```

---

## 📊 API Endpoints

```bash
# Metrics summary (24 hours)
GET /api/admin/metrics/summary?hours=24

# Metrics summary (7 days)
GET /api/admin/metrics/summary?hours=168

# Performance details
GET /api/admin/metrics/performance

# Export to CSV
POST /api/admin/metrics/export
```

---

## 📈 Metric Ranges

### **Good ✅**
```
Retrieval score        > 0.75
Function success rate  > 0.95
Execution time        < 100ms
Efficiency score      > 7.0
User satisfaction     > 0.85
```

### **Warning ⚠️**
```
Retrieval score        0.60-0.75
Function success rate  0.85-0.95
Execution time         100-200ms
Efficiency score       4.0-7.0
User satisfaction      0.70-0.85
```

### **Bad ❌**
```
Retrieval score        < 0.60
Function success rate  < 0.85
Execution time        > 200ms
Efficiency score      < 4.0
User satisfaction     < 0.70
```

---

## 📁 Files

```
backend/
  services/
    metrics_service.py          ← Core service
    chat_service.py             ← Integration
  routers/
    admin.py                    ← API endpoints
  test_metrics.py               ← Tests

logs/
  metrics.jsonl                 ← Raw data (auto-created)
  metrics_export.csv            ← Exported (auto-created)

METRICS_*.md                     ← Documentation
```

---

## 💻 Commands

### **View raw metrics**
```bash
tail -20 logs/metrics.jsonl | jq

# Pretty print
jq '.' logs/metrics.jsonl
```

### **Filter by type**
```bash
grep '"type":"function_calling"' logs/metrics.jsonl | jq
```

### **Count events**
```bash
wc -l logs/metrics.jsonl
```

### **Calculate avg execution time**
```bash
jq -r '.execution_time_ms' logs/metrics.jsonl | \
  awk '{s+=$1; n++} END {print "Avg:", s/n, "ms"}'
```

### **List all tools**
```bash
grep '"type":"function_calling"' logs/metrics.jsonl | \
  jq -r '.tool_name' | sort -u
```

---

## 📊 Excel Analysis

```
1. Export: POST /api/admin/metrics/export
2. Open: logs/metrics_export.csv
3. Data → Pivot Table
4. Fields:
   - Row: type, tool_name
   - Value: Count, Avg(execution_time)
5. Insert chart
```

---

## 🐍 Python Analysis

```python
from services.metrics_service import MetricsService

ms = MetricsService()

# Get summary
summary = ms.get_metrics_summary(hours=24)
print(summary)

# Get performance report
report = ms.get_performance_report()
print(report)

# Export CSV
ms.export_metrics_to_csv()

# Read raw
metrics = ms._read_all_metrics()
for m in metrics:
    if m['type'] == 'function_calling':
        print(f"{m['tool_name']}: {m['execution_time_ms']}ms")
```

---

## 🔍 Common Queries

### **Success rate by tool**
```bash
jq -r '.tool_name + ": " + (.success | tostring)' logs/metrics.jsonl | \
  sort | uniq -c | awk '{if ($NF=="true") print $0}'
```

### **Slow functions (> 100ms)**
```bash
jq 'select(.execution_time_ms > 100)' logs/metrics.jsonl | \
  jq '{tool: .tool_name, time: .execution_time_ms}'
```

### **Failed calls**
```bash
jq 'select(.success == false)' logs/metrics.jsonl
```

### **User feedback summary**
```bash
jq 'select(.type == "user_feedback")' logs/metrics.jsonl | \
  jq -r '.feedback' | sort | uniq -c
```

---

## 🎯 Optimization Workflow

```
Week 1: Baseline
  └─ Record current metrics

Week 2: Analyze
  └─ Find slowest function
  └─ Check failed calls
  └─ Review low scores

Week 3: Fix
  └─ Add index / optimize SQL
  └─ Upgrade model
  └─ Improve prompts

Week 4: Re-measure
  └─ Compare metrics
  └─ Calculate improvement %
  └─ Document changes
```

---

## 🚨 Alert Thresholds

```python
THRESHOLDS = {
    'retrieval_score': 0.70,
    'function_success': 0.90,
    'execution_time': 2000,  # ms
    'efficiency': 5.0,
    'satisfaction': 0.80
}

if metric < THRESHOLD:
    send_alert()
```

---

## 📚 Documentation

| Need | File |
|------|------|
| Quick start | METRICS_QUICK_START.md |
| Technical | METRICS_SYSTEM.md |
| Analysis | METRICS_VISUALIZATION.md |
| Examples | METRICS_IMPROVEMENTS.md |
| Setup | METRICS_DEPLOYMENT.md |

---

## ⚙️ Configuration

```python
# In metrics_service.py
self.metrics_file = Path("logs/metrics.jsonl")

# Modify:
self.metrics_file = Path("custom/path/metrics.jsonl")

# Retention:
def cleanup_old(days=30):
    # Add cleanup logic
    pass
```

---

## 🐛 Troubleshooting

### **No metrics file?**
```bash
mkdir -p logs
# Try again
```

### **No data in file?**
```
Need to run some chats first
Send at least one message before checking
```

### **API returning error?**
```bash
# Check backend running
curl http://localhost:8000/health

# Check file exists
ls -la logs/metrics.jsonl

# Check format
jq . logs/metrics.jsonl
```

### **CSV empty?**
```
Run metrics first:
  curl -X POST /api/admin/metrics/export
Wait a few seconds
  cat logs/metrics_export.csv
```

---

## 🎬 Example Session

```bash
# Terminal 1: Start backend
$ python backend/main_refactored.py
✅ Server running at http://localhost:8000

# Terminal 2: Send test message
$ curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"message":"hôm nay có bao nhiêu hóa đơn?"}'

# Response: AI answer

# Check metrics generated
$ curl "http://localhost:8000/api/admin/metrics/summary?hours=24"
{
  "total_events": 3,
  "retrieval": {"avg_score": 0.81},
  "function_calling": {"success_rate": 1.0},
  "response_quality": {"efficiency_score": 7.2}
}

# Export for Excel
$ curl -X POST "http://localhost:8000/api/admin/metrics/export"
✅ Metrics exported to logs/metrics_export.csv

# View raw
$ tail logs/metrics.jsonl | jq .
```

---

## 🏆 Best Practices

1. **Check daily** - Catch issues early
2. **Export weekly** - Track trends
3. **Optimize monthly** - Plan improvements
4. **Document changes** - Know what worked
5. **Set baselines** - Measure progress
6. **Test improvements** - Verify gains
7. **Monitor alerts** - Prevent regressions

---

## 🎯 Key Metrics to Track

```
Daily:
  ✓ Function success rate > 95%?
  ✓ Avg execution time < 100ms?
  ✓ No critical errors?

Weekly:
  ✓ Retrieval score trend?
  ✓ Performance improvements?
  ✓ User satisfaction?

Monthly:
  ✓ ROI of optimizations?
  ✓ Cumulative improvements?
  ✓ Next priorities?
```

---

## 🔗 Quick Links

- API Base: `http://localhost:8000`
- Metrics Summary: `/api/admin/metrics/summary?hours=24`
- Raw Data: `logs/metrics.jsonl`
- Exported CSV: `logs/metrics_export.csv`
- Docs: `METRICS_*.md` files

---

**Ready to optimize? Start with:** 
[METRICS_QUICK_START.md](./METRICS_QUICK_START.md)
