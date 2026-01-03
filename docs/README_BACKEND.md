# ChatBotAI Backend

FastAPI backend for ChatBotAI application with AI chat, OCR processing, and invoice management.

## 🚀 Quick Start

```bash
cd backend
python main_refactored.py
```

## 📋 Features

- **Authentication**: JWT-based user authentication
- **AI Chat**: Integration with Groq LLM for intelligent conversations
- **OCR Processing**: Tesseract-based text extraction from images
- **Invoice Management**: Full CRUD operations for invoices
- **Image Storage**: Database BLOB storage for uploaded images
- **Export**: Excel/PDF/CSV export functionality

## 🏗️ Architecture

```
backend/
├── main_refactored.py     # Main FastAPI application
├── config/               # Configuration settings
├── models/               # SQLAlchemy database models
├── schemas/              # Pydantic request/response schemas
├── routers/              # API route handlers
├── services/             # Business logic services
├── core/                 # Core utilities and middleware
├── utils/                # Helper utilities
└── requirements.txt      # Python dependencies
```

## 🔧 API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get JWT token
- `GET /api/auth/me` - Get current user info

### Chat
- `POST /api/chat` - Chat with AI assistant

### File Upload & OCR
- `POST /api/upload` - Upload invoice with OCR processing
- `GET /api/images/{image_id}` - Retrieve stored images

### Invoices
- `GET /api/invoices` - List invoices
- `POST /api/invoices` - Create invoice
- `GET /api/invoices/{id}` - Get invoice details
- `PUT /api/invoices/{id}` - Update invoice
- `DELETE /api/invoices/{id}` - Delete invoice

### Export
- `GET /api/export/invoices` - Export invoices in various formats

## 🛠️ Development

### Prerequisites
- Python 3.10+
- PostgreSQL (or SQLite for development)

### Setup
```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Run database migrations (if using PostgreSQL)
alembic upgrade head

# Start server
python main_refactored.py
```

### Environment Variables
```env
DATABASE_URL=postgresql://user:password@host:port/database
JWT_SECRET_KEY=your-secret-key
GROQ_API_KEY=your-groq-api-key
DEBUG=True
```

## 📚 Documentation

- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **Health Check**: http://localhost:8000/health
- **Root**: http://localhost:8000/

## 🧪 Testing

```bash
# Run health check
curl http://localhost:8000/health

# Test API endpoints
curl http://localhost:8000/docs
```</content>
<parameter name="filePath">c:\Users\Administrator\Downloads\ChatBotAI\backend\README.md