# 📊 METRICS & EVALUATION SYSTEM

## 🎯 Tổng quan

Hệ thống ghi nhận và đánh giá chất lượng của:
- **Retrieval (RAG)** - Semantic search trong vector store
- **Function Calling** - Groq gọi database functions
- **Response Quality** - Chất lượng câu trả lời
- **User Feedback** - Đánh giá từ người dùng

---

## 📁 File & Cấu trúc

```
backend/
├── services/
│   └── metrics_service.py          ✨ Metrics tracking service
├── routers/
│   └── admin.py                    ✏️ Updated with metrics endpoints
└── logs/
    └── metrics.jsonl               📝 Metrics data (JSONL format)
```

---

## 🚀 Cách sử dụng

### 1. **Automatic Metrics Logging** (ChatService)

Metrics được tự động ghi nhận khi user chat:

```python
# File: backend/services/chat_service.py

# Khi retrieve từ vector store:
self.metrics_service.log_retrieval_metrics(
    user_id=user_id,
    query=request.message,
    retrieved_count=3,
    top_k=3,
    scores=[0.85, 0.78, 0.72]  # Similarity scores
)
# Output: Precision@3, Average score = 0.78

# Khi Groq gọi function:
self.metrics_service.log_function_calling_metrics(
    user_id=user_id,
    tool_name="count_invoices_by_date",
    tool_args={"date": "2025-12-29"},
    success=True,
    execution_time=45.2,  # milliseconds
    result_count=5
)
# Output: Success rate, execution time, result count

# Khi trả lời user:
self.metrics_service.log_response_quality_metrics(
    user_id=user_id,
    conversation_id="conv_123",
    intent_type="statistics",
    intent_confidence=0.92,
    used_database=True,
    used_retrieval=True,
    used_function_calling=True,
    response_length=250,
    tokens_used=145,
    execution_time=1250.5
)
# Output: Efficiency score, token usage, response time
```

### 2. **View Metrics via API**

#### **GET /api/admin/metrics/summary**
```bash
# 24 giờ qua
curl "http://localhost:8000/api/admin/metrics/summary?hours=24"

# Hoặc 7 ngày
curl "http://localhost:8000/api/admin/metrics/summary?hours=168"
```

**Response:**
```json
{
  "status": "ok",
  "data": {
    "period_hours": 24,
    "total_events": 156,
    "retrieval": {
      "total": 45,
      "avg_score": 0.81,
      "avg_precision_at_k": 0.87,
      "retrieval_events": [...]
    },
    "function_calling": {
      "total": 52,
      "successful": 50,
      "failed": 2,
      "success_rate": 0.96,
      "avg_execution_time_ms": 38.2,
      "tools_called": [
        "count_invoices_by_date",
        "get_all_invoices",
        "filter_by_date"
      ]
    },
    "response_quality": {
      "total": 48,
      "avg_tokens_used": 142,
      "avg_execution_time_ms": 1205,
      "avg_efficiency_score": 7.2,
      "intents": ["statistics", "amount_query", "invoice_search"]
    },
    "user_feedback": {
      "total": 12,
      "breakdown": {
        "good": 10,
        "bad": 1,
        "partial": 1
      },
      "positive_rate": 0.83
    }
  },
  "timestamp": "2025-12-29T10:30:00"
}
```

#### **GET /api/admin/metrics/performance**
```bash
curl "http://localhost:8000/api/admin/metrics/performance"
```

**Response:**
```json
{
  "status": "ok",
  "data": {
    "generated_at": "2025-12-29T10:30:00",
    "total_metrics": 156,
    "tools": {
      "count_invoices_by_date": {
        "calls": 25,
        "successful": 25,
        "failed": 0,
        "success_rate": 1.0,
        "avg_execution_time_ms": 32.5,
        "min_execution_time_ms": 18.2,
        "max_execution_time_ms": 52.1
      },
      "get_all_invoices": {
        "calls": 15,
        "successful": 15,
        "failed": 0,
        "success_rate": 1.0,
        "avg_execution_time_ms": 45.3,
        "min_execution_time_ms": 28.0,
        "max_execution_time_ms": 78.5
      },
      "filter_by_date": {
        "calls": 12,
        "successful": 10,
        "failed": 2,
        "success_rate": 0.83,
        "avg_execution_time_ms": 38.2,
        "min_execution_time_ms": 20.1,
        "max_execution_time_ms": 95.3
      }
    }
  },
  "timestamp": "2025-12-29T10:30:00"
}
```

#### **POST /api/admin/metrics/export**
```bash
curl -X POST "http://localhost:8000/api/admin/metrics/export"
```

**Response:**
```json
{
  "status": "ok",
  "message": "Metrics exported to logs/metrics_export.csv",
  "timestamp": "2025-12-29T10:30:00"
}
```

