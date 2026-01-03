# Invoices API Router
# List and manage invoices

from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, List, Dict, Any
from datetime import datetime
from utils.database_tools_postgres import get_database_tools
from core.logging import logger
from pydantic import BaseModel

router = APIRouter(prefix="/api/invoices", tags=["invoices"])

# Security scheme
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user from JWT token"""
    try:
        token = credentials.credentials
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

# Invoice creation schema
class InvoiceCreate(BaseModel):
    invoice_number: str
    customer_name: str
    customer_email: Optional[str] = None
    customer_address: Optional[str] = None
    vendor: str
    tax_code: Optional[str] = None
    issue_date: str
    due_date: Optional[str] = None
    amount: float
    tax: float
    total_amount: float
    status: str = "pending"
    notes: Optional[str] = None
    items: str  # JSON string
    extracted_data: Optional[str] = None  # JSON string

# Get database instance
def get_db():
    return get_database_tools()

db = None

@router.get("/")
async def get_invoices(
    current_user = Depends(get_current_user),
    limit: int = Query(20, description="Maximum number of invoices to return"),
    offset: int = Query(0, description="Number of invoices to skip"),
    search: Optional[str] = Query(None, description="Search query for invoice code, seller, or buyer")
):
    """
    Get list of invoices with optional filtering and pagination
    🔒 REQUIRES AUTHENTICATION - Only returns invoices for the authenticated user

    Query parameters:
    - limit: Maximum number of invoices to return (default: 20)
    - offset: Number of invoices to skip for pagination (default: 0)
    - search: Search query for filtering by invoice code, seller name, or buyer name
    """
    try:
        # Lazy initialization
        global db
        if db is None:
            db = get_db()
        
        user_id = current_user.id
        logger.info(f"📊 Fetching invoices for user {user_id}: limit={limit}, offset={offset}, search={search}")

        # Get total count for this user
        stats = db.get_statistics(user_id=user_id)
        total_count = stats.get('total_invoices', 0)

        if search:
            # Search invoices (filtered by user)
            invoices = db.search_invoices(search, limit, user_id=user_id)
            logger.info(f"🔍 Found {len(invoices)} invoices matching '{search}' for user {user_id}")
        else:
            # Get all invoices with pagination (filtered by user)
            all_invoices = db.get_all_invoices(limit + offset, user_id=user_id)
            invoices = all_invoices[offset:offset + limit] if offset < len(all_invoices) else []
            logger.info(f"📄 Retrieved {len(invoices)} invoices for user {user_id} (offset: {offset}, limit: {limit})")

        # Format response with actual total count from database
        response = {
            "invoices": invoices,
            "total": total_count,  # Total invoices in database for this user
            "count": len(invoices),  # Number of invoices in current response
            "limit": limit,
            "offset": offset,
            "has_more": len(invoices) == limit
        }

        return JSONResponse(response)

    except Exception as e:
        logger.error(f"❌ Failed to fetch invoices: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch invoices: {str(e)}")

@router.get("/stats")
async def get_invoice_stats(current_user = Depends(get_current_user)):
    """
    Get basic statistics about invoices
    🔒 REQUIRES AUTHENTICATION - Only shows stats for the authenticated user
    """
    try:
        # Lazy initialization
        global db
        if db is None:
            db = get_db()
        
        user_id = current_user.id

        # Get all invoices for stats (filtered by user)
        invoices = db.get_all_invoices(limit=10000, user_id=user_id)

        total_invoices = len(invoices)
        total_amount = sum(float(inv.get('total_amount_value', 0)) for inv in invoices)

        # Count by invoice type
        type_counts = {}
        for inv in invoices:
            inv_type = inv.get('invoice_type', 'unknown')
            type_counts[inv_type] = type_counts.get(inv_type, 0) + 1

        response = {
            "total_invoices": total_invoices,
            "total_amount": total_amount,
            "invoice_types": type_counts,
            "timestamp": datetime.now().isoformat()
        }

        return JSONResponse(response)

    except Exception as e:
        logger.error(f"❌ Failed to get invoice stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.post("/create")
async def create_invoice(invoice: InvoiceCreate):
    """
    Create a new invoice (Admin only)
    
    This endpoint allows admins to manually create invoices with full details
    including line items, customer info, and calculated totals.
    """
    try:
        # Lazy initialization
        global db
        if db is None:
            db = get_db()

        logger.info(f"📝 Creating new invoice: {invoice.invoice_number}")
        
        # Get connection
        conn = db.connect()
        if not conn:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        try:
            cursor = conn.cursor()
            
            # Check if invoice_number already exists
            cursor.execute(
                "SELECT id FROM invoices WHERE invoice_number = %s",
                (invoice.invoice_number,)
            )
            if cursor.fetchone():
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invoice number '{invoice.invoice_number}' already exists"
                )
            
            # Insert invoice - user_id will be set by the authenticated user (for now, use default admin ID 16)
            # TODO: Get user_id from JWT token
            user_id = 16  # Default admin user
            
            cursor.execute("""
                INSERT INTO invoices (
                    user_id, invoice_number, vendor, tax_code, 
                    issue_date, due_date, amount, tax, total_amount,
                    status, notes, items, extracted_data, created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, invoice_number, created_at
            """, (
                user_id,
                invoice.invoice_number,
                invoice.vendor,
                invoice.tax_code,
                invoice.issue_date,
                invoice.due_date,
                invoice.amount,
                invoice.tax,
                invoice.total_amount,
                invoice.status,
                invoice.notes,
                invoice.items,
                invoice.extracted_data or invoice.items,
                datetime.utcnow()
            ))
            
            result = cursor.fetchone()
            conn.commit()
            
            logger.info(f"✅ Created invoice ID {result['id']}: {result['invoice_number']}")
            
            return JSONResponse({
                "success": True,
                "message": f"Invoice {result['invoice_number']} created successfully",
                "invoice": {
                    "id": result['id'],
                    "invoice_number": result['invoice_number'],
                    "created_at": result['created_at'].isoformat() if result['created_at'] else None
                }
            })
            
        finally:
            if conn:
                conn.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to create invoice: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create invoice: {str(e)}")