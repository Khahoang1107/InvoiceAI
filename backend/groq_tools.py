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
        Lọc hóa đơn theo khoảng thời gian (dựa trên NGÀY TRÊN HÓA ĐƠN)
        
        Args:
            start_date: Ngày bắt đầu (YYYY-MM-DD)
            end_date: Ngày kết thúc (YYYY-MM-DD)
            user_id: Lọc theo user (optional)
        
        Returns:
            Filtered invoices with invoice date in range
        """
        try:
            from datetime import datetime
            
            # Parse input dates
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            except:
                return {
                    "success": False,
                    "error": f"Invalid date format. Expected YYYY-MM-DD"
                }
            
            invoices = self.db_tools.get_all_invoices(limit=1000, user_id=user_id)
            filtered = []
            
            for inv in invoices:
                # Use invoice date (date_string field) - format DD/MM/YYYY
                inv_date_str = inv.get('date_string') or inv.get('date') or inv.get('invoice_date')
                if inv_date_str:
                    try:
                        inv_date_str = str(inv_date_str).strip()
                        inv_date = None
                        
                        # Format 1: DD/MM/YYYY (most common in database)
                        if '/' in inv_date_str:
                            parts = inv_date_str.split()[0].split('/')
                            if len(parts) == 3:
                                try:
                                    inv_date = datetime.strptime(inv_date_str.split()[0], "%d/%m/%Y")
                                except:
                                    pass
                        
                        # Format 2: YYYY-MM-DD or ISO format (fallback)
                        if not inv_date:
                            try:
                                inv_date_clean = inv_date_str.split('T')[0].split()[0]
                                inv_date = datetime.strptime(inv_date_clean, "%Y-%m-%d")
                            except:
                                pass
                        
                        # Check if date is in range
                        if inv_date and start_dt.date() <= inv_date.date() <= end_dt.date():
                            filtered.append(inv)
                    except Exception as e:
                        # Skip invalid dates
                        continue
            
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
        Đếm số hóa đơn theo NGÀY TRÊN HÓA ĐƠN (invoice date)
        
        Args:
            date: Ngày cần đếm (YYYY-MM-DD)
            user_id: Lọc theo user (optional)
        
        Returns:
            Số lượng hóa đơn có ngày trên hóa đơn trùng với ngày này
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
                # Use invoice date (date_string field) - format DD/MM/YYYY
                inv_date_str = inv.get('date_string') or inv.get('date') or inv.get('invoice_date')
                if inv_date_str:
                    try:
                        inv_date_str = str(inv_date_str).strip()
                        inv_date = None
                        
                        # Format 1: DD/MM/YYYY (most common in database)
                        if '/' in inv_date_str:
                            parts = inv_date_str.split()[0].split('/')
                            if len(parts) == 3:
                                try:
                                    inv_date = datetime.strptime(inv_date_str.split()[0], "%d/%m/%Y")
                                except:
                                    pass
                        
                        # Format 2: YYYY-MM-DD or ISO format
                        if not inv_date:
                            try:
                                inv_date_clean = inv_date_str.split('T')[0].split()[0]
                                inv_date = datetime.strptime(inv_date_clean, "%Y-%m-%d")
                            except:
                                pass
                        
                        # Compare dates
                        if inv_date and inv_date.date() == input_date.date():
                            count += 1
                    except Exception as e:
                        # Skip invalid dates
                        continue
            
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
    
    def filter_by_confidence(self, min_confidence: float = 0.0, max_confidence: float = 1.0, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Lọc hóa đơn theo độ tin cậy (confidence score)
        
        Args:
            min_confidence: Độ tin cậy tối thiểu (0.0 - 1.0)
            max_confidence: Độ tin cậy tối đa (0.0 - 1.0)
            user_id: Lọc theo user (optional)
        
        Returns:
            Invoices with confidence in range
        """
        try:
            invoices = self.db_tools.get_all_invoices(limit=1000, user_id=user_id)
            filtered = []
            
            for inv in invoices:
                confidence = inv.get('confidence_score')
                if confidence is not None:
                    try:
                        confidence_val = float(confidence)
                        if min_confidence <= confidence_val <= max_confidence:
                            filtered.append(inv)
                    except (ValueError, TypeError):
                        continue
            
            return {
                "success": True,
                "min_confidence": min_confidence,
                "max_confidence": max_confidence,
                "count": len(filtered),
                "invoices": filtered
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def search_by_invoice_code(self, invoice_code: str, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Tìm hóa đơn theo mã hóa đơn (invoice_code)
        
        Args:
            invoice_code: Mã hóa đơn cần tìm (có thể tìm một phần)
            user_id: Lọc theo user (optional)
        
        Returns:
            Invoices matching the code
        """
        try:
            invoices = self.db_tools.get_all_invoices(limit=1000, user_id=user_id)
            invoice_code_lower = invoice_code.lower()
            
            # Tìm các hóa đơn có mã khớp (exact hoặc contains)
            filtered = []
            for inv in invoices:
                inv_code = str(inv.get('invoice_code', '')).lower()
                if invoice_code_lower in inv_code or inv_code in invoice_code_lower:
                    filtered.append(inv)
            
            return {
                "success": True,
                "invoice_code": invoice_code,
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
                        "properties": {
                            "user_id": {"type": "integer", "description": "ID của user (tự động thêm)"}
                        }
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
            },
            {
                "type": "function",
                "function": {
                    "name": "filter_by_confidence",
                    "description": "Lọc hóa đơn theo độ tin cậy (confidence). Dùng khi: 'hóa đơn có độ tin cậy thấp', 'confidence < 80%', 'độ tin cậy dưới 100%'",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "min_confidence": {"type": "number", "description": "Độ tin cậy tối thiểu (0.0-1.0). VD: 0.8 = 80%"},
                            "max_confidence": {"type": "number", "description": "Độ tin cậy tối đa (0.0-1.0). VD: 1.0 = 100%"}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_by_invoice_code",
                    "description": "Tìm hóa đơn theo mã hóa đơn cụ thể (invoice code). Dùng khi user hỏi: 'có hóa đơn mã ABC123 không', 'tìm hóa đơn PB16040000191'",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "invoice_code": {"type": "string", "description": "Mã hóa đơn cần tìm"}
                        },
                        "required": ["invoice_code"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_total_spending",
                    "description": "Tính tổng chi tiêu từ tất cả hóa đơn. Dùng cho: 'tổng chi tiêu là bao nhiêu', 'tôi đã chi bao nhiêu tiền', 'tổng số tiền đã trả'",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_id": {"type": "integer", "description": "Lọc theo user (optional)"},
                            "start_date": {"type": "string", "description": "Ngày bắt đầu (YYYY-MM-DD) - optional"},
                            "end_date": {"type": "string", "description": "Ngày kết thúc (YYYY-MM-DD) - optional"}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "analyze_spending_trends",
                    "description": "Phân tích xu hướng chi tiêu theo thời gian. Dùng cho: 'xu hướng chi tiêu', 'chi tiêu tăng hay giảm', 'phân tích chi tiêu theo tháng'",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_id": {"type": "integer", "description": "Lọc theo user (optional)"},
                            "months": {"type": "integer", "description": "Số tháng phân tích (mặc định 6)"}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "detect_spending_anomalies",
                    "description": "Phát hiện các hóa đơn bất thường (giá trị cao hoặc thấp bất thường). Dùng cho: 'có hóa đơn nào bất thường không', 'phát hiện chi tiêu lạ', 'hóa đơn đáng ngờ'",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_id": {"type": "integer", "description": "Lọc theo user (optional)"},
                            "threshold_multiplier": {"type": "number", "description": "Hệ số ngưỡng (mặc định 2.0 = gấp đôi trung bình)"}
                        }
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
        elif tool_name == "filter_by_confidence":
            return self.filter_by_confidence(**kwargs)
        elif tool_name == "search_by_invoice_code":
            return self.search_by_invoice_code(**kwargs)
        elif tool_name == "get_total_spending":
            return self.get_total_spending(**kwargs)
        elif tool_name == "analyze_spending_trends":
            return self.analyze_spending_trends(**kwargs)
        elif tool_name == "detect_spending_anomalies":
            return self.detect_spending_anomalies(**kwargs)
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
    
    def get_total_spending(self, user_id: Optional[int] = None, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Tính tổng chi tiêu từ tất cả hóa đơn
        
        Args:
            user_id: Lọc theo user (optional)
            start_date: Ngày bắt đầu (YYYY-MM-DD) - optional
            end_date: Ngày kết thúc (YYYY-MM-DD) - optional
        
        Returns:
            Tổng chi tiêu và phân tích chi tiết
        """
        try:
            # Get invoices with filters
            invoices = self.db_tools.get_all_invoices(limit=10000, user_id=user_id)
            
            # Filter by date if provided
            if start_date or end_date:
                filtered_invoices = []
                for inv in invoices:
                    inv_date_str = inv.get('date_string') or inv.get('date') or inv.get('invoice_date')
                    if inv_date_str:
                        try:
                            inv_date_str = str(inv_date_str).strip()
                            inv_date = None
                            
                            # Parse date
                            if '/' in inv_date_str:
                                parts = inv_date_str.split()[0].split('/')
                                if len(parts) == 3:
                                    try:
                                        inv_date = datetime.strptime(inv_date_str.split()[0], "%d/%m/%Y")
                                    except:
                                        pass
                            
                            if not inv_date:
                                try:
                                    inv_date_clean = inv_date_str.split('T')[0].split()[0]
                                    inv_date = datetime.strptime(inv_date_clean, "%Y-%m-%d")
                                except:
                                    pass
                            
                            # Check date range
                            if inv_date:
                                if start_date:
                                    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                                    if inv_date < start_dt:
                                        continue
                                if end_date:
                                    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                                    if inv_date > end_dt:
                                        continue
                                filtered_invoices.append(inv)
                        except:
                            continue
                invoices = filtered_invoices
            
            # Calculate total spending
            total_spending = 0
            spending_by_type = {}
            spending_by_vendor = {}
            monthly_spending = {}
            
            for inv in invoices:
                amount = inv.get('total_amount_numeric') or inv.get('total_amount_value') or inv.get('amount') or 0
                total_spending += float(amount)
                
                # By type
                inv_type = inv.get('invoice_type', 'unknown')
                spending_by_type[inv_type] = spending_by_type.get(inv_type, 0) + float(amount)
                
                # By vendor
                vendor = inv.get('vendor') or inv.get('seller_name') or 'Unknown'
                spending_by_vendor[vendor] = spending_by_vendor.get(vendor, 0) + float(amount)
                
                # By month
                inv_date_str = inv.get('date_string') or inv.get('date') or inv.get('invoice_date')
                if inv_date_str:
                    try:
                        inv_date_str = str(inv_date_str).strip()
                        inv_date = None
                        
                        if '/' in inv_date_str:
                            parts = inv_date_str.split()[0].split('/')
                            if len(parts) == 3:
                                try:
                                    inv_date = datetime.strptime(inv_date_str.split()[0], "%d/%m/%Y")
                                except:
                                    pass
                        
                        if not inv_date:
                            try:
                                inv_date_clean = inv_date_str.split('T')[0].split()[0]
                                inv_date = datetime.strptime(inv_date_clean, "%Y-%m-%d")
                            except:
                                pass
                        
                        if inv_date:
                            month_key = inv_date.strftime("%Y-%m")
                            monthly_spending[month_key] = monthly_spending.get(month_key, 0) + float(amount)
                    except:
                        pass
            
            # Sort vendors by spending
            top_vendors = sorted(spending_by_vendor.items(), key=lambda x: x[1], reverse=True)[:10]
            
            return {
                "success": True,
                "total_spending": total_spending,
                "total_invoices": len(invoices),
                "average_per_invoice": total_spending / len(invoices) if invoices else 0,
                "spending_by_type": spending_by_type,
                "top_vendors": [{"vendor": v[0], "amount": v[1]} for v in top_vendors],
                "monthly_breakdown": dict(sorted(monthly_spending.items())),
                "date_range": {
                    "start": start_date,
                    "end": end_date
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def analyze_spending_trends(self, user_id: Optional[int] = None, months: int = 6) -> Dict[str, Any]:
        """
        Phân tích xu hướng chi tiêu theo thời gian
        
        Args:
            user_id: Lọc theo user (optional)
            months: Số tháng phân tích (mặc định 6 tháng)
        
        Returns:
            Xu hướng chi tiêu và insights
        """
        try:
            invoices = self.db_tools.get_all_invoices(limit=10000, user_id=user_id)
            
            # Organize by month
            monthly_data = {}
            type_trends = {}
            
            for inv in invoices:
                amount = inv.get('total_amount_numeric') or inv.get('total_amount_value') or inv.get('amount') or 0
                inv_type = inv.get('invoice_type', 'unknown')
                
                inv_date_str = inv.get('date_string') or inv.get('date') or inv.get('invoice_date')
                if inv_date_str:
                    try:
                        inv_date_str = str(inv_date_str).strip()
                        inv_date = None
                        
                        if '/' in inv_date_str:
                            parts = inv_date_str.split()[0].split('/')
                            if len(parts) == 3:
                                try:
                                    inv_date = datetime.strptime(inv_date_str.split()[0], "%d/%m/%Y")
                                except:
                                    pass
                        
                        if not inv_date:
                            try:
                                inv_date_clean = inv_date_str.split('T')[0].split()[0]
                                inv_date = datetime.strptime(inv_date_clean, "%Y-%m-%d")
                            except:
                                pass
                        
                        if inv_date:
                            month_key = inv_date.strftime("%Y-%m")
                            
                            if month_key not in monthly_data:
                                monthly_data[month_key] = {
                                    "total": 0,
                                    "count": 0,
                                    "by_type": {}
                                }
                            
                            monthly_data[month_key]["total"] += float(amount)
                            monthly_data[month_key]["count"] += 1
                            
                            if inv_type not in monthly_data[month_key]["by_type"]:
                                monthly_data[month_key]["by_type"][inv_type] = 0
                            monthly_data[month_key]["by_type"][inv_type] += float(amount)
                            
                            # Track type trends
                            if inv_type not in type_trends:
                                type_trends[inv_type] = []
                            type_trends[inv_type].append({
                                "month": month_key,
                                "amount": float(amount)
                            })
                    except:
                        pass
            
            # Calculate trends
            sorted_months = sorted(monthly_data.keys())[-months:]
            trend_data = []
            
            for month in sorted_months:
                data = monthly_data[month]
                trend_data.append({
                    "month": month,
                    "total": data["total"],
                    "count": data["count"],
                    "average": data["total"] / data["count"] if data["count"] > 0 else 0,
                    "by_type": data["by_type"]
                })
            
            # Detect trend direction
            if len(trend_data) >= 2:
                recent_avg = sum(d["total"] for d in trend_data[-3:]) / min(3, len(trend_data))
                older_avg = sum(d["total"] for d in trend_data[:3]) / min(3, len(trend_data))
                
                if recent_avg > older_avg * 1.1:
                    trend_direction = "tăng"
                    change_percent = ((recent_avg - older_avg) / older_avg * 100) if older_avg > 0 else 0
                elif recent_avg < older_avg * 0.9:
                    trend_direction = "giảm"
                    change_percent = ((older_avg - recent_avg) / older_avg * 100) if older_avg > 0 else 0
                else:
                    trend_direction = "ổn định"
                    change_percent = 0
            else:
                trend_direction = "chưa đủ dữ liệu"
                change_percent = 0
            
            return {
                "success": True,
                "months_analyzed": len(sorted_months),
                "trend_direction": trend_direction,
                "change_percent": round(change_percent, 2),
                "monthly_data": trend_data,
                "insights": {
                    "highest_month": max(trend_data, key=lambda x: x["total"]) if trend_data else None,
                    "lowest_month": min(trend_data, key=lambda x: x["total"]) if trend_data else None,
                    "average_monthly_spending": sum(d["total"] for d in trend_data) / len(trend_data) if trend_data else 0,
                    "total_invoices": sum(d["count"] for d in trend_data)
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def detect_spending_anomalies(self, user_id: Optional[int] = None, threshold_multiplier: float = 2.0) -> Dict[str, Any]:
        """
        Phát hiện các hóa đơn bất thường (giá trị cao hơn bình thường nhiều)
        
        Args:
            user_id: Lọc theo user (optional)
            threshold_multiplier: Hệ số ngưỡng (mặc định 2.0 = gấp đôi trung bình)
        
        Returns:
            Danh sách hóa đơn bất thường và phân tích
        """
        try:
            invoices = self.db_tools.get_all_invoices(limit=10000, user_id=user_id)
            
            if not invoices:
                return {
                    "success": False,
                    "error": "No invoices found"
                }
            
            # Calculate statistics
            amounts = []
            for inv in invoices:
                amount = inv.get('total_amount_numeric') or inv.get('total_amount_value') or inv.get('amount') or 0
                amounts.append(float(amount))
            
            # Calculate mean and standard deviation
            mean_amount = sum(amounts) / len(amounts) if amounts else 0
            variance = sum((x - mean_amount) ** 2 for x in amounts) / len(amounts) if amounts else 0
            std_dev = variance ** 0.5
            
            # Detect anomalies
            anomalies = []
            threshold = mean_amount * threshold_multiplier
            
            for inv in invoices:
                amount = inv.get('total_amount_numeric') or inv.get('total_amount_value') or inv.get('amount') or 0
                amount_float = float(amount)
                
                # Check if anomaly
                is_anomaly = False
                anomaly_type = ""
                severity = "low"
                
                if amount_float > threshold:
                    is_anomaly = True
                    anomaly_type = "high_value"
                    if amount_float > mean_amount * 3:
                        severity = "high"
                    elif amount_float > mean_amount * 2.5:
                        severity = "medium"
                    else:
                        severity = "low"
                elif amount_float > 0 and amount_float < mean_amount * 0.3:
                    is_anomaly = True
                    anomaly_type = "unusually_low"
                    severity = "low"
                
                # Check for suspicious patterns
                invoice_code = inv.get('invoice_code', '')
                if is_anomaly or (invoice_code and len(invoice_code) < 3):
                    # Additional checks
                    vendor = inv.get('vendor') or inv.get('seller_name') or ''
                    if not vendor or len(vendor) < 3:
                        severity = "high"
                        if not is_anomaly:
                            is_anomaly = True
                            anomaly_type = "missing_vendor"
                
                if is_anomaly:
                    deviation = ((amount_float - mean_amount) / mean_amount * 100) if mean_amount > 0 else 0
                    anomalies.append({
                        "invoice_id": inv.get('id'),
                        "invoice_number": inv.get('invoice_number'),
                        "invoice_code": inv.get('invoice_code'),
                        "amount": amount_float,
                        "vendor": inv.get('vendor') or inv.get('seller_name'),
                        "date": inv.get('date_string') or inv.get('date'),
                        "anomaly_type": anomaly_type,
                        "severity": severity,
                        "deviation_percent": round(deviation, 2),
                        "times_above_average": round(amount_float / mean_amount, 2) if mean_amount > 0 else 0
                    })
            
            # Sort by severity and amount
            severity_order = {"high": 3, "medium": 2, "low": 1}
            anomalies.sort(key=lambda x: (severity_order.get(x["severity"], 0), x["amount"]), reverse=True)
            
            return {
                "success": True,
                "total_invoices": len(invoices),
                "anomalies_found": len(anomalies),
                "statistics": {
                    "mean_amount": round(mean_amount, 2),
                    "std_deviation": round(std_dev, 2),
                    "threshold_used": round(threshold, 2),
                    "min_amount": round(min(amounts), 2) if amounts else 0,
                    "max_amount": round(max(amounts), 2) if amounts else 0
                },
                "anomalies": anomalies[:20],  # Return top 20
                "severity_breakdown": {
                    "high": len([a for a in anomalies if a["severity"] == "high"]),
                    "medium": len([a for a in anomalies if a["severity"] == "medium"]),
                    "low": len([a for a in anomalies if a["severity"] == "low"])
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
