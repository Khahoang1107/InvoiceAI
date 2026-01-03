"""
Intent Detection Service - Phân loại intent của user để route đúng xử lý
"""
from typing import Dict, List, Tuple
import re
from utils.logger import get_logger

logger = get_logger(__name__)


class IntentDetector:
    """Detect user intent to route between basic chat and RAG-based queries"""
    
    # Từ khóa cho các intent cần truy vấn database
    INVOICE_SEARCH_KEYWORDS = [
        "hóa đơn", "hoá đơn", "invoice", "bill", "receipt",
        "tìm", "tìm kiếm", "search", "xem", "danh sách",
        "có bao nhiêu", "bao nhiêu hóa đơn", "mấy hóa đơn",
        "trong db", "trong database", "đã lưu", "đã upload"
    ]
    
    STATISTICS_KEYWORDS = [
        "thống kê", "statistics", "tổng", "total", "sum",
        "chi tiêu", "spending", "expense",
        "phân tích", "analysis", "analyze",
        "so sánh", "compare", "comparison",
        "tháng này", "tháng trước", "năm nay",
        "trung bình", "average"
    ]
    
    AMOUNT_KEYWORDS = [
        "tiền", "money", "amount", "giá",
        "bao nhiêu", "how much", "얼마",
        "tổng tiền", "total amount"
    ]
    
    DATE_KEYWORDS = [
        "ngày", "date", "tháng", "month", "năm", "year",
        "hôm nay", "today", "hôm qua", "yesterday",
        "tuần này", "this week", "tuần trước", "last week"
    ]
    
    VENDOR_KEYWORDS = [
        "cửa hàng", "store", "shop", "nhà hàng", "restaurant",
        "siêu thị", "supermarket", "công ty", "company",
        "nhà cung cấp", "vendor", "supplier"
    ]
    
    # Từ khóa cho chat cơ bản (không cần RAG)
    GREETING_KEYWORDS = [
        "xin chào", "chào bạn", "hello", "hi", "hey",
        "cảm ơn", "thanks", "thank you", "tạm biệt", "bye"
    ]
    
    HELP_KEYWORDS = [
        "giúp", "help", "hướng dẫn", "guide",
        "làm gì", "what can", "chức năng", "function",
        "sử dụng", "how to use"
    ]
    
    def detect_intent(self, message: str) -> Dict[str, any]:
        """
        Phát hiện intent của user message
        
        Args:
            message: User message
            
        Returns:
            Dict chứa intent type và chi tiết
        """
        message_lower = message.lower()
        
        # 1. Check statistics queries FIRST (cần database) - ưu tiên cao
        if self._contains_keywords(message_lower, self.STATISTICS_KEYWORDS):
            return {
                "type": "data_query",
                "subtype": "statistics",
                "needs_database": True,
                "confidence": 0.85,
                "entities": self._extract_entities(message_lower)
            }
        
        # 2. Check invoice search (cần database) - ưu tiên cao
        if self._contains_keywords(message_lower, self.INVOICE_SEARCH_KEYWORDS):
            return {
                "type": "data_query",
                "subtype": "invoice_search",
                "needs_database": True,
                "confidence": 0.85,
                "entities": self._extract_entities(message_lower)
            }
        
        # 3. Check amount queries (cần database)
        if self._contains_keywords(message_lower, self.AMOUNT_KEYWORDS):
            return {
                "type": "data_query",
                "subtype": "amount_query",
                "needs_database": True,
                "confidence": 0.8,
                "entities": self._extract_entities(message_lower)
            }
        
        # 4. Check greeting/help (chat cơ bản) - ưu tiên thấp hơn
        if self._contains_keywords(message_lower, self.GREETING_KEYWORDS):
            return {
                "type": "basic_chat",
                "subtype": "greeting",
                "needs_database": False,
                "confidence": 0.9
            }
        
        if self._contains_keywords(message_lower, self.HELP_KEYWORDS):
            return {
                "type": "basic_chat",
                "subtype": "help",
                "needs_database": False,
                "confidence": 0.9
            }
        
        # 5. Default: basic chat nếu không rõ ràng
        return {
            "type": "basic_chat",
            "subtype": "general",
            "needs_database": False,
            "confidence": 0.6
        }
    
    def _contains_keywords(self, text: str, keywords: List[str]) -> bool:
        """Check if text contains any keyword"""
        return any(keyword in text for keyword in keywords)
    
    def _extract_entities(self, message: str) -> Dict[str, List[str]]:
        """
        Extract entities từ message (ngày, số tiền, tên vendor, etc.)
        
        Args:
            message: User message (lowercase)
            
        Returns:
            Dict chứa các entities được phát hiện
        """
        entities = {
            "dates": [],
            "amounts": [],
            "vendors": [],
            "time_periods": []
        }
        
        # Extract time periods
        time_patterns = [
            r"tháng (\d+)",
            r"năm (\d{4})",
            r"(hôm nay|hôm qua|tuần này|tuần trước|tháng này|tháng trước)"
        ]
        
        for pattern in time_patterns:
            matches = re.findall(pattern, message)
            if matches:
                entities["time_periods"].extend(matches)
        
        # Extract amounts (số có đơn vị tiền)
        amount_pattern = r"(\d+(?:[.,]\d+)?)\s*(?:đồng|vnđ|vnd|nghìn|triệu|k|tr)"
        amounts = re.findall(amount_pattern, message)
        if amounts:
            entities["amounts"] = amounts
        
        logger.info(f"Extracted entities: {entities}")
        return entities
    
    def should_use_database(self, intent: Dict[str, any]) -> bool:
        """
        Quyết định có cần truy vấn database không
        
        Args:
            intent: Intent dict từ detect_intent()
            
        Returns:
            True nếu cần database, False nếu không
        """
        return intent.get("needs_database", False) and intent.get("confidence", 0) > 0.7
