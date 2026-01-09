"""
Intent Detection Service - Phân loại intent của user để route đúng xử lý
Sử dụng Groq LLM để hiểu semantic thay vì keyword matching
"""
from typing import Dict, List, Tuple, Optional, Any
import re
import json
from utils.logger import get_logger
from core.dependencies import container

logger = get_logger(__name__)


class IntentDetector:
    """
    Detect user intent using both hybrid approach:
    1. Fast keyword-based detection for common patterns
    2. Groq LLM-based semantic understanding for complex queries
    """
    
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
        "trung bình", "average",
        "xu hướng", "trend", "trending",
        "bất thường", "anomaly", "anomalies", "đáng ngờ",
        "cao nhất", "thấp nhất", "highest", "lowest",
        "tăng", "giảm", "increase", "decrease",
        "biến động", "fluctuation", "variance"
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
        "cảm ơn", "thanks", "thank you", "tạm biệt", "bye", "goodbye"
    ]
    
    HELP_KEYWORDS = [
        "giúp", "help", "hướng dẫn", "guide",
        "làm gì", "what can", "chức năng", "function",
        "sử dụng", "how to use"
    ]
    
    def __init__(self):
        """Initialize with Groq client for semantic detection"""
        self.groq_client = container.groq_client
        self.settings = container.settings
    
    def detect_intent(self, message: str) -> Dict[str, Any]:
        """
        Phát hiện intent của user message sử dụng hybrid approach:
        1. Nếu có keyword rõ ràng → dùng keyword matching (nhanh)
        2. Nếu không rõ ràng → gọi Groq LLM (semantic understanding)
        
        Args:
            message: User message
            
        Returns:
            Dict chứa intent type và chi tiết
        """
        message_lower = message.lower()
        
        # PHASE 1: Fast keyword-based detection
        fast_intent = self._detect_intent_by_keywords(message_lower)
        
        if fast_intent and fast_intent.get("confidence", 0) >= 0.8:
            logger.info(f"✅ Fast intent detection: {fast_intent['type']} (confidence: {fast_intent.get('confidence')})")
            return fast_intent
        
        # PHASE 2: Semantic detection using Groq LLM (for ambiguous queries)
        if self.groq_client:
            semantic_intent = self._detect_intent_semantic(message)
            if semantic_intent:
                logger.info(f"🧠 Semantic intent detection: {semantic_intent['type']} (confidence: {semantic_intent.get('confidence')})")
                return semantic_intent
        
        # PHASE 3: Fallback to fast detection or default
        return fast_intent if fast_intent else {
            "type": "basic_chat",
            "subtype": "general",
            "needs_database": False,
            "confidence": 0.5,
            "method": "fallback"
        }
    
    def _detect_intent_by_keywords(self, message: str) -> Optional[Dict[str, Any]]:
        """Fast keyword-based intent detection"""
        
        # IMPORTANT: Kiểm tra data queries TRƯỚC (ưu tiên cao hơn)
        # Nếu có đề cập đến hóa đơn/tiền bạc → luôn là data query
        
        # 1. Check invoice search (cần database) - ƯU TIÊN CAO NHẤT
        if self._contains_keywords(message, self.INVOICE_SEARCH_KEYWORDS):
            # Nếu có "có bao nhiêu" + "hóa đơn" → đây là invoice query, không phải greeting
            return {
                "type": "data_query",
                "subtype": "invoice_search",
                "needs_database": True,
                "confidence": 0.90,
                "entities": self._extract_entities(message),
                "method": "keyword"
            }
        
        # 2. Check statistics queries (cần database)
        if self._contains_keywords(message, self.STATISTICS_KEYWORDS):
            return {
                "type": "data_query",
                "subtype": "statistics",
                "needs_database": True,
                "confidence": 0.85,
                "entities": self._extract_entities(message),
                "method": "keyword"
            }
        
        # 3. Check amount queries (cần database)
        if self._contains_keywords(message, self.AMOUNT_KEYWORDS):
            return {
                "type": "data_query",
                "subtype": "amount_query",
                "needs_database": True,
                "confidence": 0.80,
                "entities": self._extract_entities(message),
                "method": "keyword"
            }
        
        # 4. CHỈ KHI KHÔNG CÓ DATA QUERY → mới kiểm tra greeting/help
        if self._contains_keywords(message, self.GREETING_KEYWORDS):
            return {
                "type": "basic_chat",
                "subtype": "greeting",
                "needs_database": False,
                "confidence": 0.95,
                "method": "keyword"
            }
        
        if self._contains_keywords(message, self.HELP_KEYWORDS):
            return {
                "type": "basic_chat",
                "subtype": "help",
                "needs_database": False,
                "confidence": 0.95,
                "method": "keyword"
            }
        
        # Return None if no strong keywords found (will trigger semantic detection)
        return None
    
    def _detect_intent_semantic(self, message: str) -> Optional[Dict[str, Any]]:
        """
        Semantic intent detection using Groq LLM
        Cho phép hiểu các câu hỏi phức tạp, implicit, hoặc viết lại
        """
        try:
            if not self.groq_client:
                return None
            
            # Prompt cho Groq để classify intent
            system_prompt = """Bạn là chuyên gia phân loại intent cho hệ thống quản lý hóa đơn.
Phân tích user message và xác định intent của nó.

INTENT TYPES:
1. "greeting" - lời chào, cảm ơn, chào tạm biệt
2. "help" - yêu cầu hướng dẫn, tìm hiểu chức năng
3. "invoice_search" - tìm kiếm hóa đơn cụ thể (theo tên, ngày, etc.)
4. "statistics" - thống kê, phân tích, tổng hợp dữ liệu
5. "amount_query" - hỏi về số tiền, chi phí, tổng tiền
6. "spending_analysis" - phân tích chi tiêu, xu hướng, bất thường
7. "general_chat" - trò chuyện thông thường, không cần database

HƯỚNG DẪN:
- "có bao nhiêu hóa đơn tháng này" → statistics
- "hóa đơn của công ty ABC" → invoice_search
- "tôi chi bao nhiêu tuần này" → amount_query
- "tổng chi tiêu là bao nhiêu" → amount_query
- "xu hướng chi tiêu" → spending_analysis
- "phát hiện bất thường" → spending_analysis
- "xin chào" → greeting
- "có thể làm gì" → help
- "hôm nay thời tiết sao" → general_chat

TRƯỚC TIÊN KIỂM TRA:
- Có đề cập đến hóa đơn, chi tiêu, tiền bạc không? → data_query
- Có yêu cầu tìm kiếm, thống kê không? → data_query
- Có yêu cầu phân tích xu hướng, phát hiện bất thường không? → spending_analysis
- Là lời chào hoặc yêu cầu hướng dẫn không? → basic_chat

Trả lời JSON với định dạng:
{
    "type": "basic_chat" hoặc "data_query",
    "subtype": "greeting|help|invoice_search|statistics|amount_query|spending_analysis|general_chat",
    "confidence": 0.0-1.0,
    "reasoning": "giải thích ngắn"
}
"""
            
            response = self.groq_client.chat.completions.create(
                model=self.settings.GROQ_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Classify this message: '{message}'"}
                ],
                max_tokens=200,
                temperature=0.3
            )
            
            # Parse Groq response
            response_text = response.choices[0].message.content
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                intent_data = json.loads(json_match.group())
                
                # Convert to our format
                subtype = intent_data.get("subtype", "general_chat")
                intent_type = "basic_chat"
                needs_db = False
                
                if subtype in ["invoice_search", "statistics", "amount_query", "spending_analysis"]:
                    intent_type = "data_query"
                    needs_db = True
                
                return {
                    "type": intent_type,
                    "subtype": subtype,
                    "needs_database": needs_db,
                    "confidence": float(intent_data.get("confidence", 0.6)),
                    "reasoning": intent_data.get("reasoning", ""),
                    "method": "semantic",
                    "entities": self._extract_entities(message.lower())
                }
        
        except Exception as e:
            logger.warning(f"Semantic intent detection failed: {e}")
            return None
    
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
