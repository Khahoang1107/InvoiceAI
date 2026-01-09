# 🏗️ KIẾN TRÚC TỔNG THỂ HỆ THỐNG INVOICEAI

## 📊 Sơ đồ tổng quan

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│                        🌐 CLIENT LAYER (Frontend)                          │
│                                                                             │
│     ┌──────────────────────────────────────────────────────────────┐       │
│     │  React.js App (Port 3000)                                    │       │
│     │  ├─ Login/Register Pages                                     │       │
│     │  ├─ Dashboard (Analytics, Statistics)                        │       │
│     │  ├─ Invoice Management (List, View, Create, Edit, Delete)   │       │
│     │  ├─ Chat Interface (AI Chatbot)                             │       │
│     │  ├─ OCR Upload & Processing                                 │       │
│     │  ├─ Export & Reporting                                      │       │
│     │  └─ User Profile & Settings                                 │       │
│     └──────────────────────────────────────────────────────────────┘       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                         HTTP/REST API (JSON)
                                     │
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│                    ⚙️  API LAYER (FastAPI Backend - Port 8000)             │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                     FastAPI Application                             │  │
│  │  ├─ CORS & Security Middleware                                     │  │
│  │  ├─ Request/Response Logging & Monitoring                          │  │
│  │  └─ Exception & Error Handling                                     │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                        📚 ROUTERS (Endpoints)                       │  │
│  │                                                                     │  │
│  │  ├─ /api/auth/           (Authentication, JWT tokens)              │  │
│  │  │  ├─ POST /register          → Register new user                │  │
│  │  │  ├─ POST /login             → Login & get JWT token            │  │
│  │  │  ├─ POST /refresh           → Refresh expired token            │  │
│  │  │  └─ GET  /me                → Current user info                │  │
│  │  │                                                                 │  │
│  │  ├─ /api/chat/            (Chat with AI)                           │  │
│  │  │  ├─ POST /              → Send message, Groq AI responds        │  │
│  │  │  └─ GET  /{id}/history  → Get conversation history             │  │
│  │  │                                                                 │  │
│  │  ├─ /api/invoices/        (Invoice CRUD)                           │  │
│  │  │  ├─ GET  /              → List invoices with filters            │  │
│  │  │  ├─ POST /              → Create new invoice                    │  │
│  │  │  ├─ GET  /{id}          → Get invoice details                   │  │
│  │  │  ├─ PUT  /{id}          → Update invoice                        │  │
│  │  │  ├─ DELETE /{id}        → Delete invoice                        │  │
│  │  │  ├─ GET  /stats         → Get statistics & analytics            │  │
│  │  │  └─ GET  /search        → Full-text search                      │  │
│  │  │                                                                 │  │
│  │  ├─ /api/upload/          (File & OCR Processing)                  │  │
│  │  │  ├─ POST /              → Upload invoice image (async)          │  │
│  │  │  ├─ POST /ocr/{id}      → Run OCR on uploaded image             │  │
│  │  │  ├─ GET  /ocr/{id}      → Get OCR results                       │  │
│  │  │  └─ GET  /status/{id}   → Check processing status               │  │
│  │  │                                                                 │  │
│  │  ├─ /api/export/          (Export & Reports)                       │  │
│  │  │  ├─ GET  /invoices/excel    → Export all as Excel              │  │
│  │  │  ├─ GET  /invoices/csv      → Export all as CSV                │  │
│  │  │  └─ GET  /summary           → Export summary report             │  │
│  │  │                                                                 │  │
│  │  ├─ /api/images/          (Image Storage & Serving)                │  │
│  │  │  └─ GET  /{id}          → Serve stored invoice images           │  │
│  │  │                                                                 │  │
│  │  ├─ /api/admin/           (Admin Operations)                       │  │
│  │  │  ├─ GET  /health        → Health check                          │  │
│  │  │  ├─ GET  /stats         → System statistics                     │  │
│  │  │  └─ POST /cleanup       → Database cleanup                      │  │
│  │  │                                                                 │  │
│  │  └─ /docs                 (Swagger UI documentation)               │  │
│  │                                                                     │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                     🧠 SERVICE LAYER                               │  │
│  │                                                                     │  │
│  │  ┌──────────────────────────────────────────────────────────────┐  │  │
│  │  │ Chat & AI Services                                           │  │  │
│  │  │  ├─ ChatService              → Main chat handler             │  │  │
│  │  │  │   └─ Calls Groq AI API    → Sends requests & gets answer │  │  │
│  │  │  ├─ GroqDatabaseTools        → Database function calling    │  │  │
│  │  │  │   ├─ count_total_invoices → Đếm tất cả hóa đơn           │  │  │
│  │  │  │   ├─ count_invoices_by_date → Đếm hóa đơn theo ngày      │  │  │
│  │  │  │   ├─ get_all_invoices     → Lấy danh sách hóa đơn        │  │  │
│  │  │  │   ├─ search_invoices      → Tìm kiếm hóa đơn             │  │  │
│  │  │  │   ├─ filter_by_date       → Lọc theo thời gian           │  │  │
│  │  │  │   ├─ get_invoices_by_type → Lọc theo loại hóa đơn        │  │  │
│  │  │  │   └─ export_to_excel      → Xuất Excel                    │  │  │
│  │  │  ├─ IntentDetector            → Hiểu ý định người dùng      │  │  │
│  │  │  │   └─ Phân loại: statistics, amount_query, search          │  │  │
│  │  │  ├─ InvoiceQueryService      → Database queries              │  │  │
│  │  │  └─ ChatHistoryService       → Quản lý lịch sử chat          │  │  │
│  │  └──────────────────────────────────────────────────────────────┘  │  │
│  │                                                                     │  │
│  │  ┌──────────────────────────────────────────────────────────────┐  │  │
│  │  │ Invoice & File Services                                      │  │  │
│  │  │  ├─ InvoiceService           → CRUD operations               │  │  │
│  │  │  ├─ OCRService               → Tesseract OCR processing      │  │  │
│  │  │  ├─ OCRJobService            → Async job management           │  │  │
│  │  │  ├─ FileUploadService        → File handling & validation    │  │  │
│  │  │  ├─ NERService               → Named Entity Recognition      │  │  │
│  │  │  └─ ExportService            → Excel/CSV/PDF generation      │  │  │
│  │  └──────────────────────────────────────────────────────────────┘  │  │
│  │                                                                     │  │
│  │  ┌──────────────────────────────────────────────────────────────┐  │  │
│  │  │ Auth & User Services                                         │  │  │
│  │  │  ├─ UserService              → User management               │  │  │
│  │  │  ├─ JWT Authentication       → Token generation & validation │  │  │
│  │  │  └─ Authorization            → Role-based access control     │  │  │
│  │  └──────────────────────────────────────────────────────────────┘  │  │
│  │                                                                     │  │
│  │  ┌──────────────────────────────────────────────────────────────┐  │  │
│  │  │ RAG & Vector Services                                        │  │  │
│  │  │  ├─ VectorStore              → Semantic search in invoices   │  │  │
│  │  │  ├─ VectorDB (Pinecone/etc)  → Vector database backend       │  │  │
│  │  │  └─ RAGTools                 → Retrieval-augmented generation │  │  │
│  │  └──────────────────────────────────────────────────────────────┘  │  │
│  │                                                                     │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                     📋 MODEL/SCHEMA LAYER                          │  │
│  │                                                                     │  │
│  │  ├─ User          → User account & profile                          │  │
│  │  ├─ Invoice       → Invoice data model                              │  │
│  │  ├─ ChatMessage   → Chat conversation storage                       │  │
│  │  ├─ OCRJob        → OCR processing job tracking                     │  │
│  │  └─ Pydantic Schemas → Request/response validation                 │  │
│  │                                                                     │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                     🔧 UTILITIES & CORE                            │  │
│  │                                                                     │  │
│  │  ├─ config/         → Settings, environment variables              │  │
│  │  ├─ core/           → Logging, exceptions, dependencies            │  │
│  │  ├─ middleware/     → CORS, logging, error handling                │  │
│  │  ├─ utils/          → Helper functions, database tools             │  │
│  │  └─ handlers/       → Event handlers, background tasks             │  │
│  │                                                                     │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                    ┌────────────────┼─────────────────┐
                    │                │                 │
                    ▼                ▼                 ▼
         ┌──────────────────┐  ┌──────────────┐  ┌──────────────┐
         │  PostgreSQL DB   │  │ Groq AI API  │  │  Tesseract   │
         │  (Railway Cloud) │  │ (llama-3.3)  │  │    (OCR)     │
         │                  │  │              │  │              │
         │ Tables:          │  │ - Function   │  │ Extracts:    │
         │ • users          │  │   calling    │  │ • Text       │
         │ • invoices       │  │ - Analytics  │  │ • Tables     │
         │ • chat_messages  │  │ - Responses  │  │ • Amounts    │
         │ • ocr_jobs       │  │              │  │              │
         │ • documents      │  │              │  │              │
         └──────────────────┘  └──────────────┘  └──────────────┘
                    │
         ┌──────────┴──────────────┐
         │                         │
         ▼                         ▼
    ┌─────────────┐         ┌──────────────┐
    │ Pinecone    │         │ File Storage │
    │ Vector DB   │         │ (Local/S3)   │
    │             │         │              │
    │ Stores:     │         │ Stores:      │
    │ • Invoice   │         │ • Images     │
    │   embeddings│         │ • PDFs       │
    │ • Documents │         │ • Excel      │
    └─────────────┘         └──────────────┘
