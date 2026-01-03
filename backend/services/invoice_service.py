"""
Invoice Service - Handles all invoice-related business logic
"""
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path
import uuid

from utils.logger import get_logger

logger = get_logger(__name__)


class InvoiceService:
    """Service for handling invoice operations"""

    def __init__(self, db_tools=None, vector_service=None, ocr_service=None):
        self.db_tools = db_tools
        self.vector_service = vector_service
        self.ocr_service = ocr_service

        # Setup upload directory using pathlib
        self.UPLOAD_DIR = Path("backend/uploads")
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        logger.info(f"📁 Upload directory ready: {self.UPLOAD_DIR.absolute()}")

    def save_upload_file(self, upload_file) -> Path:
        """
        Lưu file upload và trả về đường dẫn file đã lưu

        Args:
            upload_file: FastAPI UploadFile object

        Returns:
            Path: Đường dẫn đến file đã lưu
        """
        # Tạo tên file duy nhất: [chuỗi_ngẫu_nhiên]_[tên_gốc]
        unique_filename = f"{uuid.uuid4().hex}_{upload_file.filename}"
        file_path = self.UPLOAD_DIR / unique_filename

        # Ghi nội dung file vào ổ cứng
        with open(file_path, "wb") as buffer:
            buffer.write(upload_file.file.read())

        logger.info(f"💾 File saved: {file_path} ({file_path.stat().st_size} bytes)")
        return file_path

    def get_invoice_list(self, time_filter: str = "all", limit: int = 20, search_query: Optional[str] = None) -> Dict[str, Any]:
        """
        Get list of invoices with optional filtering and search

        Args:
            time_filter: Time filter ("all", "today", "yesterday", "week", "month")
            limit: Maximum number of invoices to return
            search_query: Search query string

        Returns:
            Dict containing invoice list and metadata
        """
        if not self.db_tools:
            raise Exception("Database not available")

        logger.info(f"📋 Getting invoices - filter: {time_filter}, limit: {limit}")

        # Get all invoices
        invoices = self.db_tools.get_all_invoices(limit=limit)

        if not invoices:
            return {
                "success": True,
                "message": "Không có hóa đơn nào",
                "data": [],
                "count": 0
            }

        # Filter by time if needed
        if time_filter != "all":
            invoices = self._filter_invoices_by_time(invoices, time_filter)

        # Search if query provided
        if search_query:
            invoices = self._search_invoices(invoices, search_query)

        logger.info(f"✅ Returning {len(invoices)} invoices")

        return {
            "success": True,
            "message": f"Tìm thấy {len(invoices)} hóa đơn",
            "data": invoices,
            "count": len(invoices)
        }

    def get_invoice_detail(self, invoice_id: str) -> Dict[str, Any]:
        """
        Get detailed information for a specific invoice

        Args:
            invoice_id: Invoice identifier

        Returns:
            Dict containing invoice details
        """
        if not self.db_tools:
            raise Exception("Database not available")

        logger.info(f"📄 Getting invoice: {invoice_id}")

        invoice = self.db_tools.get_invoice_by_filename(invoice_id)

        if not invoice:
            raise Exception(f"Invoice not found: {invoice_id}")

        return {
            "success": True,
            "data": invoice
        }

    def search_invoices(self, query: str, limit: int = 20) -> Dict[str, Any]:
        """
        Search invoices by query

        Args:
            query: Search query string
            limit: Maximum number of results

        Returns:
            Dict containing search results
        """
        if not self.db_tools:
            raise Exception("Database not available")

        logger.info(f"🔍 Searching invoices: {query}")

        results = self.db_tools.search_invoices(query, limit=limit)

        return {
            "success": True,
            "query": query,
            "data": results,
            "count": len(results)
        }

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get invoice statistics

        Returns:
            Dict containing statistics data
        """
        if not self.db_tools:
            raise Exception("Database not available")

        logger.info("📊 Getting invoice statistics")

        stats = self.db_tools.get_statistics()

        return {
            "success": True,
            "data": stats
        }

    def process_invoice_file(self, file_path: str, filename: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process uploaded invoice file and create RAG embeddings

        Workflow:
        1. OCR: Extract text from file
        2. Create comprehensive content
        3. Generate embeddings
        4. Store in vector database

        Args:
            file_path: Path to uploaded file
            filename: Original filename
            user_id: User who uploaded the file

        Returns:
            Dict containing processing results
        """
        try:
            logger.info(f"🔄 Processing invoice file: {filename}")

            # Step 1: OCR - Extract text from file using dual engines
            if not self.ocr_service:
                raise Exception("OCR service not available")

            logger.info("📄 Step 1: Extracting text with dual OCR engines...")
            ocr_result = self.ocr_service.process_file_dual(file_path)

            # Check if we have any successful OCR results
            tess_available = ocr_result.get("tesseract", {}).get("available", False)
            easy_available = ocr_result.get("easyocr", {}).get("available", False)

            if not tess_available and not easy_available:
                raise Exception("No OCR engines available for processing")

            # Get texts from both engines
            tess_text = ocr_result.get("tesseract", {}).get("text", "")
            easy_text = ocr_result.get("easyocr", {}).get("text", "")

            logger.info(f"✅ Tesseract: {len(tess_text)} chars, EasyOCR: {len(easy_text)} chars")

            # Step 1.5: Use Groq to compare and select best text
            logger.info("🤖 Step 1.5: Using Groq to compare OCR results...")
            final_text = self._compare_ocr_results_with_groq(
                filename=filename,
                tesseract_text=tess_text,
                easyocr_text=easy_text,
                tesseract_available=tess_available,
                easyocr_available=easy_available
            )

            extracted_text = final_text
            logger.info(f"✅ Final OCR text: {len(extracted_text)} characters")

            # Step 2: Create comprehensive content
            logger.info("📝 Step 2: Creating comprehensive content...")
            comprehensive_content = self._create_comprehensive_content(
                filename=filename,
                extracted_text=extracted_text,
                user_id=user_id
            )

            # Step 3: Generate embeddings
            if not self.vector_service:
                logger.warning("⚠️  Vector service not available, skipping RAG indexing")
                return {
                    "success": True,
                    "message": "File processed successfully (OCR only)",
                    "ocr_text": extracted_text,
                    "rag_indexed": False
                }

            logger.info("🔢 Step 3: Generating embeddings...")
            # Prepare invoice data for RAG
            invoice_data = self._prepare_invoice_for_rag(
                filename=filename,
                extracted_text=extracted_text,
                comprehensive_content=comprehensive_content,
                user_id=user_id
            )

            # Add to vector database
            logger.info("☁️  Step 4: Storing in vector database...")
            document_ids = self.vector_service.add_invoice_documents([invoice_data])

            logger.info(f"✅ Successfully processed and indexed invoice: {filename}")
            logger.info(f"📊 Document ID: {document_ids[0] if document_ids else 'N/A'}")

            return {
                "success": True,
                "message": "Invoice processed and indexed successfully",
                "filename": filename,
                "ocr_text": extracted_text,
                "comprehensive_content": comprehensive_content,
                "document_id": document_ids[0] if document_ids else None,
                "rag_indexed": True,
                "ocr_engines": {
                    "tesseract": {
                        "available": tess_available,
                        "text_length": len(tess_text),
                        "confidence": ocr_result.get("tesseract", {}).get("confidence", 0)
                    },
                    "easyocr": {
                        "available": easy_available,
                        "text_length": len(easy_text),
                        "confidence": ocr_result.get("easyocr", {}).get("confidence", 0)
                    },
                    "groq_comparison_used": True,
                    "recommended_engine": ocr_result.get("recommendation", "")
                },
                "processing_steps": [
                    "File saved to disk",
                    "Dual OCR text extraction (Tesseract + EasyOCR)",
                    "Groq AI comparison and text selection",
                    "Content synthesis",
                    "Embedding generation",
                    "Vector database storage"
                ]
            }

        except Exception as e:
            logger.error(f"❌ Error processing invoice file {filename}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "filename": filename
            }

    def _create_comprehensive_content(self, filename: str, extracted_text: str, user_id: Optional[str] = None) -> str:
        """
        Create comprehensive content from filename and extracted text

        Args:
            filename: Original filename
            extracted_text: OCR extracted text
            user_id: User ID

        Returns:
            Comprehensive content string
        """
        content_parts = []

        # Add filename info
        content_parts.append(f"File: {filename}")

        # Add user info if available
        if user_id:
            content_parts.append(f"Uploaded by user: {user_id}")

        # Add timestamp
        content_parts.append(f"Processed at: {datetime.now().isoformat()}")

        # Add extracted text
        content_parts.append("Content:")
        content_parts.append(extracted_text)

        # Add metadata hints for better search
        if "invoice" in filename.lower() or "hoa don" in filename.lower():
            content_parts.append("Document type: Invoice/Hóa đơn")
        if "receipt" in filename.lower() or "bien lai" in filename.lower():
            content_parts.append("Document type: Receipt/Biên lai")

        return "\n".join(content_parts)

    def _prepare_invoice_for_rag(self, filename: str, extracted_text: str, comprehensive_content: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Prepare invoice data for RAG indexing

        Args:
            filename: Original filename
            extracted_text: OCR extracted text
            comprehensive_content: Comprehensive content
            user_id: User ID

        Returns:
            Invoice data dict for RAG
        """
        # Generate invoice ID from filename
        invoice_id = f"file_{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        return {
            "id": invoice_id,
            "invoice_number": filename,  # Use filename as invoice number
            "customer_name": f"Uploaded by {user_id}" if user_id else "Unknown user",
            "total_amount": 0,  # Will be extracted from OCR if possible
            "currency": "VND",
            "issue_date": datetime.now().strftime("%Y-%m-%d"),
            "due_date": "",  # Not applicable for file uploads
            "status": "processed",
            "items": [],  # Will be extracted from OCR if possible
            "notes": f"OCR processed file: {filename}",
            "payment_terms": "",
            "ocr_text": extracted_text,
            "comprehensive_content": comprehensive_content,
            "source": "file_upload",
            "user_id": user_id,
            "processed_at": datetime.now().isoformat()
        }

    def _filter_invoices_by_time(self, invoices: List[Dict], time_filter: str) -> List[Dict]:
        """Lọc hóa đơn theo thời gian"""
        from datetime import datetime, timedelta

        now = datetime.now()

        if time_filter == "today":
            today = now.date()
            return [inv for inv in invoices if str(inv.get('created_at', '')).startswith(str(today))]

        elif time_filter == "yesterday":
            yesterday = (now - timedelta(days=1)).date()
            return [inv for inv in invoices if str(inv.get('created_at', '')).startswith(str(yesterday))]

        elif time_filter == "week":
            week_ago = now - timedelta(days=7)
            return [inv for inv in invoices if datetime.fromisoformat(str(inv.get('created_at', '')).replace('Z', '+00:00')) >= week_ago]

        elif time_filter == "month":
            month_ago = now - timedelta(days=30)
            return [inv for inv in invoices if datetime.fromisoformat(str(inv.get('created_at', '')).replace('Z', '+00:00')) >= month_ago]

        return invoices

    def _search_invoices(self, invoices: List[Dict], query: str) -> List[Dict]:
        """Tìm kiếm hóa đơn trong danh sách"""
        query_lower = query.lower()
        results = []

        for inv in invoices:
            if any(query_lower in str(inv.get(field, '')).lower()
                   for field in ['filename', 'invoice_code', 'buyer_name', 'seller_name', 'invoice_type']):
                results.append(inv)

        return results

    def _compare_ocr_results_with_groq(
        self,
        filename: str,
        tesseract_text: str,
        easyocr_text: str,
        tesseract_available: bool,
        easyocr_available: bool
    ) -> str:
        """
        Use Groq to compare OCR results from both engines and select the best text

        Args:
            filename: Name of the file being processed
            tesseract_text: Text extracted by Tesseract
            easyocr_text: Text extracted by EasyOCR
            tesseract_available: Whether Tesseract was available
            easyocr_available: Whether EasyOCR was available

        Returns:
            Best text as determined by Groq
        """
        try:
            # Import Groq service
            from services.groq_service import GroqService

            groq_service = GroqService()

            # Create comparison prompt
            prompt = self._create_ocr_comparison_prompt(
                filename=filename,
                tesseract_text=tesseract_text,
                easyocr_text=easyocr_text,
                tesseract_available=tesseract_available,
                easyocr_available=easyocr_available
            )

            # Get Groq's analysis
            response = groq_service.generate_response(prompt, max_tokens=2000)

            # Extract the final text from Groq's response
            final_text = self._extract_final_text_from_groq_response(response)

            logger.info("✅ Groq comparison completed")
            return final_text

        except Exception as e:
            logger.warning(f"Groq comparison failed: {e}, using fallback logic")

            # Fallback: use the longer text or EasyOCR if available
            if easyocr_available and len(easyocr_text.strip()) > len(tesseract_text.strip()):
                return easyocr_text
            elif tesseract_available:
                return tesseract_text
            else:
                return easyocr_text  # Last resort

    def _create_ocr_comparison_prompt(
        self,
        filename: str,
        tesseract_text: str,
        easyocr_text: str,
        tesseract_available: bool,
        easyocr_available: bool
    ) -> str:
        """
        Create a prompt for Groq to compare OCR results
        """
        prompt = f"""Bạn là chuyên gia xử lý hóa đơn thông minh. Tôi có kết quả OCR từ 2 engine khác nhau cho file: {filename}

Hãy phân tích và chọn ra nội dung chính xác nhất cho hóa đơn này.

**KẾT QUẢ TESSERACT OCR:**
{tesseract_text if tesseract_available else "Không khả dụng"}

**KẾT QUẢ EASYOCR:**
{easyocr_text if easyocr_available else "Không khả dụng"}

**HƯỚNG DẪN PHÂN TÍCH:**
1. So sánh độ chính xác của văn bản (chính tả, định dạng, logic)
2. Ưu tiên engine có kết quả rõ ràng và có cấu trúc hơn
3. Nếu một engine có lỗi rõ ràng, bỏ qua phần đó
4. Kết hợp thông tin tốt nhất từ cả hai nếu cần thiết
5. Đảm bảo thông tin quan trọng như số tiền, ngày tháng, tên công ty được chính xác

**YÊU CẦU TRẢ VỀ:**
- Chỉ trả về nội dung văn bản cuối cùng đã được chỉnh sửa
- KHÔNG giải thích, chỉ trả về văn bản hóa đơn
- Giữ nguyên cấu trúc và định dạng của hóa đơn gốc
- Sửa lỗi chính tả và định dạng nếu có

Nội dung hóa đơn chính xác nhất:"""

        return prompt

    def _extract_final_text_from_groq_response(self, response: str) -> str:
        """
        Extract the final text from Groq's response

        Args:
            response: Raw response from Groq

        Returns:
            Cleaned text content
        """
        # Remove any introductory text or explanations
        # Look for the actual invoice content
        lines = response.strip().split('\n')

        # Remove common prefixes that might be added by Groq
        prefixes_to_remove = [
            "Nội dung hóa đơn chính xác nhất:",
            "Kết quả cuối cùng:",
            "Văn bản hóa đơn:",
            "**",
            "*"
        ]

        for prefix in prefixes_to_remove:
            if lines and lines[0].startswith(prefix):
                lines = lines[1:]

        # Clean up and join
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith(('Đây là', 'Tôi đã', 'Sau khi')):
                cleaned_lines.append(line)

        return '\n'.join(cleaned_lines).strip()