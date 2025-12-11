# Simple Mock Authentication API (No Database Required)

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timedelta
import jwt
import bcrypt

router = APIRouter(prefix="/auth", tags=["authentication"])

# Mock user storage (in-memory)
MOCK_USERS = {}

# JWT Secret (use environment variable in production)
SECRET_KEY = "your-secret-key-change-this-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


# Request/Response Models
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class UserResponse(BaseModel):
    email: str
    name: Optional[str]
    role: str = "user"


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister):
    """
    Register new user - saves to database
    """
    # Get database tools (PostgreSQL or SQLite based on .env)
    import os
    database_url = os.getenv('DATABASE_URL', '')
    
    if database_url and not database_url.startswith('sqlite'):
        from utils.database_tools_postgres import get_database_tools
    else:
        from utils.database_tools_sqlite import get_database_tools
    
    db_tools = get_database_tools()
    
    # Check if user exists
    existing_user = db_tools.get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password
    password_bytes = user_data.password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
    
    # Determine role
    role = "admin" if "admin" in user_data.email.lower() else "user"
    
    # Save user to database
    user_id = db_tools.save_user({
        "email": user_data.email,
        "name": user_data.name or user_data.email.split("@")[0],
        "hashed_password": hashed_password,
        "role": role,
        "is_active": 1,
        "is_admin": 1 if role == "admin" else 0
    })
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )
    
    # Create token
    access_token = create_access_token(
        data={
            "sub": user_data.email,
            "role": role
        }
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "email": user_data.email,
            "name": user_data.name or user_data.email.split("@")[0],
            "role": role
        }
    }


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    """
    Login user - authenticates against database
    """
    # Get database tools (PostgreSQL or SQLite based on .env)
    import os
    database_url = os.getenv('DATABASE_URL', '')
    
    if database_url and not database_url.startswith('sqlite'):
        from utils.database_tools_postgres import get_database_tools
    else:
        from utils.database_tools_sqlite import get_database_tools
    
    db_tools = get_database_tools()
    
    # Check if user exists
    user = db_tools.get_user_by_email(credentials.email)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify password
    password_bytes = credentials.password.encode('utf-8')
    hashed_bytes = user["hashed_password"].encode('utf-8')
    if not bcrypt.checkpw(password_bytes, hashed_bytes):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Update last login
    db_tools.update_user_last_login(credentials.email)
    
    # Create token
    access_token = create_access_token(
        data={
            "sub": credentials.email,
            "role": user["role"]
        }
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "email": user["email"],
            "name": user["name"],
            "role": user["role"]
        }
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user(token: str):
    """
    Get current user from token
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        
        if email is None or email not in MOCK_USERS:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        user = MOCK_USERS[email]
        return {
            "email": user["email"],
            "name": user["name"],
            "role": user["role"]
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


# Health check
@router.get("/health")
async def health_check():
    """Check auth service health"""
    return {
        "status": "healthy",
        "users_count": len(MOCK_USERS),
        "timestamp": datetime.utcnow().isoformat()
    }
