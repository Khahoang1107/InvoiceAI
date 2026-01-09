# 📊 METRICS VISUALIZATION & ANALYSIS GUIDE

Guide để analyze & visualize metrics bằng Python, Excel, hoặc web tools

---

## 🔍 Option 1: Simple Python Analysis

### **Script 1: Basic Statistics**
```python
# analyze_metrics.py
import json
from collections import defaultdict
from datetime import datetime

metrics = []
with open('logs/metrics.jsonl', 'r') as f:
    for line in f:
        metrics.append(json.loads(line))

print(f"Total events: {len(metrics)}")
print(f"Date range: {metrics[0]['timestamp']} to {metrics[-1]['timestamp']}\n")

# Group by type
by_type = defaultdict(list)
for m in metrics:
    by_type[m['type']].append(m)

print("=== Events by Type ===")
for type_name, events in by_type.items():
    print(f"{type_name}: {len(events)} events")

# Retrieval analysis
print("\n=== Retrieval Quality ===")
retrieval = by_type.get('retrieval', [])
if retrieval:
    scores = [m.get('avg_score', 0) for m in retrieval]
    print(f"Avg score: {sum(scores)/len(scores):.2f}")
    print(f"Min score: {min(scores):.2f}")
    print(f"Max score: {max(scores):.2f}")

# Function calling analysis
print("\n=== Function Calling ===")
function = by_type.get('function_calling', [])
if function:
    successful = sum(1 for f in function if f.get('success', False))
    print(f"Total calls: {len(function)}")
    print(f"Success rate: {successful/len(function):.1%}")
    
    # By tool
    by_tool = defaultdict(lambda: {'total': 0, 'success': 0})
    for f in function:
        tool = f.get('tool_name', 'unknown')
        by_tool[tool]['total'] += 1
        if f.get('success', False):
            by_tool[tool]['success'] += 1
    
    print("\nBy tool:")
    for tool, stats in sorted(by_tool.items()):
        success_rate = stats['success'] / stats['total'] if stats['total'] > 0 else 0
        print(f"  {tool}: {stats['total']} calls, {success_rate:.0%} success")

# Response quality
print("\n=== Response Quality ===")
response = by_type.get('response_quality', [])
if response:
    efficiency = [m.get('efficiency_score', 0) for m in response]
    tokens = [m.get('tokens_used', 0) for m in response]
    times = [m.get('execution_time_ms', 0) for m in response]
    
    print(f"Avg efficiency score: {sum(efficiency)/len(efficiency):.2f}/10")
    print(f"Avg tokens: {sum(tokens)//len(tokens)}")
    print(f"Avg time: {sum(times)//len(times)}ms")

# User feedback
print("\n=== User Feedback ===")
feedback = by_type.get('user_feedback', [])
if feedback:
    by_feedback = defaultdict(int)
    for f in feedback:
        by_feedback[f.get('feedback', 'unknown')] += 1
    
    total = len(feedback)
    good = by_feedback.get('good', 0)
    print(f"Total feedback: {total}")
    for feedback_type, count in by_feedback.items():
        print(f"  {feedback_type}: {count} ({count/total:.0%})")
    
    satisfaction = good / total if total > 0 else 0
    print(f"Satisfaction rate: {satisfaction:.0%}")
```

### **Script 2: Execution Time Analysis**
```python
# analyze_performance.py
import json
from statistics import mean, median, stdev

metrics = []
with open('logs/metrics.jsonl', 'r') as f:
    for line in f:
        metrics.append(json.loads(line))

# Function execution times
function_calls = [m for m in metrics if m.get('type') == 'function_calling']

by_tool = {}
for call in function_calls:
    tool = call.get('tool_name', 'unknown')
    if tool not in by_tool:
        by_tool[tool] = []
    by_tool[tool].append(call.get('execution_time_ms', 0))

print("=== Performance by Tool ===\n")
for tool, times in sorted(by_tool.items()):
    times_sorted = sorted(times)
    print(f"{tool}:")
    print(f"  Calls: {len(times)}")
    print(f"  Avg: {mean(times):.1f}ms")
    print(f"  Median: {median(times):.1f}ms")
    if len(times) > 1:
        print(f"  Stdev: {stdev(times):.1f}ms")
    print(f"  Min: {min(times):.1f}ms")
    print(f"  Max: {max(times):.1f}ms")
    print(f"  P95: {times_sorted[int(len(times)*0.95)]:.1f}ms")
    print()
```