---

## 📊 Metrics được ghi nhận

### 1. **Retrieval Metrics** (RAG Quality)

| Metric | Ý nghĩa | Công thức |
|--------|---------|----------|
| **Avg Score** | Độ tương tự trung bình | Trung bình tất cả scores |
| **Precision@K** | % kết quả relevant | min(relevant, K) / K |
| **Retrieved Count** | Số doc được lấy | Count(results) |

**Khi nào capture:**
- Khi user hỏi something và system search vector store
- Ghi min/max/avg similarity scores

**File output:** `logs/metrics.jsonl`
```json
{
  "timestamp": "2025-12-29T10:15:23",
  "type": "retrieval",
  "user_id": 1,
  "query": "hóa đơn tháng 12",
  "retrieved_count": 3,
  "top_k": 3,
  "avg_score": 0.81,
  "max_score": 0.89,
  "min_score": 0.73,
  "precision_at_k": null
}
```

### 2. **Function Calling Metrics**

| Metric | Ý nghĩa | Giá trị |
|--------|---------|--------|
| **Success Rate** | % function gọi thành công | successful / total |
| **Execution Time** | Thời gian chạy | ms |
| **Result Count** | Số kết quả trả về | integer |
| **Tool Name** | Hàm nào được gọi | string |

**Khi nào capture:**
- Mỗi lần Groq quyết định gọi function
- Trước/sau execution để đo thời gian

**File output:**
```json
{
  "timestamp": "2025-12-29T10:15:45",
  "type": "function_calling",
  "user_id": 1,
  "tool_name": "count_invoices_by_date",
  "tool_args": {"date": "2025-12-29", "user_id": 1},
  "success": true,
  "execution_time_ms": 32.5,
  "result_count": 5,
  "error": null
}
```

### 3. **Response Quality Metrics**

| Metric | Ý nghĩa | Công thức |
|--------|---------|----------|
| **Intent Type** | Loại intent được detect | string |
| **Intent Confidence** | Độ tin cậy intent | 0.0 - 1.0 |
| **Pipeline** | Thành phần được dùng | {database, retrieval, function_calling} |
| **Response Length** | Độ dài response | character count |
| **Tokens Used** | Tokens Groq sử dụng | integer |
| **Execution Time** | Total thời gian | ms |
| **Efficiency Score** | Hiệu suất tổng thể | 0 - 10 (cao = tốt) |

**Công thức Efficiency Score:**
```
token_score = max(0, 10 - (tokens / 100))        # Penalize high tokens
time_score = max(0, 10 - (time_ms / 100))        # Penalize slow
length_score = min(10, response_length / 100)    # Reward detailed

efficiency = (token_score * 0.3 + time_score * 0.3 + length_score * 0.4)
```

**File output:**
```json
{
  "timestamp": "2025-12-29T10:16:00",
  "type": "response_quality",
  "user_id": 1,
  "conversation_id": "conv_1",
  "intent_type": "statistics",
  "intent_confidence": 0.92,
  "pipeline": {
    "used_database": true,
    "used_retrieval": true,
    "used_function_calling": true
  },
  "response_length": 245,
  "tokens_used": 145,
  "execution_time_ms": 1205.3,
  "efficiency_score": 7.2
}
```

### 4. **User Feedback Metrics**

| Feedback | Ý nghĩa |
|----------|---------|
| **good** | Người dùng hài lòng |
| **bad** | Người dùng không hài lòng |
| **partial** | Kết quả tạm được |

**File output:**
```json
{
  "timestamp": "2025-12-29T10:16:30",
  "type": "user_feedback",
  "user_id": 1,
  "conversation_id": "conv_1",
  "tool_name": "count_invoices_by_date",
  "feedback": "good",
  "comment": "Kết quả chính xác"
}
```

---

## 🎯 Cải thiện dựa trên Metrics

### **Scenario 1: Success Rate thấp**

```
Hiện tại: filter_by_date success_rate = 0.80

Nguyên nhân có thể:
❌ Function parameters sai
❌ Database query lỗi
❌ Date format không consistent

Cải thiện:
✅ Thêm validation parameters
✅ Fix SQL query bugs
✅ Standardize date handling
✅ Thêm error handling
```

### **Scenario 2: Execution Time chậm**

```
Hiện tại: avg_execution_time = 150ms

Nguyên nhân:
❌ Complex SQL query
❌ Database không có index
❌ Network latency

Cải thiện:
✅ Query optimization
✅ Add database indexes
✅ Connection pooling
✅ Caching frequent results
```

### **Scenario 3: Retrieval Precision thấp**

```
Hiện tại: avg_score = 0.62

Nguyên nhân:
❌ Embedding model không tốt
❌ Vector store data quality
❌ Query không clear

Cải thiện:
✅ Upgrade embedding model
✅ Re-embed documents
✅ Clean vector store
✅ Improve prompts
```

