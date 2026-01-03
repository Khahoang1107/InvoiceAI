"""
Groq AI Tools for Database Operations
Groq sử dụng các hàm này để thao tác với database
"""

import json
from typing import Dict, Any, List, Optional
from decimal import Decimal
from datetime import datetime, date, timedelta

class DecimalEncoder(json.JSONEncoder):
    """JSON encoder that handles Decimal and datetime objects"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, date):
            return obj.isoformat()
        return super().default(obj)

class GroqDatabaseTools:
    """Tools for Groq to interact with database via API"""
    
    def __init__(self, db_tools):
        """Initialize with database tools"""
        self.db_tools = db_tools
    
    def get_all_invoices(self, limit: int = 20, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Lấy danh sách tất cả hóa đơn
        
        Args:
            limit: Số hóa đơn tối đa
            user_id: Lọc theo user (optional)
        
        Returns:
            List of invoices
        """
        try:
            invoices = self.db_tools.get_all_invoices(limit=limit, user_id=user_id)
            return {
                "success": True,
                "count": len(invoices),
                "invoices": invoices
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def search_invoices(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """
        Tìm kiếm hóa đơn theo keyword
        
        Args:
            query: Keyword tìm kiếm (code, buyer, amount, etc)
            limit: Số kết quả tối đa
        
        Returns:
            Search results
        """
        try:
            results = self.db_tools.search_invoices(query, limit=limit)
            return {
                "success": True,
                "query": query,
                "count": len(results),
                "results": results
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_invoice_by_id(self, invoice_id: int) -> Dict[str, Any]:
        """
        Lấy chi tiết một hóa đơn
        
        Args:
            invoice_id: Invoice ID
        
        Returns:
            Invoice details
        """
        try:
            invoice = self.db_tools.get_invoice_by_id(invoice_id)
            if invoice:
                return {
                    "success": True,
                    "invoice": invoice
                }
            else:
                return {
                    "success": False,
                    "error": f"Invoice {invoice_id} not found"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Lấy thống kê hóa đơn
        
        Returns:
            Statistics summary
        """
        try:
            stats = self.db_tools.get_statistics()
            return {
                "success": True,
                "statistics": stats
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def filter_by_date(self, start_date: str, end_date: str, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Lọc hóa đơn theo khoảng thời gian
        
        Args:
            start_date: Ngày bắt đầu (YYYY-MM-DD)
            end_date: Ngày kết thúc (YYYY-MM-DD)
            user_id: Lọc theo user (optional)
        
        Returns:
            Filtered invoices
        """
        try:
            invoices = self.db_tools.get_all_invoices(limit=1000, user_id=user_id)
            filtered = []
            for inv in invoices:
                # Check invoice_date first, then created_at
                inv_date_str = inv.get('invoice_date') or inv.get('created_at')
                if inv_date_str:
                    inv_date = str(inv_date_str).split('T')[0]
                    if start_date <= inv_date <= end_date:
                        filtered.append(inv)
            
            return {
                "success": True,
                "start_date": start_date,
                "end_date": end_date,
                "count": len(filtered),
                "invoices": filtered
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def count_invoices_by_date(self, date: str, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Đếm số hóa đơn trong một ngày cụ thể
        
        Args:
            date: Ngày cần đếm (YYYY-MM-DD)
            user_id: Lọc theo user (optional)
        
        Returns:
            Số lượng hóa đơn trong ngày đó
        """
        try:
            from datetime import datetime
            
            invoices = self.db_tools.get_all_invoices(limit=1000, user_id=user_id)
            count = 0
            
            # Parse input date to compare
            try:
                input_date = datetime.strptime(date, "%Y-%m-%d")
            except:
                return {
                    "success": False,
                    "error": f"Invalid date format: {date}. Expected YYYY-MM-DD"
                }
            
            for inv in invoices:
                inv_date_str = inv.get('invoice_date') or inv.get('created_at')
                if inv_date_str:
                    # Try multiple date formats
                    inv_date = None
                    inv_date_str = str(inv_date_str)
                    
                    # Format 1: dd/mm/yyyy
                    if '/' in inv_date_str and len(inv_date_str.split('/')) == 3:
                        try:
                            inv_date = datetime.strptime(inv_date_str.split()[0], "%d/%m/%Y")
                        except:
                            pass
                    
                    # Format 2: yyyy-mm-dd or ISO format
                    if not inv_date:
                        try:
                            inv_date_clean = inv_date_str.split('T')[0]
                            inv_date = datetime.strptime(inv_date_clean, "%Y-%m-%d")
                        except:
                            pass
                    
                    # Compare dates
                    if inv_date and inv_date.date() == input_date.date():
                        count += 1
            
            return {
                "success": True,
                "date": date,
                "count": count
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def count_total_invoices(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Đếm tổng số hóa đơn
        
        Args:
            user_id: Lọc theo user (optional)
        
        Returns:
            Tổng số hóa đơn
        """
        try:
            invoices = self.db_tools.get_all_invoices(limit=1000, user_id=user_id)
            
            return {
                "success": True,
                "count": len(invoices)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_invoices_by_type(self, invoice_type: str, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Lấy hóa đơn theo loại (electricity, water, sale, service)
        
        Args:
            invoice_type: Loại hóa đơn
            user_id: Lọc theo user (optional)
        
        Returns:
            Invoices of that type
        """
        try:
            invoices = self.db_tools.get_all_invoices(limit=1000, user_id=user_id)
            filtered = [inv for inv in invoices if inv.get('invoice_type') == invoice_type]
            
            return {
                "success": True,
                "type": invoice_type,
                "count": len(filtered),
                "invoices": filtered
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def export_to_excel(self, filter_type: str = "all", start_date: str = None, end_date: str = None, invoice_type: str = None) -> Dict[str, Any]:
        """
        Xuất danh sách hóa đơn ra file Excel
        
        Args:
            filter_type: Loại filter ("all", "today", "date_range", "type")
            start_date: Ngày bắt đầu (YYYY-MM-DD) - cho date_range
            end_date: Ngày kết thúc (YYYY-MM-DD) - cho date_range  
            invoice_type: Loại hóa đơn - cho type filter
        
        Returns:
            Thông tin về file Excel đã tạo
        """
        try:
            # Lấy dữ liệu theo filter
            if filter_type == "all":
                invoices = self.db_tools.get_all_invoices(limit=1000)
                filter_desc = "tất cả"
            elif filter_type == "today":
                from datetime import datetime
                today = datetime.now().strftime("%Y-%m-%d")
                all_invoices = self.db_tools.get_all_invoices(limit=1000)
                invoices = []
                for inv in all_invoices:
                    created_str = str(inv.get('created_at', ''))
                    if created_str.startswith(today):
                        invoices.append(inv)
                filter_desc = f"hôm nay ({today})"
            elif filter_type == "date_range" and start_date and end_date:
                all_invoices = self.db_tools.get_all_invoices(limit=1000)
                invoices = []
                for inv in all_invoices:
                    created_str = str(inv.get('created_at', ''))
                    inv_date = created_str.split('T')[0] if 'T' in created_str else created_str
                    if start_date <= inv_date <= end_date:
                        invoices.append(inv)
                filter_desc = f"từ {start_date} đến {end_date}"
            elif filter_type == "type" and invoice_type:
                all_invoices = self.db_tools.get_all_invoices(limit=1000)
                invoices = [inv for inv in all_invoices if inv.get('invoice_type') == invoice_type]
                filter_desc = f"loại {invoice_type}"
            else:
                return {
                    "success": False,
                    "error": "Invalid filter parameters"
                }
            
            if not invoices:
                return {
                    "success": False,
                    "error": f"Không có hóa đơn nào cho filter: {filter_desc}"
                }
            
            # Tạo file Excel
            from export_service import get_export_service
            export_service = get_export_service(self.db_tools)
            excel_bytes = export_service.export_to_excel(invoices)
            
            if not excel_bytes:
                return {
                    "success": False,
                    "error": "Không thể tạo file Excel"
                }
            
            # Lưu file tạm thời và trả về URL
            import tempfile
            import os
            from datetime import datetime
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"invoices_{filter_type}_{timestamp}.xlsx"
            
            # Tạo thư mục temp nếu chưa có
            temp_dir = os.path.join(os.getcwd(), "temp_exports")
            os.makedirs(temp_dir, exist_ok=True)
            
            file_path = os.path.join(temp_dir, filename)
            
            with open(file_path, 'wb') as f:
                f.write(excel_bytes)
            
            # Tạo URL để download (giả định server chạy trên localhost:8000)
            download_url = f"http://localhost:8000/api/export/download/{filename}"
            
            return {
                "success": True,
                "message": f"Đã xuất {len(invoices)} hóa đơn {filter_desc} ra file Excel",
                "filename": filename,
                "download_url": download_url,
                "file_size": len(excel_bytes),
                "invoice_count": len(invoices)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Lỗi khi export Excel: {str(e)}"
            }
    
    def get_tools_description(self) -> List[Dict[str, Any]]:
        """
        Trả về danh sách các tools mà Groq có thể gọi
        Format cho Groq function calling
        
        Returns:
            List of tools descriptions
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "count_invoices_by_date",
                    "description": "Đếm số hóa đơn trong một ngày cụ thể. Dùng cho: 'hôm nay có mấy hóa đơn', 'ngày 14/10 có bao nhiêu'",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "date": {"type": "string", "description": "Ngày cần đếm (YYYY-MM-DD)"}
                        },
                        "required": ["date"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "count_total_invoices",
                    "description": "Đếm tổng số hóa đơn. Dùng cho: 'có bao nhiêu hóa đơn', 'tổng cộng mấy hóa đơn'",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_all_invoices",
                    "description": "Lấy danh sách tất cả hóa đơn từ database",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "limit": {"type": "integer", "description": "Số hóa đơn tối đa (default: 20)"},
                            "user_id": {"type": "integer", "description": "Lọc theo user (optional)"}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_invoices",
                    "description": "Tìm kiếm hóa đơn theo keyword (code, buyer, amount)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Keyword tìm kiếm"},
                            "limit": {"type": "integer", "description": "Số kết quả tối đa"}
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_invoice_by_id",
                    "description": "Lấy chi tiết một hóa đơn cụ thể",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "invoice_id": {"type": "integer", "description": "ID của hóa đơn"}
                        },
                        "required": ["invoice_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "filter_by_date",
                    "description": "Lọc hóa đơn theo khoảng thời gian. Dùng cho câu hỏi: 'hôm nay', 'tuần này', 'tháng này'",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "start_date": {"type": "string", "description": "Ngày bắt đầu (YYYY-MM-DD)"},
                            "end_date": {"type": "string", "description": "Ngày kết thúc (YYYY-MM-DD)"}
                        },
                        "required": ["start_date", "end_date"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_invoices_by_type",
                    "description": "Lấy hóa đơn theo loại (electricity, water, sale, service)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "invoice_type": {"type": "string", "description": "Loại hóa đơn"}
                        },
                        "required": ["invoice_type"]
                    }
                }
            }
        ]
    
    def call_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """
        Gọi một tool theo tên
        
        Args:
            tool_name: Tên của tool
            **kwargs: Tham số của tool
        
        Returns:
            Kết quả từ tool
        """
        if tool_name == "count_invoices_by_date":
            return self.count_invoices_by_date(**kwargs)
        elif tool_name == "count_total_invoices":
            return self.count_total_invoices(**kwargs)
        elif tool_name == "get_all_invoices":
            return self.get_all_invoices(**kwargs)
        elif tool_name == "search_invoices":
            return self.search_invoices(**kwargs)
        elif tool_name == "get_invoice_by_id":
            return self.get_invoice_by_id(**kwargs)
        elif tool_name == "get_statistics":
            return self.get_statistics()
        elif tool_name == "filter_by_date":
            return self.filter_by_date(**kwargs)
        elif tool_name == "get_invoices_by_type":
            return self.get_invoices_by_type(**kwargs)
        elif tool_name == "get_high_value_invoices":
            return self.get_high_value_invoices(**kwargs)
        elif tool_name == "save_invoice_from_ocr":
            # For save_invoice_from_ocr, ocr_data should be provided by the caller
            # If not provided, this is an error
            if "ocr_data" not in kwargs:
                return {
                    "success": False,
                    "error": "ocr_data parameter is required for save_invoice_from_ocr tool"
                }
            return self.save_invoice_from_ocr(**kwargs)
        elif tool_name == "export_to_excel":
            return self.export_to_excel(**kwargs)
        elif tool_name == "analyze_invoice_details":
            return self.analyze_invoice_details(**kwargs)
        elif tool_name == "compare_invoices":
            return self.compare_invoices(**kwargs)
        elif tool_name == "analyze_invoice_items":
            return self.analyze_invoice_items(**kwargs)
        else:
            return {
                "success": False,
                "error": f"Tool {tool_name} not found"
            }
    
    def analyze_invoice_details(self, invoice_id: int) -> Dict[str, Any]:
        """
        Phân tích chi tiết một hóa đơn bao gồm:
        - Tất cả thông tin cơ bản
        - Items (nếu có)
        - Tình trạng thanh toán
        - Cảnh báo (overdue, high value, etc)
        - So sánh với hóa đơn tương tự
        
        Args:
            invoice_id: ID của hóa đơn cần phân tích
        
        Returns:
            Phân tích chi tiết hóa đơn
        """
        try:
            invoice = self.db_tools.get_invoice_by_id(invoice_id)
            if not invoice:
                return {
                    "success": False,
                    "error": f"Invoice {invoice_id} not found"
                }
            
            # Parse items nếu là JSON
            items = []
            if invoice.get('items'):
                try:
                    items = json.loads(invoice['items']) if isinstance(invoice['items'], str) else invoice['items']
                except:
                    items = []
            
            # Phân tích extracted_data
            extracted_data = {}
            if invoice.get('extracted_data'):
                try:
                    extracted_data = json.loads(invoice['extracted_data']) if isinstance(invoice['extracted_data'], str) else invoice['extracted_data']
                except:
                    extracted_data = {}
            
            # Tính toán insights
            total_amount = invoice.get('total_amount_numeric') or invoice.get('total_amount_value') or invoice.get('amount') or 0
            
            # Check if overdue
            is_overdue = False
            days_until_due = None
            if invoice.get('due_date'):
                try:
                    due_date = invoice['due_date']
                    if isinstance(due_date, str):
                        due_date = datetime.strptime(due_date, '%Y-%m-%d').date()
                    elif isinstance(due_date, datetime):
                        due_date = due_date.date()
                    
                    today = datetime.now().date()
                    days_until_due = (due_date - today).days
                    is_overdue = days_until_due < 0
                except:
                    pass
            
            # Lấy hóa đơn tương tự (cùng vendor hoặc gần giá trị)
            similar_invoices = []
            try:
                vendor = invoice.get('vendor') or invoice.get('seller_name')
                if vendor:
                    all_invoices = self.db_tools.get_all_invoices(limit=100)
                    for inv in all_invoices:
                        if inv['id'] != invoice_id:
                            inv_vendor = inv.get('vendor') or inv.get('seller_name')
                            if inv_vendor and vendor.lower() in inv_vendor.lower():
                                similar_invoices.append(inv)
                    
                    # Limit to 5 most recent
                    similar_invoices = similar_invoices[:5]
            except:
                pass
            
            # Tạo warnings
            warnings = []
            if is_overdue:
                warnings.append({
                    "type": "overdue",
                    "message": f"Hóa đơn đã quá hạn {abs(days_until_due)} ngày",
                    "severity": "high"
                })
            elif days_until_due is not None and days_until_due <= 7:
                warnings.append({
                    "type": "due_soon",
                    "message": f"Hóa đơn sắp đến hạn trong {days_until_due} ngày",
                    "severity": "medium"
                })
            
            if total_amount > 10000000:
                warnings.append({
                    "type": "high_value",
                    "message": f"Hóa đơn có giá trị cao ({total_amount:,.0f} VND)",
                    "severity": "info"
                })
            
            if invoice.get('status') == 'pending':
                warnings.append({
                    "type": "unpaid",
                    "message": "Hóa đơn chưa được thanh toán",
                    "severity": "medium"
                })
            
            return {
                "success": True,
                "invoice": invoice,
                "items_breakdown": items,
                "extracted_data": extracted_data,
                "payment_status": {
                    "status": invoice.get('status', 'unknown'),
                    "is_overdue": is_overdue,
                    "days_until_due": days_until_due
                },
                "warnings": warnings,
                "similar_invoices": similar_invoices,
                "insights": {
                    "is_high_value": total_amount > 10000000,
                    "is_overdue": is_overdue,
                    "days_until_due": days_until_due,
                    "has_items": len(items) > 0,
                    "total_items": len(items),
                    "confidence_score": invoice.get('confidence_score')
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def compare_invoices(self, invoice_ids: List[int]) -> Dict[str, Any]:
        """
        So sánh nhiều hóa đơn với nhau về giá trị, vendor, thời gian
        
        Args:
            invoice_ids: Danh sách ID các hóa đơn cần so sánh
        
        Returns:
            Kết quả so sánh
        """
        try:
            invoices = []
            for inv_id in invoice_ids:
                invoice = self.db_tools.get_invoice_by_id(inv_id)
                if invoice:
                    invoices.append(invoice)
            
            if not invoices:
                return {
                    "success": False,
                    "error": "No valid invoices found"
                }
            
            # Extract values for comparison
            total_values = []
            vendors = []
            dates = []
            
            for inv in invoices:
                total_amount = inv.get('total_amount_numeric') or inv.get('total_amount_value') or inv.get('amount') or 0
                total_values.append(total_amount)
                
                vendor = inv.get('vendor') or inv.get('seller_name') or 'Unknown'
                vendors.append(vendor)
                
                date_val = inv.get('issue_date') or inv.get('date') or inv.get('date_string') or 'Unknown'
                dates.append(str(date_val))
            
            # Calculate statistics
            avg_value = sum(total_values) / len(total_values) if total_values else 0
            highest_invoice = max(invoices, key=lambda x: x.get('total_amount_numeric', 0) or x.get('total_amount_value', 0) or x.get('amount', 0))
            lowest_invoice = min(invoices, key=lambda x: x.get('total_amount_numeric', 0) or x.get('total_amount_value', 0) or x.get('amount', 0))
            
            return {
                "success": True,
                "total_compared": len(invoices),
                "invoices": invoices,
                "comparison": {
                    "total_values": total_values,
                    "vendors": vendors,
                    "dates": dates,
                    "average_value": avg_value,
                    "total_sum": sum(total_values),
                    "highest_value": {
                        "id": highest_invoice.get('id'),
                        "invoice_number": highest_invoice.get('invoice_number'),
                        "amount": max(total_values)
                    },
                    "lowest_value": {
                        "id": lowest_invoice.get('id'),
                        "invoice_number": lowest_invoice.get('invoice_number'),
                        "amount": min(total_values)
                    }
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def analyze_invoice_items(self, invoice_id: int) -> Dict[str, Any]:
        """
        Phân tích chi tiết các items trong hóa đơn
        
        Args:
            invoice_id: ID của hóa đơn
        
        Returns:
            Phân tích items
        """
        try:
            invoice = self.db_tools.get_invoice_by_id(invoice_id)
            if not invoice:
                return {
                    "success": False,
                    "error": f"Invoice {invoice_id} not found"
                }
            
            items = []
            if invoice.get('items'):
                try:
                    items = json.loads(invoice['items']) if isinstance(invoice['items'], str) else invoice['items']
                except:
                    items = []
            
            # Analyze items
            total_quantity = 0
            total_value = 0
            categories = {}
            
            for item in items:
                qty = item.get('quantity', 0)
                price = item.get('price', 0) or item.get('amount', 0)
                category = item.get('category', 'other')
                
                total_quantity += qty
                total_value += qty * price
                
                if category not in categories:
                    categories[category] = {
                        "count": 0,
                        "total_value": 0
                    }
                categories[category]["count"] += 1
                categories[category]["total_value"] += qty * price
            
            # Find most expensive item
            most_expensive = None
            if items:
                most_expensive = max(items, key=lambda x: (x.get('quantity', 0) * (x.get('price', 0) or x.get('amount', 0))))
            
            return {
                "success": True,
                "invoice_id": invoice_id,
                "invoice_number": invoice.get('invoice_number'),
                "total_items": len(items),
                "items_detail": items,
                "analysis": {
                    "total_quantity": total_quantity,
                    "total_value": total_value,
                    "categories": categories,
                    "most_expensive_item": most_expensive,
                    "average_price_per_item": total_value / len(items) if items else 0
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


class RAGTools:
    """RAG (Retrieval-Augmented Generation) Tools for enhanced invoice understanding"""

    def __init__(self, vector_service=None):
        """
        Initialize RAG tools

        Args:
            vector_service: VectorService instance for document retrieval
        """
        self.vector_service = vector_service

    def search_invoice_context(self, query: str, top_k: int = 3) -> Dict[str, Any]:
        """
        Tìm kiếm ngữ cảnh liên quan từ hóa đơn để hỗ trợ trả lời câu hỏi

        Args:
            query: Câu hỏi hoặc từ khóa tìm kiếm
            top_k: Số lượng kết quả tối đa

        Returns:
            Relevant invoice context and metadata
        """
        try:
            if not self.vector_service:
                return {
                    "success": False,
                    "error": "Vector service not initialized"
                }

            # Search for relevant documents
            results = self.vector_service.search_invoices(query, top_k=top_k)

            # Prepare context
            context = self.vector_service.get_invoice_context(query)

            return {
                "success": True,
                "query": query,
                "results_count": len(results),
                "context": context,
                "documents": [
                    {
                        "id": doc.get("id"),
                        "invoice_number": doc.get("metadata", {}).get("invoice_number"),
                        "customer_name": doc.get("metadata", {}).get("customer_name"),
                        "total_amount": doc.get("metadata", {}).get("total_amount"),
                        "status": doc.get("metadata", {}).get("status"),
                        "relevance_score": doc.get("score", 0)
                    }
                    for doc in results
                ]
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def get_invoice_insights(self, query: str) -> Dict[str, Any]:
        """
        Lấy insights thông minh về hóa đơn dựa trên truy vấn

        Args:
            query: Câu hỏi về hóa đơn

        Returns:
            Insights and analysis based on retrieved context
        """
        try:
            if not self.vector_service:
                return {
                    "success": False,
                    "error": "Vector service not initialized"
                }

            # Get context
            context_result = self.search_invoice_context(query, top_k=5)

            if not context_result["success"]:
                return context_result

            # Analyze context for insights
            context = context_result["context"]
            documents = context_result["documents"]

            # Basic analysis
            total_amount = sum(doc.get("total_amount", 0) for doc in documents if doc.get("total_amount"))
            status_counts = {}
            for doc in documents:
                status = doc.get("status", "unknown")
                status_counts[status] = status_counts.get(status, 0) + 1

            insights = {
                "total_invoices_found": len(documents),
                "total_amount_sum": total_amount,
                "status_distribution": status_counts,
                "top_customers": list(set(doc.get("customer_name", "") for doc in documents if doc.get("customer_name")))[:3]
            }

            return {
                "success": True,
                "query": query,
                "insights": insights,
                "context": context,
                "documents": documents
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


class GroqTools:
    """Enhanced Groq Tools with RAG capabilities"""

    def __init__(self, db_tools, vector_service=None):
        """
        Initialize Groq tools with database and RAG capabilities

        Args:
            db_tools: Database tools instance
            vector_service: Vector service for RAG (optional)
        """
        self.db_tools = GroqDatabaseTools(db_tools)
        self.rag_tools = RAGTools(vector_service) if vector_service else None

    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get all available tools for Groq"""
        tools = []

        # Database tools
        db_methods = [method for method in dir(self.db_tools) if not method.startswith('_') and callable(getattr(self.db_tools, method))]
        for method_name in db_methods:
            method = getattr(self.db_tools, method_name)
            if hasattr(method, '__doc__') and method.__doc__:
                # Parse method signature and docstring
                tools.append({
                    "name": method_name,
                    "description": method.__doc__.strip().split('\n')[0],  # First line of docstring
                    "parameters": {
                        "type": "object",
                        "properties": {},  # Would need more sophisticated parsing
                        "required": []
                    }
                })

        # RAG tools (if available)
        if self.rag_tools:
            rag_methods = [method for method in dir(self.rag_tools) if not method.startswith('_') and callable(getattr(self.rag_tools, method))]
            for method_name in rag_methods:
                method = getattr(self.rag_tools, method_name)
                if hasattr(method, '__doc__') and method.__doc__:
                    tools.append({
                        "name": f"rag_{method_name}",
                        "description": f"RAG-enhanced: {method.__doc__.strip().split('\n')[0]}",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "Search query or question"
                                },
                                "top_k": {
                                    "type": "integer",
                                    "description": "Number of results to retrieve",
                                    "default": 3
                                }
                            },
                            "required": ["query"]
                        }
                    })

        return tools

    def execute_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """
        Execute a tool by name

        Args:
            tool_name: Name of the tool to execute
            **kwargs: Tool parameters

        Returns:
            Tool execution result
        """
        try:
            # Handle RAG tools
            if tool_name.startswith('rag_') and self.rag_tools:
                actual_method = tool_name[4:]  # Remove 'rag_' prefix
                if hasattr(self.rag_tools, actual_method):
                    method = getattr(self.rag_tools, actual_method)
                    return method(**kwargs)

            # Handle database tools
            elif hasattr(self.db_tools, tool_name):
                method = getattr(self.db_tools, tool_name)
                return method(**kwargs)

            else:
                return {
                    "success": False,
                    "error": f"Tool '{tool_name}' not found"
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"Error executing tool '{tool_name}': {str(e)}"
            }

    # Convenience methods for backward compatibility
    def __getattr__(self, name):
        """Delegate method calls to appropriate tool class"""
        if self.rag_tools and hasattr(self.rag_tools, name):
            return getattr(self.rag_tools, name)
        elif hasattr(self.db_tools, name):
            return getattr(self.db_tools, name)
        else:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
