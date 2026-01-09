# 🎓 Hệ thống AI Learning - Tài liệu hướng dẫn

## Tổng quan

Hệ thống InvoiceAI giờ đây có khả năng **học từ các tương tác** và ngày càng thông minh hơn theo thời gian. AI sẽ ghi nhớ cách bạn hỏi và cải thiện responses dựa trên patterns.

---

## ✨ Các tính năng đã implement

### 1. **Lưu trữ tương tác thành công** 💾
- Mỗi khi user hỏi và AI trả lời thành công, tương tác này được lưu vào hệ thống
- Bao gồm: câu hỏi, câu trả lời, intent, metadata (thời gian, tokens, function calls)
- Dữ liệu được lưu trong:
  * Vector store (semantic search)
  * Memory cache (fast access)
  * User patterns database

### 2. **Tìm kiếm câu hỏi tương tự** 🔍
- Khi user hỏi một câu mới, AI tìm các câu hỏi tương tự đã được hỏi trước
- Sử dụng semantic search để hiểu ngữ nghĩa, không chỉ từ khóa
- Top 2-3 câu hỏi tương tự nhất được dùng làm reference

### 3. **Học patterns của user** 📊
- Hệ thống phân tích:
  * Intent nào user thường dùng nhất
  * Keywords nào user hay nhắc đến
  * Thời gian và frequency của interactions
- Dựa vào đó để cải thiện accuracy

### 4. **Personalized suggestions** 🎯
- Mỗi user có profile riêng
- Suggestions được tùy chỉnh theo thói quen sử dụng
- User mới sẽ thấy suggestions mặc định
- User quen thuộc sẽ thấy suggestions phù hợp với patterns của họ

### 5. **Continuous improvement** 📈
- AI tự động phân tích tất cả interactions
- Tìm ra patterns chung để cải thiện system
- Không cần manual training hay fine-tuning

---

## 🔧 Cách hoạt động

### Flow khi user gửi message:

```
1. User gửi câu hỏi
   ↓
2. Tìm câu hỏi tương tự trong lịch sử (learning_service)
   ↓
3. Lấy database context + RAG context + past queries context
   ↓
4. AI xử lý với full context
   ↓
5. Trả response cho user
   ↓
6. Lưu interaction thành công vào learning system
   ↓
7. Cập nhật user patterns
```

### Data được lưu cho mỗi interaction:

```python
{
    "user_id": 2,
    "query": "lọc hóa đơn theo ngày 10/11/2025",
    "response": "Có 3 hóa đơn ngày 10/11/2025...",
    "intent": "invoice_search",
    "timestamp": "2026-01-09T00:15:30",
    "metadata": {
        "intent_confidence": 0.95,
        "used_database": true,
        "used_function_calling": true,
        "tokens_used": 345,
        "execution_time_ms": 1230
    }
}
```

### User patterns được track:

```python
{
    "common_intents": {
        "invoice_search": 15,  # User hay tìm kiếm hóa đơn
        "statistics": 8,       # Thỉnh thoảng xem thống kê
        "amount_query": 5      # Ít khi hỏi về tổng tiền
    },
    "common_keywords": {
        "lọc": 12,
        "hóa đơn": 20,
        "tháng": 8,
        "ngày": 15
    },
    "query_count": 28,
    "last_updated": "2026-01-09T00:15:30"
}
```

---

## 📁 Files mới được tạo

### 1. `backend/services/learning_service.py`

**Purpose**: Core service quản lý AI learning

**Key methods**:
- `save_successful_interaction()` - Lưu tương tác thành công
- `get_similar_past_queries()` - Tìm câu hỏi tương tự
- `get_user_preferences()` - Lấy preferences của user
- `generate_personalized_suggestions()` - Tạo suggestions tùy chỉnh
- `learn_from_feedback()` - Học từ feedback (TODO)
- `analyze_query_patterns()` - Phân tích patterns

---

## 🚀 Cách sử dụng

### Tự động (đã tích hợp)

Learning service đã được tích hợp vào `chat_service.py`. Mỗi lần user chat, AI tự động:
1. Tìm past queries tương tự
2. Sử dụng context từ past queries
3. Lưu interaction mới
4. Cập nhật patterns

**Không cần làm gì thêm** - AI tự học!

### API endpoint mới (có thể thêm)

#### 1. Get user preferences
```http
GET /api/user/preferences
Response:
{
    "is_new_user": false,
    "query_count": 28,
    "common_intents": ["invoice_search", "statistics"],
    "common_keywords": ["lọc", "hóa đơn", "tháng"],
    "suggestions": [
        "🔍 Tìm hóa đơn gần đây",
        "📊 Thống kê chi tiêu",
        "💰 Tổng tiền hóa đơn"
    ]
}
```

#### 2. Get personalized suggestions
```http
GET /api/user/suggestions
Response:
{
    "suggestions": [
        "🔍 Tìm hóa đơn gần đây",
        "📊 Thống kê chi tiêu",
        "💰 Tổng tiền hóa đơn"
    ]
}
```