### **Script 3: Generate HTML Report**
```python
# generate_report.py
import json
from datetime import datetime

metrics = []
with open('logs/metrics.jsonl', 'r') as f:
    for line in f:
        metrics.append(json.loads(line))

html = f"""
<html>
<head>
<title>Metrics Report</title>
<style>
body {{ font-family: Arial; margin: 20px; }}
h1 {{ color: #333; }}
.metric {{ border: 1px solid #ddd; padding: 15px; margin: 10px 0; }}
.good {{ color: green; }}
.warning {{ color: orange; }}
.bad {{ color: red; }}
</style>
</head>
<body>
<h1>📊 System Metrics Report</h1>
<p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
<p>Total events: {len(metrics)}</p>

<div class="metric">
<h2>Retrieval Quality</h2>
"""

retrieval = [m for m in metrics if m.get('type') == 'retrieval']
if retrieval:
    avg_score = sum(m.get('avg_score', 0) for m in retrieval) / len(retrieval)
    status = "good" if avg_score > 0.75 else "warning" if avg_score > 0.60 else "bad"
    html += f"""
    <p>Average Score: <span class="{status}">{avg_score:.2f}</span></p>
    <p>Events: {len(retrieval)}</p>
    """

html += """
</div>

<div class="metric">
<h2>Function Calling</h2>
"""

function = [m for m in metrics if m.get('type') == 'function_calling']
if function:
    success_rate = sum(1 for m in function if m.get('success')) / len(function)
    status = "good" if success_rate > 0.95 else "warning" if success_rate > 0.85 else "bad"
    html += f"""
    <p>Success Rate: <span class="{status}">{success_rate:.1%}</span></p>
    <p>Total Calls: {len(function)}</p>
    """

html += """
</div>

<div class="metric">
<h2>User Feedback</h2>
"""

feedback = [m for m in metrics if m.get('type') == 'user_feedback']
if feedback:
    good = sum(1 for m in feedback if m.get('feedback') == 'good')
    satisfaction = good / len(feedback)
    status = "good" if satisfaction > 0.85 else "warning" if satisfaction > 0.70 else "bad"
    html += f"""
    <p>Satisfaction: <span class="{status}">{satisfaction:.1%}</span></p>
    <p>Total Feedback: {len(feedback)}</p>
    """

html += """
</div>
</body>
</html>
"""

with open('logs/metrics_report.html', 'w') as f:
    f.write(html)

print("✅ Report generated: logs/metrics_report.html")
```

---

## 📈 Option 2: Excel Analysis

### **Step 1: Export to CSV**
```bash
curl -X POST "http://localhost:8000/api/admin/metrics/export"
# Creates: logs/metrics_export.csv
```

### **Step 2: Open in Excel**
```
1. File → Open → logs/metrics_export.csv
2. Data → Pivot Table
3. Add fields:
   - Rows: type, tool_name
   - Values: Count (success), Avg(execution_time_ms)
4. Insert charts to visualize
```

### **Step 3: Create Pivot Tables**

**Pivot 1: Success Rate by Tool**
```
Tool Name          | Total Calls | Successful | Rate
count_invoices_by_date | 25      | 25         | 100%
filter_by_date     | 12          | 10         | 83%
get_all_invoices   | 15          | 15         | 100%
```

**Pivot 2: Execution Time by Tool**
```
Tool Name          | Avg Time | Min Time | Max Time
count_invoices_by_date | 32.5ms  | 18ms     | 52ms
filter_by_date     | 38.2ms  | 20ms     | 95ms
get_all_invoices   | 45.3ms  | 28ms     | 78ms
```

### **Step 4: Create Charts**

```excel
Chart 1: Success Rate Comparison
Type: Column chart
X-axis: Tool names
Y-axis: Success rate %
Target: All bars should be > 90%

Chart 2: Execution Time Trends
Type: Line chart with error bars
X-axis: Time (date)
Y-axis: Execution time (ms)
Target: Downward trend = optimization working
```

---

## 🎨 Option 3: Web Dashboard (Grafana)

### **Step 1: Install Grafana**
```bash
# Docker
docker run -d -p 3000:3000 grafana/grafana

# Or download from grafana.com
```

### **Step 2: Add Data Source**
```
1. Configuration → Data Sources
2. Add → JSON API
3. URL: http://localhost:8000/api/admin/metrics/summary
4. Save
```

### **Step 3: Create Dashboard**
```
1. Create → Dashboard
2. Add panels:
   - Retrieval score (Gauge)
   - Function success rate (Gauge)
   - Execution time trend (Graph)
   - User satisfaction (Gauge)
3. Set refresh: 1 minute
4. Access at http://localhost:3000
```

---

## 📊 Option 4: Real-time Monitoring with Python

