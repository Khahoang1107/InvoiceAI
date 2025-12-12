# Pydantic Request/Response Models

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr
    name: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100)
    
    @validator('password')
    def password_strength(cls, v):
        # Password must contain uppercase letter and digit
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter (A-Z)')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit (0-9)')
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class UserResponse(UserBase):
    id: int
    created_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True
        
    @validator('is_active', pre=True)
    def convert_is_active(cls, v):
        return bool(v)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int


class MessageBase(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)


class MessageCreate(MessageBase):
    pass


class MessageResponse(MessageBase):
    id: int
    sender: str
    user_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    tokens_used: int


class FileUploadResponse(BaseModel):
    file_id: str
    filename: str
    file_size: int
    upload_at: datetime


class OCRResult(BaseModel):
    file_id: str
    extracted_text: str
    confidence: float
    processing_time: float


class InvoiceBase(BaseModel):
    invoice_number: str
    amount: float = Field(..., gt=0)
    date: datetime
    vendor: Optional[str] = None


class InvoiceCreate(InvoiceBase):
    pass


class InvoiceResponse(BaseModel):
    confidence: float
    invoice_type: str
    invoice_code: str
    date: str
    seller_name: str
    buyer_name: str
    seller_address: Optional[str] = None
    buyer_address: Optional[str] = None
    seller_tax_id: Optional[str] = None
    buyer_tax_id: Optional[str] = None
    subtotal: float = 0
    tax_amount: float = 0
    tax_percentage: float = 0
    currency: str = "VND"
    total_amount: Optional[str] = None
    total_amount_value: float = 0
    transaction_id: Optional[str] = None
    payment_method: Optional[str] = None
    ocr_text: Optional[str] = None
    
    class Config:
        from_attributes = True


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[dict] = None
    request_id: Optional[str] = None