```

---

## 📊 Chi tiết các thành phần

### 1️⃣ FRONTEND (React.js - Port 3000)
**Vị trí:** `frontend/`
**Chức năng:**
- Giao diện người dùng responsive
- Quản lý invoices: xem, tạo, sửa, xóa
- Chat trực tiếp với Groq AI
- Upload ảnh và xem kết quả OCR
- Xuất báo cáo, thống kê
- Đăng nhập/đăng ký

**Công nghệ:**
- React.js
- Tailwind CSS (styling)
- Axios (API calls)
- React Query (data fetching)

---

### 2️⃣ BACKEND API (FastAPI - Port 8000)
**Vị trí:** `backend/`
**Chức năng:** Xử lý tất cả business logic

#### **📍 Routers (API Endpoints)**
- `routers/auth.py` → Đăng nhập, đăng ký, JWT
- `routers/chat.py` → Chat endpoint gọi ChatService
- `routers/invoices.py` → CRUD invoices
- `routers/upload.py` → Upload & OCR processing
- `routers/export.py` → Xuất Excel/CSV
- `routers/images.py` → Serve stored images
- `routers/admin.py` → Admin operations

#### **🧠 Services (Business Logic)**
| Service | Chức năng |
|---------|----------|
| `ChatService` | Xử lý chat, gọi Groq AI, function calling |
| `GroqDatabaseTools` | Các function mà Groq AI có thể gọi |
| `InvoiceService` | CRUD invoices, validation |
| `InvoiceQueryService` | Complex queries từ database |
| `OCRService` | Tesseract OCR processing |
| `UserService` | User management |
| `VectorStore` | Semantic search (RAG) |
| `ExportService` | Generate Excel/CSV/PDF |

#### **📋 Models & Schemas**
- `models/user.py` → User data model
- `models/invoice.py` → Invoice data model (định nghĩa trong db)
- `schemas/` → Pydantic request/response models

#### **🔧 Core Infrastructure**
- `config/settings.py` → Environment variables
- `core/dependencies.py` → Dependency injection container
- `core/logging.py` → Centralized logging
- `core/exceptions.py` → Custom exceptions
- `middleware/` → CORS, logging, error handling

---

### 3️⃣ DATABASE (PostgreSQL - Railway Cloud)
**Quản lý dữ liệu:**

```sql
-- Users & Authentication
users (id, email, password_hash, role, created_at)

