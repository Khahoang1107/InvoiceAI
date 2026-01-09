# 🚀 METRICS-DRIVEN IMPROVEMENTS

Hướng dẫn cải thiện hệ thống dựa trên metrics

---

## 📊 Real-world Scenarios & Solutions

### **Scenario 1: Success Rate thấp (80%)**

```
📈 Metrics:
  function_calling: {
    "tool_name": "filter_by_date",
    "success_rate": 0.80,
    "failed": 2,
    "errors": ["Invalid date format", "User not found"]
  }

🔍 Root Cause Analysis:
  1. Check logs/ → Xem chi tiết error
  2. Metrics show "Invalid date format" → Date parsing bug
  3. "User not found" → User ID filtering issue

✅ Solutions:

  Option A: Fix Date Parsing
  ─────────────────────────
  BEFORE:
  def filter_by_date(start_date, end_date, user_id):
      # Wrong: Assumes format always YYYY-MM-DD
      start = datetime.strptime(start_date, "%Y-%m-%d")
  
  AFTER:
  def filter_by_date(start_date, end_date, user_id):
      # Robust parsing
      for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"]:
          try:
              start = datetime.strptime(start_date, fmt)
              break
          except ValueError:
              continue
      if not start:
          raise ValueError(f"Invalid date format: {start_date}")

  Option B: Add User Validation
  ─────────────────────────────
  def filter_by_date(start_date, end_date, user_id):
      # Validate user exists
      user = db.query(User).filter(User.id == user_id).first()
      if not user:
          raise ValueError(f"User {user_id} not found")
      
      return db.query(Invoice).filter(
          Invoice.user_id == user_id,
          Invoice.invoice_date >= start_date,
          Invoice.invoice_date <= end_date
      ).all()

📊 After fix:
  success_rate: 0.80 → 0.98 ✅
  Test: Re-run same queries → should all pass
```

---

### **Scenario 2: Execution time too slow (200ms → target 80ms)**

```
📈 Metrics:
  function_calling: {
    "tool_name": "get_all_invoices",
    "avg_execution_time_ms": 200.5,
    "min_execution_time_ms": 95.2,
    "max_execution_time_ms": 450.1
  }

🔍 Bottleneck Analysis:
  1. Check database slow query logs
  2. Profile the function
  3. Identify N+1 query, missing index, etc.

✅ Solutions:

  Option A: Add Database Index
  ────────────────────────────
  # Check current schema
  BEFORE:
  CREATE TABLE invoices (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    invoice_date DATE,
    amount NUMERIC
    -- No indexes! 😱
  );

  AFTER:
  CREATE INDEX idx_invoices_user_id ON invoices(user_id);
  CREATE INDEX idx_invoices_date ON invoices(invoice_date);
  CREATE INDEX idx_invoices_user_date ON invoices(user_id, invoice_date);

  Improvement: 200ms → 45ms 🚀

  Option B: Optimize Query
  ─────────────────────────
  BEFORE:
  # Loads all columns + eager relationships
  invoices = db.query(Invoice).all()
  
  AFTER:
  # Only load needed columns
  invoices = db.query(Invoice.id, Invoice.vendor_name, Invoice.amount)\
    .filter(Invoice.user_id == user_id)\
    .limit(20)\
    .all()

  Improvement: 200ms → 65ms 🚀

  Option C: Add Caching
  ─────────────────────
  from functools import lru_cache
  from datetime import timedelta
  
  cache = {}
  cache_ttl = timedelta(minutes=5)
  
  def get_all_invoices(user_id):
      cache_key = f"invoices_{user_id}"
      
      if cache_key in cache:
          data, timestamp = cache[cache_key]
          if datetime.now() - timestamp < cache_ttl:
              return data  # Return cached (instant!)
      
      # Fresh query
      result = expensive_db_query(user_id)
      cache[cache_key] = (result, datetime.now())
      return result

  Improvement: 200ms → 5ms (cached) 🚀

📊 After fix:
  avg_execution_time: 200ms → 65ms ✅
  max_execution_time: 450ms → 150ms ✅
  Test: Re-run metrics → verify improvement
```

---

### **Scenario 3: Retrieval precision too low (62%)**