#### 3. Submit feedback (để AI học tốt hơn)
```http
POST /api/chat/feedback
Body:
{
    "query": "lọc hóa đơn theo ngày 10/11/2025",
    "response": "Có 3 hóa đơn...",
    "feedback": "Kết quả chính xác, rất hài lòng",
    "rating": 5
}
```

---

## 💡 Ví dụ thực tế

### Scenario 1: User mới

**Lần đầu tiên hỏi:**
```
User: "lọc hóa đơn theo ngày 10/11/2025"
AI: [Xử lý bình thường, không có past context]
     → Trả về 3 hóa đơn
     → Lưu interaction này
```

**Lần thứ 2 hỏi tương tự:**
```
User: "lọc hóa đơn ngày 15/11/2025"
AI: [Tìm thấy câu hỏi tương tự trước đó]
     → Biết ngay user muốn filter theo ngày
     → Response nhanh và chính xác hơn
     → Lưu pattern: user hay filter theo ngày
```

### Scenario 2: User quen thuộc

**Sau 20 lần tương tác:**
```
User patterns:
- Thường hỏi về "lọc theo ngày" (60%)
- Thỉnh thoảng "thống kê" (30%)
- Ít khi "tìm kiếm theo vendor" (10%)

Personalized suggestions:
✅ "📅 Lọc hóa đơn theo ngày"  <- Ưu tiên cao
✅ "📊 Thống kê chi tiêu tháng này"
❌ "🔍 Tìm theo vendor" <- Không show vì user ít dùng
```

### Scenario 3: Learning from patterns

**Sau 100+ interactions từ nhiều users:**
```
System insights:
- 70% users hỏi "lọc theo ngày" → Cải thiện date parsing
- 25% users hỏi "thống kê tháng" → Add quick suggestions
- 15% users gặp lỗi với "ngày 32/13/2025" → Add validation

AI tự động cải thiện:
→ Intent detection tốt hơn
→ Error handling tốt hơn
→ Response templates tốt hơn
```

---

## 🔮 Tương lai (có thể mở rộng)

### 1. **Fine-tuning with user data**
- Thu thập 1000+ successful interactions
- Fine-tune Groq model cho domain cụ thể
- Accuracy tăng 10-20%

### 2. **Feedback loop**
- User rate responses (1-5 stars)
- AI học từ negative feedback
- Tự động cải thiện prompts

### 3. **Multi-user learning**
- User A hỏi một câu khó → AI học
- User B hỏi câu tương tự → AI trả lời ngay

### 4. **Smart suggestions**
- Predict user needs trước khi họ hỏi
- "Bạn có muốn xem thống kê tháng này không?"

### 5. **Context awareness**
- Nhớ preferences: "user thích format ngắn gọn"
- Auto-adjust response style

---

## ⚙️ Cấu hình

### Tuning parameters trong `learning_service.py`:

```python
# Số lượng past queries để retrieve
SIMILAR_QUERIES_TOP_K = 2  # Mặc định: 2

# Số interactions giữ trong memory
MAX_MEMORY_INTERACTIONS = 1000  # Mặc định: 1000

# Minimum confidence để lưu interaction
MIN_CONFIDENCE_TO_SAVE = 0.5  # Chỉ lưu nếu confident

# Personalization level
ENABLE_PERSONALIZATION = True  # Bật/tắt personalization
```

---

## 📊 Metrics & Monitoring

### Metrics được track:

1. **Learning effectiveness**
   - % queries có similar past queries
   - Response quality improvement over time
   - User satisfaction trend

2. **User patterns**
   - Common intents distribution
   - Query frequency heatmap
   - User segmentation

3. **System performance**
   - Learning storage size
   - Retrieval latency
   - Pattern analysis time

### Logs để monitor:

```
🎓 Found 2 similar past queries for learning
💾 Saved interaction for learning: user=2, intent=invoice_search
📊 Updated patterns for user 2
```

---

## ⚠️ Lưu ý quan trọng

### Privacy & Security
- Learning data chỉ accessible bởi user đó (hoặc admin)
- Có thể implement user-level isolation
- Option để user opt-out khỏi learning

### Performance
- Learning service chạy async, không block main flow
- Cache patterns trong memory để fast access
- Periodic cleanup old interactions

### Storage
- Vector store cần enough capacity
- Consider retention policy (keep 6 months?)
- Archive old interactions

---

## 🎯 Kết luận

Hệ thống AI Learning giúp:
✅ AI ngày càng hiểu user tốt hơn
✅ Response chính xác hơn theo thời gian
✅ Personalized experience cho mỗi user
✅ Tự động cải thiện không cần manual work
✅ Scale tốt với nhiều users

**AI của bạn giờ đây có "trí nhớ" và "học hỏi" thực sự!** 🧠✨
