# Service Layer: AI Learning & Personalization
"""
Service này giúp AI học từ các tương tác và trở nên thông minh hơn theo thời gian.

Các tính năng chính:
1. Lưu successful interactions vào vector store
2. Retrieve similar past queries để cải thiện responses
3. Học user preferences và patterns
4. Phân tích và cải thiện intent detection
"""

import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import Counter

logger = logging.getLogger(__name__)


class LearningService:
    """
    Service quản lý việc học và cải thiện AI từ các tương tác
    """
    
    def __init__(self, vector_store=None):
        """
        Initialize learning service
        
        Args:
            vector_store: Vector store để lưu trữ và tìm kiếm interactions
        """
        self.vector_store = vector_store
        self.user_patterns = {}  # Cache user patterns in memory
        self.interaction_history = []  # Recent interactions for analysis
        
    async def save_successful_interaction(
        self,
        user_id: int,
        user_query: str,
        ai_response: str,
        intent_type: str,
        metadata: Dict[str, Any]
    ):
        """
        Lưu một tương tác thành công để học từ đó
        
        Args:
            user_id: ID của user
            user_query: Câu hỏi của user
            ai_response: Câu trả lời của AI
            intent_type: Loại intent được detect
            metadata: Thông tin bổ sung (function called, execution time, etc.)
        """
        try:
            # Tạo document để lưu vào vector store
            interaction_doc = {
                "user_id": user_id,
                "query": user_query,
                "response": ai_response,
                "intent": intent_type,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": metadata
            }
            
            # Lưu vào vector store (nếu có)
            if self.vector_store:
                await self.vector_store.add_interaction(interaction_doc)
                logger.info(f"💾 Saved interaction for learning: user={user_id}, intent={intent_type}")
            
            # Cache trong memory để phân tích nhanh
            self.interaction_history.append(interaction_doc)
            
            # Giữ chỉ 1000 interactions gần nhất trong memory
            if len(self.interaction_history) > 1000:
                self.interaction_history = self.interaction_history[-1000:]
            
            # Cập nhật user patterns
            await self._update_user_patterns(user_id, user_query, intent_type)
            
        except Exception as e:
            logger.error(f"Failed to save interaction for learning: {e}")
    
    async def get_similar_past_queries(
        self,
        current_query: str,
        user_id: Optional[int] = None,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Tìm các câu hỏi tương tự đã được hỏi trước đó
        
        Args:
            current_query: Câu hỏi hiện tại
            user_id: ID của user (optional, để filter theo user)
            top_k: Số lượng results cần trả về
            
        Returns:
            List các past queries tương tự với response của chúng
        """
        try:
            if not self.vector_store:
                return []
            
            # Tìm kiếm semantic trong past interactions
            similar_interactions = await self.vector_store.search_interactions(
                query=current_query,
                user_id=user_id,
                top_k=top_k
            )
            
            if similar_interactions:
                logger.info(f"🔍 Found {len(similar_interactions)} similar past queries")
            
            return similar_interactions
            
        except Exception as e:
            logger.warning(f"Failed to retrieve similar queries: {e}")
            return []
    
    async def _update_user_patterns(
        self,
        user_id: int,
        query: str,
        intent_type: str
    ):
        """
        Cập nhật patterns của user để hiểu cách họ thường hỏi
        """
        if user_id not in self.user_patterns:
            self.user_patterns[user_id] = {
                "common_intents": Counter(),
                "common_keywords": Counter(),
                "query_count": 0,
                "last_updated": datetime.utcnow()
            }
        
        patterns = self.user_patterns[user_id]
        patterns["common_intents"][intent_type] += 1
        patterns["query_count"] += 1
        patterns["last_updated"] = datetime.utcnow()
        
        # Extract keywords từ query (simple version)
        keywords = [word.lower() for word in query.split() if len(word) > 3]
        patterns["common_keywords"].update(keywords)
        
        logger.debug(f"📊 Updated patterns for user {user_id}")
    
    def get_user_preferences(self, user_id: int) -> Dict[str, Any]:
        """
        Lấy preferences và patterns của user
        
        Returns:
            Dict chứa thông tin về cách user thường interact với hệ thống
        """
        if user_id not in self.user_patterns:
            return {
                "is_new_user": True,
                "common_intents": [],
                "suggestions": []
            }
        
        patterns = self.user_patterns[user_id]
        
        # Top intents user thường dùng
        top_intents = patterns["common_intents"].most_common(3)
        
        # Top keywords user thường nhắc
        top_keywords = patterns["common_keywords"].most_common(5)
        
        return {
            "is_new_user": False,
            "query_count": patterns["query_count"],
            "common_intents": [intent for intent, _ in top_intents],
            "common_keywords": [kw for kw, _ in top_keywords],
            "last_interaction": patterns["last_updated"].isoformat()
        }
    
    def generate_personalized_suggestions(self, user_id: int) -> List[str]:
        """
        Tạo suggestions được personalized dựa trên user patterns
        
        Returns:
            List các câu hỏi gợi ý phù hợp với user
        """
        preferences = self.get_user_preferences(user_id)
        
        if preferences["is_new_user"]:
            # Suggestions mặc định cho user mới
            return [
                "📊 Xem danh sách hóa đơn",
                "💰 Tổng chi tiêu tháng này",
                "🔍 Tìm kiếm hóa đơn"
            ]
        
        # Personalized suggestions dựa trên common intents
        suggestions = []
        common_intents = preferences.get("common_intents", [])
        
        if "invoice_search" in common_intents:
            suggestions.append("🔍 Tìm hóa đơn gần đây")
        
        if "statistics" in common_intents:
            suggestions.append("📊 Thống kê chi tiêu")
        
        if "amount_query" in common_intents:
            suggestions.append("💰 Tổng tiền hóa đơn")
        
        # Fallback nếu không có enough data
        if not suggestions:
            suggestions = [
                "📋 Xem tất cả hóa đơn",
                "📅 Lọc theo ngày"
            ]
        
        return suggestions[:3]  # Max 3 suggestions
    
    async def learn_from_feedback(
        self,
        user_id: int,
        query: str,
        response: str,
        feedback: str,
        rating: Optional[int] = None
    ):
        """
        Học từ feedback của user về response
        
        Args:
            user_id: ID của user
            query: Câu hỏi gốc
            response: Response của AI
            feedback: Feedback từ user (text)
            rating: Rating từ 1-5 (optional)
        """
        try:
            feedback_doc = {
                "user_id": user_id,
                "query": query,
                "response": response,
                "feedback": feedback,
                "rating": rating,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Log feedback để phân tích sau
            logger.info(f"📝 Received feedback from user {user_id}: rating={rating}")
            
            # TODO: Implement advanced learning từ feedback
            # - Phân tích negative feedback
            # - Cải thiện intent detection
            # - Fine-tune responses
            
        except Exception as e:
            logger.error(f"Failed to process feedback: {e}")
    
    def analyze_query_patterns(self) -> Dict[str, Any]:
        """
        Phân tích patterns từ toàn bộ interactions để cải thiện hệ thống
        
        Returns:
            Dict chứa insights về user behaviors
        """
        if not self.interaction_history:
            return {"status": "insufficient_data"}
        
        # Phân tích intents phổ biến
        intent_counter = Counter()
        for interaction in self.interaction_history:
            intent_counter[interaction.get("intent")] += 1
        
        # Phân tích thời gian response
        avg_tokens = sum(
            interaction.get("metadata", {}).get("tokens_used", 0)
            for interaction in self.interaction_history
        ) / len(self.interaction_history)
        
        return {
            "total_interactions": len(self.interaction_history),
            "most_common_intents": intent_counter.most_common(5),
            "avg_tokens_per_response": avg_tokens,
            "unique_users": len(set(i.get("user_id") for i in self.interaction_history))
        }


# Singleton instance
_learning_service_instance = None


def get_learning_service(vector_store=None) -> LearningService:
    """
    Get or create learning service instance
    
    Args:
        vector_store: Vector store instance (optional)
        
    Returns:
        LearningService instance
    """
    global _learning_service_instance
    
    if _learning_service_instance is None:
        _learning_service_instance = LearningService(vector_store=vector_store)
        logger.info("✅ Learning service initialized")
    
    return _learning_service_instance