### **Scenario 4: Efficiency Score thấp**

```
Hiện tại: avg_efficiency = 4.2

Nguyên nhân:
❌ High token usage
❌ Slow execution
❌ Short responses

Cải thiện:
✅ Optimize prompts (less verbose)
✅ Faster database queries
✅ Better response generation
```

---

## 📈 Dashboard (Optional)

Bạn có thể tạo dashboard bằng:

### **Option 1: Python Script + matplotlib**
```python
import json
import matplotlib.pyplot as plt
from collections import defaultdict

# Read metrics
metrics = []
with open('logs/metrics.jsonl', 'r') as f:
    for line in f:
        metrics.append(json.loads(line))

# Group by tool
tool_success_rate = defaultdict(lambda: {'success': 0, 'total': 0})
for m in metrics:
    if m['type'] == 'function_calling':
        tool = m['tool_name']
        tool_success_rate[tool]['total'] += 1
        if m['success']:
            tool_success_rate[tool]['success'] += 1

# Plot
tools = list(tool_success_rate.keys())
rates = [tool_success_rate[t]['success'] / tool_success_rate[t]['total'] for t in tools]

plt.figure(figsize=(10, 6))
plt.bar(tools, rates)
plt.ylabel('Success Rate')
plt.title('Function Calling Success Rate by Tool')
plt.ylim(0, 1.0)
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('logs/metrics_dashboard.png')
```

### **Option 2: Web Dashboard (Grafana/Kibana)**
- Import metrics.jsonl vào Elasticsearch/InfluxDB
- Tạo Grafana dashboard để visualize

### **Option 3: Excel Analysis**
```bash
# Export to CSV
curl -X POST "http://localhost:8000/api/admin/metrics/export"

# Open logs/metrics_export.csv in Excel
# Create pivot tables & charts
```

---

## 🔍 Interpreting Metrics

### **Good Metrics**

```
✅ Retrieval:
   - avg_score > 0.75
   - precision_at_k > 0.80

✅ Function Calling:
   - success_rate > 0.95
   - execution_time < 100ms
   - avg_result_count > 1

✅ Response Quality:
   - intent_confidence > 0.85
   - efficiency_score > 6.0
   - execution_time < 2000ms

✅ User Feedback:
   - positive_rate > 0.85
   - feedback_count > 50/month
```

### **Warning Signs**

```
⚠️ Retrieval:
   - avg_score < 0.60
   - precision_at_k < 0.60

⚠️ Function Calling:
   - success_rate < 0.85
   - execution_time > 200ms

⚠️ Response Quality:
   - intent_confidence < 0.70
   - efficiency_score < 4.0
   - execution_time > 3000ms

⚠️ User Feedback:
   - positive_rate < 0.70
```

---

## 🛠️ Code Examples

### **Add feedback from Frontend**

```python
# User click thumbs up/down
@router.post("/api/chat/{conversation_id}/feedback")
async def save_feedback(conversation_id: str, feedback: dict):
    """
    Save user feedback on response
    
    Body:
    {
      "tool_name": "count_invoices_by_date",
      "feedback": "good|bad|partial",
      "comment": "optional"
    }
    """
    from services.metrics_service import MetricsService
    
    metrics = MetricsService()
    metrics.log_user_feedback(
        user_id=current_user.id,
        conversation_id=conversation_id,
        tool_name=feedback.get("tool_name"),
        feedback=feedback.get("feedback"),
        comment=feedback.get("comment")
    )
    
    return {"status": "ok"}
```

### **Monitoring via logs**

```bash
# Watch metrics in real-time
tail -f logs/metrics.jsonl | jq 'select(.type=="function_calling" and .success==false)'

# Count failures
grep '"success":false' logs/metrics.jsonl | wc -l

# Average execution time
jq -r '.execution_time_ms' logs/metrics.jsonl | awk '{sum+=$1; count++} END {print "Average:", sum/count, "ms"}'
```

---

## 📝 Summary

| Component | Tracked | API Endpoint | Use Case |
|-----------|---------|--------------|----------|
| **Retrieval** | Score, Precision | `/api/admin/metrics/summary` | Monitor RAG quality |
| **Function Calling** | Success rate, Time | `/api/admin/metrics/performance` | Track function reliability |
| **Response Quality** | Efficiency score | `/api/admin/metrics/summary` | Monitor overall performance |
| **User Feedback** | Satisfaction | `/api/admin/metrics/summary` | Measure user happiness |

**Next Steps:**
1. Monitor metrics daily
2. Set alerts for low scores
3. Investigate failures
4. Optimize based on findings
5. Re-monitor to verify improvements
