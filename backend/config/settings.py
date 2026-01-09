# ChatBotAI - Enterprise Configuration Management

from pydantic_settings import BaseSettings
from typing import List, Optional
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # API
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "ChatBotAI"
    PROJECT_VERSION: str = "2.0.0"
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost/chatbotai")
    DATABASE_ECHO: bool = False
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", os.getenv("SECRET_KEY", "your-secret-key-change-in-production"))
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
    ]
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 60  # seconds
    
    # Groq AI
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")  # Current working model
    
    # Google AI
    GOOGLE_AI_API_KEY: str = os.getenv("GOOGLE_AI_API_KEY", "")
    
    # Pinecone Vector Database
    PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY", "")
    PINECONE_ENVIRONMENT: str = os.getenv("PINECONE_ENVIRONMENT", "gcp-starter")
    PINECONE_INDEX_NAME: str = os.getenv("PINECONE_INDEX_NAME", "invoiceai-vectors")
    
    # UBIAI Configuration (Optional)
    UBIAI_API_KEY: str = os.getenv("UBIAI_API_KEY", "")
    UBIAI_PROJECT_ID: str = os.getenv("UBIAI_PROJECT_ID", "")
    
    # OCR Configuration
    TESSERACT_CMD: str = os.getenv("TESSERACT_CMD", "tesseract")
    
    # File Upload
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: List[str] = ["jpg", "jpeg", "png", "pdf"]
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = "logs/chatbot.log"
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = ENVIRONMENT == "development"
    PORT: int = 8000
    
    # Backend/Frontend URLs
    BACKEND_URL: str = os.getenv("BACKEND_URL", "http://localhost:8000")
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
