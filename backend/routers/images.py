# Images API Router
# Serve images stored in database

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from ..utils.database_tools_postgres import get_database_tools
from ..core.logging import logger
import io

router = APIRouter(prefix="/api", tags=["images"])

# Security scheme for extracting token from Authorization header
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependency to get current authenticated user from JWT token in Authorization header"""
    try:
        # Extract token from Authorization header
        token = credentials.credentials
        # Get user service and verify token
        from ..services.user_service import UserService
        user_service = UserService()
        user_data = user_service.verify_token(token)
        return user_data
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

# Lazy database initialization
def get_db():
    return get_database_tools()

db = None

@router.get("/images/{image_id}")
async def get_image(image_id: int, current_user: dict = Depends(get_current_user)):
    """
    Serve image from database by ID
    
    Args:
        image_id: Image ID in database
        current_user: Authenticated user
        
    Returns:
        StreamingResponse with image data
    """
    try:
        # Lazy database initialization
        global db
        if db is None:
            db = get_db()
        
        # Get image from database
        image_data = db.get_image(image_id)
        
        if not image_data:
            raise HTTPException(status_code=404, detail="Image not found")
        
        # Check if user owns this image (if user_id is set)
        if image_data.get('user_id') and image_data['user_id'] != current_user['id']:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Create streaming response with image data
        image_bytes = image_data['file_data']
        mime_type = image_data['mime_type']
        
        def iter_image():
            yield image_bytes
        
        logger.info(f"✅ Serving image {image_id} ({len(image_bytes)} bytes, {mime_type})")
        
        return StreamingResponse(
            iter_image(),
            media_type=mime_type,
            headers={"Content-Length": str(len(image_bytes))}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to serve image {image_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")