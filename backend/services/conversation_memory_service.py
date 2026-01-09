"""
Conversation Memory Service
Quản lý bộ nhớ cuộc hội thoại để cung cấp context awareness tốt hơn
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class ConversationMemoryService:
    """
    Quản lý bộ nhớ ngắn hạn của các cuộc hội thoại
    Giúp chatbot ghi nhớ context và thực hiện multi-turn conversations tốt hơp
    """
    
    def __init__(self, max_history: int = 10, ttl_minutes: int = 30):
        """
        Initialize memory service
        
        Args:
            max_history: Max messages to keep per conversation (default 10)
            ttl_minutes: Time to live for conversation context (default 30 mins)
        """
        self.max_history = max_history
        self.ttl = timedelta(minutes=ttl_minutes)
        
        # In-memory storage: conversation_id -> List[Message]
        self.memory: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        
        # Conversation metadata
        self.metadata: Dict[str, Dict[str, Any]] = {}
    
    def add_message(
        self,
        conversation_id: str,
        user_id: int,
        role: str,  # "user" or "assistant"
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add a message to conversation memory
        
        Args:
            conversation_id: Unique conversation ID
            user_id: User who initiated conversation
            role: "user" or "assistant"
            content: Message content
            metadata: Optional metadata (intent, confidence, etc.)
        """
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now(),
            "metadata": metadata or {}
        }
        
        self.memory[conversation_id].append(message)
        
        # Keep only recent messages
        if len(self.memory[conversation_id]) > self.max_history:
            self.memory[conversation_id] = self.memory[conversation_id][-self.max_history:]
        
        # Update conversation metadata
        self._update_metadata(conversation_id, user_id, role)
        
        logger.debug(f"✅ Message added to conversation {conversation_id}: {role}")
    
    def get_context(self, conversation_id: str, num_messages: int = 5) -> List[Dict[str, str]]:
        """
        Get recent conversation context in Groq API format
        
        Args:
            conversation_id: Conversation to retrieve
            num_messages: Number of recent messages to include
            
        Returns:
            List of messages in format [{"role": "user"|"assistant", "content": "..."}]
        """
        if conversation_id not in self.memory:
            return []
        
        # Get recent messages (up to num_messages)
        recent = self.memory[conversation_id][-num_messages:]
        
        # Filter out expired conversations
        now = datetime.now()
        valid_messages = []
        
        for msg in recent:
            msg_time = msg.get("timestamp")
            
            # If timestamp is from before TTL, skip
            if msg_time and (now - msg_time) > self.ttl:
                continue
            
            valid_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        return valid_messages
    
    def get_full_context(self, conversation_id: str) -> List[Dict[str, str]]:
        """Get all messages in conversation (for export or analysis)"""
        if conversation_id not in self.memory:
            return []
        
        return [
            {
                "role": msg["role"],
                "content": msg["content"],
                "timestamp": msg["timestamp"].isoformat()
            }
            for msg in self.memory[conversation_id]
        ]
    
    def get_conversation_summary(self, conversation_id: str) -> Dict[str, Any]:
        """
        Get conversation summary (intent history, topics discussed, etc.)
        """
        if conversation_id not in self.memory:
            return {
                "conversation_id": conversation_id,
                "status": "not_found"
            }
        
        meta = self.metadata.get(conversation_id, {})
        messages = self.memory[conversation_id]
        
        # Count intents
        intents = defaultdict(int)
        for msg in messages:
            intent = msg.get("metadata", {}).get("intent_type")
            if intent:
                intents[intent] += 1
        
        return {
            "conversation_id": conversation_id,
            "user_id": meta.get("user_id"),
            "created_at": meta.get("created_at"),
            "last_updated": meta.get("last_updated"),
            "message_count": len(messages),
            "intents_detected": dict(intents),
            "topics": meta.get("topics", []),
            "current_context": self.get_context(conversation_id, num_messages=3)
        }
    
    def clear_conversation(self, conversation_id: str) -> None:
        """Clear a conversation from memory"""
        if conversation_id in self.memory:
            del self.memory[conversation_id]
        if conversation_id in self.metadata:
            del self.metadata[conversation_id]
        logger.info(f"🧹 Conversation {conversation_id} cleared")
    
    def clear_expired_conversations(self) -> int:
        """
        Clear conversations older than TTL
        
        Returns:
            Number of conversations cleared
        """
        now = datetime.now()
        expired = []
        
        for conv_id, meta in self.metadata.items():
            last_updated = meta.get("last_updated")
            if last_updated and (now - last_updated) > self.ttl:
                expired.append(conv_id)
        
        for conv_id in expired:
            self.clear_conversation(conv_id)
        
        if expired:
            logger.info(f"🧹 Cleared {len(expired)} expired conversations")
        
        return len(expired)
    
    def extract_entities_from_context(self, conversation_id: str) -> Dict[str, List[str]]:
        """
        Extract entities (vendors, dates, amounts) from conversation history
        Useful for implicit references in new messages
        
        Example: 
        - User: "tôi mua laptop hôm qua"
        - Later: "lần đó chi bao nhiêu"
        -> Extract: vendor="laptop", date="yesterday"
        """
        if conversation_id not in self.memory:
            return {"vendors": [], "dates": [], "amounts": []}
        
        # For now, return empty (can be enhanced with NER)
        entities = {
            "vendors": [],
            "dates": [],
            "amounts": []
        }
        
        # TODO: Parse message content to extract entities
        
        return entities
    
    def get_recent_intents(
        self,
        conversation_id: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get recent intents detected in conversation"""
        if conversation_id not in self.memory:
            return []
        
        intents = []
        for msg in self.memory[conversation_id][-limit:]:
            intent = msg.get("metadata", {}).get("intent_type")
            confidence = msg.get("metadata", {}).get("intent_confidence", 0)
            
            if intent:
                intents.append({
                    "type": intent,
                    "confidence": confidence,
                    "timestamp": msg["timestamp"].isoformat()
                })
        
        return intents
    
    def _update_metadata(
        self,
        conversation_id: str,
        user_id: int,
        role: str
    ) -> None:
        """Update conversation metadata"""
        if conversation_id not in self.metadata:
            self.metadata[conversation_id] = {
                "user_id": user_id,
                "created_at": datetime.now(),
                "topics": []
            }
        
        self.metadata[conversation_id]["last_updated"] = datetime.now()
        self.metadata[conversation_id]["last_role"] = role
    
    def get_stats(self) -> Dict[str, Any]:
        """Get overall memory stats"""
        total_conversations = len(self.memory)
        total_messages = sum(len(msgs) for msgs in self.memory.values())
        
        return {
            "total_conversations": total_conversations,
            "total_messages": total_messages,
            "avg_messages_per_conversation": (
                total_messages // total_conversations if total_conversations > 0 else 0
            ),
            "memory_usage_mb": sum(
                len(str(msgs)) for msgs in self.memory.values()
            ) / (1024 * 1024)
        }


# Global memory service instance
_memory_service: Optional[ConversationMemoryService] = None


def get_memory_service() -> ConversationMemoryService:
    """Get or create global memory service"""
    global _memory_service
    if _memory_service is None:
        _memory_service = ConversationMemoryService()
    return _memory_service