```python
# monitor_metrics.py (run in separate terminal)
import json
import time
from datetime import datetime, timedelta
from collections import defaultdict

def monitor():
    """Monitor metrics in real-time"""
    last_check = datetime.now() - timedelta(hours=1)
    
    while True:
        metrics = []
        with open('logs/metrics.jsonl', 'r') as f:
            for line in f:
                m = json.loads(line)
                if m['timestamp'] > last_check.isoformat():
                    metrics.append(m)
        
        if metrics:
            print(f"\n📊 {len(metrics)} new events since {last_check.strftime('%H:%M')}\n")
            
            # Function failures
            failures = [m for m in metrics 
                       if m.get('type') == 'function_calling' 
                       and not m.get('success', True)]
            if failures:
                print(f"⚠️ {len(failures)} function failures:")
                for f in failures:
                    print(f"  - {f['tool_name']}: {f.get('error', 'unknown error')}")
            
            # Slow functions
            slow = [m for m in metrics 
                   if m.get('type') == 'function_calling' 
                   and m.get('execution_time_ms', 0) > 100]
            if slow:
                print(f"\n🐌 {len(slow)} slow functions (>100ms):")
                for s in slow:
                    print(f"  - {s['tool_name']}: {s['execution_time_ms']:.1f}ms")
            
            # Bad feedback
            bad_feedback = [m for m in metrics 
                           if m.get('type') == 'user_feedback' 
                           and m.get('feedback') == 'bad']
            if bad_feedback:
                print(f"\n😞 {len(bad_feedback)} negative feedback:")
                for b in bad_feedback:
                    comment = b.get('comment', 'no comment')
                    print(f"  - {comment}")
            
            last_check = datetime.now()
        
        time.sleep(30)  # Check every 30 seconds

if __name__ == "__main__":
    monitor()
```

---

## 📋 Common Analysis Queries

### **View metrics of last 24 hours**
```bash
# JSON format
tail -100 logs/metrics.jsonl | jq

# Specific type
grep '"type":"function_calling"' logs/metrics.jsonl | jq '.success' | sort | uniq -c
```

### **Calculate statistics**
```bash
# Average execution time
jq -r '.execution_time_ms' logs/metrics.jsonl | awk '{s+=$1; n++} END {print s/n}'

# Count successes
jq 'select(.success==true)' logs/metrics.jsonl | wc -l

# Group by tool
jq -r '.tool_name' logs/metrics.jsonl | sort | uniq -c
```

### **Create CSV from JSON**
```bash
# Convert to CSV manually
jq -r '[.timestamp, .type, .tool_name, .success, .execution_time_ms] | @csv' logs/metrics.jsonl > metrics.csv
```

---

## 🎯 Key Metrics to Monitor

### **Daily Monitoring**
```
1. Function success rate > 95%?
2. Avg execution time < 100ms?
3. No critical failures?
4. User satisfaction > 80%?
```

### **Weekly Review**
```
1. Retrieval score trend (up or down?)
2. Performance improvements realized?
3. User feedback patterns?
4. Any regressions?
```

### **Monthly Analysis**
```
1. Overall system health
2. ROI of improvements
3. User satisfaction evolution
4. Performance benchmarks
5. Plan next quarter optimizations
```

---

## 🚀 Automation Ideas

### **Auto-alert on failures**
```python
def check_health():
    summary = get_metrics_summary()
    
    if summary['function_calling']['success_rate'] < 0.90:
        send_email("⚠️ Function success rate dropped!")
    
    if summary['user_feedback']['positive_rate'] < 0.80:
        send_slack("😞 User satisfaction low")
```

### **Auto-generate weekly report**
```bash
# crontab -e
0 9 * * 1 python /path/to/generate_report.py  # Every Monday at 9am
```

### **Live dashboard**
```bash
# Terminal
watch -n 30 'tail -20 logs/metrics.jsonl | jq .'  # Refresh every 30s
```

---

## 📞 Tools Comparison

| Tool | Setup | Ease | Power | Cost |
|------|-------|------|-------|------|
| **Python Scripts** | Easy | ⭐⭐⭐ | ⭐⭐⭐⭐ | Free |
| **Excel** | Easy | ⭐⭐⭐⭐ | ⭐⭐ | Free |
| **Grafana** | Medium | ⭐⭐⭐ | ⭐⭐⭐⭐ | Free |
| **Kibana** | Medium | ⭐⭐ | ⭐⭐⭐⭐⭐ | Free |
| **Tableau** | Hard | ⭐⭐ | ⭐⭐⭐⭐⭐ | $$$ |

---

## 💡 Tips

1. **Start with Excel** - easiest, no setup
2. **Use Python for automation** - flexible, scriptable
3. **Add Grafana later** - for team dashboards
4. **Export regularly** - backup your metrics data
5. **Track trends** - compare week-to-week improvements

**Good luck with metrics! 📊**
