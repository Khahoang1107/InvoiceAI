# 🚀 Invoice Management System with AI Chatbot

Hệ thống quản lý hóa đơn thông minh với AI chatbot tích hợp, được thiết kế đơn giản và hiệu quả.

> ⚠️ **Important:** For full NER (Named Entity Recognition) support, use Python 3.12. See [PYTHON312_SETUP.md](PYTHON312_SETUP.md)

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

## � Railway Cloud Deployment

Hệ thống được tối ưu hóa để deploy lên [Railway](https://railway.app) - một platform cloud đơn giản và mạnh mẽ.

### 📋 Yêu cầu chuẩn bị

1. **Railway Account**: Đăng ký tại [railway.app](https://railway.app)
2. **API Keys**:
   - [Groq API Key](https://console.groq.com) - cho AI chatbot
   - [Pinecone API Key](https://pinecone.io) - cho vector database
   - [Google AI API Key](https://makersuite.google.com/app/apikey) - optional

### 🚀 Các bước deploy

#### 1. Push code lên GitHub

```bash
git add .
git commit -m "Ready for Railway deployment"
git push origin main
```

#### 2. Deploy trên Railway

1. Truy cập [Railway Dashboard](https://railway.app/dashboard)
2. Click **"New Project"** → **"Deploy from GitHub"**
3. Chọn repository của bạn
4. Railway sẽ tự động detect Python app và cài dependencies

#### 3. Cấu hình Environment Variables

Trong Railway project settings → **Variables**:

```bash
# Database (Railway sẽ tự tạo PostgreSQL)
DATABASE_URL=${{Postgres.DATABASE_URL}}

# Security
SECRET_KEY=your-super-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AI Services
GROQ_API_KEY=your_groq_api_key_here
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_ENVIRONMENT=gcp-starter
GOOGLE_AI_API_KEY=your_google_ai_key_here

# File Upload
UPLOAD_DIR=uploads
MAX_FILE_SIZE=10485760
ALLOWED_EXTENSIONS=["jpg","jpeg","png","pdf"]

# Application
DEBUG=False
ENVIRONMENT=production
```

#### 4. Thêm PostgreSQL Database

- Trong Railway project → **"Add Plugin"** → **PostgreSQL**
- Railway sẽ tự động cấu hình `DATABASE_URL`

#### 5. Truy cập ứng dụng

- **Frontend**: `https://your-project-name.up.railway.app`
- **Backend API**: `https://your-project-name.up.railway.app/docs`

### 📁 Files cần thiết cho Railway

```
InvoiceAI/
├── Procfile              # Railway startup command
├── runtime.txt          # Python version
├── requirements.txt     # Python dependencies
├── .env.example         # Environment template
├── backend/
│   ├── main.py         # FastAPI app
│   └── ...            # Other backend files
└── README.md
```

### 🔧 Troubleshooting

**Build fails**:
- Check `requirements.txt` có đủ dependencies
- Đảm bảo tất cả packages được list đúng version
- Xem Railway build logs để debug

**Runtime errors**:
- Verify environment variables được set
- Check database connectivity
- Review application logs trong Railway dashboard

**Memory issues**:
- EasyOCR và Sentence Transformers cần nhiều RAM
- Consider upgrade Railway plan cho ML workloads

### 🧪 Pre-deployment Testing

Chạy test script để kiểm tra trước khi deploy:

```bash
python test_deployment.py
```

## �🔧 Development

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

## 🚀 Railway Deployment

### Prerequisites

1. **Railway Account**: [Sign up at railway.app](https://railway.app)
2. **API Keys**:
   - Groq API Key: [console.groq.com](https://console.groq.com)
   - Pinecone API Key: [pinecone.io](https://pinecone.io)
   - Google AI API Key (optional): [makersuite.google.com](https://makersuite.google.com/app/apikey)

### Deploy Steps

1. **Connect Repository**:
   ```bash
   # Push code to GitHub first
   git add .
   git commit -m "Ready for Railway deployment"
   git push origin main
   ```

2. **Deploy on Railway**:
   - Go to [Railway Dashboard](https://railway.app/dashboard)
   - Click "New Project" → "Deploy from GitHub"
   - Select your repository
   - Railway will auto-detect Python app and install dependencies

3. **Configure Environment Variables**:
   ```bash
   # In Railway project settings → Variables
   DATABASE_URL=${{Postgres.DATABASE_URL}}
   SECRET_KEY=your-super-secret-key-change-this
   GROQ_API_KEY=your_groq_api_key_here
   PINECONE_API_KEY=your_pinecone_api_key_here
   PINECONE_ENVIRONMENT=gcp-starter
   GOOGLE_AI_API_KEY=your_google_ai_key_here
   ```

4. **Add PostgreSQL Database**:
   - In Railway project → "Add Plugin" → PostgreSQL
   - Railway will auto-configure DATABASE_URL

5. **Access Your App**:
   - Frontend: `https://your-project-name.up.railway.app`
   - Backend API: `https://your-project-name.up.railway.app/docs`

### File Structure for Deployment

```
InvoiceAI/
├── Procfile              # Railway startup command
├── runtime.txt          # Python version specification
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variables template
├── backend/
│   ├── main.py         # FastAPI application
│   └── ...            # Other backend files
├── frontend/
│   ├── build/         # Built React app (auto-generated)
│   └── ...           # React source files
└── README.md
```

### Troubleshooting

**Build Fails**:
- Check `requirements.txt` for correct package versions
- Ensure all dependencies are listed
- Check Railway build logs for specific errors

**Runtime Errors**:
- Verify all environment variables are set
- Check database connectivity
- Review application logs in Railway dashboard

**Memory Issues**:
- EasyOCR and Sentence Transformers require significant RAM
- Consider Railway's higher-tier plans for ML workloads

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
