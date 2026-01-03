# ⚡ METRICS QUICK START GUIDE

## 🚀 Nhanh chóng bắt đầu

### 1. **Metrics tự động ghi nhận**
```
Không cần setup gì thêm! 
Khi user chat → metrics được tự động log vào logs/metrics.jsonl
```

### 2. **View metrics qua API**

```bash
# Terminal 1: Start backend
cd backend
python main_refactored.py

# Terminal 2: Check metrics (24 giờ qua)
curl "http://localhost:8000/api/admin/metrics/summary?hours=24"

# View performance report
curl "http://localhost:8000/api/admin/metrics/performance"

# Export to CSV
curl -X POST "http://localhost:8000/api/admin/metrics/export"
```

---

## 📊 Các metrics được track

### **Tự động:**
✅ Retrieval (vector search)  
✅ Function calling (Groq tool calls)  
✅ Response quality (efficiency score)  

### **User feedback (Optional):**
Người dùng có thể đánh giá response (👍/👎)

---

## 📈 Dữ liệu output

### **File:** `logs/metrics.jsonl`
```
Mỗi dòng = 1 event JSON
Tự động append khi có chat
```

### **API Endpoints:**
```
GET  /api/admin/metrics/summary        → 24/168 giờ qua
GET  /api/admin/metrics/performance    → Chi tiết từng tool
POST /api/admin/metrics/export         → Export CSV
```

---

## 🎯 Các chỉ số quan trọng

| Metrics | Good | Warning | Bad |
|---------|------|---------|-----|
| **Retrieval Score** | > 0.75 | 0.60-0.75 | < 0.60 |
| **Function Success Rate** | > 0.95 | 0.85-0.95 | < 0.85 |
| **Execution Time** | < 100ms | 100-200ms | > 200ms |
| **Efficiency Score** | > 7.0 | 4-7 | < 4 |
| **User Satisfaction** | > 85% | 70-85% | < 70% |

---

## 📝 Ví dụ

### **Check metrics hôm nay**
```bash
curl "http://localhost:8000/api/admin/metrics/summary?hours=24" | jq

# Output:
# {
#   "total_events": 156,
#   "retrieval": {
#     "avg_score": 0.81
#   },
#   "function_calling": {
#     "success_rate": 0.96,
#     "avg_execution_time_ms": 38.2
#   },
#   "user_feedback": {
#     "positive_rate": 0.83
#   }
# }
```

### **Chi tiết từng function**
```bash
curl "http://localhost:8000/api/admin/metrics/performance" | jq '.data.tools'

# Output:
# {
#   "count_invoices_by_date": {
#     "calls": 25,
#     "success_rate": 1.0,
#     "avg_execution_time_ms": 32.5
#   },
#   "filter_by_date": {
#     "calls": 12,
#     "success_rate": 0.83,
#     "avg_execution_time_ms": 38.2
#   }
# }
```

### **Export để analysis**
```bash
curl -X POST "http://localhost:8000/api/admin/metrics/export"
# File tạo: logs/metrics_export.csv

# Mở Excel → Pivot tables, charts, analysis
```

---

## 🔧 Tích hợp Frontend (Optional)

### **Add feedback button**
```javascript
// Sau khi Groq trả lời, user click 👍 or 👎

async function saveFeedback(conversationId, feedback) {
  const response = await fetch(`/api/chat/${conversationId}/feedback`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      tool_name: 'count_invoices_by_date',
      feedback: feedback,  // 'good' | 'bad' | 'partial'
      comment: 'optional comment'
    })
  });
  return response.json();
}

// Usage:
// saveFeedback('conv_123', 'good')
```

---

## 📚 Chi tiết xem

👉 [METRICS_SYSTEM.md](../METRICS_SYSTEM.md) - Full documentation

---

## ✨ Key Files

- `backend/services/metrics_service.py` - Metrics logic
- `backend/routers/admin.py` - API endpoints
- `logs/metrics.jsonl` - Metrics data
- `METRICS_SYSTEM.md` - Full docs

---

**Thế đó! System sẽ tự động track tất cả metrics khi user chat.** 📊
