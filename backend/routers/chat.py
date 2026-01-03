from fastapi import APIRouter, HTTPException, status, Depends
from typing import Optional
from pydantic import BaseModel
import logging
from utils.auth_utils import get_current_user
from services.chat_service import ChatService
from schemas.models import ChatRequest, ChatResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["chat"])

class ChatMessage(BaseModel):
    message: str
    conversation_id: Optional[str] = None

# Dependency for chat service - lazy initialization
def get_chat_service() -> ChatService:
    """Get chat service instance"""
    return ChatService()

@router.post("/")
async def chat(
    request: ChatMessage, 
    current_user = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Chat endpoint with RAG - Process message through Groq AI with retrieved context
    
    Features:
    - Natural language understanding with RAG
    - Context-aware responses using vector search
    - Invoice data retrieval and analysis
    - Safe responses (admits when information not found)
    """
    try:
        logger.info(f"RAG Chat message from user {current_user.user_id}: {request.message[:50]}...")
        
        # Create ChatRequest object
        chat_request = ChatRequest(
            message=request.message,
            conversation_id=request.conversation_id
        )
        
        # Process through ChatService with RAG
        user_id = current_user.user_id or 1  # Default to user ID 1 if not available
        response = await chat_service.send_message(user_id, chat_request)
        
        # Format response for frontend
        return {
            "response": response.response,
            "conversation_id": response.conversation_id,
            "success": True,
            "type": "rag_response",
            "metadata": {
                "tokens_used": response.tokens_used,
                "rag_enabled": chat_service.rag_available,
                "model": "mixtral-8x7b-32768"
            }
        }
        
    except Exception as e:
        logger.error(f"RAG Chat failed: {str(e)}")
        
        # Provide helpful fallback response
        return {
            "response": """⚠️ Xin lỗi, tôi gặp sự cố khi xử lý câu hỏi của bạn.

💡 **Gợi ý:**
- Kiểm tra kết nối internet
- Thử hỏi lại với câu khác
- Upload thêm hóa đơn để tôi có thêm dữ liệu

Nếu vấn đề tiếp tục, vui lòng liên hệ hỗ trợ.""",
            "conversation_id": request.conversation_id or "default",
            "success": False,
            "type": "error",
            "error": str(e)
        }

