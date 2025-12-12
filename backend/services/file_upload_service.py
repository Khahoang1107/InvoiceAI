# Service Layer: File Upload and OCR Processing

from typing import Optional, Tuple
from pathlib import Path
from datetime import datetime
import mimetypes
from core.exceptions import (
    ValidationException,
    ExternalServiceException,
    DatabaseException
)
from core.dependencies import container
from schemas.models import FileUploadResponse, OCRResult, InvoiceResponse
from core.logging import logger
from utils.database_tools_postgres import get_database_tools


class FileUploadService:
    """Handle file uploads and OCR processing"""
    
    def __init__(self):
        self.db = get_database_tools()
        self.settings = container.settings
        self.upload_dir = Path("uploads")
        self.upload_dir.mkdir(exist_ok=True)
        
        # Debug settings
        logger.info(f"Settings MAX_FILE_SIZE: {self.settings.MAX_FILE_SIZE}")
        logger.info(f"Settings ALLOWED_EXTENSIONS: {self.settings.ALLOWED_EXTENSIONS}")
    
    async def upload_file(self, user_id: int, file_path: Path, filename: str) -> FileUploadResponse:
        """
        Upload file and validate
        
        Args:
            user_id: ID of user uploading file
            file_path: Path to uploaded file
            filename: Original filename
            
        Returns:
            FileUploadResponse with file metadata
            
        Raises:
            ValidationException: If file validation fails
            DatabaseException: If database operation fails
        """
        try:
            # Validate file
            self._validate_file(file_path, filename)
            
            # Get file size
            file_size = file_path.stat().st_size
            
            # Generate unique file ID
            file_id = f"{user_id}_{int(datetime.utcnow().timestamp())}"
            
            # Store file in upload directory
            upload_path = self.upload_dir / f"{file_id}_{filename}"
            file_path.rename(upload_path)
            
            # Store metadata in database
            # file_record = UploadedFile(
            #     user_id=user_id,
            #     file_id=file_id,
            #     filename=filename,
            #     file_size=file_size,
            #     file_path=str(upload_path),
            #     upload_at=datetime.utcnow()
            # )
            # self.db.add(file_record)
            # self.db.commit()
            
            return FileUploadResponse(
                file_id=file_id,
                filename=filename,
                file_size=file_size,
                upload_at=datetime.utcnow()
            )
            
        except ValidationException:
            raise
        except Exception as e:
            raise DatabaseException(f"File upload failed: {str(e)}")
    
    async def upload_and_process_ocr(self, user_id: int, file_path: Path, filename: str) -> InvoiceResponse:
        """
        Upload file and immediately process OCR to extract invoice data
        
        Args:
            user_id: ID of user uploading file
            file_path: Path to uploaded file
            filename: Original filename
            
        Returns:
            InvoiceResponse with extracted invoice data
            
        Raises:
            ValidationException: If file validation fails
            ExternalServiceException: If OCR processing fails
        """
        try:
            # Validate file
            self._validate_file(file_path, filename)
            
            # Get file size and read file content
            file_size = file_path.stat().st_size
            
            # Read file as bytes for database storage
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            # Get MIME type
            mime_type, _ = mimetypes.guess_type(filename)
            if not mime_type:
                mime_type = 'application/octet-stream'
            
            # Generate unique file ID
            file_id = f"{user_id}_{int(datetime.utcnow().timestamp())}"
            
            # Save image to database
            image_id = self.db.save_image(
                filename=file_id,
                original_filename=filename,
                file_data=file_data,
                file_size=file_size,
                mime_type=mime_type,
                user_id=user_id
            )
            
            if not image_id:
                raise DatabaseException("Failed to save image to database")
            
            # Process OCR immediately (using the file data in memory)
            extracted_text, confidence = await self._extract_text_ocr_from_bytes(file_data, filename)
            
            # Parse invoice fields from OCR text
            from services.ocr_service import OCRService
            ocr_service = OCRService()
            invoice_data = ocr_service.extract_invoice_fields(extracted_text, filename)
            
            # Add confidence and OCR text
            invoice_data['confidence'] = confidence
            invoice_data['ocr_text'] = extracted_text
            
            # Save invoice to database (linked to image)
            invoice_id = self._save_invoice_to_db(user_id, file_id, filename, image_id, invoice_data)
            
            # Convert to InvoiceResponse
            return InvoiceResponse(**invoice_data)
            
        except ValidationException:
            raise
        except Exception as e:
            raise ExternalServiceException("OCR", f"Upload and OCR processing failed: {str(e)}")
    
    def _save_invoice_to_db(self, user_id: int, file_id: str, filename: str, image_id: int, invoice_data: dict) -> int:
        """Save invoice data to database and return invoice ID"""
        try:
            # Convert invoice data for database
            db_data = {
                'filename': filename,
                'filepath': f"/api/images/{image_id}",  # Reference to image endpoint
                'invoice_code': invoice_data.get('invoice_code', 'INV-UNKNOWN'),
                'invoice_type': invoice_data.get('invoice_type', 'general'),
                'date': invoice_data.get('date', datetime.now().strftime('%d/%m/%Y')),
                'seller_name': invoice_data.get('seller_name', 'Unknown'),
                'seller_address': invoice_data.get('seller_address', ''),
                'seller_tax_id': invoice_data.get('seller_tax_id', ''),
                'buyer_name': invoice_data.get('buyer_name', 'Unknown'),
                'buyer_address': invoice_data.get('buyer_address', ''),
                'buyer_tax_id': invoice_data.get('buyer_tax_id', ''),
                'subtotal': invoice_data.get('subtotal', 0),
                'tax_percentage': invoice_data.get('tax_percentage', 0),
                'tax_amount': invoice_data.get('tax_amount', 0),
                'total_amount': invoice_data.get('total_amount', '0 VND'),
                'total_amount_value': invoice_data.get('total_amount_value', 0),
                'currency': invoice_data.get('currency', 'VND'),
                'confidence_score': invoice_data.get('confidence', 0),
                'ocr_text': invoice_data.get('ocr_text', ''),
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
            
            # Save to database using db_tools
            invoice_id = self.db.save_invoice(db_data)
            
            # Update image with invoice_id reference
            if invoice_id:
                self.db.update_image_invoice_id(image_id, invoice_id)
            
            return invoice_id
            
        except Exception as e:
            logger.error(f"Failed to save invoice to database: {str(e)}")
            raise DatabaseException(f"Database save failed: {str(e)}")
    
    def _validate_file(self, file_path: Path, filename: str):
        """Validate file type and size"""
        # Check if file exists
        if not file_path.exists():
            raise ValidationException("File does not exist")
        
        # Check file size
        file_size = file_path.stat().st_size
        max_size = 10 * 1024 * 1024  # 10MB hardcoded for now
        
        if file_size > max_size:
            raise ValidationException(
                f"File size {file_size / 1024 / 1024:.2f}MB exceeds limit of {max_size / 1024 / 1024:.0f}MB"
            )
        
        # Check file extension
        _, ext = Path(filename).suffix.lower(), Path(filename).suffix.lower()
        mime_type, _ = mimetypes.guess_type(filename)
        
        allowed_types = ["jpg", "jpeg", "png", "pdf"]  # hardcoded for now
        if ext.lstrip('.').lower() not in [e.lower() for e in allowed_types]:
            raise ValidationException(
                f"File type {ext} not allowed. Allowed types: {', '.join(allowed_types)}"
            )
    
    async def process_ocr(self, file_id: str, user_id: int) -> OCRResult:
        """
        Process file with OCR
        
        Args:
            file_id: ID of uploaded file
            user_id: ID of user
            
        Returns:
            OCRResult with extracted text and confidence
            
        Raises:
            ResourceNotFoundException: If file not found
            ExternalServiceException: If OCR processing fails
        """
        try:
            # Get file from database
            # file_record = self.db.query(UploadedFile).filter(
            #     UploadedFile.file_id == file_id,
            #     UploadedFile.user_id == user_id
            # ).first()
            # if not file_record:
            #     raise ResourceNotFoundException(f"File {file_id} not found")
            
            # Call OCR service (Tesseract or Google Vision API)
            import time
            start_time = time.time()
            
            extracted_text, confidence = await self._extract_text_ocr(file_id)
            
            processing_time = time.time() - start_time
            
            # Store OCR result
            # ocr_result = OCRJobData(
            #     file_id=file_id,
            #     user_id=user_id,
            #     extracted_text=extracted_text,
            #     confidence=confidence,
            #     processing_time=processing_time,
            #     processed_at=datetime.utcnow()
            # )
            # self.db.add(ocr_result)
            # self.db.commit()
            
            return OCRResult(
                file_id=file_id,
                extracted_text=extracted_text,
                confidence=confidence,
                processing_time=processing_time
            )
            
        except Exception as e:
            raise ExternalServiceException("OCR", f"OCR processing failed: {str(e)}")
    
    async def _extract_text_ocr(self, file_path: str) -> Tuple[str, float]:
        """
        Extract text from file using OCR
        
        Returns:
            Tuple of (extracted_text, confidence_score)
        """
        try:
            from PIL import Image
            import pytesseract
            from ocr_config import configure_tesseract
            
            # Open image
            image = Image.open(file_path)
            
            # Configure Tesseract
            if configure_tesseract():
                # Extract text
                ocr_text = pytesseract.image_to_string(image, lang='vie+eng')
                
                # Calculate confidence based on text length and quality
                confidence = min(len(ocr_text.strip()) / 500, 1.0)
                if confidence < 0.1:
                    confidence = 0.1  # Minimum confidence
                
                logger.info(f"✅ OCR extracted {len(ocr_text)} characters with confidence {confidence:.2f}")
                return ocr_text.strip(), confidence
            else:
                logger.warning("⚠️ Tesseract not available, using fallback")
                return "OCR not available - please install Tesseract", 0.1
                
        except ImportError as e:
            logger.error(f"❌ OCR dependencies not available: {e}")
            return f"OCR not available: {e}", 0.1
        except Exception as e:
            logger.error(f"❌ OCR extraction failed: {e}")
            return f"OCR failed: {e}", 0.1

    async def _extract_text_ocr_from_bytes(self, file_data: bytes, filename: str) -> Tuple[str, float]:
        """
        Extract text from file bytes using OCR
        
        Args:
            file_data: Raw file bytes
            filename: Original filename (for logging)
            
        Returns:
            Tuple of (extracted_text, confidence_score)
        """
        try:
            from PIL import Image
            import pytesseract
            from ocr_config import configure_tesseract
            from io import BytesIO
            
            # Try Tesseract first
            if configure_tesseract():
                # Open image from bytes
                image = Image.open(BytesIO(file_data))
                
                # Extract text
                ocr_text = pytesseract.image_to_string(image, lang='vie+eng')
                
                # Check if we got meaningful text
                if len(ocr_text.strip()) > 10 and not "OCR not available" in ocr_text:
                    # Log the raw OCR text for debugging
                    logger.info(f"🔍 Raw OCR text from {filename}: '{ocr_text[:500]}...'")
                    
                    # Calculate confidence based on text length and quality
                    confidence = min(len(ocr_text.strip()) / 500, 1.0)
                    if confidence < 0.1:
                        confidence = 0.1  # Minimum confidence
                    
                    logger.info(f"✅ OCR extracted {len(ocr_text)} characters from {filename} with confidence {confidence:.2f}")
                    return ocr_text.strip(), confidence
            
            # Tesseract failed or not available, try online OCR
            logger.warning(f"⚠️ Tesseract OCR failed for {filename}, trying online OCR fallback")
            online_text, online_confidence = await self._extract_text_online_ocr(file_data, filename)
            return online_text, online_confidence
                
        except ImportError as e:
            logger.error(f"❌ OCR dependencies not available: {e}")
            # Try online OCR as fallback
            online_text, online_confidence = await self._extract_text_online_ocr(file_data, filename)
            return online_text, online_confidence
        except Exception as e:
            logger.error(f"❌ OCR extraction from bytes failed for {filename}: {e}")
            # Try online OCR as fallback
            online_text, online_confidence = await self._extract_text_online_ocr(file_data, filename)
            return online_text, online_confidence

    async def _extract_text_online_ocr(self, file_data: bytes, filename: str) -> Tuple[str, float]:
        """
        Extract text using online OCR API as fallback
        
        Args:
            file_data: Raw image bytes
            filename: Original filename
            
        Returns:
            Tuple of (extracted_text, confidence_score)
        """
        try:
            import base64
            import httpx
            
            # Encode image to base64
            image_b64 = base64.b64encode(file_data).decode('utf-8')
            
            # Use OCR.space free API (limited to 10k requests/month)
            api_url = "https://api.ocr.space/parse/image"
            payload = {
                'apikey': 'helloworld',  # Free API key
                'base64Image': f"data:image/png;base64,{image_b64}",
                'language': 'eng',
                'isOverlayRequired': False,
                'scale': True
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(api_url, data=payload)
                result = response.json()
                
                if result.get('IsErroredOnProcessing'):
                    logger.error(f"❌ Online OCR failed: {result.get('ErrorMessage')}")
                    return f"Online OCR failed: {result.get('ErrorMessage')}", 0.1
                
                if result.get('ParsedResults'):
                    ocr_text = result['ParsedResults'][0].get('ParsedText', '')
                    confidence = float(result['ParsedResults'][0].get('TextOverlay', {}).get('HasOverlay', False))
                    
                    if confidence == 0:
                        confidence = 0.5  # Default confidence for online OCR
                    
                    logger.info(f"✅ Online OCR extracted {len(ocr_text)} characters from {filename}")
                    return ocr_text.strip(), confidence
                else:
                    logger.warning(f"⚠️ Online OCR returned no results for {filename}")
                    return "Online OCR returned no text", 0.1
                    
        except Exception as e:
            logger.error(f"❌ Online OCR failed for {filename}: {e}")
            return f"Online OCR unavailable: {e}", 0.1

    async def get_ocr_result(self, file_id: str, user_id: int) -> OCRResult:
        """Retrieve OCR result for file"""
        try:
            # ocr_result = self.db.query(OCRJobData).filter(
            #     OCRJobData.file_id == file_id,
            #     OCRJobData.user_id == user_id
            # ).first()
            # if not ocr_result:
            #     raise ResourceNotFoundException(f"OCR result for {file_id} not found")
            
            # return OCRResult.from_orm(ocr_result)
            return None
        except Exception as e:
            raise DatabaseException(f"Failed to retrieve OCR result: {str(e)}")
