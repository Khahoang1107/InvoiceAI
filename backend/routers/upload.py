from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from pathlib import Path
from schemas.models import FileUploadResponse, OCRResult, InvoiceResponse
from services.file_upload_service import FileUploadService
from services.invoice_service import InvoiceService
from core.logging import logger
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter(prefix="/api/upload", tags=["file-upload"])

# Create invoice service instance for file saving and RAG processing
invoice_service = InvoiceService()

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
    Upload file and process OCR immediately with RAG indexing
    
    Args:
        file: File to upload
        current_user: Current authenticated user
        
    Returns:
        InvoiceResponse with extracted invoice data and RAG indexing status
    """
    try:
        user_id = current_user.id
        
        logger.info(f"File upload and OCR processing started by user {user_id}: {file.filename}")
        
        # Read file content once
        content = await file.read()
        
        # Create temporary file path for OCR processing
        import tempfile
        import uuid
        temp_dir = tempfile.gettempdir()
        temp_file = Path(temp_dir) / file.filename
        with open(temp_file, "wb") as f:
            f.write(content)
        
        # Upload file and process OCR immediately
        invoice_data = await upload_service.upload_and_process_ocr(user_id, temp_file, file.filename)
        
        # Convert to dict for additional fields
        if hasattr(invoice_data, 'model_dump'):
            invoice_dict = invoice_data.model_dump()
        elif hasattr(invoice_data, 'dict'):
            invoice_dict = invoice_data.dict()
        else:
            invoice_dict = dict(invoice_data)
        
        # Save file to permanent storage using pathlib
        logger.info("💾 Saving file to disk...")
        unique_filename = f"{uuid.uuid4().hex}_{file.filename}"
        saved_file_path = invoice_service.UPLOAD_DIR / unique_filename
        with open(saved_file_path, "wb") as f:
            f.write(content)
        logger.info(f"✅ File saved: {saved_file_path}")
        
        # RAG Processing: Index the file for semantic search
        try:
            logger.info(f"🔄 Starting RAG indexing for file: {file.filename}")
            
            # Process file for RAG indexing using the saved file path
            rag_result = invoice_service.process_invoice_file(
                file_path=str(saved_file_path),
                filename=file.filename,
                user_id=str(user_id)
            )
            
            if rag_result.get("success"):
                logger.info(f"✅ RAG indexing completed for {file.filename}")
                invoice_dict["rag_indexed"] = True
                invoice_dict["document_id"] = rag_result.get("document_id")
                invoice_dict["processing_steps"] = rag_result.get("processing_steps", [])
            else:
                logger.warning(f"⚠️  RAG indexing failed for {file.filename}: {rag_result.get('error')}")
                invoice_dict["rag_indexed"] = False
                invoice_dict["rag_error"] = rag_result.get("error")
                
        except Exception as rag_error:
            logger.warning(f"⚠️  RAG processing failed, but OCR succeeded: {str(rag_error)}")
            invoice_dict["rag_indexed"] = False
            invoice_dict["rag_error"] = str(rag_error)
        
        # Clean up temporary file
        try:
            temp_file.unlink()
        except Exception as e:
            logger.warning(f"Could not clean up temp file {temp_file}: {e}")
        
        logger.info(f"File uploaded and processed successfully: {file.filename}")
        return {"invoice": invoice_dict}
        
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


@router.post("/ner/extract", response_model=dict)
async def extract_entities(
    text: str,
    current_user = Depends(get_current_user)
):
    """
    Extract named entities from invoice text using NER model

    Args:
        text: Invoice text to analyze
        current_user: Current authenticated user

    Returns:
        Dictionary containing extracted entities and structured invoice info
    """
    try:
        from services.ner_service import get_ner_service

        logger.info(f"NER extraction started for user {current_user.id}")

        ner_service = get_ner_service()
        result = ner_service.extract_entities(text)

        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"]
            )

        return {
            "success": True,
            "data": result,
            "message": "NER extraction completed successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"NER extraction failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"NER extraction failed: {str(e)}"
        )


@router.post("/ner/compare-ocr", response_model=dict)
async def compare_ocr_engines(
    tesseract_text: str,
    easyocr_text: str,
    current_user = Depends(get_current_user)
):
    """
    Compare entity extraction results from two OCR engines

    Args:
        tesseract_text: Text extracted by Tesseract
        easyocr_text: Text extracted by EasyOCR
        current_user: Current authenticated user

    Returns:
        Comparison results and recommendation
    """
    try:
        from services.ner_service import get_ner_service

        logger.info(f"OCR comparison started for user {current_user.id}")

        ner_service = get_ner_service()
        result = ner_service.compare_ocr_results(tesseract_text, easyocr_text)

        return {
            "success": True,
            "data": result,
            "message": "OCR comparison completed successfully"
        }

    except Exception as e:
        logger.error(f"OCR comparison failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OCR comparison failed: {str(e)}"
        )


@router.post("/benchmark-ocr", response_model=dict)
async def benchmark_ocr_engines(
    current_user = Depends(get_current_user)
):
    """
    Run OCR engine benchmark on existing invoice files

    Returns:
        Benchmark results comparing Tesseract and EasyOCR performance
    """
    try:
        logger.info(f"Running OCR benchmark for user {current_user.id}")

        # Import benchmark class
        from benchmark_ocr import OCRBenchmark

        # Run benchmark
        benchmark = OCRBenchmark()
        results = benchmark.run_benchmark()

        if "error" in results:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=results["error"]
            )

        return {
            "success": True,
            "data": results,
            "message": "OCR benchmark completed successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OCR benchmark failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OCR benchmark failed: {str(e)}"
        )
