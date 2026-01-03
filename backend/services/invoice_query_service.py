"""
Invoice Query Service - Truy vấn thông tin hóa đơn từ database
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from utils.logger import get_logger

logger = get_logger(__name__)


class InvoiceQueryService:
    """Service to query invoice data from database"""
    
    def __init__(self, db_tools):
        self.db_tools = db_tools
    
    def search_invoices_by_criteria(
        self, 
        user_id: int,
        time_period: Optional[str] = None,
        vendor: Optional[str] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Tìm kiếm hóa đơn theo các tiêu chí
        
        Args:
            user_id: ID của user
            time_period: "hôm nay", "tuần này", "tháng này", etc.
            vendor: Tên vendor/cửa hàng
            min_amount: Số tiền tối thiểu
            max_amount: Số tiền tối đa
            limit: Số lượng kết quả tối đa
            
        Returns:
            List các hóa đơn matching
        """
        try:
            # Get all user invoices
            invoices = self.db_tools.get_all_invoices(limit=100, user_id=user_id)
            
            if not invoices:
                return []
            
            # Filter by time period
            if time_period:
                invoices = self._filter_by_time_period(invoices, time_period)
            
            # Filter by vendor
            if vendor:
                invoices = [inv for inv in invoices 
                           if vendor.lower() in str(inv.get('vendor_name', '')).lower()]
            
            # Filter by amount range
            if min_amount is not None:
                invoices = [inv for inv in invoices 
                           if float(inv.get('total_amount', 0)) >= min_amount]
            
            if max_amount is not None:
                invoices = [inv for inv in invoices 
                           if float(inv.get('total_amount', 0)) <= max_amount]
            
            # Limit results
            return invoices[:limit]
            
        except Exception as e:
            logger.error(f"Error searching invoices: {e}")
            return []
    
    def get_statistics(
        self, 
        user_id: int,
        time_period: Optional[str] = None,
        group_by: str = "month"
    ) -> Dict[str, Any]:
        """
        Lấy thống kê chi tiêu
        
        Args:
            user_id: ID của user
            time_period: "tháng này", "năm nay", etc.
            group_by: "day", "week", "month", "year"
            
        Returns:
            Dict chứa thống kê
        """
        try:
            invoices = self.db_tools.get_all_invoices(limit=1000, user_id=user_id)
            
            if not invoices:
                return {
                    "total_amount": 0,
                    "total_count": 0,
                    "average_amount": 0,
                    "time_period": time_period or "all"
                }
            
            # Filter by time if specified
            if time_period:
                invoices = self._filter_by_time_period(invoices, time_period)
            
            # Calculate statistics
            total_amount = sum(float(inv.get('total_amount', 0)) for inv in invoices)
            total_count = len(invoices)
            average_amount = total_amount / total_count if total_count > 0 else 0
            
            # Group by specified period
            grouped_data = self._group_invoices(invoices, group_by)
            
            return {
                "total_amount": round(total_amount, 2),
                "total_count": total_count,
                "average_amount": round(average_amount, 2),
                "time_period": time_period or "all",
                "grouped_data": grouped_data,
                "invoices": invoices[:10]  # Sample invoices
            }
            
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {
                "total_amount": 0,
                "total_count": 0,
                "average_amount": 0,
                "error": str(e)
            }
    
    def get_total_amount(
        self, 
        user_id: int,
        time_period: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Lấy tổng tiền chi tiêu
        
        Args:
            user_id: ID của user
            time_period: "hôm nay", "tháng này", etc.
            
        Returns:
            Dict chứa tổng tiền và thông tin
        """
        try:
            invoices = self.db_tools.get_all_invoices(limit=1000, user_id=user_id)
            
            if time_period:
                invoices = self._filter_by_time_period(invoices, time_period)
            
            total = sum(float(inv.get('total_amount', 0)) for inv in invoices)
            
            return {
                "total_amount": round(total, 2),
                "invoice_count": len(invoices),
                "time_period": time_period or "all",
                "currency": "VND"
            }
            
        except Exception as e:
            logger.error(f"Error getting total amount: {e}")
            return {
                "total_amount": 0,
                "invoice_count": 0,
                "error": str(e)
            }
    
    def _filter_by_time_period(self, invoices: List[Dict], period: str) -> List[Dict]:
        """Filter invoices by time period"""
        now = datetime.now()
        
        if period in ["hôm nay", "today"]:
            start_date = now.replace(hour=0, minute=0, second=0)
        elif period in ["hôm qua", "yesterday"]:
            start_date = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0)
        elif period in ["tuần này", "this week"]:
            start_date = now - timedelta(days=now.weekday())
        elif period in ["tuần trước", "last week"]:
            start_date = now - timedelta(days=now.weekday() + 7)
        elif period in ["tháng này", "this month"]:
            start_date = now.replace(day=1, hour=0, minute=0, second=0)
        elif period in ["tháng trước", "last month"]:
            last_month = now.replace(day=1) - timedelta(days=1)
            start_date = last_month.replace(day=1, hour=0, minute=0, second=0)
        elif period in ["năm nay", "this year"]:
            start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0)
        else:
            return invoices
        
        filtered = []
        for inv in invoices:
            inv_date_str = inv.get('invoice_date') or inv.get('created_at')
            if inv_date_str:
                try:
                    inv_date = datetime.fromisoformat(str(inv_date_str).replace('Z', '+00:00'))
                    if inv_date >= start_date:
                        filtered.append(inv)
                except:
                    continue
        
        return filtered
    
    def _group_invoices(self, invoices: List[Dict], group_by: str) -> Dict[str, Any]:
        """Group invoices by time period"""
        grouped = {}
        
        for inv in invoices:
            inv_date_str = inv.get('invoice_date') or inv.get('created_at')
            if not inv_date_str:
                continue
                
            try:
                inv_date = datetime.fromisoformat(str(inv_date_str).replace('Z', '+00:00'))
                
                if group_by == "day":
                    key = inv_date.strftime("%Y-%m-%d")
                elif group_by == "week":
                    key = f"{inv_date.year}-W{inv_date.isocalendar()[1]}"
                elif group_by == "month":
                    key = inv_date.strftime("%Y-%m")
                elif group_by == "year":
                    key = str(inv_date.year)
                else:
                    key = "all"
                
                if key not in grouped:
                    grouped[key] = {
                        "count": 0,
                        "total": 0
                    }
                
                grouped[key]["count"] += 1
                grouped[key]["total"] += float(inv.get('total_amount', 0))
                
            except:
                continue
        
        return grouped