-- Invoices
invoices (
  id, user_id, invoice_number, invoice_date, 
  vendor_name, buyer_name, total_amount, status, 
  items JSON, extracted_data JSON, ...
)

-- Chat History
chat_messages (id, user_id, conversation_id, role, content, created_at)

-- OCR Jobs
ocr_jobs (id, user_id, file_path, status, result JSON, created_at)

-- Vector embeddings
documents (id, invoice_id, embedding, metadata, created_at)
```

---

### 4️⃣ AI INTEGRATION (Groq LLM)

#### **🤖 Groq AI Flow**

```
User: "Hôm nay có mấy hóa đơn?"
    ↓
ChatService.send_message()
    ↓
Intent Detection → intent_type = "statistics", time_period = "today"
    ↓
Query Database → invoices for today
    ↓
Call Groq with:
  - System prompt (instructions)
  - Chat history (context)
  - Database results (data)
  - Tools available (functions)
    ↓
Groq AI decides: "Cần gọi count_invoices_by_date(date='2025-12-29')"
    ↓
GroqDatabaseTools.count_invoices_by_date() executes
    ↓
Tool result → Tool result sent back to Groq
    ↓
Groq generates: "Hôm nay 29/12 bạn có 5 hóa đơn, tổng tiền: 50.000.000 VND"
    ↓
