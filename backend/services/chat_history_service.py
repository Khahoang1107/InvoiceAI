"""
Chat History Service
Xử lý lưu trữ và truy vấn lịch sử chat
"""

from sqlalchemy.orm import Session
from sqlalchemy import text, desc
from typing import List, Optional
from datetime import datetime
import uuid


class ChatHistoryService:
    """Service quản lý lịch sử chat"""
    
    @staticmethod
    def create_conversation_id() -> str:
        """Tạo conversation ID mới"""
        return f"conv_{uuid.uuid4().hex[:12]}"
    
    @staticmethod
    def save_message(
        db: Session,
        user_id: int,
        conversation_id: str,
        role: str,
        message: str,
        tokens_used: int = 0,
        model: str = None
    ) -> dict:
        """
        Lưu một message vào database
        
        Args:
            db: Database session
            user_id: ID của user
            conversation_id: ID của conversation
            role: 'user' hoặc 'assistant'
            message: Nội dung message
            tokens_used: Số token đã dùng
            model: Model đã dùng (llama, gpt, etc.)
        
        Returns:
            dict: Message đã lưu
        """
        query = text("""
            INSERT INTO chat_history 
            (user_id, conversation_id, role, message, tokens_used, model, created_at)
            VALUES (:user_id, :conversation_id, :role, :message, :tokens_used, :model, NOW())
            RETURNING id, user_id, conversation_id, role, message, tokens_used, model, created_at
        """)
        
        result = db.execute(query, {
            "user_id": user_id,
            "conversation_id": conversation_id,
            "role": role,
            "message": message,
            "tokens_used": tokens_used,
            "model": model
        })
        
        db.commit()
        row = result.fetchone()
        
        return {
            "id": row[0],
            "user_id": row[1],
            "conversation_id": row[2],
            "role": row[3],
            "message": row[4],
            "tokens_used": row[5],
            "model": row[6],
            "created_at": row[7]
        }
    
    @staticmethod
    def get_conversation_history(
        db: Session,
        user_id: int,
        conversation_id: str,
        limit: int = 50
    ) -> List[dict]:
        """
        Lấy lịch sử chat của một conversation
        
        Args:
            db: Database session
            user_id: ID của user
            conversation_id: ID của conversation
            limit: Giới hạn số message (default: 50)
        
        Returns:
            List[dict]: Danh sách messages
        """
        query = text("""
            SELECT id, user_id, conversation_id, role, message, tokens_used, model, created_at
            FROM chat_history
            WHERE user_id = :user_id 
              AND conversation_id = :conversation_id
              AND is_deleted = FALSE
            ORDER BY created_at ASC
            LIMIT :limit
        """)
        
        result = db.execute(query, {
            "user_id": user_id,
            "conversation_id": conversation_id,
            "limit": limit
        })
        
        messages = []
        for row in result:
            messages.append({
                "id": row[0],
                "user_id": row[1],
                "conversation_id": row[2],
                "role": row[3],
                "message": row[4],
                "tokens_used": row[5],
                "model": row[6],
                "created_at": row[7]
            })
        
        return messages
    
    @staticmethod
    def get_user_conversations(
        db: Session,
        user_id: int,
        limit: int = 20
    ) -> List[dict]:
        """
        Lấy danh sách conversations của user
        
        Args:
            db: Database session
            user_id: ID của user
            limit: Giới hạn số conversations (default: 20)
        
        Returns:
            List[dict]: Danh sách conversations với thông tin tóm tắt
        """
        query = text("""
            SELECT 
                conversation_id,
                COUNT(*) as message_count,
                MAX(created_at) as last_updated,
                MIN(created_at) as created_at,
                (
                    SELECT message 
                    FROM chat_history ch2 
                    WHERE ch2.conversation_id = ch.conversation_id 
                      AND ch2.user_id = :user_id
                    ORDER BY created_at DESC 
                    LIMIT 1
                ) as last_message
            FROM chat_history ch
            WHERE user_id = :user_id AND is_deleted = FALSE
            GROUP BY conversation_id
            ORDER BY MAX(created_at) DESC
            LIMIT :limit
        """)
        
        result = db.execute(query, {
            "user_id": user_id,
            "limit": limit
        })
        
        conversations = []
        for row in result:
            conversations.append({
                "conversation_id": row[0],
                "message_count": row[1],
                "last_updated": row[2],
                "created_at": row[3],
                "last_message": row[4][:100] if row[4] else ""  # Truncate
            })
        
        return conversations
    
    @staticmethod
    def delete_conversation(
        db: Session,
        user_id: int,
        conversation_id: str
    ) -> bool:
        """
        Xóa (soft delete) một conversation
        
        Args:
            db: Database session
            user_id: ID của user
            conversation_id: ID của conversation
        
        Returns:
            bool: True nếu xóa thành công
        """
        query = text("""
            UPDATE chat_history
            SET is_deleted = TRUE
            WHERE user_id = :user_id AND conversation_id = :conversation_id
        """)
        
        result = db.execute(query, {
            "user_id": user_id,
            "conversation_id": conversation_id
        })
        
        db.commit()
        return result.rowcount > 0
    
    @staticmethod
    def get_conversation_stats(
        db: Session,
        user_id: int,
        conversation_id: str
    ) -> dict:
        """
        Lấy thống kê của một conversation
        
        Args:
            db: Database session
            user_id: ID của user
            conversation_id: ID của conversation
        
        Returns:
            dict: Thống kê (total_messages, total_tokens, etc.)
        """
        query = text("""
            SELECT 
                COUNT(*) as total_messages,
                SUM(tokens_used) as total_tokens,
                MIN(created_at) as created_at,
                MAX(created_at) as last_updated
            FROM chat_history
            WHERE user_id = :user_id 
              AND conversation_id = :conversation_id
              AND is_deleted = FALSE
        """)
        
        result = db.execute(query, {
            "user_id": user_id,
            "conversation_id": conversation_id
        })
        
        row = result.fetchone()
        
        return {
            "total_messages": row[0] or 0,
            "total_tokens": row[1] or 0,
            "created_at": row[2],
            "last_updated": row[3]
        }
    
    @staticmethod
    def search_messages(
        db: Session,
        user_id: int,
        search_query: str,
        limit: int = 20
    ) -> List[dict]:
        """
        Tìm kiếm messages theo nội dung
        
        Args:
            db: Database session
            user_id: ID của user
            search_query: Từ khóa tìm kiếm
            limit: Giới hạn kết quả
        
        Returns:
            List[dict]: Danh sách messages tìm được
        """
        query = text("""
            SELECT id, user_id, conversation_id, role, message, tokens_used, model, created_at
            FROM chat_history
            WHERE user_id = :user_id 
              AND is_deleted = FALSE
              AND message ILIKE :search_query
            ORDER BY created_at DESC
            LIMIT :limit
        """)
        
        result = db.execute(query, {
            "user_id": user_id,
            "search_query": f"%{search_query}%",
            "limit": limit
        })
        
        messages = []
        for row in result:
            messages.append({
                "id": row[0],
                "user_id": row[1],
                "conversation_id": row[2],
                "role": row[3],
                "message": row[4],
                "tokens_used": row[5],
                "model": row[6],
                "created_at": row[7]
            })
        
        return messages
