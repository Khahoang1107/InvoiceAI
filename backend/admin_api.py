"""
Admin API endpoints for user management
========================================

Endpoints for admin users to manage other users in the system.

Endpoints:
- GET /admin/users - Get all users (admin only)
- PUT /admin/users/{user_id}/toggle-admin - Toggle admin status
- PUT /admin/users/{user_id}/toggle-active - Toggle user active status
- DELETE /admin/users/{user_id} - Delete user (admin only)
- GET /admin/ocr-jobs - Get all OCR jobs (admin only)
- GET /admin/ocr-jobs/statistics - Get OCR jobs statistics (admin only)
- GET /admin/invoices - Get all invoices (admin only)
- GET /admin/invoices/statistics - Get invoice statistics (admin only)
- DELETE /admin/invoices/{invoice_id} - Delete invoice (admin only)
"""

from fastapi import APIRouter, HTTPException, Depends, status as http_status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional
from datetime import datetime
from sqlalchemy import text

# Import models và services
from models.user import User, UserResponse, UserRole
from utils.database_tools_postgres import get_database_tools

# Import auth utilities
from utils.auth_utils import get_current_admin_user, get_current_user

# Database tools
db_tools = get_database_tools()

# Tạo router cho admin endpoints
admin_router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden - Admin access required"},
        404: {"description": "Not found"},
        422: {"description": "Validation error"},
    },
)

def require_admin(current_user = Depends(get_current_admin_user)):
    """Dependency to ensure user is admin"""
    return current_user

