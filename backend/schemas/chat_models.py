# Chat History Models

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ChatMessageCreate(BaseModel):
    """Schema for creating a chat message"""
    message: str = Field(..., min_length=1, max_length=5000)
    conversation_id: Optional[str] = None


class ChatMessageResponse(BaseModel):
    """Schema for chat message response"""
    id: int
    user_id: int
    conversation_id: str
    role: str  # 'user' or 'assistant'
    message: str
    tokens_used: int
    model: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class ChatHistoryResponse(BaseModel):
    """Schema for chat history list"""
    conversation_id: str
    messages: List[ChatMessageResponse]
    total_messages: int
    total_tokens: int
    created_at: datetime
    last_updated: datetime


class ConversationListResponse(BaseModel):
    """Schema for conversation list"""
    conversation_id: str
    last_message: str
    message_count: int
    created_at: datetime
    last_updated: datetime


class ChatRequest(BaseModel):
    """Schema for chat request"""
    message: str = Field(..., min_length=1, max_length=5000)
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Schema for chat response"""
    response: str
    conversation_id: str
    tokens_used: int
    model: str
