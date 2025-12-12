# Export API Router
# Export invoices in various formats (Excel, PDF, CSV, JSON)

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse, JSONResponse
from typing import Optional, List
from datetime import datetime
from pathlib import Path
from utils.database_tools_postgres import get_database_tools
from core.logging import logger
import io

router = APIRouter(prefix="/api/export", tags=["export"])

# Get services
def get_db():
    return get_database_tools()

def get_export_service():
    db = get_db()
    from export_service import ExportService
    return ExportService(db)

db = None
export_service = None

@router.get("/invoices")
async def export_invoices(
    format: str = Query(..., description="Export format: excel, pdf, csv, json"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    year: Optional[int] = Query(None, description="Filter by year"),
    month: Optional[int] = Query(None, description="Filter by month (1-12)"),
    specific_date: Optional[str] = Query(None, description="Specific date (YYYY-MM-DD)")
):
    """
    Export invoices with optional filtering

    Query parameters:
    - format: Required. One of: excel, pdf, csv, json
    - start_date: Optional start date for date range filter
    - end_date: Optional end date for date range filter
    - year: Optional year filter
    - month: Optional month filter (requires year)
    - specific_date: Optional specific date filter
    """
    try:
        # Lazy initialization
        global db, export_service
        if db is None:
            db = get_db()
        if export_service is None:
            export_service = get_export_service()
        
        # Validate format
        supported_formats = ["excel", "pdf", "csv", "json"]
        if format.lower() not in supported_formats:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported format. Supported: {', '.join(supported_formats)}"
            )

        # Get all invoices
        logger.info("📊 Fetching invoices for export...")
        invoices = db.get_all_invoices(limit=10000)  # Large limit for export

        if not invoices:
            raise HTTPException(status_code=404, detail="No invoices found")

        logger.info(f"📊 Found {len(invoices)} invoices to export")

        # Apply filters
        if specific_date:
            try:
                datetime.strptime(specific_date, "%Y-%m-%d")
                invoices = export_service.filter_by_date(invoices, specific_date)
                logger.info(f"📅 Filtered by date {specific_date}: {len(invoices)} invoices")
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

        elif year and month:
            if not (1 <= month <= 12):
                raise HTTPException(status_code=400, detail="Month must be between 1-12")
            invoices = export_service.filter_by_month(invoices, year, month)
            logger.info(f"📅 Filtered by {year}-{month:02d}: {len(invoices)} invoices")

        elif start_date and end_date:
            try:
                datetime.strptime(start_date, "%Y-%m-%d")
                datetime.strptime(end_date, "%Y-%m-%d")
                if start_date > end_date:
                    raise HTTPException(status_code=400, detail="Start date must be before end date")
                invoices = export_service.filter_by_date_range(invoices, start_date, end_date)
                logger.info(f"📅 Filtered by range {start_date} to {end_date}: {len(invoices)} invoices")
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

        if not invoices:
            raise HTTPException(status_code=404, detail="No invoices match the filter criteria")

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"invoices_{timestamp}"

        # Export based on format
        if format.lower() == "excel":
            excel_data = export_service.export_to_excel(invoices)
            if not excel_data:
                raise HTTPException(status_code=500, detail="Failed to generate Excel file")

            def iter_excel():
                yield excel_data

            return StreamingResponse(
                iter_excel(),
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f"attachment; filename={base_filename}.xlsx"}
            )

        elif format.lower() == "pdf":
            pdf_data = export_service.export_to_pdf(invoices)
            if not pdf_data:
                raise HTTPException(status_code=500, detail="Failed to generate PDF file")

            def iter_pdf():
                yield pdf_data

            return StreamingResponse(
                iter_pdf(),
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename={base_filename}.pdf"}
            )

        elif format.lower() == "csv":
            csv_content = export_service.export_to_csv(invoices)
            if not csv_content:
                raise HTTPException(status_code=500, detail="Failed to generate CSV file")

            def iter_csv():
                yield csv_content

            return StreamingResponse(
                iter_csv(),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename={base_filename}.csv"}
            )

        elif format.lower() == "json":
            json_content = export_service.export_to_json(invoices, pretty=True)
            if not json_content:
                raise HTTPException(status_code=500, detail="Failed to generate JSON file")

            def iter_json():
                yield json_content

            return StreamingResponse(
                iter_json(),
                media_type="application/json",
                headers={"Content-Disposition": f"attachment; filename={base_filename}.json"}
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Export error: {e}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@router.get("/invoices/summary")
async def get_export_summary(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    year: Optional[int] = Query(None),
    month: Optional[int] = Query(None),
    specific_date: Optional[str] = Query(None)
):
    """
    Get summary statistics for invoices (without full export)

    Returns count, total amount, average confidence, etc.
    """
    try:
        # Lazy initialization
        global db, export_service
        if db is None:
            db = get_db()
        if export_service is None:
            export_service = get_export_service()
        
        # Get all invoices
        invoices = db.get_all_invoices(limit=10000)

        if not invoices:
            return JSONResponse({
                "total_invoices": 0,
                "total_amount": 0,
                "average_confidence": 0,
                "invoice_types": {}
            })

        # Apply filters (same logic as export)
        if specific_date:
            try:
                datetime.strptime(specific_date, "%Y-%m-%d")
                invoices = export_service.filter_by_date(invoices, specific_date)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format")

        elif year and month:
            if not (1 <= month <= 12):
                raise HTTPException(status_code=400, detail="Month must be between 1-12")
            invoices = export_service.filter_by_month(invoices, year, month)

        elif start_date and end_date:
            try:
                datetime.strptime(start_date, "%Y-%m-%d")
                datetime.strptime(end_date, "%Y-%m-%d")
                if start_date > end_date:
                    raise HTTPException(status_code=400, detail="Start date must be before end date")
                invoices = export_service.filter_by_date_range(invoices, start_date, end_date)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format")

        # Get summary
        summary = export_service.calculate_statistics(invoices)

        return JSONResponse(summary)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Summary error: {e}")
        raise HTTPException(status_code=500, detail=f"Summary failed: {str(e)}")