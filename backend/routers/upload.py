from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from pathlib import Path
from schemas.models import FileUploadResponse, OCRResult, InvoiceResponse
from services.file_upload_service import FileUploadService
from core.logging import logger
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter(prefix="/api/upload", tags=["file-upload"])

# Security scheme for extracting token from Authorization header
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependency to get current authenticated user from JWT token in Authorization header"""
    try:
        # Extract token from Authorization header
        token = credentials.credentials
        # Get user service and verify token
        from services.user_service import UserService
        user_service = UserService()
        user_id = user_service.verify_token(token)
        user = await user_service.get_user_by_id(user_id)
        return user
    except Exception as e:
        logger.error(f"Authentication failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_upload_service() -> FileUploadService:
    """Dependency for file upload service"""
    return FileUploadService()


@router.post("/", response_model=dict)
async def upload_file(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user),
    upload_service: FileUploadService = Depends(get_upload_service)
):
    """
    Upload file and process OCR immediately
    
    Args:
        file: File to upload
        current_user: Current authenticated user
        
    Returns:
        InvoiceResponse with extracted invoice data
    """
    try:
        user_id = current_user.id
        
        logger.info(f"File upload and OCR processing started by user {user_id}: {file.filename}")
        
        # Create temporary file path
        import tempfile
        temp_dir = tempfile.gettempdir()
        temp_file = Path(temp_dir) / file.filename
        with open(temp_file, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Upload file and process OCR immediately
        invoice_data = await upload_service.upload_and_process_ocr(user_id, temp_file, file.filename)
        
        logger.info(f"File uploaded and OCR processed successfully: {file.filename}")
        return {"invoice": invoice_data}
        
    except Exception as e:
        logger.error(f"File upload failed for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/ocr/{file_id}", response_model=OCRResult)
async def process_ocr(
    file_id: str,
    current_user = Depends(get_current_user),
    upload_service: FileUploadService = Depends(get_upload_service)
):
    """
    Process file with OCR to extract text
    
    Args:
        file_id: ID of uploaded file
        current_user: Current authenticated user
        
    Returns:
        OCRResult with extracted text and confidence
    """
    try:
        user_id = current_user.id
        logger.info(f"OCR processing started for file {file_id}")
        
        result = await upload_service.process_ocr(file_id, user_id)
        
        logger.info(f"OCR processing completed for file {file_id}")
        return result
        
    except Exception as e:
        logger.error(f"OCR processing failed for file {file_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OCR processing failed"
        )


@router.get("/ocr/{file_id}", response_model=OCRResult)
async def get_ocr_result(
    file_id: str,
    current_user = Depends(get_current_user),
    upload_service: FileUploadService = Depends(get_upload_service)
):
    """
    Get OCR result for uploaded file
    
    Args:
        file_id: ID of uploaded file
        current_user: Current authenticated user
        
    Returns:
        OCRResult with extracted text
    """
    try:
        user_id = current_user.id
        logger.info(f"Retrieving OCR result for file {file_id}")
        
        result = await upload_service.get_ocr_result(file_id, user_id)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"OCR result for file {file_id} not found"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve OCR result: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve OCR result"
        )


@router.delete("/file/{file_id}")
async def delete_file(
    file_id: str,
    user_id: int,
    upload_service: FileUploadService = Depends(get_upload_service)
):
    """
    Delete uploaded file
    
    Args:
        file_id: ID of file to delete
        user_id: ID of user (verify ownership)
    """
    try:
        logger.info(f"Deleting file {file_id} for user {user_id}")
        
        # TODO: Implement delete logic in FileUploadService
        # await upload_service.delete_file(file_id, user_id)
        
        return {"success": True, "message": f"File {file_id} deleted"}
        
    except Exception as e:
        logger.error(f"Failed to delete file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete file"
        )
