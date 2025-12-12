# 🚀 Invoice Management System with AI Chatbot

Hệ thống quản lý hóa đơn thông minh với AI chatbot tích hợp, được thiết kế đơn giản và hiệu quả.

## ⭐ Version 2.1 - FastAPI Only

**🎉 Update:** Flask removed! All services now run on **FastAPI:8000**

- ✅ Unified single service (no more port 5001)
- ✅ Better performance (+50% faster)
- ✅ Interactive API docs at `/docs`
- ✅ See `MIGRATION_SUMMARY.md` for details

## ✨ Tính năng chính

- 📄 **Quản lý hóa đơn**: CRUD hoàn chình với search và filter
- 🤖 **AI Chatbot**: Trợ lý AI (Groq LLM) phân tích hóa đơn
- 🔍 **OCR Processing**: Tesseract xử lý hình ảnh, trích xuất dữ liệu tự động (ASYNC)
- 📊 **Analytics**: Dashboard với thống kê và báo cáo
- 🎨 **Modern UI**: Giao diện đẹp với React + Tailwind CSS
- 🔐 **Authentication**: JWT-based security system
- ⚡ **Async OCR**: Upload return in 50ms, processing in background

## 🏗️ Kiến trúc hệ thống (v2.1)

```
┌──────────────────────────────────────────────────┐
│   Frontend (React)  :3000                        │
└─────────────────────┬──────────────────────────┘
                      │
┌─────────────────────▼──────────────────────────┐
│   FastAPI Backend (Unified) :8000 ✨           │
│   ├─ /api/auth (JWT Authentication)            │
│   ├─ /api/chat (Groq LLM)                      │
│   ├─ /api/upload (async OCR + DB storage)     │
│   ├─ /api/images/{id} (serve stored images)   │
│   ├─ /api/invoices (CRUD)                      │
│   ├─ /api/export (Excel/PDF/CSV export)       │
│   └─ /docs (Swagger UI)                        │
└─────────────────────┬──────────────────────────┘
                      │
        ┌─────────────┴──────────────┐
        │                            │
        ▼                            ▼
  PostgreSQL DB            OCR Worker (Python)
  (Railway Cloud)          (background processing)
```

## 🚀 Khởi động nhanh

### Local Development (Recommended)

```bash
# Terminal 1: Start FastAPI Backend
cd backend
python main_refactored.py

# Terminal 2: Start Frontend
cd frontend
npm run dev

# Access:
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
# Health Check: http://localhost:8000/health
```

## 📋 API Documentation

Hệ thống cung cấp RESTful API hoàn chỉnh:

- 📖 **Interactive Docs**: http://localhost:8000/docs (Swagger UI)
- 🩺 **Health Check**: http://localhost:8000/health
- 📄 **Full API List**: Xem [API_DOCUMENTATION.md](./API_DOCUMENTATION.md)
- 📚 **Migration Guide**: [FLASK_TO_FASTAPI_MIGRATION.md](./FLASK_TO_FASTAPI_MIGRATION.md)

### Main Endpoints:

```bash
# Authentication
POST   /api/auth/register          # Register new user
POST   /api/auth/login             # Login and get JWT token
GET    /api/auth/me                # Get current user info

# Chat & AI
POST   /api/chat                   # Chat with Groq AI

# Upload & OCR (Async)
POST   /api/upload                 # Upload invoice (OCR processing + DB storage)
GET    /api/images/{image_id}      # Get stored image from database

# Invoices Management
GET    /api/invoices               # List invoices
POST   /api/invoices               # Create invoice
GET    /api/invoices/{id}          # Get invoice details
PUT    /api/invoices/{id}          # Update invoice
DELETE /api/invoices/{id}          # Delete invoice

# Export
GET    /api/export/invoices        # Export invoices (Excel/PDF/CSV)

# System
GET    /health                     # Health check
GET    /                           # API Home + Docs
GET    /docs                       # Swagger UI
```

## 🛠️ Cấu hình môi trường

Tạo file `.env` từ template:

```bash
# Database Configuration
DATABASE_URL=postgresql://user:password@host:port/database
# Or for SQLite (development): DATABASE_URL=sqlite:///./chatbot.db

# Security
JWT_SECRET_KEY=your-super-secret-key-change-this-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# AI Configuration
GROQ_API_KEY=your_groq_api_key_here
GOOGLE_AI_API_KEY=your_google_ai_key_here

# Application
DEBUG=True
ENVIRONMENT=development
PORT=8000

# CORS Origins
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

## 📁 Cấu trúc dự án

```
ChatBotAI/
├── 📁 backend/              # FastAPI Backend
│   ├── main_refactored.py   # Main FastAPI application
│   ├── main.py              # Alternative main file
│   ├── config/              # Configuration modules
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Pydantic schemas
│   ├── routers/             # API route handlers
│   ├── services/            # Business logic services
│   ├── core/                # Core utilities
│   ├── utils/               # Helper utilities
│   ├── requirements.txt     # Python dependencies
│   └── Dockerfile           # Docker configuration
├── 📁 frontend/             # React Frontend
│   ├── src/                 # Source code
│   │   ├── components/      # React components
│   │   ├── pages/           # Page components
│   │   ├── services/        # API services
│   │   └── types/           # TypeScript types
│   ├── package.json         # Node dependencies
│   ├── vite.config.ts       # Vite configuration
│   └── Dockerfile           # Docker configuration
├── 📁 docs/                 # Documentation
│   ├── README.md            # Documentation index
│   ├── *.md                 # Various guides and reports
├── 📁 scripts/              # Utility scripts
├── docker-compose.yml       # Docker orchestration
├── .env.example             # Environment variables template
└── README.md                # This file
```

## 🧪 Testing

```bash
# Health checks
curl http://localhost:8000/health
curl http://localhost:8000/

# API Documentation
open http://localhost:8000/docs

# Frontend
open http://localhost:3000
```

## 🔧 Development

### Backend Development

```bash
cd backend
# Activate virtual environment (if using venv)
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run backend
python main_refactored.py
```

### Frontend Development

```bash
cd frontend
npm install
npm run dev
```
npm run dev
```

### Chatbot Development

```bash
cd chatbot
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

## 📊 Monitoring & Logging

- **Logs**: Xem logs trong console mỗi service
- **Health Checks**: Tự động health check cho tất cả services
- **Database**: PostgreSQL với automatic migrations

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- OpenAI for GPT models
- Flask & React communities
- All open source contributors

---

**Made with ❤️ by Invoice AI Team**
