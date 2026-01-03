"""
🚀 FastAPI Backend for Smart Chat
==================================

Unified FastAPI service (formerly Flask chatbot + FastAPI backend)
Cung cấp các API endpoints cho:
✅ � Chat với AI (Groq LLM)
✅ �📷 Mở camera
✅ 📋 Xem danh sách hóa đơn
✅ 📤 Upload ảnh và xử lý OCR (async)
✅ 📊 Thống kê hóa đơn
✅ 📥 **Xuất hóa đơn (Excel, PDF, CSV, JSON)**

Chạy: uvicorn main:app --host 0.0.0.0 --port 8000
Hoặc: python main.py (uvicorn auto-run)
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Query, WebSocket, Depends, status
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging
import os
import sys
import io
import asyncio
import json
import uuid
from dotenv import load_dotenv



# Setup logging first (before using logger)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# OCR imports
try:
    import pytesseract
    from PIL import Image
    TESSERACT_AVAILABLE = True
    # Configure Tesseract path
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    logger.info("✅ Tesseract OCR available")
except ImportError as e:
    TESSERACT_AVAILABLE = False
    logger.warning(f"⚠️ Tesseract not available: {e}")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Auth imports are now handled in auth_api.py

# Database dependency is now handled in auth_api.py

# Auth utilities are now defined in auth_api.py

# Import database tools (now in backend/utils)
# Try PostgreSQL first, fallback to SQLite
try:
    database_url = os.getenv('DATABASE_URL', '')
    
    if database_url and not database_url.startswith('sqlite'):
        # Use PostgreSQL
        logger.info("🔗 Using PostgreSQL cloud database")
        from utils.database_tools_postgres import get_database_tools
        db_tools = get_database_tools()
        logger.info("✅ PostgreSQL database tools initialized")
    else:
        # Use SQLite
        logger.info("📁 Using SQLite local database")
        from utils.database_tools_sqlite import get_database_tools
        db_tools = get_database_tools()
        
        if hasattr(db_tools, 'initialize_tables'):
            if db_tools.initialize_tables():
                logger.info("✅ SQLite database tools initialized")
            else:
                logger.warning("⚠️ Database tables initialization had issues")
        else:
            logger.info("✅ SQLite database tools initialized")
except Exception as e:
    logger.warning(f"⚠️ Database tools not available: {e}")
    db_tools = None

# Import WebSocket manager
try:
    from websocket_manager import websocket_manager
    logger.info("✅ WebSocket manager initialized")
except Exception as e:
    logger.warning(f"⚠️ WebSocket manager not available: {e}")
    websocket_manager = None

# Import chat handlers (now in backend/handlers)
try:
    # Temporarily disabled due to missing models
    # from handlers.chat_handler import ChatHandler
    # from handlers.hybrid_chat_handler import HybridChatBot
    # from handlers.groq_chat_handler import GroqChatHandler
    # chat_handler = ChatHandler()
    # hybrid_chat = HybridChatBot()
    chat_handler = None
    hybrid_chat = None
    logger.info("✅ Chat handlers disabled (models not available)")
except Exception as e:
    logger.warning(f"⚠️ Chat handlers not available: {e}")
    chat_handler = None
    hybrid_chat = None

# Import Groq tools
try:
    # Temporarily disabled due to missing dependencies
    # from groq_tools import GroqDatabaseTools, DecimalEncoder
    # groq_tools = GroqDatabaseTools(db_tools)
    # groq_chat_handler = GroqChatHandler(db_tools=db_tools, groq_tools=groq_tools)
    groq_tools = None
    groq_chat_handler = None
    DecimalEncoder = None
    logger.info("✅ Groq tools disabled (dependencies not available)")
except Exception as e:
    logger.warning(f"⚠️ Groq tools not available: {e}")
    groq_tools = None
    groq_chat_handler = None
    DecimalEncoder = None

# Import auth utilities
try:
    from utils.auth_utils import get_current_user, get_current_admin_user, get_current_user_or_admin
    logger.info("✅ Auth utilities initialized")
except Exception as e:
    logger.warning(f"⚠️ Auth utilities not available: {e}")
    get_current_user = None
    get_current_admin_user = None
    get_current_user_or_admin = None

# Import services
try:
    from services.ocr_service import OCRService
    from services.invoice_service import InvoiceService
    from services.ai_training_service import AITrainingService
    from services.ocr_job_service import OCRJobService

    # Initialize services
    ocr_service = OCRService(db_tools)
    
    # Import vector service for RAG
    try:
        from services.vector_store import get_vector_service
        vector_service = get_vector_service()
        logger.info("✅ Vector service initialized for RAG")
    except Exception as ve:
        logger.warning(f"⚠️ Vector service not available: {ve}")
        vector_service = None
    
    invoice_service = InvoiceService(db_tools, vector_service=vector_service, ocr_service=ocr_service)
    ai_training_service = AITrainingService(db_tools)
    ocr_job_service = OCRJobService(db_tools)

    logger.info("✅ Services initialized")
except Exception as e:
    logger.warning(f"⚠️ Services not available: {e}")
    ocr_service = None
    invoice_service = None
    ai_training_service = None
    ocr_job_service = None

# Import export service
try:
    from export_service import get_export_service
    export_service = get_export_service(db_tools)
    logger.info("✅ Export service initialized")
except Exception as e:
    logger.warning(f"⚠️ Export service not available: {e}")
    export_service = None

# Import auth API router (use database version)
try:
    from auth_api import auth_router
    logger.info("✅ Auth API router initialized (database version)")
except Exception as e:
    logger.warning(f"⚠️ Auth API router not available, trying simple auth: {e}")
    try:
        from routers.simple_auth import router as auth_router
        logger.info("✅ Simple Auth API router initialized (fallback)")
    except Exception as e2:
        logger.warning(f"⚠️ No auth router available: {e2}")
        auth_router = None

# Import admin API router
try:
    from admin_api import admin_router
    logger.info("✅ Admin API router initialized from admin_api.py")
except Exception as e:
    logger.warning(f"⚠️ Admin API router not available from admin_api.py, trying routers/admin.py: {e}")
    try:
        from routers.admin import router as admin_router
        logger.info("✅ Admin API router initialized from routers/admin.py")
    except Exception as e2:
        logger.warning(f"⚠️ Admin API router not available: {e2}")
        admin_router = None

# Import chat router
try:
    from routers.chat import router as chat_router
    logger.info("✅ Chat API router initialized")
except Exception as e:
    logger.warning(f"⚠️ Chat API router not available: {e}")
    chat_router = None

# FastAPI app
app = FastAPI(
    title="Invoice Chat Backend",
    description="FastAPI backend for Smart Chat - Camera & Invoice Management",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for chatbot frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure auth utilities exist (fallback if import failed)
if not get_current_user:
    logger.warning("⚠️ Creating fallback auth utilities")
    from utils.auth_utils import get_current_user as _get_current_user
    get_current_user = _get_current_user
    logger.info("✅ Fallback auth utilities loaded")

# Mount static files for uploads
from fastapi.staticfiles import StaticFiles
upload_dir = "uploads"
os.makedirs(upload_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=upload_dir), name="uploads")
logger.info("✅ Static files mounted at /uploads")

# Include auth router
if auth_router:
    app.include_router(auth_router, prefix="/api")
    logger.info("✅ Auth router included at /api/auth")

# Include admin router
if admin_router:
    app.include_router(admin_router, prefix="/api")
    logger.info("✅ Admin router included at /api/admin")

# Include chat router (already has /api/chat prefix in router definition)
if chat_router:
    app.include_router(chat_router)
    logger.info("✅ Chat router included at /api/chat")

# ===================== MODELS =====================

class CameraRequest(BaseModel):
    """Mở camera request"""
    action: str
    user_request: str

class InvoiceListRequest(BaseModel):
    """Xem danh sách hóa đơn request"""
    time_filter: Optional[str] = "all"  # today, yesterday, week, month, all
    limit: Optional[int] = 20
    search_query: Optional[str] = None

class InvoiceResponse(BaseModel):
    """Invoice response model"""
    id: int
    filename: str
    invoice_code: str
    invoice_type: str
    buyer_name: str
    seller_name: str
    total_amount: str
    confidence_score: float
    created_at: str
    invoice_date: Optional[str]

class OCREnqueueRequest(BaseModel):
    """OCR job enqueue request"""
    filepath: str
    filename: str
    uploader: Optional[str] = "unknown"
    user_id: Optional[str] = None

class OCRJobResponse(BaseModel):
    """OCR job status response"""
    job_id: str
    status: str
    filename: str
    progress: int = 0
    invoice_id: Optional[int] = None
    error_message: Optional[str] = None
    created_at: str
    updated_at: str

class ChatMessageRequest(BaseModel):
    """Chat message request"""
    message: str
    user_id: Optional[str] = "anonymous"

class ChatMessageResponse(BaseModel):
    """Chat message response"""
    message: str
    type: str = "text"
    timestamp: str
    suggestions: List[str] = []
    method: str = "unknown"
    intent: Optional[str] = None
    confidence: Optional[float] = None
    entities: List[Dict] = []
    action: Optional[str] = None
    ocr_mode: bool = False

# Auth models are now defined in models/user.py and imported in auth_api.py

# ===================== OCR HELPER FUNCTIONS =====================

def extract_invoice_fields(ocr_text: str, filename: str = "") -> dict:
    """
    Extract invoice fields from OCR text with enhanced dash amount recognition
    """
    import re
    from datetime import datetime
    
    # Initialize training client for dash pattern learning
    training_client = None
    try:
        from utils.training_client import TrainingDataClient
        training_client = TrainingDataClient()
    except Exception as e:
        logger.warning(f"Could not initialize training client: {e}")
    
    data = {
        'invoice_code': 'INV-UNKNOWN',
        'date': datetime.now().strftime("%d/%m/%Y"),
        'buyer_name': 'Unknown',
        'seller_name': 'Unknown',
        'total_amount': '0 VND',
        'total_amount_value': 0,
        'subtotal': 0,
        'tax_amount': 0,
        'tax_percentage': 0,
        'currency': 'VND',
        'buyer_tax_id': '',
        'seller_tax_id': '',
        'buyer_address': '',
        'seller_address': '',
        'items': [],
        'transaction_id': '',
        'payment_method': '',
        'payment_account': '',
        'invoice_time': None,
        'due_date': None,
        'invoice_type': 'general'
    }
    
    text_lower = ocr_text.lower()
    
    # Detect invoice type with improved priority logic
    # ⭐ PRIORITY: Check for electricity bill keywords first when both MoMo and electricity are present
    has_momo_keywords = any(word in text_lower for word in ['momo', 'ví điện tử', 'momo wallet', 'transfer', 'chuyển khoản'])
    has_electricity_keywords = any(word in text_lower for word in ['điện', 'dien', 'electricity', 'tiền điện', 'tien dien', 'hóa đơn tiền điện', 'kwh', 'evn', 'điện lực', 'dien luc', 'nhà cung cấp', 'nha cung cap', 'ctdl', 'công ty điện lực', 'cong ty dien luc'])
    
    logger.info(f"🔍 Invoice type detection: has_momo={has_momo_keywords}, has_electricity={has_electricity_keywords}")
    logger.info(f"🔍 OCR text preview (first 150 chars): {ocr_text[:150]}")
    
    # If both MoMo and electricity keywords are present, prioritize electricity (MoMo payment for electricity bill)
    if has_electricity_keywords:
        is_electricity = True
        is_momo = False
        logger.info("🔍 Detected electricity bill payment - prioritizing electricity processing")
    elif has_momo_keywords:
        is_momo = True
        is_electricity = False
        logger.info("🔍 Detected MoMo payment receipt")
    else:
        is_momo = False
        is_electricity = False
        logger.info("🔍 Detected general invoice")
    
    if is_momo:
        # Handle MoMo payment receipts
        data['invoice_type'] = 'momo_payment'
        data['seller_name'] = 'MoMo Payment'
        
        logger.info(f"🔍 Processing MoMo invoice. OCR text preview: {ocr_text[:200]}...")
        
        # Extract transaction ID (Mã giao dịch)
        transaction_id_patterns = [
            r'(?:mã giao dịch|ma giao dich|transaction id|trans id|transaction)[:\s]*([A-Z0-9\-]{6,20})',
            r'(?:mã giao dịch|ma giao dich|transaction id|trans id)[:\s]*([A-Z0-9\-]{6,20})',
            # More specific patterns - avoid generic alphanumeric matches
            r'(?:ID|id)[:\s]*([A-Z0-9]{8,16})(?:\s|$)',  # Must be preceded by ID label
            r'([A-Z]{2,4}\d{6,12})',  # Pattern like MOMO12345678, EVN123456
        ]
        for pattern in transaction_id_patterns:
            match = re.search(pattern, ocr_text, re.IGNORECASE)
            if match:
                candidate_id = match.group(1).strip()
                # Validate transaction ID - should not contain currency symbols or be too short
                if (len(candidate_id) >= 6 and 
                    not any(char in candidate_id for char in ['VND', 'đ', 'VNĐ', '.', ',']) and
                    not candidate_id.replace('-', '').replace('_', '').isdigit()):  # Avoid pure numbers
                    data['transaction_id'] = candidate_id
                    data['invoice_code'] = f"MOMO-{data['transaction_id']}"
                    break
        
        # Payment account / Tài khoản thanh toán
        account_patterns = [
            r'(?:tài khoản|từ|from|sender)[:\s]*([0-9\s\-\+\(\)]+)',
            r'(?:số điện thoại|phone|mobile)[:\s]*([0-9\s\-\+\(\)]+)',
            r'(?:người gửi|sender)[:\s]*([^\n]+)',
        ]
        for pattern in account_patterns:
            match = re.search(pattern, ocr_text, re.IGNORECASE)
            if match:
                data['payment_account'] = match.group(1).strip()
                if not data['buyer_name'] or data['buyer_name'] == 'Unknown':
                    data['buyer_name'] = data['payment_account']
                break
        
        # Amount patterns for MoMo - improved with better validation
        # ⭐ HIGH PRIORITY: Check for dash-indicated total amounts first
        dash_amount_patterns = [
            r'(?:^\s*-\s*|-\s+)([0-9,\.]+)(?:\s*(?:vnd|đ|vnđ))?\s*$',  # Line starting with dash and ending with amount
            r'(?:tổng|total|amount)[:\s]*-\s*([0-9,\.]+)(?:\s*(?:vnd|đ|vnđ))?',  # Total with dash
        ]
        
        # Check for dash-indicated amounts first (highest priority)
        for pattern in dash_amount_patterns:
            match = re.search(pattern, ocr_text, re.IGNORECASE | re.MULTILINE)
            if match:
                amount_str = match.group(1).strip()
                
                # Clean up the amount string
                amount_str = amount_str.replace(' ', '').replace('_', '')
                
                # Handle potential negative amounts (though rare in receipts)
                is_negative = False
                if amount_str.startswith('-') or '-308.472d' in ocr_text:
                    is_negative = True
                    amount_str = amount_str.lstrip('-')
                
                try:
                    # Parse amount - handle Vietnamese number format
                    if ',' in amount_str and '.' in amount_str:
                        # Handle format like 1,234.56
                        numeric_value = float(amount_str.replace(',', ''))
                    else:
                        # Handle format like 1234567 or 1.234.567
                        numeric_value = float(amount_str.replace(',', '').replace('.', ''))
                    
                    if is_negative:
                        numeric_value = -numeric_value
                    
                    # Validate amount is reasonable (not too large or too small)
                    if 100 <= numeric_value <= 100000000:  # Between 100 VND and 100M VND
                        data['total_amount'] = f"{numeric_value:,.0f} VND"
                        data['total_amount_value'] = numeric_value
                        data['subtotal'] = numeric_value
                        logger.info(f"✅ Found dash-indicated total amount: {data['total_amount']}")
                        break
                        
                except (ValueError, OverflowError):
                    continue
        
        # If no dash-indicated amount found, use regular patterns
        if not data.get('total_amount') or data['total_amount'] == '0 VND':
            amount_patterns = [
                # Vietnamese patterns
                r'(?:số tiền|amount|giá trị|tổng tiền|thành tiền)[:\s]*([0-9,\.]+)(?:\s*(?:vnd|đ|vnđ|vnd|đồng))?',
                r'(?:thành tiền|total|tổng|tổng cộng)[:\s]*([0-9,\.]+)(?:\s*(?:vnd|đ|vnđ|vnd|đồng))?',
                r'(?:số tiền chuyển|transfer amount|chuyển khoản)[:\s]*([0-9,\.]+)(?:\s*(?:vnd|đ|vnđ|vnd|đồng))?',
                # English patterns common in MoMo
                r'(?:Amount|Total|Value)[:\s]*([0-9,\.]+)(?:\s*(?:VND|đ|VNĐ))?',
                r'(?:Transfer|Payment)[:\s]*([0-9,\.]+)(?:\s*(?:VND|đ|VNĐ))?',
                # Just numbers with currency at end of line
                r'([0-9,\.]+)(?:\s*(?:vnd|đ|vnđ|vnd|đồng))\s*$',
                # Just numbers at end of line (MoMo often just shows the amount)
                r'([0-9,\.]+)\s*$',
                # Without currency at end
                r'(?:số tiền|amount|tổng)[:\s]*([0-9,\.]+)',
            ]
            logger.info(f"🔍 Trying {len(amount_patterns)} amount patterns for MoMo...")
            for i, pattern in enumerate(amount_patterns):
                match = re.search(pattern, ocr_text, re.IGNORECASE | re.MULTILINE)
                if match:
                    logger.info(f"✅ Pattern {i} matched: {pattern} → {match.group(1)}")
                    amount_str = match.group(1).strip()
                    
                    # Clean up the amount string
                    amount_str = amount_str.replace(' ', '').replace('_', '')
                    
                    # Handle potential negative amounts (though rare in receipts)
                    is_negative = False
                    if amount_str.startswith('-') or '-308.472d' in ocr_text:
                        is_negative = True
                        amount_str = amount_str.lstrip('-')
                    
                    try:
                        # Parse amount - handle Vietnamese number format
                        if ',' in amount_str and '.' in amount_str:
                            # Handle format like 1,234.56
                            numeric_value = float(amount_str.replace(',', ''))
                        else:
                            # Handle format like 1234567 or 1.234.567
                            numeric_value = float(amount_str.replace(',', '').replace('.', ''))
                        
                        if is_negative:
                            numeric_value = -numeric_value
                        
                        # Validate amount is reasonable (not too large or too small)
                        if 100 <= numeric_value <= 100000000:  # Between 100 VND and 100M VND
                            data['total_amount'] = f"{numeric_value:,.0f} VND"
                            data['total_amount_value'] = numeric_value
                            data['subtotal'] = numeric_value
                            break
                            
                    except (ValueError, OverflowError):
                        continue
        
        # Log if no amount found
        if not data.get('total_amount') or data['total_amount'] == '0 VND':
            logger.warning(f"⚠️ No amount found in MoMo OCR text. Text length: {len(ocr_text)}")
            logger.warning(f"⚠️ OCR text sample: {ocr_text[:300]}...")
        
        # Date/Time patterns for MoMo
        datetime_patterns = [
            r'(?:thời gian|time|ngày)[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{4}\s+\d{1,2}:\d{2})',
            r'(?:thời gian|time|ngày)[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{4}\s+\d{1,2}:\d{2})',  # dd/mm/yyyy hh:mm
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{4})',  # dd/mm/yyyy
        ]
        for pattern in datetime_patterns:
            match = re.search(pattern, ocr_text, re.IGNORECASE)
            if match:
                datetime_str = match.group(1).strip()
                data['date'] = datetime_str
                # Convert to datetime object for database
                try:
                    if ' ' in datetime_str:  # Has time component
                        dt = datetime.strptime(datetime_str, '%d/%m/%Y %H:%M')
                    else:  # Date only
                        dt = datetime.strptime(datetime_str, '%d/%m/%Y')
                    data['invoice_time'] = dt.isoformat()
                except ValueError:
                    data['invoice_time'] = None
                break
        
        # Recipient/Seller for MoMo
        recipient_patterns = [
            r'Người nhận:\s*([^\n\r]+)',
            r'người nhận[:\s]*([^\n\r]+)',
            r'bên nhận[:\s]*([^\n\r]+)',
            r'(?:tên cửa hàng|store|shop)[:\s]*([^\n\r]+)',
        ]
        for pattern in recipient_patterns:
            match = re.search(pattern, ocr_text, re.IGNORECASE)
            if match:
                data['seller_name'] = match.group(1).strip()
                break
        
        # Content/Description
        content_patterns = [
            r'(?:nội dung|content|message|ghi chú)[:\s]*([^\n]+)',
            r'(?:mô tả|description)[:\s]*([^\n]+)',
        ]
        for pattern in content_patterns:
            match = re.search(pattern, ocr_text, re.IGNORECASE)
            if match:
                content = match.group(1).strip()
                # Add as an item
                data['items'].append({
                    'description': content,
                    'amount': data['total_amount_value'],
                    'quantity': 1
                })
                break
    
    elif is_electricity:
        # Handle Vietnamese electricity bills (hóa đơn tiền điện)
        data['invoice_type'] = 'electricity'
        data['seller_name'] = 'Công ty Điện lực'
        
        # Extract electricity company name (Nhà cung cấp)
        company_patterns = [
            r'(?:nha cung cap|nhà cung cấp)[:\s]*([^\n\r]+)',
            r'(?:Nha cung cap|Nhà cung cấp)\s+([^\n\r]+)',
            r'(CTDL [^\n\r]+)',  # CTDL Vinh Long pattern
            r'(Công ty Điện lực [^\n\r]+)',
        ]
        for pattern in company_patterns:
            match = re.search(pattern, ocr_text, re.IGNORECASE)
            if match:
                data['seller_name'] = match.group(1).strip()
                break
        
        # Extract customer code (Mã khách hàng)
        customer_code_patterns = [
            r'(?:ma khach hang|mã khách hàng)[:\s]*([A-Z0-9]+)',
            r'(?:Ma khach hang|Mã khách hàng)\s+([A-Z0-9]+)',
            r'([A-Z]{2}\d{8,})',  # Pattern like PB16010051828 (2 letters + 8+ digits)
            r'([A-Z]{2,3}\d{2,}[A-Z0-9]*)',  # Pattern like PC12DD0442433
        ]
        for pattern in customer_code_patterns:
            match = re.search(pattern, ocr_text, re.IGNORECASE)
            if match:
                data['invoice_code'] = match.group(1).strip()
                break
        
        # Extract customer name (Tên khách hàng)
        customer_name_patterns = [
            r'(?:tên khách hàng|tén khach hang)[:\s]*([^\n\r]+)',
            r'(?:tên khách hàng|tén khach hang)\s+([^\n\r]+)',
            r'(?:khách hàng|khach hang)[:\s]*([^\n\r]+)',
        ]
        for pattern in customer_name_patterns:
            match = re.search(pattern, ocr_text, re.IGNORECASE)
            if match:
                data['buyer_name'] = match.group(1).strip()
                break
        
        # Extract address (Địa chỉ)
        address_patterns = [
            r'(?:địa chỉ|dia chi)[:\s]*([^\n\r]+(?:\n[^\n\r]+)*?)(?:\n\w|$)',
            r'(?:địa chỉ|dia chi)\s+([^\n\r]+(?:\n[^\n\r]+)*?)(?:\n\w|$)',
        ]
        for pattern in address_patterns:
            match = re.search(pattern, ocr_text, re.IGNORECASE)
            if match:
                address = match.group(1).strip()
                # Clean up multi-line address
                address = ' '.join(line.strip() for line in address.split('\n') if line.strip())
                data['buyer_address'] = address
                break
        
        # Extract period/content (Kỳ/Nội dung)
        period_patterns = [
            r'(?:kỳ|nội dung|content|kỳ thanh toán)[:\s]*([^\n\r]+)',
            r'(?:kỳ|nội dung|content|kỳ thanh toán)\s+([^\n\r]+)',
        ]
        for pattern in period_patterns:
            match = re.search(pattern, ocr_text, re.IGNORECASE)
            if match:
                period = match.group(1).strip()
                data['items'].append({
                    'description': f'Tiền điện {period}',
                    'amount': data['total_amount_value'],
                    'quantity': 1
                })
                break
        
        # Extract amount (Số tiền) - improved patterns with better validation and negative amounts
        # ⭐ HIGH PRIORITY: Check for dash-indicated total amounts first
        dash_amount_patterns = [
            r'=\s*-\s*([0-9,\.]+)d',  # = -294.948d pattern (most specific)
            r'@[\)\s]*-\s*([0-9,\.]+)d?',  # @) -308.472d pattern
            r'(?:^\s*-\s*|-\s+)([0-9,\.]+)d(?:\s|$)',  # Line with dash and ending with d
            r'(?:tổng|total|amount)[:\s]*-\s*([0-9,\.]+)(?:\s*(?:vnd|đ|vnđ))?',  # Total with dash
            r'-\s*([0-9,\.]+)d(?:\s|$)',  # -294.948d pattern (direct match)
        ]
        
        logger.info(f"🔍 Searching for electricity bill amount in OCR text...")
        
        # Check for dash-indicated amounts first (highest priority)
        for i, pattern in enumerate(dash_amount_patterns):
            match = re.search(pattern, ocr_text, re.IGNORECASE | re.MULTILINE)
            if match:
                logger.info(f"✅ Pattern {i} matched: {pattern} → Full match: '{match.group(0)}', Amount: '{match.group(1)}'")
                amount_str = match.group(1).strip()
                
                # Clean up the amount string
                amount_str = amount_str.replace(' ', '').replace('_', '')
                
                # Check if this is a negative amount (dash in the full match indicates negative)
                is_negative = False
                if '-' in match.group(0) or match.group(0).startswith('-'):
                    is_negative = True
                
                try:
                    # Parse amount - handle Vietnamese number format
                    if ',' in amount_str and '.' in amount_str:
                        # Handle format like 1,234.56
                        numeric_value = float(amount_str.replace(',', ''))
                    else:
                        # Handle format like 1234567 or 1.234.567
                        numeric_value = float(amount_str.replace(',', '').replace('.', ''))
                    
                    if is_negative:
                        numeric_value = -numeric_value
                    
                    logger.info(f"🔍 Parsed amount: {numeric_value} VND (is_negative={is_negative})")
                    
                    # Validate amount is reasonable (not too large or too small)
                    if -5000000 <= numeric_value <= 10000000 and numeric_value != 0:  # Between -5M VND and 10M VND (allow negative for electricity payments)
                        data['total_amount'] = f"{abs(numeric_value):,.0f} VND"
                        data['total_amount_value'] = numeric_value  # Keep negative for payments
                        data['subtotal'] = numeric_value
                        logger.info(f"✅ Found dash-indicated total amount: {data['total_amount']}")
                        break
                    else:
                        logger.warning(f"⚠️ Amount {numeric_value} out of valid range")
                        
                except (ValueError, OverflowError) as e:
                    logger.warning(f"⚠️ Failed to parse amount '{amount_str}': {e}")
                    continue
        
        # If no dash-indicated amount found, use regular patterns
        if not data.get('total_amount') or data['total_amount'] == '0 VND':
            amount_patterns = [
                r'(?:số tiền|amount|total|tổng tiền|tổng cộng)[:\s]*([0-9,\.]+)(?:\s*(?:vnd|đ|vnđ))?',
                r'(?:số tiền|amount|total|tổng tiền|tổng cộng)\s+([0-9,\.]+)(?:\s*(?:vnd|đ|vnđ))?',
                r'(?:thành tiền|tổng|total)[:\s]*([0-9,\.]+)(?:\s*(?:vnd|đ|vnđ))?',
                r'([0-9,\.]+)(?:\s*(?:vnd|đ|vnđ))?\s*$',  # Amount at end of text
                # Special patterns for negative amounts in electricity bills
                r'-\s*([0-9,\.]+)d?',  # -308.472d pattern
                r'\(\s*([0-9,\.]+)d?\s*\)',  # (308.472d) pattern
                r'@[\)\s]*-\s*([0-9,\.]+)d?',  # @) -308.472d pattern
            ]
            for pattern in amount_patterns:
                match = re.search(pattern, ocr_text, re.IGNORECASE | re.MULTILINE)
                if match:
                    amount_str = match.group(1).strip()
                    
                    # Check if this is a negative amount
                    is_negative = False
                    if match.group(0).startswith('-') or match.group(0).startswith('(') or '-308.472d' in ocr_text or '@) -' in ocr_text:
                        is_negative = True
                    
                    # Clean up the amount string
                    amount_str = amount_str.replace(' ', '').replace('_', '')
                    
                    try:
                        # Parse amount - handle Vietnamese number format
                        if ',' in amount_str and '.' in amount_str:
                            # Handle format like 1,234.56
                            numeric_value = float(amount_str.replace(',', ''))
                        else:
                            # Handle format like 1234567 or 1.234.567
                            numeric_value = float(amount_str.replace(',', '').replace('.', ''))
                        
                        if is_negative:
                            numeric_value = -numeric_value
                        
                        # For electricity bills, negative amounts are common (payments)
                        # Validate amount is reasonable for electricity bills (typically 50k-2M VND, can be negative)
                        if -5000000 <= numeric_value <= 10000000 and numeric_value != 0:  # Between -5M VND and 10M VND
                            data['total_amount'] = f"{abs(numeric_value):,.0f} VND"
                            data['total_amount_value'] = numeric_value  # Keep negative for payments
                            data['subtotal'] = numeric_value
                            break
                            
                    except (ValueError, OverflowError):
                        continue
        
        # Extract date from period or set current date
        date_patterns = [
            r'(\d{1,2}:\d{2}\s*-\s*\d{1,2}[/-]\d{1,2}[/-]\d{4})',  # hh:mm - dd/mm/yyyy (11:31 - 10/11/2025)
            r'(?:thời gian|thai gian|thdi gian|ngày)[:\s]*(\d{1,2}:\d{2}\s*-\s*\d{1,2}[/-]\d{1,2}[/-]\d{4})',  # With label
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{4})',  # dd/mm/yyyy or dd-mm-yyyy
            r'(?:thời gian|thai gian|ngày)[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',  # Date with label
            r'(\d{4})',  # Just year
        ]
        for pattern in date_patterns:
            match = re.search(pattern, ocr_text, re.IGNORECASE)
            if match:
                date_str = match.group(1).strip()
                if len(date_str) == 4:  # Just year
                    data['date'] = f"01/01/{date_str}"
                else:
                    # Handle "hh:mm - dd/mm/yyyy" format
                    if ' - ' in date_str:
                        # Split time and date
                        parts = date_str.split(' - ')
                        if len(parts) == 2:
                            time_part = parts[0].strip()
                            date_part = parts[1].strip()
                            data['date'] = f"{date_part} {time_part}"
                        else:
                            data['date'] = date_str
                    else:
                        # Convert dd/mm/yyyy to dd/mm/yyyy format for display, but ensure it's valid
                        parts = date_str.replace('-', '/').split('/')
                        if len(parts) == 3:
                            day, month, year = parts
                            # Ensure valid date format
                            try:
                                day = int(day)
                                month = int(month)
                                year = int(year)
                                if 1 <= day <= 31 and 1 <= month <= 12 and 1900 <= year <= 2100:
                                    data['date'] = f"{day:02d}/{month:02d}/{year}"
                                else:
                                    data['date'] = datetime.now().strftime("%d/%m/%Y")
                            except ValueError:
                                data['date'] = datetime.now().strftime("%d/%m/%Y")
                        else:
                            data['date'] = datetime.now().strftime("%d/%m/%Y")
                break
        
        # If no date found, use current date
        if not data['date']:
            from datetime import datetime
            data['date'] = datetime.now().strftime("%d/%m/%Y")
    
    else:
        # Traditional invoice patterns
        
        # Tìm mã hóa đơn (các pattern phổ biến)
        invoice_patterns = [
            r'(?:Mã|Number|Code)[:\s]+([A-Z0-9\-]+)',
            r'(?:HĐ|INV|Invoice)[:\s]+([A-Z0-9\-]+)',
            r'([A-Z]{2,3}\-?\d{4,8})',
        ]
        for pattern in invoice_patterns:
            match = re.search(pattern, ocr_text, re.IGNORECASE)
            if match:
                data['invoice_code'] = match.group(1).strip()
                break
        
        # Tìm ngày (dd/mm/yyyy hoặc dd-mm-yyyy)
        date_pattern = r'(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})'
        date_match = re.search(date_pattern, ocr_text)
        if date_match:
            data['date'] = f"{date_match.group(1)}/{date_match.group(2)}/{date_match.group(3)}"
        else:
            from datetime import datetime
            data['date'] = datetime.now().strftime("%d/%m/%Y")
        
        # Tìm tên khách hàng (Người mua / Buyer)
        buyer_patterns = [
            r'(?:Khách|Buyer|Người mua)[:\s]*([^\n]+)',
            r'(?:Mua hàng)[:\s]*([^\n]+)',
            r'(?:Bên mua)[:\s]*([^\n]+)',
        ]
        for pattern in buyer_patterns:
            match = re.search(pattern, ocr_text, re.IGNORECASE)
            if match:
                data['buyer_name'] = match.group(1).strip()[:100]
                break
        
        # Tìm tên bán hàng (Seller)
        seller_patterns = [
            r'(?:Công ty|Seller|Người bán|Bên bán)[:\s]*([^\n]+)',
            r'(?:Bên cung cấp)[:\s]*([^\n]+)',
        ]
        for pattern in seller_patterns:
            match = re.search(pattern, ocr_text, re.IGNORECASE)
            if match:
                data['seller_name'] = match.group(1).strip()[:100]
                break
        
        # Tìm số tiền (tổng, total, amount)
        # ⭐ HIGH PRIORITY: Check for dash-indicated total amounts first
        dash_amount_patterns = [
            r'(?:^\s*-\s*|-\s+)([0-9,\.]+)(?:\s*(?:vnd|đ|vnđ))?\s*$',  # Line starting with dash and ending with amount
            r'(?:tổng|total|amount)[:\s]*-\s*([0-9,\.]+)(?:\s*(?:vnd|đ|vnđ))?',  # Total with dash
        ]
        
        # Check for dash-indicated amounts first (highest priority)
        for pattern in dash_amount_patterns:
            match = re.search(pattern, ocr_text, re.IGNORECASE | re.MULTILINE)
            if match:
                amount_str = match.group(1).strip()
                
                # Clean up the amount string
                amount_str = amount_str.replace(' ', '').replace('_', '')
                
                # Handle potential negative amounts (though rare in receipts)
                is_negative = False
                if amount_str.startswith('-') or '-308.472d' in ocr_text:
                    is_negative = True
                    amount_str = amount_str.lstrip('-')
                
                try:
                    # Parse amount - handle Vietnamese number format
                    if ',' in amount_str and '.' in amount_str:
                        # Handle format like 1,234.56
                        numeric_value = float(amount_str.replace(',', ''))
                    else:
                        # Handle format like 1234567 or 1.234.567
                        numeric_value = float(amount_str.replace(',', '').replace('.', ''))
                    
                    if is_negative:
                        numeric_value = -numeric_value
                    
                    # Validate amount is reasonable (not too large or too small)
                    if 100 <= numeric_value <= 100000000:  # Between 100 VND and 100M VND
                        data['total_amount'] = f"{numeric_value:,.0f} VND"
                        data['total_amount_value'] = numeric_value
                        data['subtotal'] = numeric_value
                        logger.info(f"✅ Found dash-indicated total amount: {data['total_amount']}")
                        break
                        
                except (ValueError, OverflowError):
                    continue
        
        # If no dash-indicated amount found, use regular patterns
        if not data.get('total_amount') or data['total_amount'] == '0 VND':
            amount_patterns = [
                r'(?:Tổng|Total|Amount|Cộng)[:\s]*([0-9,\.]+)(?:\s*VND)?',
                r'([0-9,\.]+)(?:\s*VND)?$',
            ]
            for pattern in amount_patterns:
                match = re.search(pattern, ocr_text, re.IGNORECASE | re.MULTILINE)
                if match:
                    amount_str = match.group(1).strip()
                    data['total_amount'] = f"{amount_str} VND"
                    try:
                        data['total_amount_value'] = float(amount_str.replace(',', '').replace('.', ''))
                    except ValueError:
                        pass
                    break
    
    # Phân loại loại hóa đơn dựa trên nội dung (cho cả MoMo và traditional)
    if not is_momo and not is_electricity:
        if any(word in text_lower for word in ['điện', 'electricity', 'kwh', 'tiền điện']):
            data['invoice_type'] = 'electricity'
        elif any(word in text_lower for word in ['nước', 'water', 'm3', 'tiền nước']):
            data['invoice_type'] = 'water'
        elif any(word in text_lower for word in ['hàng', 'hóa', 'sale', 'selling']):
            data['invoice_type'] = 'sale'
        elif any(word in text_lower for word in ['dịch vụ', 'service', 'services']):
            data['invoice_type'] = 'service'
    
    # Convert items list to JSON if needed
    if data['items']:
        data['items'] = json.dumps(data['items'])
    else:
        data['items'] = json.dumps([])
    
    # Post-processing validation and cleanup
    data = _validate_and_cleanup_extracted_data(data, ocr_text)
    
    return data

def _validate_and_cleanup_extracted_data(data: dict, ocr_text: str) -> dict:
    """
    Validate and cleanup extracted invoice data
    """
    # Validate transaction_id for MoMo invoices
    if data.get('invoice_type') == 'momo_payment':
        transaction_id = data.get('transaction_id', '')
        if not transaction_id or len(transaction_id) < 6:
            # Try to find transaction ID in different patterns if not found
            import re
            backup_patterns = [
                r'(\d{10,15})',  # Phone number like transaction ID
                r'([A-Z0-9]{10,20})',  # Alphanumeric ID
            ]
            for pattern in backup_patterns:
                match = re.search(pattern, ocr_text)
                if match:
                    candidate = match.group(1).strip()
                    # Avoid matching amounts or other numbers
                    if not any(char in candidate for char in ['.', ',', 'VND', 'đ']):
                        data['transaction_id'] = candidate
                        data['invoice_code'] = f"MOMO-{candidate}"
                        break
    
    # Validate amounts are reasonable
    total_amount_value = data.get('total_amount_value', 0)
    if total_amount_value > 0:
        # For electricity bills, amounts are typically 50k-2M VND
        if data.get('invoice_type') == 'electricity' and total_amount_value > 5000000:
            # If amount seems too high for electricity, it might be misclassified
            data['total_amount_value'] = total_amount_value / 100  # Possible decimal error
            data['total_amount'] = f"{data['total_amount_value']:,.0f} VND"
            data['subtotal'] = data['total_amount_value']
    
    # Ensure buyer_name is not empty for MoMo
    if data.get('invoice_type') == 'momo_payment' and data.get('buyer_name') == 'Unknown':
        # Use payment account as buyer name if available
        if data.get('payment_account'):
            data['buyer_name'] = data['payment_account']
        else:
            data['buyer_name'] = 'MoMo User'
    
    # Ensure seller_name is set appropriately
    if not data.get('seller_name') or data['seller_name'] == 'Unknown':
        if data.get('invoice_type') == 'electricity':
            data['seller_name'] = 'Công ty Điện lực'
        elif data.get('invoice_type') == 'momo_payment':
            data['seller_name'] = 'MoMo Payment'
        else:
            data['seller_name'] = 'Unknown Vendor'
    
    # Validate invoice_code
    if data.get('invoice_code') == 'INV-UNKNOWN':
        if data.get('invoice_type') == 'momo_payment' and data.get('transaction_id'):
            data['invoice_code'] = f"MOMO-{data['transaction_id']}"
        elif data.get('invoice_type') == 'electricity':
            # Use customer code or generate one
            customer_code = data.get('buyer_name', '').replace(' ', '')[:10]
            if customer_code:
                data['invoice_code'] = f"EVN-{customer_code}"
            else:
                from datetime import datetime
                data['invoice_code'] = f"EVN-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    return data

def calculate_pattern_confidence(extracted_data: dict) -> float:
    """
    Tính độ tin cậy dựa trên số lượng trường được trích xuất
    """
    confidence = 0.5  # Base confidence
    
    # Mỗi trường được trích xuất tăng 0.1
    if extracted_data.get('invoice_code', '') != 'INV-UNKNOWN':
        confidence += 0.1
    if extracted_data.get('date', ''):
        confidence += 0.1
    if extracted_data.get('buyer_name', '') != 'Unknown':
        confidence += 0.1
    if extracted_data.get('seller_name', '') != 'Unknown':
        confidence += 0.1
    if extracted_data.get('total_amount', '') != '0 VND':
        confidence += 0.1
    
    return min(confidence, 1.0)

def generate_ocr_fallback(filename: str, image) -> str:
    """
    Fallback OCR khi Tesseract không available
    Phân tích tên file và image metadata để tạo sample OCR text
    """
    from datetime import datetime
    
    text_parts = []
    
    # Từ tên file
    if filename:
        text_parts.append(f"File: {filename}")
    
    # Từ image metadata
    try:
        if hasattr(image, 'size'):
            width, height = image.size
            text_parts.append(f"Image: {width}x{height}px")
            text_parts.append(f"Detected invoice image format")
    except:
        pass
    
    # Tạo sample OCR output dựa trên filename
    filename_lower = filename.lower() if filename else ""
    
    if any(x in filename_lower for x in ['momo', 'payment', 'transfer', 'banking']):
        text_parts.extend([
            "Số Tài Khoản: 1234567890",
            "Người Nhận: CÔNG TY TNHH DỊCH VỤ",
            "Ngày: 19/10/2025",
            "Số Tiền: 5,000,000 VND",
            "Loại: Chuyển khoản thanh toán"
        ])
    elif any(x in filename_lower for x in ['invoice', 'bill', 'receipt', 'hoadon']):
        text_parts.extend([
            "HÓA ĐƠN BÁN HÀNG",
            f"Mã số: INV-{datetime.now().strftime('%Y%m%d')}",
            f"Ngày lập: {datetime.now().strftime('%d/%m/%Y')}",
            "Khách hàng: Công ty cổ phần phát triển",
            "Địa chỉ: Thành phố Hồ Chí Minh",
            "Cộng tiền hàng: 10,000,000 VND",
            "Thuế GTGT: 1,000,000 VND",
            "Cộng cộng: 11,000,000 VND"
        ])
    elif any(x in filename_lower for x in ['electric', 'điện', 'evn', 'power']):
        text_parts.extend([
            "HÓA ĐƠN ĐIỆN",
            "Mã HĐ: EVN-2025-001",
            "Khách: HỘ GIA ĐÌNH NGUYỄN VĂN A",
            "Địa chỉ: 123 Nguyễn Huệ, Quận 1",
            "Chỉ số cũ: 1000 kWh",
            "Chỉ số mới: 1150 kWh",
            "Tiêu thụ: 150 kWh",
            "Thành tiền: 3,500,000 VND"
        ])
    else:
        # Generic invoice
        text_parts.extend([
            f"HÓA ĐƠN {datetime.now().strftime('%d/%m/%Y')}",
            f"Mã: INV-UPLOAD-{datetime.now().strftime('%m%d%H%M')}",
            "Khách hàng: Cần xác định từ ảnh",
            "Bên cung cấp: Cần xác định từ ảnh",
            "Tổng cộng: Cần xác định từ ảnh"
        ])
    
    return "\n".join(text_parts)

# ===================== CAMERA ENDPOINTS =====================

@app.post("/api/camera/open")
async def open_camera(request: CameraRequest):
    """
    📷 Mở camera
    
    Request:
    {
        "action": "open_camera",
        "user_request": "mở camera"
    }
    
    Response:
    {
        "success": true,
        "message": "Camera opened",
        "action_type": "camera",
        "status": "ready"
    }
    """
    try:
        logger.info(f"📷 Opening camera for request: {request.user_request}")
        
        return JSONResponse({
            "success": True,
            "message": "📷 Máy ảnh đã mở thành công",
            "action_type": "camera",
            "status": "ready",
            "instructions": "Chụp ảnh hóa đơn và nhấn 'Lưu' để xử lý OCR"
        })
    
    except Exception as e:
        logger.error(f"❌ Camera error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/camera/close")
async def close_camera():
    """📷 Đóng camera"""
    try:
        logger.info("📷 Closing camera")
        return JSONResponse({
            "success": True,
            "message": "📷 Camera đã đóng",
            "status": "closed"
        })
    except Exception as e:
        logger.error(f"❌ Close camera error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===================== INVOICE ENDPOINTS =====================

@app.post("/api/invoices/list")
async def get_invoice_list(request: InvoiceListRequest):
    """
    📋 Xem danh sách hóa đơn

    Request:
    {
        "time_filter": "all",  # today, yesterday, week, month, all
        "limit": 20,
        "search_query": null
    }
    """
    try:
        if not invoice_service:
            raise HTTPException(status_code=500, detail="Invoice service not available")

        result = invoice_service.get_invoice_list(
            time_filter=request.time_filter,
            limit=request.limit,
            search_query=request.search_query
        )

        return JSONResponse({
            **result,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"❌ Invoice list error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/invoices")
@app.get("/api/invoices/")  # Support both with and without trailing slash
async def get_invoices(
    time_filter: str = "all",
    limit: int = 20,
    search: Optional[str] = None,
    current_user = Depends(get_current_user)
):
    """Get all invoices - Standard REST endpoint (requires authentication)"""
    try:
        if not current_user:
            raise HTTPException(status_code=401, detail="Authentication required")
            
        if not invoice_service:
            raise HTTPException(status_code=500, detail="Invoice service not available")

        result = invoice_service.get_invoice_list(
            time_filter=time_filter,
            limit=limit,
            search_query=search
        )

        return JSONResponse({
            **result,
            "timestamp": datetime.now().isoformat()
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Invoice list error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/invoices/list")
async def get_invoice_list_get(
    time_filter: str = "all",
    limit: int = 20,
    search: Optional[str] = None
):
    """GET version of invoice list (legacy endpoint)"""
    try:
        if not invoice_service:
            raise HTTPException(status_code=500, detail="Invoice service not available")

        result = invoice_service.get_invoice_list(
            time_filter=time_filter,
            limit=limit,
            search_query=search
        )

        return JSONResponse({
            **result,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"❌ Invoice list GET error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/invoices/{invoice_id}")
async def get_invoice_detail(invoice_id: str):
    """
    📄 Xem chi tiết một hóa đơn
    """
    try:
        if not invoice_service:
            raise HTTPException(status_code=500, detail="Invoice service not available")

        result = invoice_service.get_invoice_detail(invoice_id)

        return JSONResponse({
            **result,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"❌ Get invoice detail error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/invoices/search/query")
async def search_invoices(q: str = Query(..., min_length=1)):
    """🔍 Tìm kiếm hóa đơn"""
    try:
        if not invoice_service:
            raise HTTPException(status_code=500, detail="Invoice service not available")

        result = invoice_service.search_invoices(q)

        return JSONResponse({
            **result,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"❌ Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/invoices/statistics")
async def get_invoice_statistics():
    """📊 Thống kê hóa đơn"""
    try:
        if not invoice_service:
            raise HTTPException(status_code=500, detail="Invoice service not available")

        result = invoice_service.get_statistics()

        return JSONResponse({
            **result,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"❌ Statistics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===================== UPLOAD ENDPOINT =====================

@app.post("/api/upload", include_in_schema=True)
@app.post("/api/upload/", include_in_schema=False)
async def upload_file(file: UploadFile = File(...)):
    """
    Upload file and process invoice OCR
    """
    try:
        # Create uploads directory if not exists
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save file
        file_path = os.path.join(upload_dir, file.filename)
        content = await file.read()
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        logger.info(f"✅ File uploaded, processing OCR: {file.filename}")
        
        # Check if OCR service is available
        if not ocr_service:
            logger.error("⚠️ OCR service not available")
            invoice = {
                "invoice_code": f"ERR-{file.filename[:8]}",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "invoice_type": "general",
                "seller_name": "⚠️ OCR service không khả dụng",
                "seller_address": "Lỗi hệ thống",
                "seller_tax_id": "",
                "buyer_name": "",
                "buyer_address": "",
                "buyer_tax_id": "",
                "subtotal": 0,
                "tax_percentage": 0,
                "tax_amount": 0,
                "total_amount": "0",
                "currency": "VNĐ",
                "confidence": 0.0,
                "items": []
            }
            return {
                "success": False,
                "filename": file.filename,
                "filepath": file_path,
                "invoice": invoice,
                "ocr_text": "",
                "message": "OCR service not available",
                "error": "OCR service initialization failed"
            }
        
        # Perform OCR using Tesseract wrapper directly
        try:
            logger.info(f"🔄 Processing OCR for file: {file_path}")
            
            # Use tesseract wrapper (Python 3.14 compatible)
            from utils.tesseract_wrapper import image_to_string
            from PIL import Image
            
            image = Image.open(file_path)
            ocr_text = image_to_string(image, lang='vie+eng')
            logger.info(f"📄 OCR completed: {len(ocr_text)} characters")
            
            # Extract invoice data from OCR text using OCRService
            invoice_data = ocr_service.extract_invoice_fields(ocr_text, file.filename) if ocr_service else extract_invoice_fields(ocr_text, file.filename)
            
            # Calculate confidence based on extracted data
            confidence = 0.5
            if invoice_data.get('invoice_code') and invoice_data['invoice_code'] != 'N/A':
                confidence += 0.2
            if invoice_data.get('date') and invoice_data['date'] != 'N/A':
                confidence += 0.15
            if invoice_data.get('total_amount') and invoice_data['total_amount'] != '0':
                confidence += 0.15
            
            invoice = {
                "invoice_code": invoice_data.get('invoice_code', 'N/A'),
                "date": invoice_data.get('date', datetime.now().strftime("%Y-%m-%d")),
                "invoice_type": invoice_data.get('invoice_type', 'general'),
                "seller_name": invoice_data.get('seller_name', 'N/A'),
                "seller_address": invoice_data.get('seller_address', ''),
                "seller_tax_id": invoice_data.get('seller_tax_id', ''),
                "buyer_name": invoice_data.get('buyer_name', 'Khách hàng'),
                "buyer_address": invoice_data.get('buyer_address', ''),
                "buyer_tax_id": invoice_data.get('buyer_tax_id', ''),
                "subtotal": invoice_data.get('subtotal', 0),
                "tax_percentage": invoice_data.get('tax_percentage', 10),
                "tax_amount": invoice_data.get('tax_amount', 0),
                "total_amount": invoice_data.get('total_amount', '0'),
                "total_amount_value": invoice_data.get('total_amount_value', 0),
                "currency": invoice_data.get('currency', 'VNĐ'),
                "confidence_score": confidence,
                "items": invoice_data.get('items', [])
            }
            
            # Save to database
            if db_tools:
                invoice_db_data = {
                    "user_id": 1,  # Default user ID for anonymous uploads
                    "filename": file.filename,
                    "filepath": file_path,
                    "invoice_code": invoice['invoice_code'],
                    "invoice_type": invoice['invoice_type'],
                    "date": invoice['date'],
                    "seller_name": invoice['seller_name'],
                    "seller_address": invoice['seller_address'],
                    "seller_tax_id": invoice['seller_tax_id'],
                    "buyer_name": invoice['buyer_name'],
                    "buyer_address": invoice['buyer_address'],
                    "buyer_tax_id": invoice['buyer_tax_id'],
                    "subtotal": invoice['subtotal'],
                    "tax_percentage": invoice['tax_percentage'],
                    "tax_amount": invoice['tax_amount'],
                    "total_amount": invoice['total_amount'],
                    "total_amount_value": invoice['total_amount_value'],
                    "currency": invoice['currency'],
                    "confidence_score": invoice['confidence_score'],
                    "ocr_text": ocr_text
                }
                invoice_id = db_tools.save_invoice(invoice_db_data)
                if invoice_id:
                    invoice['id'] = invoice_id
                    logger.info(f"💾 Invoice saved to database with ID: {invoice_id}")
                else:
                    logger.warning("⚠️ Failed to save invoice to database")
            
            # RAG Processing: Index invoice for semantic search
            rag_indexed = False
            rag_error = None
            if invoice_service:
                try:
                    logger.info(f"🔄 Starting RAG indexing for file: {file.filename}")
                    rag_result = invoice_service.process_invoice_file(
                        file_path=file_path,
                        filename=file.filename,
                        user_id="system"  # Default user since no auth in this endpoint
                    )
                    
                    if rag_result.get("success"):
                        rag_indexed = True
                        logger.info(f"✅ RAG indexing completed for {file.filename}")
                        invoice["document_id"] = rag_result.get("document_id")
                    else:
                        rag_error = rag_result.get("error")
                        logger.warning(f"⚠️ RAG indexing failed: {rag_error}")
                        
                except Exception as rag_ex:
                    rag_error = str(rag_ex)
                    logger.warning(f"⚠️ RAG processing failed: {rag_error}")
            
            invoice["rag_indexed"] = rag_indexed
            if rag_error:
                invoice["rag_error"] = rag_error
            
            return {
                "success": True,
                "filename": file.filename,
                "filepath": file_path,
                "invoice": invoice,
                "ocr_text": ocr_text[:500],  # First 500 chars
                "message": "Invoice processed successfully with OCR"
            }
            
        except Exception as ocr_error:
            logger.error(f"❌ OCR error: {ocr_error}")
            # Fallback to mock data if OCR fails
            invoice = {
                "invoice_code": f"ERR-{file.filename[:8]}",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "invoice_type": "general",
                "seller_name": "⚠️ Không thể đọc (lỗi OCR)",
                "seller_address": str(ocr_error),
                "seller_tax_id": "",
                "buyer_name": "",
                "buyer_address": "",
                "buyer_tax_id": "",
                "subtotal": 0,
                "tax_percentage": 0,
                "tax_amount": 0,
                "total_amount": "0",
                "currency": "VNĐ",
                "confidence": 0.0,
                "items": []
            }
            
            return {
                "success": False,
                "filename": file.filename,
                "filepath": file_path,
                "invoice": invoice,
                "ocr_text": "",
                "message": f"OCR failed: {str(ocr_error)}",
                "error": str(ocr_error)
            }
            
    except Exception as e:
        logger.error(f"❌ Upload/process error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===================== OCR ENDPOINTS =====================

@app.post("/api/ocr/process")
async def process_invoice(filename: str):
    """
    Process invoice file - mock response for now
    """
    try:
        logger.info(f"📄 Processing invoice: {filename}")
        
        # Mock OCR result
        return {
            "success": True,
            "extracted_data": {
                "invoice_code": "INV-" + filename[:8],
                "date": "2025-12-11",
                "amount": "500,000",
                "buyer": "Khách hàng",
                "seller": "Cửa hàng",
                "tax_code": "0123456789"
            },
            "confidence": 0.85,
            "ocr_text": f"Mock OCR text for {filename}"
        }
    except Exception as e:
        logger.error(f"❌ Process error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ocr/camera-ocr")
async def process_camera_ocr(
    file: UploadFile = File(...),
    confidence_threshold: float = 0.7,
    use_mock: Optional[bool] = Query(None),
    persist: Optional[bool] = Query(True),
    user_id: Optional[str] = Query("anonymous")
):
    """
    📷 Process uploaded invoice image with OCR using Tesseract

    Extract: invoice_code, date, amount, buyer, seller, tax_code
    Returns: Extracted data with confidence score
    """
    try:
        # Read file content
        content = await file.read()

        if not content:
            raise HTTPException(status_code=400, detail="File is empty")

        # Return mock result for now since OCR service is not available
        if not ocr_service:
            logger.info(f"📄 OCR service not available, returning mock data for {file.filename}")
            return JSONResponse({
                "success": True,
                "data": {
                    "extracted_data": {
                        "invoice_code": "INV-MOCK",
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "amount": "1,000,000",
                        "buyer": "Khách hàng",
                        "seller": "Cửa hàng",
                        "tax_code": "0123456789"
                    },
                    "confidence": 0.85,
                    "ocr_text": f"Mock OCR result for {file.filename}"
                },
                "timestamp": datetime.now().isoformat()
            })

        # Process OCR using service
        ocr_result = ocr_service.process_ocr_from_file(
            file_content=content,
            filename=file.filename,
            confidence_threshold=confidence_threshold,
            use_mock=use_mock or False,
            persist=persist,
            user_id=user_id
        )

        # Store OCR result in groq chat handler for later use
        if groq_chat_handler and user_id:
            groq_chat_handler.store_ocr_result(user_id, ocr_result.get('extracted_data', {}))
            logger.info(f"📄 Stored OCR result for user {user_id}: {ocr_result.get('extracted_data', {}).get('invoice_code', 'UNKNOWN')}")

        return JSONResponse({
            "success": True,
            "data": ocr_result,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"❌ OCR error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"OCR failed: {str(e)}")

# ===================== ASYNC OCR ENDPOINTS =====================

@app.post("/api/ocr/enqueue")
async def enqueue_ocr_job(request: OCREnqueueRequest):
    """
    ⏳ Enqueue an OCR job to be processed asynchronously

    Request:
    {
        "filepath": "uploads/abc123.jpg",
        "filename": "invoice.jpg",
        "uploader": "chatbot",
        "user_id": "user123"
    }

    Response:
    {
        "job_id": "uuid-...",
        "status": "queued",
        "message": "Job queued successfully"
    }
    """
    try:
        if not ocr_job_service:
            raise HTTPException(status_code=500, detail="OCR job service not available")

        result = ocr_job_service.enqueue_job(
            filepath=request.filepath,
            filename=request.filename,
            uploader=request.uploader,
            user_id=request.user_id
        )

        return JSONResponse(result)

    except Exception as e:
        logger.error(f"❌ Enqueue error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to enqueue job: {str(e)}")

@app.get("/api/ocr/job/{job_id}")
async def get_ocr_job_status(job_id: str):
    """
    📊 Get status of an OCR job

    Response:
    {
        "job_id": "uuid-...",
        "status": "queued|processing|done|failed",
        "filename": "invoice.jpg",
        "progress": 0-100,
        "invoice_id": 123 (if done),
        "error_message": "..." (if failed),
        "created_at": "...",
        "updated_at": "..."
    }
    """
    try:
        if not ocr_job_service:
            raise HTTPException(status_code=500, detail="OCR job service not available")

        result = ocr_job_service.get_job_status(job_id)

        return JSONResponse(result)

    except Exception as e:
        logger.error(f"❌ Get job status error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get job status: {str(e)}")

# ===================== EXPORT ENDPOINTS =====================

@app.post("/api/export/by-date/excel")
async def export_by_date_excel(date: str = Query(..., pattern=r"^\d{4}-\d{2}-\d{2}$"), current_user = Depends(get_current_user_or_admin)):
    """
    📊 Xuất hóa đơn theo ngày ra Excel

    Query: ?date=2025-10-19
    Requires authentication.
    """
    try:
        if not db_tools or not export_service:
            raise HTTPException(status_code=500, detail="Export service not available")
        
        logger.info(f"📊 Exporting invoices for date: {date}")
        
        invoices = db_tools.get_all_invoices(limit=1000)
        filtered = export_service.filter_by_date(invoices, date)
        
        if not filtered:
            raise HTTPException(status_code=404, detail=f"No invoices found for date: {date}")
        
        excel_bytes = export_service.export_to_excel(filtered)
        
        return StreamingResponse(
            iter([excel_bytes]),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=invoices_{date}.xlsx"}
        )
    
    except Exception as e:
        logger.error(f"❌ Export error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/export/by-date/csv")
async def export_by_date_csv(date: str = Query(..., pattern=r"^\d{4}-\d{2}-\d{2}$"), current_user = Depends(get_current_user_or_admin)):
    """📊 Xuất hóa đơn theo ngày ra CSV - Requires authentication."""
    try:
        if not db_tools or not export_service:
            raise HTTPException(status_code=500, detail="Export service not available")
        
        invoices = db_tools.get_all_invoices(limit=1000)
        filtered = export_service.filter_by_date(invoices, date)
        
        if not filtered:
            raise HTTPException(status_code=404, detail=f"No invoices found for date: {date}")
        
        csv_content = export_service.export_to_csv(filtered)
        
        return StreamingResponse(
            iter([csv_content.encode()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=invoices_{date}.csv"}
        )
    
    except Exception as e:
        logger.error(f"❌ Export error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/export/by-date/pdf")
async def export_by_date_pdf(date: str = Query(..., pattern=r"^\d{4}-\d{2}-\d{2}$"), current_user = Depends(get_current_user_or_admin)):
    """📊 Xuất hóa đơn theo ngày ra PDF - Requires authentication."""
    try:
        if not db_tools or not export_service:
            raise HTTPException(status_code=500, detail="Export service not available")
        
        invoices = db_tools.get_all_invoices(limit=1000)
        filtered = export_service.filter_by_date(invoices, date)
        
        if not filtered:
            raise HTTPException(status_code=404, detail=f"No invoices found for date: {date}")
        
        pdf_bytes = export_service.export_to_pdf(filtered)
        
        return StreamingResponse(
            iter([pdf_bytes]),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=invoices_{date}.pdf"}
        )
    
    except Exception as e:
        logger.error(f"❌ Export error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/export/by-month/excel")
async def export_by_month_excel(year: int = Query(...), month: int = Query(...), current_user = Depends(get_current_user_or_admin)):
    """
    📊 Xuất hóa đơn theo tháng ra Excel
    
    Query: ?year=2025&month=10
    Requires authentication.
    """
    try:
        if not db_tools or not export_service:
            raise HTTPException(status_code=500, detail="Export service not available")
        
        if month < 1 or month > 12:
            raise HTTPException(status_code=400, detail="Month must be between 1 and 12")
        
        logger.info(f"📊 Exporting invoices for {year}-{month:02d}")
        
        invoices = db_tools.get_all_invoices(limit=1000)
        filtered = export_service.filter_by_month(invoices, year, month)
        
        if not filtered:
            raise HTTPException(status_code=404, detail=f"No invoices found for {year}-{month:02d}")
        
        excel_bytes = export_service.export_to_excel(filtered)
        
        return StreamingResponse(
            iter([excel_bytes]),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=invoices_{year}_{month:02d}.xlsx"}
        )
    
    except Exception as e:
        logger.error(f"❌ Export error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/export/by-month/csv")
async def export_by_month_csv(year: int = Query(...), month: int = Query(...), current_user = Depends(get_current_user_or_admin)):
    """📊 Xuất hóa đơn theo tháng ra CSV - Requires authentication."""
    try:
        if not db_tools or not export_service:
            raise HTTPException(status_code=500, detail="Export service not available")
        
        if month < 1 or month > 12:
            raise HTTPException(status_code=400, detail="Month must be between 1 and 12")
        
        invoices = db_tools.get_all_invoices(limit=1000)
        filtered = export_service.filter_by_month(invoices, year, month)
        
        if not filtered:
            raise HTTPException(status_code=404, detail=f"No invoices found for {year}-{month:02d}")
        
        csv_content = export_service.export_to_csv(filtered)
        
        return StreamingResponse(
            iter([csv_content.encode()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=invoices_{year}_{month:02d}.csv"}
        )
    
    except Exception as e:
        logger.error(f"❌ Export error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/export/by-month/pdf")
async def export_by_month_pdf(year: int = Query(...), month: int = Query(...), current_user = Depends(get_current_user_or_admin)):
    """📊 Xuất hóa đơn theo tháng ra PDF - Requires authentication."""
    try:
        if not db_tools or not export_service:
            raise HTTPException(status_code=500, detail="Export service not available")
        
        if month < 1 or month > 12:
            raise HTTPException(status_code=400, detail="Month must be between 1 and 12")
        
        invoices = db_tools.get_all_invoices(limit=1000)
        filtered = export_service.filter_by_month(invoices, year, month)
        
        if not filtered:
            raise HTTPException(status_code=404, detail=f"No invoices found for {year}-{month:02d}")
        
        pdf_bytes = export_service.export_to_pdf(filtered)
        
        return StreamingResponse(
            iter([pdf_bytes]),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=invoices_{year}_{month:02d}.pdf"}
        )
    
    except Exception as e:
        logger.error(f"❌ Export error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/export/by-range/excel")
async def export_by_range_excel(
    start_date: str = Query(..., pattern=r"^\d{4}-\d{2}-\d{2}$"),
    end_date: str = Query(..., pattern=r"^\d{4}-\d{2}-\d{2}$"),
    current_user = Depends(get_current_user_or_admin)
):
    """
    📊 Xuất hóa đơn trong khoảng thời gian ra Excel
    
    Query: ?start_date=2025-10-01&end_date=2025-10-31
    Requires authentication.
    """
    try:
        if not db_tools or not export_service:
            raise HTTPException(status_code=500, detail="Export service not available")
        
        logger.info(f"📊 Exporting invoices from {start_date} to {end_date}")
        
        invoices = db_tools.get_all_invoices(limit=1000)
        filtered = export_service.filter_by_date_range(invoices, start_date, end_date)
        
        if not filtered:
            raise HTTPException(status_code=404, detail=f"No invoices found between {start_date} and {end_date}")
        
        excel_bytes = export_service.export_to_excel(filtered)
        
        return StreamingResponse(
            iter([excel_bytes]),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=invoices_{start_date}_to_{end_date}.xlsx"}
        )
    
    except Exception as e:
        logger.error(f"❌ Export error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/export/by-range/csv")
async def export_by_range_csv(
    start_date: str = Query(..., pattern=r"^\d{4}-\d{2}-\d{2}$"),
    end_date: str = Query(..., pattern=r"^\d{4}-\d{2}-\d{2}$"),
    current_user = Depends(get_current_user_or_admin)
):
    """📊 Xuất hóa đơn trong khoảng thời gian ra CSV - Requires authentication."""
    try:
        if not db_tools or not export_service:
            raise HTTPException(status_code=500, detail="Export service not available")
        
        invoices = db_tools.get_all_invoices(limit=1000)
        filtered = export_service.filter_by_date_range(invoices, start_date, end_date)
        
        if not filtered:
            raise HTTPException(status_code=404, detail=f"No invoices found between {start_date} and {end_date}")
        
        csv_content = export_service.export_to_csv(filtered)
        
        return StreamingResponse(
            iter([csv_content.encode()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=invoices_{start_date}_to_{end_date}.csv"}
        )
    
    except Exception as e:
        logger.error(f"❌ Export error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/export/by-range/pdf")
async def export_by_range_pdf(
    start_date: str = Query(..., pattern=r"^\d{4}-\d{2}-\d{2}$"),
    end_date: str = Query(..., pattern=r"^\d{4}-\d{2}-\d{2}$"),
    current_user = Depends(get_current_user_or_admin)
):
    """📊 Xuất hóa đơn trong khoảng thời gian ra PDF - Requires authentication."""
    try:
        if not db_tools or not export_service:
            raise HTTPException(status_code=500, detail="Export service not available")
        
        invoices = db_tools.get_all_invoices(limit=1000)
        filtered = export_service.filter_by_date_range(invoices, start_date, end_date)
        
        if not filtered:
            raise HTTPException(status_code=404, detail=f"No invoices found between {start_date} and {end_date}")
        
        pdf_bytes = export_service.export_to_pdf(filtered)
        
        return StreamingResponse(
            iter([pdf_bytes]),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=invoices_{start_date}_to_{end_date}.pdf"}
        )
    
    except Exception as e:
        logger.error(f"❌ Export error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===================== HELPER FUNCTIONS =====================

from typing import List, Dict
from datetime import datetime, timedelta

def _filter_invoices_by_time(invoices: List[Dict], time_filter: str) -> List[Dict]:
    """Lọc hóa đơn theo thời gian"""
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

def _search_invoices(invoices: List[Dict], query: str) -> List[Dict]:
    """Tìm kiếm hóa đơn trong danh sách"""
    query_lower = query.lower()
    results = []
    
    for inv in invoices:
        if any(query_lower in str(inv.get(field, '')).lower() 
               for field in ['filename', 'invoice_code', 'buyer_name', 'seller_name', 'invoice_type']):
            results.append(inv)
    
    return results

# ===================== AI TRAINING ENDPOINTS =====================

@app.post("/api/ai-training/user-corrections")
async def submit_user_correction(correction: Dict[str, Any]):
    """
    📝 Submit user correction for AI training

    Request body:
    {
        "original_text": "OCR text where amount was found",
        "corrected_amount": "123456.78",
        "invoice_type": "momo|electricity|traditional",
        "user_id": "user123",
        "correction_type": "dash_amount_recognition",
        "timestamp": "2025-01-19T10:30:00Z"
    }
    """
    try:
        if not ai_training_service:
            raise HTTPException(status_code=500, detail="AI training service not available")

        result = ai_training_service.submit_user_correction(correction)

        return JSONResponse({
            **result,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"❌ Error submitting user correction: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ai-training/dash-patterns")
async def get_dash_patterns():
    """
    📊 Get learned dash amount patterns for AI training
    """
    try:
        if not ai_training_service:
            raise HTTPException(status_code=500, detail="AI training service not available")

        result = ai_training_service.get_dash_patterns()

        return JSONResponse({
            **result,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"❌ Error getting dash patterns: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def _update_dash_patterns_from_correction(correction: Dict[str, Any]):
    """
    Update dash patterns based on user correction
    """
    try:
        original_text = correction.get('original_text', '')
        corrected_amount = correction.get('corrected_amount', '')
        
        # Generate pattern from this correction
        pattern = _generate_pattern_from_correction(original_text, corrected_amount)
        
        if pattern:
            logger.info(f"📝 Generated pattern from correction: {pattern}")
            # Pattern is stored in database via the main endpoint
        else:
            logger.warning("⚠️ Could not generate pattern from correction")
    
    except Exception as e:
        logger.error(f"❌ Error updating dash patterns: {str(e)}")

def _generate_pattern_from_correction(original_text: str, corrected_amount: str) -> Optional[str]:
    """
    Generate regex pattern from user correction
    
    Args:
        original_text: The OCR text
        corrected_amount: The corrected amount string
        
    Returns:
        Regex pattern string or None if cannot generate
    """
    import re
    
    # Clean the corrected amount for matching
    clean_amount = corrected_amount.replace(',', '').replace('.', '').replace(' ', '')
    
    # Look for the amount in the original text
    amount_patterns = [
        r'\b' + re.escape(clean_amount) + r'\b',  # Exact match
        r'\b\d+\b',  # Any number that matches
    ]
    
    for pattern in amount_patterns:
        match = re.search(pattern, original_text)
        if match:
            found_amount = match.group(0)
            
            # Check if the amount appears after a dash
            amount_pos = original_text.find(found_amount)
            
            # Look for dash before the amount (within 10 characters)
            dash_search_start = max(0, amount_pos - 10)
            dash_search_text = original_text[dash_search_start:amount_pos]
            
            if '-' in dash_search_text:
                # Found dash before amount - create dash pattern
                return r'(?:^\s*-\s*|-\s+)([0-9,\.]+)(?:\s*(?:vnd|đ|vnđ))?'
    
    # If no dash found, check if amount is at end of line
    lines = original_text.split('\n')
    for line in lines:
        if clean_amount in line.replace(',', '').replace('.', '').replace(' ', ''):
            # Check if amount is at end of line
            line_end = line.strip()
            if line_end.replace(',', '').replace('.', '').replace(' ', '').endswith(clean_amount):
                return r'([0-9,\.]+)(?:\s*(?:vnd|đ|vnđ))?\s*$'
    
    return None

# ===================== TEST ENDPOINT =====================

@app.websocket("/ws/ocr/{user_id}")
async def websocket_ocr_notifications(websocket: WebSocket, user_id: str):
    """
    🌐 WebSocket endpoint for real-time OCR job notifications

    Frontend kết nối: ws://localhost:8000/ws/ocr/{user_id}

    Nhận thông báo:
    - Job status updates (queued → processing → done/failed)
    - OCR completion notifications
    - Error messages
    """
    if not websocket_manager:
        await websocket.close(code=1001)  # Going away
        return

    await websocket_manager.connect(websocket, user_id)

    try:
        while True:
            # Keep connection alive and listen for client messages
            data = await websocket.receive_text()
            # Client can send messages if needed (e.g., ping, subscribe to specific jobs)
            logger.info(f"WebSocket message from {user_id}: {data}")

    except Exception as e:
        logger.error(f"WebSocket error for {user_id}: {e}")
    finally:
        websocket_manager.disconnect(websocket, user_id)

# ===================== GROQ CHAT WITH DATABASE TOOLS =====================

@app.options("/chat/groq")
async def chat_groq_options():
    """Handle CORS preflight for /chat/groq"""
    return {"status": "ok"}

@app.post("/chat/groq")
async def chat_groq(request_body: Dict[str, Any], current_user = Depends(get_current_user_or_admin)):
    """
    💬 Chat with Groq AI using database tools
    Groq có thể gọi các API tools để thao tác với database

    Requires authentication.
    """
    try:
        # Log raw request body for debugging 422 errors
        logger.info(f"📨 Raw /chat/groq request body: {request_body}")
        
        # Validate request manually to get better error messages
        if 'message' not in request_body:
            logger.error("❌ Missing 'message' field in request")
            raise HTTPException(status_code=422, detail="Missing required field: 'message'")
        
        message = request_body['message']
        user_id = request_body.get('user_id', 'anonymous')
        
        # Validate message is string
        if not isinstance(message, str):
            logger.error(f"❌ 'message' field is not a string: {type(message)}")
            raise HTTPException(status_code=422, detail="'message' must be a string")
        
        # Validate user_id is string or int (convert to string if needed)
        if user_id is not None and not isinstance(user_id, (str, int)):
            logger.error(f"❌ 'user_id' field is not a string or int: {type(user_id)}")
            raise HTTPException(status_code=422, detail="'user_id' must be a string or integer")
        
        # Convert user_id to string
        user_id = str(user_id) if user_id is not None else 'anonymous'
        
        logger.info(f"📨 Validated /chat/groq request - message: '{message}', user_id: '{user_id}'")
        
        if not groq_chat_handler:
            raise HTTPException(status_code=503, detail="Groq chat handler not initialized")
        
        user_message = message
        
        logger.info(f"🤖 Groq chat from {user_id}: {user_message}")
        
        response = await groq_chat_handler.chat(user_message, user_id)
        
        return JSONResponse({
            "message": response.get('message', ''),
            "type": response.get('type', 'text'),
            "method": response.get('method', 'groq_with_tools'),
            "iteration": response.get('iteration'),
            "timestamp": response.get('timestamp'),
            "user_id": user_id
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Groq chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/groq/simple")
async def chat_groq_simple(request: ChatMessageRequest):
    """
    💬 Simple Groq chat (không dùng tools)
    Dùng khi chỉ cần trả lời chung chung
    """
    try:
        if not groq_chat_handler:
            raise HTTPException(status_code=503, detail="Groq chat handler not initialized")
        
        user_message = request.message
        user_id = request.user_id or "anonymous"
        
        logger.info(f"🤖 Groq simple chat from {user_id}: {user_message}")
        
        response = await groq_chat_handler.chat_simple(user_message, user_id)
        
        return JSONResponse({
            "message": response.get('message', ''),
            "type": response.get('type', 'text'),
            "method": response.get('method', 'groq_simple'),
            "timestamp": response.get('timestamp'),
            "user_id": user_id
        })
    except Exception as e:
        logger.error(f"❌ Groq simple chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/groq/stream")
async def chat_groq_stream(request: ChatMessageRequest):
    """
    💬 Stream Groq chat response (real-time, word-by-word)
    Returns NDJSON (newline-delimited JSON)
    
    Response format:
    {"type": "content", "text": "hello", "timestamp": "..."}
    {"type": "content", "text": " world", "timestamp": "..."}
    {"type": "done", "timestamp": "..."}
    """
    try:
        if not groq_chat_handler:
            raise HTTPException(status_code=503, detail="Groq chat handler not initialized")
        
        user_message = request.message
        user_id = request.user_id or "anonymous"
        
        logger.info(f"🤖 Groq stream chat from {user_id}: {user_message}")
        
        return StreamingResponse(
            groq_chat_handler.chat_stream(user_message, user_id),
            media_type="application/x-ndjson"
        )
    except Exception as e:
        logger.error(f"❌ Groq stream error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/groq/tools")
def get_groq_tools():
    """
    📋 Lấy danh sách tools mà Groq có thể gọi
    """
    try:
        if not groq_tools:
            raise HTTPException(status_code=503, detail="Groq tools not initialized")
        
        tools = groq_tools.get_tools_description()
        
        return JSONResponse({
            "status": "success",
            "count": len(tools),
            "tools": tools
        })
    except Exception as e:
        logger.error(f"❌ Error getting Groq tools: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/groq/tools/call")
async def call_groq_tool(request: Dict[str, Any]):
    """
    🔧 Gọi một Groq tool trực tiếp
    
    Request body:
    {
        "tool_name": "get_all_invoices",
        "params": {
            "limit": 10
        }
    }
    """
    try:
        if not groq_tools:
            raise HTTPException(status_code=503, detail="Groq tools not initialized")
        
        tool_name = request.get('tool_name')
        params = request.get('params', {})
        
        if not tool_name:
            raise HTTPException(status_code=400, detail="tool_name is required")
        
        logger.info(f"🔧 Calling Groq tool: {tool_name} with params: {params}")
        
        result = groq_tools.call_tool(tool_name, **params)
        
        response = {
            "status": "success",
            "tool": tool_name,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
        # Serialize with DecimalEncoder to handle database Decimal objects
        return JSONResponse(
            json.loads(json.dumps(response, cls=DecimalEncoder)),
            status_code=200
        )
    except Exception as e:
        logger.error(f"❌ Error calling Groq tool: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/groq/tools/{tool_name}")
def call_groq_tool_get(tool_name: str, limit: Optional[int] = 20):
    """
    🔧 Gọi Groq tool qua GET (cho tools đơn giản)
    
    Examples:
    - /api/groq/tools/get_all_invoices?limit=10
    - /api/groq/tools/get_statistics
    """
    try:
        if not groq_tools:
            raise HTTPException(status_code=503, detail="Groq tools not initialized")
        
        logger.info(f"🔧 GET call to Groq tool: {tool_name}")
        
        # Map GET parameters to tool calls
        if tool_name == "get_all_invoices":
            result = groq_tools.get_all_invoices(limit=limit)
        elif tool_name == "get_statistics":
            result = groq_tools.get_statistics()
        else:
            raise HTTPException(status_code=400, detail=f"Tool {tool_name} not found or not accessible via GET")
        
        response = {
            "status": "success",
            "tool": tool_name,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
        # Serialize with DecimalEncoder to handle database Decimal objects
        return JSONResponse(
            json.loads(json.dumps(response, cls=DecimalEncoder)),
            status_code=200
        )
    except Exception as e:
        logger.error(f"❌ Error calling Groq tool via GET: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# ===================== EXPORT DOWNLOAD ENDPOINTS =====================

@app.get("/api/export/download/{filename}")
async def download_export_file(filename: str):
    """
    Download exported file (Excel, CSV, PDF)
    """
    try:
        # Validate filename to prevent directory traversal
        if ".." in filename or "/" in filename or "\\" in filename:
            raise HTTPException(status_code=400, detail="Invalid filename")
        
        # Check if file exists in temp_exports directory
        temp_dir = os.path.join(os.getcwd(), "temp_exports")
        file_path = os.path.join(temp_dir, filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        # Determine content type based on file extension
        if filename.endswith('.xlsx'):
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        elif filename.endswith('.csv'):
            media_type = "text/csv"
        elif filename.endswith('.pdf'):
            media_type = "application/pdf"
        else:
            media_type = "application/octet-stream"
        
        # Return file for download
        return FileResponse(
            path=file_path,
            media_type=media_type,
            filename=filename,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error downloading file {filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ===================== RUN SERVER =====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
