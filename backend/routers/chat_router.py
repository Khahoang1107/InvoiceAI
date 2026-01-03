"""
Chat Router với lưu lịch sử
API endpoints cho chatbot với RAG và history
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.config.database import get_db
from backend.middleware.auth_middleware import get_current_user
from backend.schemas.chat_models import (
    ChatRequest,
    ChatResponse,
    ChatHistoryResponse,
    ConversationListResponse,
    ChatMessageResponse
)
from backend.services.chat_history_service import ChatHistoryService
from backend.services.rag_service import RAGService
from groq import Groq
import os

router = APIRouter(prefix="/api/chat", tags=["chat"])

# Initialize services
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))


@router.post("/", response_model=ChatResponse)
async def chat_with_history(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Chat với chatbot - Tự động lưu lịch sử
    
    - Tạo conversation_id mới nếu chưa có
    - Lưu user message
    - Query RAG để lấy context từ invoices
    - Generate response từ LLM
    - Lưu assistant response
    - Return response + conversation_id
    """
    try:
        user_id = current_user["id"]
        
        # Tạo hoặc dùng conversation_id hiện có
        conversation_id = request.conversation_id
        if not conversation_id:
            conversation_id = ChatHistoryService.create_conversation_id()
        
        # Lưu user message
        user_message = ChatHistoryService.save_message(
            db=db,
            user_id=user_id,
            conversation_id=conversation_id,
            role="user",
            message=request.message,
            tokens_used=0
        )
        
        # Lấy context từ RAG (invoices)
        rag_context = ""
        try:
            # TODO: Implement RAG search here
            # rag_results = RAGService.search_invoices(request.message)
            # rag_context = format_rag_context(rag_results)
            pass
        except Exception as e:
            print(f"RAG error: {e}")
        
        # Lấy lịch sử conversation (5 messages gần nhất)
        history_messages = ChatHistoryService.get_conversation_history(
            db=db,
            user_id=user_id,
            conversation_id=conversation_id,
            limit=5
        )
        
        # Build messages cho LLM (bao gồm history)
        llm_messages = [
            {
                "role": "system",
                "content": """Bạn là trợ lý AI quản lý hóa đơn thông minh.
Nhiệm vụ:
- Trả lời câu hỏi về hóa đơn
- Thống kê, phân tích dữ liệu
- Tra cứu thông tin chi tiết
- Hỗ trợ người dùng quản lý tài chính

Trả lời ngắn gọn, chính xác, hữu ích."""
            }
        ]
        
        # Thêm context từ RAG nếu có
        if rag_context:
            llm_messages.append({
                "role": "system",
                "content": f"Dữ liệu hóa đơn liên quan:\n{rag_context}"
            })
        
        # Thêm history (trừ message cuối cùng vì đã có ở user_message)
        for msg in history_messages[:-1]:
            llm_messages.append({
                "role": msg["role"],
                "content": msg["message"]
            })
        
        # Thêm current message
        llm_messages.append({
            "role": "user",
            "content": request.message
        })
        
        # Generate response từ Groq
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=llm_messages,
            temperature=0.3,
            max_tokens=1000
        )
        
        assistant_response = completion.choices[0].message.content
        tokens_used = completion.usage.total_tokens
        
        # Lưu assistant response
        ChatHistoryService.save_message(
            db=db,
            user_id=user_id,
            conversation_id=conversation_id,
            role="assistant",
            message=assistant_response,
            tokens_used=tokens_used,
            model="llama-3.3-70b-versatile"
        )
        
        return ChatResponse(
            response=assistant_response,
            conversation_id=conversation_id,
            tokens_used=tokens_used,
            model="llama-3.3-70b-versatile"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat error: {str(e)}"
        )


@router.get("/conversations", response_model=List[ConversationListResponse])
async def get_conversations(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    limit: int = 20
):
    """
    Lấy danh sách conversations của user
    """
    try:
        user_id = current_user["id"]
        
        conversations = ChatHistoryService.get_user_conversations(
            db=db,
            user_id=user_id,
            limit=limit
        )
        
        return conversations
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching conversations: {str(e)}"
        )


@router.get("/history/{conversation_id}", response_model=ChatHistoryResponse)
async def get_conversation_history(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    limit: int = 50
):
    """
    Lấy lịch sử chat của một conversation
    """
    try:
        user_id = current_user["id"]
        
        # Lấy messages
        messages = ChatHistoryService.get_conversation_history(
            db=db,
            user_id=user_id,
            conversation_id=conversation_id,
            limit=limit
        )
        
        # Lấy stats
        stats = ChatHistoryService.get_conversation_stats(
            db=db,
            user_id=user_id,
            conversation_id=conversation_id
        )
        
        return ChatHistoryResponse(
            conversation_id=conversation_id,
            messages=messages,
            total_messages=stats["total_messages"],
            total_tokens=stats["total_tokens"],
            created_at=stats["created_at"],
            last_updated=stats["last_updated"]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching history: {str(e)}"
        )


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Xóa một conversation (soft delete)
    """
    try:
        user_id = current_user["id"]
        
        deleted = ChatHistoryService.delete_conversation(
            db=db,
            user_id=user_id,
            conversation_id=conversation_id
        )
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        return {"message": "Conversation deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting conversation: {str(e)}"
        )


@router.get("/search", response_model=List[ChatMessageResponse])
async def search_messages(
    query: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    limit: int = 20
):
    """
    Tìm kiếm messages theo nội dung
    """
    try:
        user_id = current_user["id"]
        
        messages = ChatHistoryService.search_messages(
            db=db,
            user_id=user_id,
            search_query=query,
            limit=limit
        )
        
        return messages
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching messages: {str(e)}"
        )
