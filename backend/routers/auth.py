# API Router: Authentication

from fastapi import APIRouter, Depends, HTTPException, status
from schemas.models import UserCreate, UserResponse, TokenResponse, LoginRequest
from services.user_service import UserService
from core.logging import logger

router = APIRouter(prefix="/api/auth", tags=["authentication"])


async def get_user_service() -> UserService:
    """Dependency for user service"""
    return UserService()


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, user_service: UserService = Depends(get_user_service)):
    """
    Register new user and return JWT token (auto-login after registration)
    
    Args:
        user_data: User registration data (email, name, password)
        
    Returns:
        User response with JWT access token
    """
    try:
        logger.info(f"User registration attempt: {user_data.email}")
        logger.info(f"Registration data: email={user_data.email}, name={user_data.name}, password_length={len(user_data.password)}")
        user = await user_service.create_user(user_data)
        
        # Create JWT token for auto-login with role and is_admin
        access_token = user_service.create_access_token(
            user.id, 
            user_role=user.role if hasattr(user, 'role') else 'user',
            is_admin=user.is_admin if hasattr(user, 'is_admin') else False
        )
        
        logger.info(f"User registered successfully: {user_data.email}")
        
        # Return same format as login for consistency
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": 1800,  # 30 minutes
            "user": user
        }
    except ValueError as e:
        logger.error(f"Validation failed for {user_data.email}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Registration failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login")
async def login(credentials: LoginRequest, user_service: UserService = Depends(get_user_service)):
    """
    Authenticate user and return JWT token
    
    Args:
        credentials: Login credentials (email and password)
        
    Returns:
        JWT access token
    """
    try:
        email = credentials.email
        password = credentials.password
        
        logger.info(f"Login attempt: {email}")
        user = await user_service.authenticate_user(email, password)
        
        if not user:
            logger.warning(f"Failed login attempt: {email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Debug log user object
        logger.info(f"🔍 User object: {user}")
        logger.info(f"🔍 User has role: {hasattr(user, 'role')}, value: {getattr(user, 'role', None)}")
        logger.info(f"🔍 User has is_admin: {hasattr(user, 'is_admin')}, value: {getattr(user, 'is_admin', None)}")
        
        # Create JWT token with role and is_admin
        access_token = user_service.create_access_token(
            user.id,
            user_role=user.role if hasattr(user, 'role') else 'user',
            is_admin=user.is_admin if hasattr(user, 'is_admin') else False
        )
        
        logger.info(f"User logged in successfully: {email}")
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": 1800,  # 30 minutes
            "user": user
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed for {credentials.email}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_token: str, user_service: UserService = Depends(get_user_service)):
    """
    Refresh JWT token
    
    Args:
        refresh_token: Refresh token from previous login
        
    Returns:
        New access token
    """
    try:
        # In production, verify refresh token validity and expiration
        # For now, just issue new token if valid
        user_id = user_service.verify_token(refresh_token)
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Get user to include role in new token
        user = await user_service.get_user_by_id(user_id)
        
        # Create new token with role and is_admin
        access_token = user_service.create_access_token(
            user_id,
            user_role=user.role if hasattr(user, 'role') else 'user',
            is_admin=user.is_admin if hasattr(user, 'is_admin') else False
        )
        logger.info(f"Token refreshed for user: {user_id}")
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=1800
        )
    except Exception as e:
        logger.error(f"Token refresh failed: {str(e)}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.get("/me", response_model=UserResponse)
async def get_current_user(token: str, user_service: UserService = Depends(get_user_service)):
    """
    Get current logged-in user info
    
    Args:
        token: JWT access token from Authorization header
        
    Returns:
        Current user data
    """
    try:
        user_id = user_service.verify_token(token)
        user = await user_service.get_user_by_id(user_id)
        return user
    except Exception as e:
        logger.error(f"Failed to get current user: {str(e)}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
