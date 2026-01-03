from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from config.settings import settings

# JWT Configuration
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

# Password hashing - Hỗ trợ cả bcrypt và Argon2
import bcrypt
try:
    from argon2 import PasswordHasher
    from argon2.exceptions import VerifyMismatchError
    argon2_hasher = PasswordHasher()
    HAS_ARGON2 = True
except ImportError:
    HAS_ARGON2 = False

# Security scheme
security = HTTPBearer()

class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[int] = None
    role: Optional[str] = None
    is_admin: Optional[bool] = None

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password - support both bcrypt (old users) and Argon2 (new users)."""
    # Check if it's bcrypt hash (starts with $2a$, $2b$, or $2y$)
    if hashed_password.startswith(('$2a$', '$2b$', '$2y$')):
        try:
            return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
        except Exception:
            return False
    
    # Try Argon2 if available
    if HAS_ARGON2:
        try:
            argon2_hasher.verify(hashed_password, plain_password)
            return True
        except VerifyMismatchError:
            return False
    
    return False

def get_password_hash(password: str) -> str:
    """Hash password - use Argon2 if available, otherwise bcrypt."""
    if HAS_ARGON2:
        return argon2_hasher.hash(password)
    else:
        # Truncate to 72 bytes for bcrypt
        password_bytes = password.encode('utf-8')[:72]
        return bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> TokenData:
    """Verify and decode JWT token."""
    try:
        print(f"🔍 Verifying token with SECRET_KEY: {SECRET_KEY[:10]}...")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print(f"✅ Token decoded successfully: {payload}")
        username: str = payload.get("sub")
        # Try user_id first, fallback to sub for user_id
        user_id: int = payload.get("user_id") or (int(username) if username and username.isdigit() else None)
        role: str = payload.get("role")
        is_admin: bool = payload.get("is_admin", False)
        print(f"📋 Extracted: username={username}, user_id={user_id}, role={role}, is_admin={is_admin}")
        if username is None:
            print("❌ Username is None")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return TokenData(username=username, user_id=user_id, role=role, is_admin=is_admin)
    except JWTError as e:
        print(f"❌ JWT Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> TokenData:
    """Dependency to get current authenticated user."""
    return verify_token(credentials.credentials)

async def get_current_admin_user(current_user: TokenData = Depends(get_current_user)) -> TokenData:
    """Dependency to get current authenticated admin user."""
    if not (current_user.role == "admin" or current_user.is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Admin access required.",
        )
    return current_user

async def get_current_user_or_admin(current_user: TokenData = Depends(get_current_user)) -> TokenData:
    """Dependency to get current user (any role)."""
    return current_user