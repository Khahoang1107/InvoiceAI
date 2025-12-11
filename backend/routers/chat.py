# API Router: Chat Messaging with Groq AI

from fastapi import APIRouter, HTTPException, status, Depends
from typing import Optional
from pydantic import BaseModel
import logging
import os

logger = logging.getLogger(__name__)
router = APIRouter(tags=["chat"])

class ChatMessage(BaseModel):
    message: str
    conversation_id: Optional[str] = None

# Global chat handler instance (initialized on first use)
_chat_handler = None

def get_chat_handler():
    """Initialize and return Groq chat handler"""
    global _chat_handler
    
    if _chat_handler is None:
        try:
            # Get database tools based on DATABASE_URL
            database_url = os.getenv('DATABASE_URL', '')
            
            if database_url and not database_url.startswith('sqlite'):
                from utils.database_tools_postgres import get_database_tools
            else:
                from utils.database_tools_sqlite import get_database_tools
            
            db_tools = get_database_tools()
            
            # Import and setup Groq tools
            from groq_tools import GroqDatabaseTools
            groq_tools = GroqDatabaseTools(db_tools)
            
            # Import and setup Groq handler
            from handlers.groq_chat_handler import GroqChatHandler
            _chat_handler = GroqChatHandler(db_tools=db_tools, groq_tools=groq_tools)
            
            logger.info("✅ Groq chat handler initialized successfully")
        except Exception as e:
            logger.warning(f"⚠️ Failed to initialize Groq handler: {e}")
            _chat_handler = None
    
    return _chat_handler

@router.post("/chat")
async def chat(request: ChatMessage):
    """
    Chat endpoint - Process message through Groq AI
    
    Features:
    - Natural language understanding
    - Database operations via function calling
    - Context-aware responses
    - Invoice management commands
    """
    try:
        logger.info(f"Chat message: {request.message[:50]}...")
        
        # Get or initialize chat handler
        chat_handler = get_chat_handler()
        
        if chat_handler is None:
            # Fallback response with basic intent recognition when Groq not available
            message_lower = request.message.lower().strip()
            
            # Check for export/xuất intent
            export_keywords = ["xuất", "export", "tải", "download", "báo cáo", "excel"]
            if any(keyword in message_lower for keyword in export_keywords):
                return {
                    "response": """📊 **Xuất báo cáo hóa đơn**

Vui lòng chọn:
1. **Xuất Excel tất cả** - Tất cả hóa đơn
2. **Xuất Excel hôm nay** - Hóa đơn hôm nay
3. **Xuất Excel theo loại** - Lọc theo loại hóa đơn

💡 Hoặc vào phần **"Quản lý hóa đơn"** → Chọn hóa đơn → Nhấn nút **"Xuất Excel"**""",
                    "conversation_id": request.conversation_id or "default",
                    "success": True,
                    "type": "export_guide"
                }
            
            # Check for statistics/thống kê intent
            stats_keywords = ["thống kê", "statistics", "tổng", "số lượng", "bao nhiêu"]
            if any(keyword in message_lower for keyword in stats_keywords):
                try:
                    # Get database tools
                    database_url = os.getenv('DATABASE_URL', '')
                    if database_url and not database_url.startswith('sqlite'):
                        from utils.database_tools_postgres import get_database_tools
                    else:
                        from utils.database_tools_sqlite import get_database_tools
                    
                    db_tools = get_database_tools()
                    stats = db_tools.get_statistics()
                    
                    return {
                        "response": f"""📊 **Thống kê hóa đơn**

📋 Tổng số hóa đơn: **{stats.get('total_invoices', 0)}**
💰 Tổng tiền: **{stats.get('total_amount_sum', 0):,.0f} VND**
📅 7 ngày gần nhất: **{stats.get('recent_7days', 0)}** hóa đơn""",
                        "conversation_id": request.conversation_id or "default",
                        "success": True,
                        "type": "statistics"
                    }
                except Exception as e:
                    logger.error(f"Error getting statistics: {e}")
            
            # Default fallback
            return {
                "response": """⚠️ Groq AI chưa được cấu hình.

🎯 Tôi có thể giúp bạn:
1. 📋 Xem danh sách hóa đơn
2. 🔍 Tìm kiếm hóa đơn
3. 📊 Xem thống kê
4. 📤 Xuất báo cáo Excel

Vui lòng kiểm tra GROQ_API_KEY trong file .env""",
                "conversation_id": request.conversation_id or "default",
                "success": False,
                "type": "error"
            }
        
        # Process message through Groq
        user_id = request.conversation_id or "default"
        response = await chat_handler.chat(request.message, user_id=user_id)
        
        # Format response for frontend
        return {
            "response": response.get("message", ""),
            "conversation_id": user_id,
            "success": True,
            "type": response.get("type", "text"),
            "metadata": {
                "model": response.get("model"),
                "method": response.get("method"),
                "tools_used": response.get("tools_used", [])
            }
        }
        
    except Exception as e:
        logger.error(f"Chat failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat failed: {str(e)}"
        )