@admin_router.get(
    "/users/statistics",
    summary="Get user statistics",
    description="""
    Get comprehensive statistics about users in the system.

    **Requirements:**
    - Admin privileges required

    **Response:** Statistics including total users, admin count, active/inactive breakdown
    """,
    response_description="User statistics"
)
async def get_user_statistics(admin_user: User = Depends(require_admin)):
    """
    📊 Get user statistics (Admin only)

    Returns comprehensive statistics about users.
    """
    try:
        with db_tools.engine.connect() as conn:
            # Total users
            result = conn.execute(text("SELECT COUNT(*) as count FROM users"))
            row = result.fetchone()
            total_users = row[0] if row else 0

            # Admin users
            result = conn.execute(text("SELECT COUNT(*) as count FROM users WHERE is_admin = 1"))
            row = result.fetchone()
            admin_count = row[0] if row else 0

            # Active users
            result = conn.execute(text("SELECT COUNT(*) as count FROM users WHERE is_active = 1"))
            row = result.fetchone()
            active_count = row[0] if row else 0

            # Inactive users
            result = conn.execute(text("SELECT COUNT(*) as count FROM users WHERE is_active = 0"))
            row = result.fetchone()
            inactive_count = row[0] if row else 0

            # Recent users (last 7 days)
            result = conn.execute(text("""
                SELECT COUNT(*) as count 
                FROM users 
                WHERE created_at >= NOW() - INTERVAL '7 days'
            """))
            row = result.fetchone()
            recent_7days = row[0] if row else 0

            # Recent users (last 30 days)
            result = conn.execute(text("""
                SELECT COUNT(*) as count 
                FROM users 
                WHERE created_at >= NOW() - INTERVAL '30 days'
            """))
            row = result.fetchone()
            recent_30days = row[0] if row else 0

            return {
                "success": True,
                "data": {
                    "total_users": total_users,
                    "admin_count": admin_count,
                    "active_count": active_count,
                    "inactive_count": inactive_count,
                    "recent_7days": recent_7days,
                    "recent_30days": recent_30days
                },
                "timestamp": datetime.utcnow().isoformat()
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

@admin_router.get(
    "/users",
    response_model=List[UserResponse],
    summary="Get all users",
    description="""
    Retrieve a list of all users in the system.

    **Requirements:**
    - Admin privileges required
    - Returns all user information except passwords

    **Response:** List of user objects with full details
    """,
    response_description="List of all users"
)
async def get_all_users(admin_user: User = Depends(require_admin)):
    """
    👥 Get all users (Admin only)

    Returns a complete list of all users in the system.
    """
    try:
        print("📊 Getting all users...")
        with db_tools.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT id, name as username, email, name as full_name, is_active, is_admin, created_at, last_login
                FROM users
                ORDER BY created_at DESC
            """))

            users = []
            rows = result.fetchall()
            print(f"📋 Found {len(rows)} users")
            for row in rows:
                print(f"  - Row: {row}")
                users.append(UserResponse(
                    id=row[0],
                    username=row[1] or row[2].split('@')[0],
                    email=row[2],
                    full_name=row[3] or row[2].split('@')[0],
                    is_active=bool(row[4]),
                    is_admin=bool(row[5]),
                    role=UserRole.admin if row[5] else UserRole.user,
                    created_at=row[6],
                    last_login=row[7]
                ))

            return users

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"❌ Error in get_all_users: {e}")
        traceback.print_exc()
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

@admin_router.put(
    "/users/{user_id}/toggle-admin",
    response_model=UserResponse,
    summary="Toggle admin status",
    description="""
    Toggle the admin status of a user.

    **Requirements:**
    - Admin privileges required
    - Cannot remove admin status from yourself

    **Parameters:**
    - user_id: ID of the user to modify

    **Response:** Updated user information
    """,
    response_description="Updated user information"
)
async def toggle_admin_status(
    user_id: int,
    admin_user: User = Depends(require_admin)
):
    """
    👑 Toggle admin status (Admin only)

    Grant or revoke admin privileges for a user.
    """
    try:
        # Prevent admin from removing their own admin status
        if user_id == admin_user.id:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Cannot modify your own admin status"
            )

        with db_tools.engine.begin() as conn:
            # Check if user exists
            result = conn.execute(text("""
                SELECT id, name as username, email, name as full_name, is_active, is_admin, created_at, last_login
                FROM users WHERE id = :user_id
            """), {"user_id": user_id})

            row = result.fetchone()
            if not row:
                raise HTTPException(
                    status_code=http_status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )

            # Toggle admin status
            new_admin_status = not bool(row[5])

            result = conn.execute(text("""
                UPDATE users SET is_admin = :admin_status WHERE id = :user_id
                RETURNING id, name as username, email, name as full_name, is_active, is_admin, created_at, last_login
            """), {"admin_status": new_admin_status, "user_id": user_id})

            updated_row = result.fetchone()
            if not updated_row:
                raise HTTPException(
                    status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update user"
                )

            return UserResponse(
                id=updated_row[0],
                username=updated_row[1] or updated_row[2].split('@')[0],
                email=updated_row[2],
                full_name=updated_row[3] or updated_row[2].split('@')[0],
                is_active=bool(updated_row[4]),
                is_admin=bool(updated_row[5]),
                role=UserRole.admin if updated_row[5] else UserRole.user,
                created_at=updated_row[6],
                last_login=updated_row[7]
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

@admin_router.put(
    "/users/{user_id}/toggle-active",
    response_model=UserResponse,
    summary="Toggle user active status",
    description="""
    Activate or deactivate a user account.

    **Requirements:**
    - Admin privileges required
    - Cannot deactivate your own account

    **Parameters:**
    - user_id: ID of the user to modify

    **Response:** Updated user information
    """,
    response_description="Updated user information"
)
async def toggle_user_active_status(
    user_id: int,
    admin_user: User = Depends(require_admin)
):
    """
    🚫 Toggle user active status (Admin only)

    Activate or deactivate a user account.
    """
    try:
        # Prevent admin from deactivating their own account
        if user_id == admin_user.id:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate your own account"
            )

        with db_tools.engine.begin() as conn:
            # Check if user exists
            result = conn.execute(text("""
                SELECT id, name as username, email, name as full_name, is_active, is_admin, created_at, last_login
                FROM users WHERE id = :user_id
            """), {"user_id": user_id})

            row = result.fetchone()
            if not row:
                raise HTTPException(
                    status_code=http_status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )

            # Toggle active status
            new_active_status = not bool(row[4])

            result = conn.execute(text("""
                UPDATE users SET is_active = :active_status WHERE id = :user_id
                RETURNING id, name as username, email, name as full_name, is_active, is_admin, created_at, last_login
            """), {"active_status": new_active_status, "user_id": user_id})

            updated_row = result.fetchone()
            if not updated_row:
                raise HTTPException(
                    status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update user"
                )

            return UserResponse(
                id=updated_row[0],
                username=updated_row[1] or updated_row[2].split('@')[0],
                email=updated_row[2],
                full_name=updated_row[3] or updated_row[2].split('@')[0],
                is_active=bool(updated_row[4]),
                is_admin=bool(updated_row[5]),
                role=UserRole.admin if updated_row[5] else UserRole.user,
                created_at=updated_row[6],
                last_login=updated_row[7]
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

@admin_router.delete(
    "/users/{user_id}",
    summary="Delete user",
    description="""
    Permanently delete a user account.

    **Requirements:**
    - Admin privileges required
    - Cannot delete your own account
    - Cannot delete other admin accounts

    **Parameters:**
    - user_id: ID of the user to delete

    **Response:** Success message
    """,
    response_description="Success message"
)
async def delete_user(
    user_id: int,
    admin_user: User = Depends(require_admin)
):
    """
    🗑️ Delete user (Admin only)

    Permanently remove a user account from the system.
    """
    try:
        # Prevent admin from deleting their own account
        if user_id == admin_user.id:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete your own account"
            )

        with db_tools.engine.begin() as conn:
            # Check if user exists and is not admin
            result = conn.execute(text("""
                SELECT id, name as username, email, is_admin FROM users WHERE id = :user_id
            """), {"user_id": user_id})

            row = result.fetchone()
            if not row:
                raise HTTPException(
                    status_code=http_status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )

            # Prevent deleting other admin accounts
            if bool(row[3]):
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail="Cannot delete admin accounts"
                )

            username = row[1] or row[2].split('@')[0]
            email = row[2]

            # Delete the user
            conn.execute(text("DELETE FROM users WHERE id = :user_id"), {"user_id": user_id})

            return {
                "success": True,
                "message": f"User {username} ({email}) has been deleted successfully",
                "deleted_user_id": user_id,
                "timestamp": datetime.utcnow().isoformat()
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

@admin_router.get(
    "/ocr-jobs",
    summary="Get all OCR jobs",
    description="""
    Retrieve a list of all OCR jobs with their status and progress.

    **Requirements:**
    - Admin privileges required

    **Query Parameters:**
    - status: Filter by status (queued, processing, done, failed)
    - limit: Maximum number of jobs to return (default: 50)

    **Response:** List of OCR jobs with details
    """,
    response_description="List of all OCR jobs"
)
async def get_all_ocr_jobs(
    status: Optional[str] = None,
    limit: int = 50,
    admin_user: User = Depends(require_admin)
):
    """
    📋 Get all OCR jobs (Admin only)

    Returns a complete list of all OCR processing jobs in the system.
    """
    try:
        with db_tools.engine.connect() as conn:
            if status:
                result = conn.execute(text("""
                    SELECT id, filename, filepath, status, progress, invoice_id, 
                           error_message, created_at, updated_at, started_at, completed_at, user_id
                    FROM ocr_jobs
                    WHERE status = :status
                    ORDER BY created_at DESC
                    LIMIT :limit
                """), {"status": status, "limit": limit})
            else:
                result = conn.execute(text("""
                    SELECT id, filename, filepath, status, progress, invoice_id, 
                           error_message, created_at, updated_at, started_at, completed_at, user_id
                    FROM ocr_jobs
                    ORDER BY created_at DESC
                    LIMIT :limit
                """), {"limit": limit})

            jobs = []
            for row in result.fetchall():
                jobs.append({
                    "id": row[0],
                    "filename": row[1],
                    "filepath": row[2],
                    "status": row[3],
                    "progress": row[4] if row[4] else 0,
                    "invoice_id": row[5],
                    "error_message": row[6],
                    "user_id": row[11],
                    "created_at": row[7].isoformat() if row[7] else None,
                    "updated_at": row[8].isoformat() if row[8] else None,
                    "started_at": row[9].isoformat() if row[9] else None,
                    "completed_at": row[10].isoformat() if row[10] else None,
                })

            return {
                "success": True,
                "count": len(jobs),
                "jobs": jobs,
                "timestamp": datetime.utcnow().isoformat()
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

@admin_router.get(
    "/ocr-jobs/statistics",
    summary="Get OCR jobs statistics",
    description="""
    Get statistics about OCR jobs processing.

    **Requirements:**
    - Admin privileges required

    **Response:** Statistics including total jobs, status breakdown, success rate
    """,
    response_description="OCR jobs statistics"
)
async def get_ocr_jobs_statistics(admin_user: User = Depends(require_admin)):
    """
    📊 Get OCR jobs statistics (Admin only)

    Returns statistics about OCR processing jobs.
    """
    try:
        with db_tools.engine.connect() as conn:
            # Total jobs
            result = conn.execute(text("SELECT COUNT(*) as count FROM ocr_jobs"))
            row = result.fetchone()
            total_jobs = row[0] if row else 0

            # Jobs by status
            result = conn.execute(text("""
                SELECT status, COUNT(*) as count 
                FROM ocr_jobs 
                GROUP BY status
            """))
            status_breakdown = {}
            for row in result.fetchall():
                status_breakdown[row[0]] = row[1]

            # Recent jobs (last 24 hours)
            result = conn.execute(text("""
                SELECT COUNT(*) as count 
                FROM ocr_jobs 
                WHERE created_at >= NOW() - INTERVAL '24 hours'
            """))
            row = result.fetchone()
            recent_24h = row[0] if row else 0

            # Success rate
            done_jobs = status_breakdown.get('done', 0)
            failed_jobs = status_breakdown.get('failed', 0)
            total_completed = done_jobs + failed_jobs
            success_rate = (done_jobs / total_completed * 100) if total_completed > 0 else 0

            # Average processing time
            result = conn.execute(text("""
                SELECT AVG(EXTRACT(EPOCH FROM (completed_at - started_at))) as avg_time
                FROM ocr_jobs
                WHERE status = 'done' AND completed_at IS NOT NULL AND started_at IS NOT NULL
            """))
            row = result.fetchone()
            avg_processing_time = row[0] if row and row[0] else 0

            return {
                "success": True,
                "data": {
                    "total_jobs": total_jobs,
                    "status_breakdown": status_breakdown,
                    "recent_24h": recent_24h,
                    "success_rate": round(success_rate, 2),
                    "avg_processing_time_seconds": round(avg_processing_time, 2) if avg_processing_time else 0,
                    "queued": status_breakdown.get('queued', 0),
                    "processing": status_breakdown.get('processing', 0),
                    "done": done_jobs,
                    "failed": failed_jobs
                },
                "timestamp": datetime.utcnow().isoformat()
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

@admin_router.get(
    "/invoices",
    summary="Get all invoices",
    description="""
    Retrieve a list of all invoices in the system.

    **Requirements:**
    - Admin privileges required

    **Query Parameters:**
    - limit: Maximum number of invoices to return (default: 100)
    - offset: Number of invoices to skip (default: 0)

    **Response:** List of invoices with full details
    """,
    response_description="List of all invoices"
)
async def get_all_invoices(
    limit: int = 100,
    offset: int = 0,
    admin_user: User = Depends(require_admin)
):
    """
    📄 Get all invoices (Admin only)

    Returns a complete list of all invoices in the database.
    """
    try:
        with db_tools.engine.connect() as conn:
            # Get total count
            result = conn.execute(text("SELECT COUNT(*) as count FROM invoices"))
            row = result.fetchone()
            total_count = row[0] if row else 0

            # Get invoices
            result = conn.execute(text("""
                SELECT id, filename, filepath, invoice_code, invoice_type,
                       buyer_name, seller_name, invoice_date, total_amount, 
                       total_amount_value, confidence_score, created_at, updated_at,
                       buyer_tax_id, seller_tax_id, currency, subtotal, tax_amount
                FROM invoices
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
            """), {"limit": limit, "offset": offset})

            invoices = []
            for row in result.fetchall():
                invoices.append({
                    "id": row[0],
                    "filename": row[1],
                    "filepath": row[2],
                    "invoice_code": row[3],
                    "invoice_type": row[4],
                    "buyer_name": row[5],
                    "seller_name": row[6],
                    "invoice_date": row[7].isoformat() if row[7] else None,
                    "total_amount": row[8],
                    "total_amount_value": float(row[9]) if row[9] else 0,
                    "confidence_score": float(row[10]) if row[10] else 0,
                    "buyer_tax_id": row[13],
                    "seller_tax_id": row[14],
                    "currency": row[15] if row[15] else 'VND',
                    "subtotal": float(row[16]) if row[16] else 0,
                    "tax_amount": float(row[17]) if row[17] else 0,
                    "created_at": row[11].isoformat() if row[11] else None,
                    "updated_at": row[12].isoformat() if row[12] else None,
                })

            return {
                "success": True,
                "total": total_count,
                "count": len(invoices),
                "limit": limit,
                "offset": offset,
                "invoices": invoices,
                "timestamp": datetime.utcnow().isoformat()
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

@admin_router.get(
    "/invoices/statistics",
    summary="Get invoice statistics",
    description="""
    Get comprehensive statistics about invoices in the system.

    **Requirements:**
    - Admin privileges required

    **Response:** Statistics including total amount, average confidence, type breakdown
    """,
    response_description="Invoice statistics"
)
async def get_invoice_statistics(admin_user: User = Depends(require_admin)):
    """
    📊 Get invoice statistics (Admin only)

    Returns comprehensive statistics about invoices.
    """
    try:
        with db_tools.engine.connect() as conn:
            # Total invoices
            result = conn.execute(text("SELECT COUNT(*) as count FROM invoices"))
            row = result.fetchone()
            total_invoices = row[0] if row else 0

            # Total amount
            result = conn.execute(text("SELECT SUM(total_amount_value) as total FROM invoices"))
            row = result.fetchone()
            total_amount = row[0] if row and row[0] else 0

            # Average confidence
            result = conn.execute(text("SELECT AVG(confidence_score) as avg FROM invoices"))
            row = result.fetchone()
            avg_confidence = row[0] if row and row[0] else 0

            # Invoice types
            result = conn.execute(text("""
                SELECT invoice_type, COUNT(*) as count 
                FROM invoices 
                GROUP BY invoice_type
            """))
            type_breakdown = {}
            for row in result.fetchall():
                type_breakdown[row[0] if row[0] else 'unknown'] = row[1]

            # Recent invoices (last 7 days)
            result = conn.execute(text("""
                SELECT COUNT(*) as count 
                FROM invoices 
                WHERE created_at >= NOW() - INTERVAL '7 days'
            """))
            row = result.fetchone()
            recent_7days = row[0] if row else 0

            # Recent invoices (last 30 days)
            result = conn.execute(text("""
                SELECT COUNT(*) as count 
                FROM invoices 
                WHERE created_at >= NOW() - INTERVAL '30 days'
            """))
            row = result.fetchone()
            recent_30days = row[0] if row else 0

            return {
                "success": True,
                "data": {
                    "total_invoices": total_invoices,
                    "total_amount": float(total_amount),
                    "avg_confidence": round(float(avg_confidence), 2),
                    "type_breakdown": type_breakdown,
                    "recent_7days": recent_7days,
                    "recent_30days": recent_30days
                },
                "timestamp": datetime.utcnow().isoformat()
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

@admin_router.get(
    "/activities/recent",
    summary="Get recent activities",
    description="""
    Get recent user activities in the system.

    **Requirements:**
    - Admin privileges required

    **Response:** List of recent activities
    """,
    response_description="Recent activities"
)
async def get_recent_activities(admin_user: User = Depends(require_admin)):
    """
    📋 Get recent activities (Admin only)

    Returns recent user activities including logins, registrations, and actions.
    """
    try:
        with db_tools.engine.connect() as conn:
            # Get recent user registrations
            result = conn.execute(text("""
                SELECT 
                    name as user_name,
                    email,
                    'Đăng ký tài khoản' as action,
                    created_at,
                    EXTRACT(EPOCH FROM (NOW() - created_at)) as seconds_ago
                FROM users
                ORDER BY created_at DESC
                LIMIT 10
            """))
            
            activities = []
            for row in result.fetchall():
                seconds = int(row[4])
                if seconds < 60:
                    time_ago = f"{seconds} giây trước"
                elif seconds < 3600:
                    time_ago = f"{seconds // 60} phút trước"
                elif seconds < 86400:
                    time_ago = f"{seconds // 3600} giờ trước"
                else:
                    time_ago = f"{seconds // 86400} ngày trước"
                
                activities.append({
                    "user": row[0] if row[0] else row[1],
                    "action": row[2],
                    "time": time_ago,
                    "type": "success"
                })

            return {
                "success": True,
                "data": activities,
                "timestamp": datetime.utcnow().isoformat()
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

@admin_router.get(
    "/users/top",
    summary="Get top users",
    description="""
    Get top active users in the system.

    **Requirements:**
    - Admin privileges required

    **Response:** List of top users with activity counts
    """,
    response_description="Top users"
)
async def get_top_users(admin_user: User = Depends(require_admin)):
    """
    👥 Get top users (Admin only)

    Returns most active users based on their activity.
    """
    try:
        with db_tools.engine.connect() as conn:
            # Get users with invoice count
            result = conn.execute(text("""
                SELECT 
                    u.id,
                    u.name,
                    u.email,
                    COUNT(i.id) as invoice_count
                FROM users u
                LEFT JOIN invoices i ON i.user_id = u.id
                GROUP BY u.id, u.name, u.email
                ORDER BY invoice_count DESC
                LIMIT 10
            """))
            
            top_users = []
            for row in result.fetchall():
                top_users.append({
                    "name": row[1] if row[1] else row[2].split('@')[0],
                    "email": row[2],
                    "invoice_count": row[3]
                })

            return {
                "success": True,
                "data": top_users,
                "timestamp": datetime.utcnow().isoformat()
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

@admin_router.get(
    "/statistics/monthly",
    summary="Get monthly statistics",
    description="""
    Get monthly statistics for users, invoices, and revenue.

    **Requirements:**
    - Admin privileges required

    **Response:** Monthly data for charts
    """,
    response_description="Monthly statistics"
)
async def get_monthly_statistics(admin_user: User = Depends(require_admin)):
    """
    📊 Get monthly statistics (Admin only)

    Returns monthly data for users, invoices, and revenue.
    """
    try:
        with db_tools.engine.connect() as conn:
            # Get monthly user growth (last 7 months)
            result = conn.execute(text("""
                SELECT 
                    TO_CHAR(created_at, 'TMMonth') as month,
                    EXTRACT(MONTH FROM created_at) as month_num,
                    COUNT(*) as count
                FROM users
                WHERE created_at >= NOW() - INTERVAL '7 months'
                GROUP BY TO_CHAR(created_at, 'TMMonth'), EXTRACT(MONTH FROM created_at)
                ORDER BY EXTRACT(MONTH FROM created_at)
            """))
            user_growth = [{"month": row[0], "count": row[2]} for row in result.fetchall()]

            # Get monthly invoice statistics (last 7 months)
            result = conn.execute(text("""
                SELECT 
                    TO_CHAR(created_at, 'TMMonth') as month,
                    EXTRACT(MONTH FROM created_at) as month_num,
                    COUNT(*) as invoice_count,
                    COALESCE(SUM(total_amount_value), 0) as revenue
                FROM invoices
                WHERE created_at >= NOW() - INTERVAL '7 months'
                GROUP BY TO_CHAR(created_at, 'TMMonth'), EXTRACT(MONTH FROM created_at)
                ORDER BY EXTRACT(MONTH FROM created_at)
            """))
            monthly_data = []
            for row in result.fetchall():
                monthly_data.append({
                    "month": row[0],
                    "invoices": row[2],
                    "revenue": float(row[3])
                })

            return {
                "success": True,
                "data": {
                    "user_growth": user_growth,
                    "monthly_invoices": monthly_data
                },
                "timestamp": datetime.utcnow().isoformat()
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

@admin_router.delete(
    "/invoices/{invoice_id}",
    summary="Delete invoice",
    description="""
    Delete an invoice from the system (Admin only).

    **Requirements:**
    - Admin privileges required

    **Parameters:**
    - invoice_id: ID of the invoice to delete

    **Response:** Success message
    """,
    response_description="Success message"
)
async def delete_invoice(
    invoice_id: int,
    admin_user: User = Depends(require_admin)
):
    """
    🗑️ Delete invoice (Admin only)

    Permanently remove an invoice from the database.
    """
    try:
        with db_tools.engine.begin() as conn:
            # Check if invoice exists
            result = conn.execute(text("SELECT id, invoice_code FROM invoices WHERE id = :invoice_id"), {"invoice_id": invoice_id})
            row = result.fetchone()
            if not row:
                raise HTTPException(
                    status_code=http_status.HTTP_404_NOT_FOUND,
                    detail="Invoice not found"
                )

            invoice_code = row[1] if row[1] else f"ID-{row[0]}"

            # Delete the invoice
            conn.execute(text("DELETE FROM invoices WHERE id = :invoice_id"), {"invoice_id": invoice_id})

            return {
                "success": True,
                "message": f"Invoice {invoice_code} (ID: {invoice_id}) has been deleted successfully",
                "deleted_invoice_id": invoice_id,
                "timestamp": datetime.utcnow().isoformat()
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

# Export router để import vào main.py
__all__ = ["admin_router"]