Response → Frontend → User
```

#### **📞 Groq Function Calling**
Các function Groq có thể tự động gọi:
- `count_total_invoices()` → Đếm tổng hóa đơn
- `count_invoices_by_date(date)` → Đếm hóa đơn theo ngày
- `get_all_invoices(limit)` → Lấy danh sách hóa đơn
- `search_invoices(query)` → Tìm kiếm
- `get_invoice_by_id(id)` → Chi tiết 1 hóa đơn
- `filter_by_date(start, end)` → Lọc theo thời gian
- `get_invoices_by_type(type)` → Lọc theo loại
- `export_to_excel(filter)` → Xuất Excel

---

### 5️⃣ OCR PROCESSING (Tesseract)
**Luồng:**
1. User upload ảnh hóa đơn → `/api/upload/`
2. API nhận file, trả về response nhanh (50ms)
3. **Async background job** xử lý OCR
4. Tesseract trích xuất text, tables, amounts
5. NER service nhận dạng thực thể (vendor, buyer, amount)
6. Kết quả lưu vào database
7. User xem kết quả qua `/api/upload/ocr/{id}`

---

### 6️⃣ RAG (Retrieval-Augmented Generation)
**Tính năng:**
- Chuyển invoice → vector embeddings (semantic search)
- Lưu vào Pinecone vector DB
- Khi user hỏi, tìm invoice tương tự dùng semantic search
- Cung cấp context tốt hơn cho Groq AI

```
User question → Embedding → Search Pinecone
    ↓
Top 3 similar invoices found
    ↓
Context + Database results → Send to Groq
    ↓
Groq generates better answer
```

---

## 🔄 Luồng hoạt động chính

### Kịch bản 1: Chat với AI

```
Frontend (User types) 
  ↓ POST /api/chat/
Backend (ChatService.send_message)
  ↓ Detect intent
  ↓ Query database if needed
  ↓ Search vector store for context
  ↓ Call Groq AI API with:
    - System prompt
    - Chat history
    - Database results
    - Available functions
  ↓ Groq decides to call function → count_invoices_by_date
  ↓ Execute tool → get results
  ↓ Send results back to Groq
  ↓ Groq generates final answer
  ↓ Store conversation in database
  ↓ Return response to Frontend
