# Invoices API Router
# List and manage invoices

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Optional, List
from datetime import datetime
from ..utils.database_tools_postgres import get_database_tools
from ..core.logging import logger

router = APIRouter(prefix="/api/invoices", tags=["invoices"])

# Get database instance
def get_db():
    return get_database_tools()

db = None

@router.get("/")
async def get_invoices(
    limit: int = Query(20, description="Maximum number of invoices to return"),
    offset: int = Query(0, description="Number of invoices to skip"),
    search: Optional[str] = Query(None, description="Search query for invoice code, seller, or buyer")
):
    """
    Get list of invoices with optional filtering and pagination

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

        logger.info(f"📊 Fetching invoices: limit={limit}, offset={offset}, search={search}")

        if search:
            # Search invoices
            invoices = db.search_invoices(search, limit)
            logger.info(f"🔍 Found {len(invoices)} invoices matching '{search}'")
        else:
            # Get all invoices with pagination
            all_invoices = db.get_all_invoices(limit + offset)
            invoices = all_invoices[offset:offset + limit] if offset < len(all_invoices) else []
            logger.info(f"📄 Retrieved {len(invoices)} invoices (offset: {offset}, limit: {limit})")

        # Format response
        response = {
            "invoices": invoices,
            "total": len(invoices),
            "limit": limit,
            "offset": offset,
            "has_more": len(invoices) == limit
        }

        return JSONResponse(response)

    except Exception as e:
        logger.error(f"❌ Failed to fetch invoices: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch invoices: {str(e)}")

@router.get("/stats")
async def get_invoice_stats():
    """
    Get basic statistics about invoices
    """
    try:
        # Lazy initialization
        global db
        if db is None:
            db = get_db()

        # Get all invoices for stats
        invoices = db.get_all_invoices(limit=10000)

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