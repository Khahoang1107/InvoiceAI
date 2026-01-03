"""
🚀 FastAPI Backend - Refactored with Clean Architecture

Enterprise-grade FastAPI application with:
- Service layer architecture
- Dependency injection container
- Exception handling middleware
- Structured logging
- Modular routers
- Type validation with Pydantic

Run: uvicorn main:app --reload --port 8000
Or:  python main.py
"""

# Add current directory to path for imports
import sys
import os
from pathlib import Path
from contextlib import asynccontextmanager

# Ensure the current directory is in Python path
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

# Also add the parent directory if running from backend/ subdirectory
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

# Core imports
from config.settings import settings
from core.logging import logger
from core.dependencies import container
from core.exceptions import APIException

# Middleware imports
from middleware.logging import LoggingMiddleware
from middleware.errors import api_exception_handler, general_exception_handler

# Router imports
from routers import auth, chat, upload, images, export, invoices

# Legacy imports (backward compatibility)
try:
    from auth_api import router as auth_api_router
except ImportError:
    auth_api_router = None

try:
    from admin_api import admin_router as admin_api_router
except ImportError:
    admin_api_router = None


# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage app lifecycle
    
    Startup: Initialize services
    Shutdown: Clean up resources
    """
    # Startup
    logger.info("🚀 Application starting...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info(f"Database: {settings.DATABASE_URL}")
    
    try:
        # Create database tables
        from models.user import Base
        # from models.chat import ChatHistory, UserSession  # Commented out - models not implemented yet
        engine = container.engine
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created")
    except Exception as e:
        logger.warning(f"⚠️ Could not create tables: {str(e)}")
    
    try:
        # Test database connection
        _ = container.db
        logger.info("✅ Database connection established")
    except Exception as e:
        logger.warning(f"⚠️ Database connection failed: {str(e)}")
    
    try:
        # Test Groq client
        groq = container.groq_client
        if groq:
            logger.info("✅ Groq AI client initialized")
        else:
            logger.warning("⚠️ Groq API key not configured")
    except Exception as e:
        logger.warning(f"⚠️ Groq client initialization failed: {str(e)}")
    
    logger.info("✅ Application ready to handle requests")
    
    yield  # App runs here
    
    # Shutdown
    logger.info("🛑 Application shutting down...")
    container.close()
    logger.info("✅ Resources cleaned up")


# Create FastAPI app with lifespan
app = FastAPI(
    title="ChatBotAI API",
    description="Enterprise chat and OCR backend",
    version="2.0.0",
    lifespan=lifespan
)

# Middleware configuration
logger.info("Configuring middleware...")

# Add logging middleware
app.add_middleware(LoggingMiddleware)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

logger.info("✅ Middleware configured")

# Exception handlers
app.add_exception_handler(APIException, api_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Add validation error handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """Handle validation errors with detailed messages"""
    errors = []
    for error in exc.errors():
        field = ".".join(str(x) for x in error["loc"][1:])
        message = error["msg"]
        errors.append(f"{field}: {message}")
    
    logger.error(f"Validation error: {'; '.join(errors)}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": errors,
            "error_type": "validation_error"
        }
    )

logger.info("✅ Exception handlers registered")


# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """API root endpoint"""
    return {
        "message": "ChatBotAI API v2.0",
        "status": "running",
        "version": "2.0.0",
        "docs": "/docs",
        "environment": settings.ENVIRONMENT
    }


# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {}
    }
    
    # Check database
    try:
        db = container.db
        health_status["services"]["database"] = "connected"
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        health_status["services"]["database"] = "disconnected"
    
    # Check Groq
    try:
        groq = container.groq_client
        health_status["services"]["groq"] = "available" if groq else "not_configured"
    except Exception as e:
        logger.error(f"Groq health check failed: {str(e)}")
        health_status["services"]["groq"] = "unavailable"
    
    # Return degraded service if critical services down
    if health_status["services"].get("database") == "disconnected":
        health_status["status"] = "degraded"
        return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=health_status)
    
    return health_status


# Register routers (new architecture)
logger.info("Registering API routers...")

# New modular routers - no prefix since routers already have /api/auth, /api/chat, etc.
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(upload.router)
app.include_router(images.router)
app.include_router(export.router)
app.include_router(invoices.router)

logger.info("✅ API routers registered")

# Legacy routers (backward compatibility)
if auth_api_router:
    app.include_router(auth_api_router)
    logger.info("✅ Legacy auth_api router registered")

if admin_api_router:
    app.include_router(admin_api_router, prefix="/api")
    logger.info("✅ Legacy admin_api router registered")


# Run application
if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting server on http://0.0.0.0:{settings.PORT}")
    
    # Disable reload to avoid Python 3.14 multiprocessing bug
    uvicorn.run(
        "main_refactored:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=False,  # Temporarily disabled for Python 3.14 compatibility
        log_level="info"
    )