Frontend (Display answer)
```

### Kịch bản 2: Upload & OCR

```
Frontend (User upload image)
  ↓ POST /api/upload/
Backend (FileUploadService)
  ↓ Validate file (size, format)
  ↓ Save to storage
  ↓ Create OCR job record
  ↓ Return job_id immediately (fast response)
  ↓ Background: Start async OCR processing
    ├─ Tesseract OCR → extract text
    ├─ NER → identify entities
    └─ Save results to DB
Frontend (Poll /api/upload/ocr/{id})
  ↓ When status = "completed"
  ↓ Display results to user
```

### Kịch bản 3: Invoice CRUD

```
Frontend (Create/Update/Delete)
  ↓ POST/PUT/DELETE /api/invoices/
Backend (InvoiceService)
  ↓ Validate data (Pydantic schemas)
  ↓ Check authorization (user owns invoice)
  ↓ Database transaction
  ↓ Update embeddings in vector store
  ↓ Return result
Frontend (Update local state)
```

---

## 🔐 Security Architecture

```
┌─────────────────┐
│   Frontend      │
│  (Port 3000)    │
└────────┬────────┘
         │ JWT Token in header
         ↓
┌────────────────────────────────┐
│  FastAPI Backend (Port 8000)   │
│  ├─ CORS Middleware            │
│  ├─ Rate Limiting              │
│  └─ JWT Verification           │
└────────┬───────────────────────┘
         │ user_id after verification
         ↓
┌────────────────────────────────┐
│  Service Layer                 │
│  ├─ Check user ownership       │
│  └─ Filter data by user_id     │
└────────┬───────────────────────┘
         │
         ↓
┌────────────────────────────────┐
│  Database                      │
│  (Only return user's data)     │
└────────────────────────────────┘
```

---

## 📊 Technology Stack

| Layer | Technologies |
|-------|--------------|
| **Frontend** | React, Tailwind CSS, Axios |
| **Backend** | FastAPI, Python 3.11+ |
| **Database** | PostgreSQL (Railway Cloud) |
| **AI/LLM** | Groq API (llama-3.3-70b) |
| **OCR** | Tesseract, OpenCV |
| **NLP** | spaCy (NER) |
| **Vector DB** | Pinecone (RAG) |
| **File Storage** | Local filesystem / S3 |
| **Authentication** | JWT tokens |
| **Deployment** | Docker, Railway |

---

## 🚀 Deployment Architecture

```
┌──────────────────────────────────────────────┐
│           Deployment Environments            │
│                                              │
│  Local Dev          |   Production           │
│  ─────────────      |   ──────────────       │
│  • Frontend :3000   |   • Frontend (CDN)     │
│  • Backend :8000    |   • FastAPI (Cloud)    │
│  • SQLite/PG        |   • PostgreSQL (Cloud) │
│  • Tesseract        |   • Docker containers  │
│  • Groq API         |   • Groq API           │
│                     |   • Railway hosting    │
└──────────────────────────────────────────────┘
```

---

## 📈 Performance & Optimization

- **Async Operations:** OCR processing runs in background
- **Caching:** Database query caching for frequently accessed data
- **Vector Search:** Fast semantic search using Pinecone
- **Lazy Loading:** Services initialize only when needed
- **Connection Pooling:** Database connection reuse

---

## 🔄 Data Flow Diagram

```
User Input (Frontend)
    ↓
Validate (Pydantic)
    ↓
Route to Service
    ↓
┌─────────────────────────────┐
│ Business Logic              │
├─────────────────────────────┤
│ • Query Database            │
│ • Call External APIs        │
│ • Process Files             │
│ • Call AI/Groq              │
└─────────────────────────────┘
    ↓
Database Transaction
    ↓
Format Response
    ↓
Return to Frontend
```

---

**Version:** 2.1 (FastAPI Only)  
**Last Updated:** December 2025  
**Architecture Pattern:** Layered + Service-Oriented