```
📈 Metrics:
  retrieval: {
    "avg_score": 0.62,
    "retrieved_count": 3,
    "precision_at_k": 0.62
  }

🔍 Analysis:
  Score 0.62 = khá thấp
  User hỏi: "hóa đơn điện tháng 12"
  Vector search trả: [nước, gas, khác] → không relevant ❌

✅ Solutions:

  Option A: Improve Embedding Model
  ──────────────────────────────────
  BEFORE:
  # Using simple TF-IDF embeddings
  from sklearn.feature_extraction.text import TfidfVectorizer
  
  embedding = TfidfVectorizer().fit_transform(texts)
  # Kém cho semantic understanding

  AFTER:
  # Use better embeddings (multilingual)
  from sentence_transformers import SentenceTransformer
  
  model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')
  embedding = model.encode(texts)  # Much better!
  
  Implementation:
  1. Install: pip install sentence-transformers
  2. Re-embed all invoices:
     embeddings = model.encode([inv.text for inv in invoices])
  3. Store in vector DB (Pinecone/Milvus)

  Improvement: 0.62 → 0.84 🚀

  Option B: Improve Data Quality
  ───────────────────────────────
  # Some invoices might have bad/missing data
  
  BEFORE:
  invoices = [
    {"id": 1, "vendor": "ABC", "type": None},  # Missing type
    {"id": 2, "vendor": "", "type": "electric"},  # Empty vendor
    {"id": 3, "vendor": "XYZ", "type": "water"}
  ]
  
  AFTER:
  # Clean data before embedding
  for inv in invoices:
    if not inv["vendor"]:
      continue  # Skip incomplete
    if not inv["type"]:
      inv["type"] = "other"
    
    # Rich context for embedding
    text = f"{inv['vendor']} {inv['type']} {inv.get('description', '')}"
    inv["embedding"] = model.encode(text)

  Improvement: Better matches 🚀

  Option C: Query Expansion
  ─────────────────────────
  BEFORE:
  # User query as-is
  query = "hóa đơn điện tháng 12"
  results = vector_store.search(query)

  AFTER:
  # Expand query with synonyms
  query_expansion = {
    "điện": ["electric", "electricity", "power"],
    "hóa đơn": ["invoice", "bill", "receipt"]
  }
  
  expanded_queries = [
    "hóa đơn điện tháng 12",
    "invoice electric December",
    "bill power month 12"
  ]
  
  # Search all, merge results
  all_results = []
  for q in expanded_queries:
    all_results.extend(vector_store.search(q, top_k=2))
  
  # Deduplicate & re-rank
  results = deduplicate_and_rank(all_results)

  Improvement: Coverage & relevance 🚀

📊 After fix:
  avg_score: 0.62 → 0.85 ✅
  precision_at_k: 0.62 → 0.88 ✅
  Test: Re-run retrieval metrics
```

---

### **Scenario 4: User satisfaction low (65% → target 90%)**

```
📈 Metrics:
  user_feedback: {
    "positive_rate": 0.65,
    "feedback_breakdown": {
      "good": 13,
      "bad": 5,
      "partial": 2
    }
  }

🔍 User Feedback Analysis:
  Read comments from "bad" feedback:
  - "Groq didn't understand my question"
  - "Results not accurate"
  - "Takes too long"

✅ Solutions:

  Option A: Better Intent Detection
  ─────────────────────────────────
  BEFORE:
  intent = IntentDetector.detect(user_message)
  # Simple regex-based → many false positives

  AFTER:
  # Use fine-tuned model
  intent = GPT2IntentDetector.detect(user_message)
  # Or use Groq itself to detect intent!
  
  Improvement: 65% → 78% satisfaction 🚀

  Option B: Improve Groq Prompts
  ──────────────────────────────
  BEFORE:
  system_prompt = "You are an invoice assistant. Answer questions."
  # Too generic

  AFTER:
  system_prompt = """
  You are an expert invoice management assistant.
  
  CAPABILITIES:
  - Analyze invoice patterns
  - Find spending trends
  - Compare vendors
  - Forecast costs
  
  TONE: Friendly, professional, concise
  
  IMPORTANT:
  - Always cite data sources
  - Ask clarifying questions if needed
  - Suggest relevant insights
  """

  Improvement: 65% → 82% satisfaction 🚀

  Option C: Add Response Feedback Loop
  ────────────────────────────────────
  BEFORE:
  # No feedback mechanism
  Response: "You have 5 invoices"
  # User clicks away unhappy

  AFTER:
  # Add feedback buttons
  Response: "You have 5 invoices"
  [👍 Helpful]  [👎 Not helpful]  [💬 Comment]
  
  If user clicks 👎:
  → Ask: "What were you looking for?"
  → Log feedback → Analyze patterns
  → Improve system based on feedback
  
  Improvement: 65% → 85% satisfaction 🚀

  Option D: Faster Response
  ────────────────────────
  Users complain "takes too long"
  
  BEFORE:
  Response time: 2500ms
  
  AFTER:
  # Optimize full pipeline
  - Query caching: -500ms
  - Parallel processing: -800ms
  - Prompt optimization: -300ms
  
  Result: 2500ms → 900ms ✅
  
  User perception: Fast response → happier!
  Improvement: 65% → 83% satisfaction 🚀

📊 After fix:
  positive_rate: 65% → 90% ✅
  bad_feedback: 5 → 1 ✅
  Test: Run full week, collect feedback
```

---

## 📊 Metrics Improvement Timeline

```
Week 1:
  Baseline metrics captured
  └─ Retrieval: 0.62, Function: 80%, Response: 2500ms, Satisfaction: 65%

Week 2-3:
  Improvements deployed (indexing, embedding upgrade)
  └─ Retrieval: 0.85 (+37%), Function: 95% (+19%), Response: 900ms (-64%), Satisfaction: 82%

Week 4:
  Fine-tuning based on user feedback
  └─ Retrieval: 0.87 (+2%), Function: 97% (+2%), Response: 750ms (-17%), Satisfaction: 90%

Month 2+:
  Continuous monitoring & optimization
  └─ Metrics dashboard → Track trends → Prevent regressions
```

---

## 🎯 Implementation Checklist

- [ ] Deploy metrics_service.py
- [ ] Integrate with ChatService
- [ ] Check /api/admin/metrics/summary endpoint works
- [ ] Baseline metrics (current state)
- [ ] Identify top 3 pain points from metrics
- [ ] Create improvement plan
- [ ] Implement fixes
- [ ] Re-measure metrics
- [ ] Compare before/after
- [ ] Document learnings
- [ ] Set up monitoring alerts

---

## 🔗 Related Files

- [METRICS_SYSTEM.md](./METRICS_SYSTEM.md) - Full technical docs
- [METRICS_QUICK_START.md](./METRICS_QUICK_START.md) - Quick reference
- `backend/services/metrics_service.py` - Source code
- `backend/services/chat_service.py` - Integration code
