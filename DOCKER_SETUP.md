# 🐳 Docker Setup Guide - InvoiceAI

## 📋 Prerequisites

1. **Docker Desktop** installed and running
2. **Docker Compose** (included with Docker Desktop)

## 🚀 Quick Start

### 1. Setup Environment Variables

```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your API keys
# Minimum required: GROQ_API_KEY
```

### 2. Start All Services

```bash
# Build and start all containers
docker-compose up -d --build

# View logs
docker-compose logs -f
```

### 3. Access Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **PostgreSQL**: localhost:5432

## 🛠️ Docker Commands

### Basic Operations

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Rebuild containers
docker-compose up -d --build

# View logs
docker-compose logs -f [service_name]

# Restart specific service
docker-compose restart backend
docker-compose restart frontend
```

### Database Operations

```bash
# Access PostgreSQL
docker exec -it invoice_postgres psql -U postgres -d invoice_db

# Backup database
docker exec invoice_postgres pg_dump -U postgres invoice_db > backup.sql

# Restore database
cat backup.sql | docker exec -i invoice_postgres psql -U postgres invoice_db
```

### Debugging

```bash
# Check container status
docker ps

# Enter container shell
docker exec -it invoice_backend /bin/bash
docker exec -it chatbot_frontend /bin/sh

# View container logs
docker logs invoice_backend
docker logs chatbot_frontend
docker logs invoice_postgres

# Check container resources
docker stats
```

## 📦 Services Architecture

### 1. PostgreSQL Database
- **Container**: `invoice_postgres`
- **Image**: `postgres:15-alpine`
- **Port**: 5432
- **Volume**: `postgres_data` (persistent storage)

### 2. Backend API (Python 3.12)
- **Container**: `invoice_backend`
- **Image**: Custom (built from Dockerfile)
- **Port**: 8000
- **Features**:
  - FastAPI REST API
  - OCR with Tesseract + Vietnamese
  - NER (Named Entity Recognition) with spaCy
  - Groq AI integration
  - Vector database (Pinecone)
- **Volumes**:
  - `./backend:/app` (hot reload in dev)
  - `backend_uploads:/app/uploads` (persistent uploads)

### 3. Frontend (React + Vite)
- **Container**: `chatbot_frontend`
- **Image**: Custom (multi-stage build)
- **Port**: 3000 (mapped to internal 80)
- **Web Server**: Nginx
- **Build**: Optimized production build

## 🔧 Configuration

### Backend Environment Variables

Required:
- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: JWT token secret
- `GROQ_API_KEY`: Groq AI API key

Optional:
- `PINECONE_API_KEY`: Vector database
- `GOOGLE_AI_API_KEY`: Google AI services

### Frontend Environment Variables

- `VITE_API_URL`: Backend API URL (default: http://backend:8000)
- `NODE_ENV`: Environment mode

## 🔄 Development vs Production

### Development Mode (Hot Reload)

```yaml
# docker-compose.override.yml
services:
  backend:
    volumes:
      - ./backend:/app  # Enable hot reload
    environment:
      - DEBUG=true
      - LOG_LEVEL=DEBUG
```

### Production Mode

```bash
# Remove development overrides
docker-compose -f docker-compose.yml up -d --build
```

## 🧹 Cleanup

```bash
# Stop and remove containers
docker-compose down

# Remove containers + volumes (WARNING: deletes data!)
docker-compose down -v

# Remove images
docker-compose down --rmi all

# Clean up everything
docker system prune -a --volumes
```

## 🐛 Troubleshooting

### Backend won't start
```bash
# Check logs
docker-compose logs backend

# Common issues:
# - Missing GROQ_API_KEY
# - Database connection failed
# - Port 8000 already in use
```

### Frontend build fails
```bash
# Check logs
docker-compose logs frontend

# Common issues:
# - Node version incompatibility
# - Missing dependencies
# - Build errors in source code
```

### Database connection issues
```bash
# Check postgres is healthy
docker-compose ps postgres

# Test connection
docker exec invoice_backend python -c "from utils.database_tools_postgres import DatabaseToolsPostgres; db = DatabaseToolsPostgres(); print('Connected!')"
```

## 📊 Performance

- **Backend startup**: ~15-30 seconds (includes NER model training)
- **Frontend build**: ~2-3 minutes
- **Database init**: ~5 seconds

## 🔐 Security Notes

1. **Change default passwords** in production
2. **Use secrets management** for API keys
3. **Enable HTTPS** with reverse proxy (nginx/traefik)
4. **Restrict database access** to backend network only
5. **Update base images** regularly

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Reference](https://docs.docker.com/compose/compose-file/)
- [FastAPI in Docker](https://fastapi.tiangolo.com/deployment/docker/)
