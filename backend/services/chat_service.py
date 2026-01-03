# Service Layer: Chat Management

import logging
import json
import time
from typing import List, Optional, Dict, Any, Union, cast
from datetime import datetime
from core.exceptions import (
    AuthenticationException,
    ExternalServiceException,
    DatabaseException,
    ValidationException
)
from core.dependencies import container
from schemas.models import ChatRequest, ChatResponse
from services.intent_detector import IntentDetector
from services.invoice_query_service import InvoiceQueryService
from services.metrics_service import MetricsService

try:
    from groq import Groq
    from groq.types.chat import ChatCompletion
except ImportError:
    Groq = None  # type: ignore
    ChatCompletion = None  # type: ignore

logger = logging.getLogger(__name__)


class ChatService:
    """Chat message handling and Groq AI integration with RAG"""

    def __init__(self):
        self.db = container.db
        self.groq_client = container.groq_client
        self.settings = container.settings
        
        # Initialize intent detector
        self.intent_detector = IntentDetector()
        
        # Initialize metrics service
        self.metrics_service = MetricsService()
        
        # Lazy initialization flags
        self.database_available = False
        self.invoice_query_service = None
        self.rag_available = False
        self.vector_store = None
        self.groq_tools = None  # Groq function calling tools

    def _ensure_database(self):
        """Lazy initialize database connection"""
        if self.database_available or self.invoice_query_service:
            return
            
        try:
            from utils.database_tools_postgres import DatabaseToolsPostgres
            db_tools = DatabaseToolsPostgres()
            self.invoice_query_service = InvoiceQueryService(db_tools)
            self.database_available = True
            
            # Initialize Groq Tools for function calling
            from groq_tools import GroqDatabaseTools
            self.groq_tools = GroqDatabaseTools(db_tools)
            
            logger.info("✅ Database query service initialized")
        except Exception as e:
            logger.warning(f"Database query service not available: {e}")
            self.database_available = False

    def _ensure_rag(self):
        """Lazy initialize RAG components"""
        if self.rag_available or self.vector_store:
            return
            
        try:
            from services.vector_store import get_vector_store
            
            self.vector_store = get_vector_store()
            self.rag_available = True
            logger.info("✅ Vector store initialized for RAG")
        except Exception as e:
            logger.warning(f"RAG components not available: {e}")
            self.rag_available = False
            self.vector_store = None
    
    async def send_message(self, user_id: int, request: ChatRequest) -> ChatResponse:
        """
        Send user message and get AI response from Groq
        
        Args:
            user_id: ID of user sending message
            request: ChatRequest with message content
            
        Returns:
            ChatResponse with AI response
            
        Raises:
            ValidationException: If message is empty or too long
            ExternalServiceException: If Groq API fails
            DatabaseException: If database operation fails
        """
        start_time = time.time()
        
        try:
            # Validate message
            if not request.message or len(request.message.strip()) == 0:
                raise ValidationException("Message cannot be empty")
            
            if len(request.message) > 2000:
                raise ValidationException("Message too long (max 2000 characters)")
            
            # Detect intent
            intent = self.intent_detector.detect_intent(request.message)
            logger.info(f"Detected intent: {intent['type']}/{intent.get('subtype', 'unknown')} (confidence: {intent.get('confidence', 0)})")
            
            # Handle basic chat intents with predefined responses
            if intent['type'] == 'basic_chat':
                if intent['subtype'] == 'greeting':
                    return self._create_greeting_response(request.conversation_id or str(user_id))
                elif intent['subtype'] == 'help':
                    return self._create_help_response(request.conversation_id or str(user_id))
            
            # Lazy initialize database if needed
            if intent['needs_database']:
                self._ensure_database()
            
            # Get conversation context
            conversation_id = request.conversation_id or str(user_id)
            context_messages = self._get_conversation_context(user_id, conversation_id)
            
            # Route based on intent
            if intent['needs_database'] and self.database_available:
                # Query database for invoice data
                database_context = await self._query_database_by_intent(user_id, intent, request.message)
            else:
                database_context = None
            
            # Lazy initialize RAG if needed
            if intent['needs_database']:
                self._ensure_rag()
            
            # Retrieve from RAG if available (semantic vector search)
            retrieved_context = ""
            retrieval_scores = []
            if self.rag_available and self.vector_store and intent['needs_database']:
                try:
                    # Semantic search in vector store
                    relevant_docs = await self.vector_store.search(
                        request.message, 
                        top_k=3
                    )
                    if relevant_docs:
                        # Collect scores for metrics
                        retrieval_scores = [doc.get('score', 0) for doc in relevant_docs]
                        retrieved_context = self._format_retrieved_context(relevant_docs)
                        logger.info(f"✅ Retrieved {len(relevant_docs)} relevant documents from vector store")
                        
                        # Log retrieval metrics
                        self.metrics_service.log_retrieval_metrics(
                            user_id=user_id,
                            query=request.message,
                            retrieved_count=len(relevant_docs),
                            top_k=3,
                            scores=retrieval_scores
                        )
                except Exception as e:
                    logger.warning(f"Vector search failed: {e}")
            
            # Call Groq API with context
            groq_response = await self._call_groq_with_context(
                request.message, 
                context_messages, 
                database_context,
                retrieved_context,
                user_id  # Pass user_id for function calling
            )
            
            # Store messages in database
            self._store_messages(
                user_id=user_id,
                user_message=request.message,
                ai_response=groq_response["content"],
                conversation_id=conversation_id
            )
            
            # Log response quality metrics
            execution_time_ms = (time.time() - start_time) * 1000
            self.metrics_service.log_response_quality_metrics(
                user_id=user_id,
                conversation_id=conversation_id,
                intent_type=intent.get('type', 'unknown'),
                intent_confidence=intent.get('confidence', 0),
                used_database=database_context is not None,
                used_retrieval=len(retrieved_context) > 0,
                used_function_calling=groq_response.get('used_tool_calling', False),
                response_length=len(groq_response["content"]),
                tokens_used=groq_response.get("tokens", 0),
                execution_time=execution_time_ms
            )
            
            return ChatResponse(
                response=groq_response["content"],
                conversation_id=conversation_id,
                tokens_used=groq_response.get("tokens", 0)
            )
            
        except (ValidationException, ExternalServiceException):
            raise
        except Exception as e:
            raise DatabaseException(f"Chat processing failed: {str(e)}")
    
    async def _call_groq_with_context(
        self, 
        message: str, 
        context: List[dict], 
        database_context: Optional[Dict[str, Any]],
        retrieved_context: str,
        user_id: int
    ) -> dict:
        """
        Call Groq API with message, chat context, database results, and RAG context
        
        Args:
            message: User message
            context: Previous messages for context
            database_context: Query results from database
            retrieved_context: Retrieved documents from vector store
            user_id: Current user ID for filtering
            
        Returns:
            Dict with content and tokens
        """
        try:
            # Create system prompt with all context
            system_prompt = self._create_system_prompt_with_data(
                database_context, 
                retrieved_context
            )
            
            # Prepare messages for Groq
            messages = [
                {"role": "system", "content": system_prompt}
            ] + context + [
                {"role": "user", "content": message}
            ]
            
            # ENABLE GROQ FUNCTION CALLING if tools available
            if self.groq_tools and self.groq_client:
                tools = self.groq_tools.get_tools_description()
                response = self.groq_client.chat.completions.create(
                    model=self.settings.GROQ_MODEL,
                    messages=cast(List[Dict[str, Any]], messages),  # type: ignore
                    tools=cast(List[Dict[str, Any]], tools),  # type: ignore
                    tool_choice="auto",  # Let Groq decide when to call
                    max_tokens=1024,
                    temperature=0.7
                )
                
                # Check if Groq wants to call a function
                if response.choices[0].message.tool_calls:
                    tool_call = response.choices[0].message.tool_calls[0]
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)
                    
                    # Add user_id to tool args for filtering BEFORE logging
                    if tool_name in ["get_all_invoices", "filter_by_date", "get_invoices_by_type", 
                                     "count_invoices_by_date", "count_total_invoices"]:
                        tool_args["user_id"] = user_id
                    
                    logger.info(f"🔧 Groq calling tool: {tool_name} with args: {tool_args}")
                    
                    # Execute the tool and measure time
                    tool_start_time = time.time()
                    try:
                        tool_result = self.groq_tools.call_tool(tool_name, **tool_args)
                        tool_execution_time = (time.time() - tool_start_time) * 1000
                        
                        # Log successful function calling
                        result_count = None
                        if isinstance(tool_result, dict):
                            if 'invoices' in tool_result:
                                result_count = len(tool_result['invoices'])
                            elif 'count' in tool_result:
                                result_count = tool_result['count']
                        
                        self.metrics_service.log_function_calling_metrics(
                            user_id=user_id,
                            tool_name=tool_name,
                            tool_args=tool_args,
                            success=True,
                            execution_time=tool_execution_time,
                            result_count=result_count
                        )
                    except Exception as e:
                        tool_execution_time = (time.time() - tool_start_time) * 1000
                        
                        # Log failed function calling
                        self.metrics_service.log_function_calling_metrics(
                            user_id=user_id,
                            tool_name=tool_name,
                            tool_args=tool_args,
                            success=False,
                            execution_time=tool_execution_time,
                            error=str(e)
                        )
                        raise
                    
                    # Send tool result back to Groq
                    messages.append({
                        "role": "assistant",
                        "content": "",
                        "tool_calls": [tool_call]  # type: ignore
                    })
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(tool_result)
                    })  # type: ignore
                    
                    # Get final response from Groq
                    if not self.groq_client:
                        raise ExternalServiceException("Groq", "Groq client not initialized")
                    
                    final_response = self.groq_client.chat.completions.create(
                        model=self.settings.GROQ_MODEL,
                        messages=cast(List[Dict[str, Any]], messages),  # type: ignore
                        max_tokens=1024,
                        temperature=0.7
                    )
                    
                    return {
                        "content": final_response.choices[0].message.content or "",
                        "tokens": final_response.usage.total_tokens if final_response.usage else 0,
                        "used_tool_calling": True
                    }
            else:
                # Call Groq API without tools
                if not self.groq_client:
                    raise ExternalServiceException("Groq", "Groq client not initialized")
                
                response = self.groq_client.chat.completions.create(
                    model=self.settings.GROQ_MODEL,
                    messages=cast(List[Dict[str, Any]], messages),  # type: ignore
                    max_tokens=1024,
                    temperature=0.7
                )
            
            return {
                "content": response.choices[0].message.content or "",
                "tokens": response.usage.total_tokens if response.usage else 0,
                "used_tool_calling": False
            }
            
        except Exception as e:
            raise ExternalServiceException("Groq", f"API call failed: {str(e)}")
    
    def _create_system_prompt_with_data(
        self, 
        database_context: Optional[Dict[str, Any]], 
        retrieved_context: str
    ) -> str:
        """
        Create system prompt with database results and RAG context
        
        Args:
            database_context: Query results from database
            retrieved_context: Retrieved documents from vector store
            
        Returns:
            System prompt string
        """
        base_prompt = """Bạn là Trợ lý Hóa đơn tận tâm và chính xác.
        
QUY TẮC VÀNG:
1. Sử dụng TOOLS/FUNCTIONS để lấy dữ liệu thời gian thực từ database khi cần.
2. CHỈ trả lời dựa trên dữ liệu được cung cấp hoặc lấy từ tools.
3. NẾU cần dữ liệu mà chưa có, GỌI FUNCTION tương ứng (filter_by_date, get_all_invoices, etc.)
4. KHÔNG được bịa ra, ước đoán, hoặc thêm thắt thông tin.
5. Trả lời CHI TIẾT, DỄ HIỂU, và HỮU ÍCH.

CÁC FUNCTION KHẢ DỤNG:
- filter_by_date: Lọc hóa đơn theo ngày (hôm nay, tuần này, tháng này)
- get_all_invoices: Lấy tất cả hóa đơn
- get_invoices_by_type: Lọc theo loại hóa đơn
- get_statistics: Thống kê tổng hợp

VÍ DỤ SỬ DỤNG:
- "hôm nay có mấy hóa đơn" → Gọi filter_by_date(start_date="2025-12-28", end_date="2025-12-28")
- "tháng này chi bao nhiêu" → Gọi filter_by_date với start_date = đầu tháng
- "có bao nhiêu hóa đơn" → Gọi get_all_invoices()

HƯỚNG DẪN TRẢ LỜI:
- Với câu hỏi về số tiền: Trích dẫn chính xác từ dữ liệu
- Với câu hỏi về ngày tháng: Đưa ra định dạng dễ đọc
- Với câu hỏi về sản phẩm/dịch vụ: Liệt kê rõ ràng
- Với câu hỏi tổng hợp: Tóm tắt có cấu trúc"""

        # Add database query results
        data_section = ""
        if database_context:
            data_section += "\n\n--- DỮ LIỆU TỪ DATABASE ---\n"
            
            if "total_amount" in database_context:
                try:
                    total = float(database_context['total_amount'])
                    data_section += f"Tổng tiền: {total:,.0f} VND\n"
                except (ValueError, TypeError):
                    data_section += f"Tổng tiền: {database_context['total_amount']} VND\n"
                data_section += f"Số hóa đơn: {database_context.get('invoice_count', 0)}\n"
                if database_context.get('time_period'):
                    data_section += f"Thời gian: {database_context['time_period']}\n"
            
            if "invoices" in database_context and database_context["invoices"]:
                data_section += f"\nDanh sách {len(database_context['invoices'])} hóa đơn:\n"
                for idx, inv in enumerate(database_context["invoices"][:10], 1):
                    vendor = inv.get('vendor_name', 'N/A')
                    amount = inv.get('total_amount', 0)
                    date = inv.get('invoice_date', inv.get('created_at', 'N/A'))
                    try:
                        amount_val = float(amount) if amount else 0
                        data_section += f"{idx}. {vendor}: {amount_val:,.0f} VND (Ngày: {date})\n"
                    except (ValueError, TypeError):
                        data_section += f"{idx}. {vendor}: {amount} VND (Ngày: {date})\n"
            
            if "grouped_data" in database_context:
                data_section += "\nThống kê theo thời gian:\n"
                for period, stats in database_context["grouped_data"].items():
                    try:
                        total_val = float(stats['total'])
                        data_section += f"- {period}: {stats['count']} hóa đơn, Tổng: {total_val:,.0f} VND\n"
                    except (ValueError, TypeError):
                        data_section += f"- {period}: {stats['count']} hóa đơn, Tổng: {stats['total']} VND\n"
        
        # Add RAG context if available
        if retrieved_context.strip():
            data_section += "\n\n--- DỮ LIỆU TỪ VECTOR STORE ---\n"
            data_section += retrieved_context
        
        if data_section:
            return f"{base_prompt}\n{data_section}\n\nHãy trả lời dựa trên dữ liệu ở trên."
        else:
            return f"""{base_prompt}

DỮ LIỆU: Không tìm thấy dữ liệu liên quan trong kho lưu trữ.

Vui lòng upload hóa đơn để tôi có thể hỗ trợ bạn tốt hơn."""
    
    def _format_retrieved_context(self, documents: List[Dict[str, Any]]) -> str:
        """
        Format retrieved documents into readable context
        
        Args:
            documents: List of retrieved documents from vector store
            
        Returns:
            Formatted context string
        """
        if not documents:
            return ""
        
        context_parts = []
        for i, doc in enumerate(documents, 1):
            # New vector store format
            invoice_id = doc.get('invoice_id', 'N/A')
            invoice_num = doc.get('invoice_number', 'N/A')
            client = doc.get('client_name', 'N/A')
            vendor = doc.get('vendor_name', 'N/A')
            amount = doc.get('amount', 0)
            date = doc.get('date', 'N/A')
            status = doc.get('status', 'N/A')
            score = doc.get('score', 0)
            
            # Format invoice info
            doc_info = f"""
--- HÓA ĐƠN #{i} (Độ liên quan: {score:.2f}) ---
Số hóa đơn: {invoice_num}
Khách hàng: {client}
Nhà cung cấp: {vendor}
Số tiền: {amount:,.0f} VND
Ngày: {date}
Trạng thái: {status}
ID: {invoice_id}
"""
            context_parts.append(doc_info)
        
        return "\n".join(context_parts)
    
    def _get_conversation_context(self, user_id: int, conversation_id: str) -> List[dict]:
        """Fetch recent messages from conversation"""
        try:
            # Query messages from database
            # messages = self.db.query(Message).filter(
            #     Message.user_id == user_id,
            #     Message.conversation_id == conversation_id
            # ).order_by(Message.created_at.desc()).limit(5).all()
            
            # Placeholder
            return []
        except Exception as e:
            raise DatabaseException(f"Failed to get conversation context: {str(e)}")
    
    def _store_messages(self, user_id: int, user_message: str, ai_response: str, conversation_id: str):
        """Store user and AI messages in database"""
        try:
            # message1 = Message(
            #     user_id=user_id,
            #     sender="user",
            #     content=user_message,
            #     conversation_id=conversation_id,
            #     created_at=datetime.utcnow()
            # )
            # message2 = Message(
            #     user_id=user_id,
            #     sender="ai",
            #     content=ai_response,
            #     conversation_id=conversation_id,
            #     created_at=datetime.utcnow()
            # )
            # self.db.add(message1)
            # self.db.add(message2)
            # self.db.commit()
            pass
        except Exception as e:
            self.db.rollback()
            raise DatabaseException(f"Failed to store messages: {str(e)}")
    
    async def get_conversation_history(self, user_id: int, conversation_id: str, limit: int = 50):
        """Retrieve conversation history"""
        try:
            # messages = self.db.query(Message).filter(
            #     Message.user_id == user_id,
            #     Message.conversation_id == conversation_id
            # ).order_by(Message.created_at.asc()).limit(limit).all()
            
            # return [MessageResponse.from_orm(m) for m in messages]
            return []
        except Exception as e:
            raise DatabaseException(f"Failed to retrieve conversation: {str(e)}")
    
    async def _query_database_by_intent(
        self, 
        user_id: int, 
        intent: Dict[str, Any], 
        message: str
    ) -> Optional[Dict[str, Any]]:
        """
        Query database based on detected intent
        
        Args:
            user_id: User ID
            intent: Detected intent dict
            message: Original user message
            
        Returns:
            Dict with query results or None
        """
        if not self.invoice_query_service:
            return None
        
        try:
            subtype = intent.get('subtype')
            entities = intent.get('entities', {})
            time_period = entities.get('time_periods', [None])[0] if entities.get('time_periods') else None
            
            logger.info(f"Querying database for intent: {subtype}, time_period: {time_period}")
            
            if subtype == "statistics":
                # Get statistics
                stats = self.invoice_query_service.get_statistics(
                    user_id=user_id,
                    time_period=time_period,
                    group_by="month"
                )
                return stats
                
            elif subtype == "amount_query":
                # Get total amount
                result = self.invoice_query_service.get_total_amount(
                    user_id=user_id,
                    time_period=time_period
                )
                return result
                
            elif subtype == "invoice_search":
                # Search invoices
                invoices = self.invoice_query_service.search_invoices_by_criteria(
                    user_id=user_id,
                    time_period=time_period,
                    limit=10
                )
                return {
                    "invoices": invoices,
                    "invoice_count": len(invoices)
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Database query failed: {e}")
            return None
    
    def _create_greeting_response(self, conversation_id: str) -> ChatResponse:
        """
        Create a friendly greeting response
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            ChatResponse with greeting message
        """
        greeting_message = """👋 **Xin chào! Tôi là Trợ lý Hóa đơn thông minh của bạn.**

Tôi có thể giúp bạn:

🔍 **Tìm kiếm & Tra cứu:**
• "Tìm hóa đơn công ty ABC"
• "Hóa đơn tháng này"
• "Có bao nhiêu hóa đơn trong database?"

📊 **Thống kê & Phân tích:**
• "Thống kê chi tiêu tháng này"
• "Tổng chi phí quý 4"
• "So sánh doanh thu các tháng"

💰 **Tính toán:**
• "Tổng tiền hóa đơn hôm nay"
• "Chi bao nhiêu tuần này?"

📤 **Xuất báo cáo:**
• "Xuất hóa đơn ra Excel"
• "Tạo báo cáo PDF"

💡 **Gợi ý:** Hãy thử hỏi tôi bất cứ điều gì về hóa đơn của bạn!"""

        return ChatResponse(
            response=greeting_message,
            conversation_id=conversation_id,
            tokens_used=0
        )
    
    def _create_help_response(self, conversation_id: str) -> ChatResponse:
        """
        Create a helpful guide response showing what the bot can do
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            ChatResponse with help information
        """
        help_message = """❓ **Hướng dẫn sử dụng Trợ lý Hóa đơn**

### 📋 **Các câu hỏi bạn có thể hỏi:**

#### 1️⃣ **Tìm kiếm hóa đơn**
```
• "Tìm hóa đơn công ty XYZ"
• "Hóa đơn mua laptop tháng trước"
• "Có bao nhiêu hóa đơn trong hệ thống?"
• "Xem hóa đơn hôm nay"
```

#### 2️⃣ **Thống kê & Báo cáo**
```
• "Thống kê chi tiêu tháng 12"
• "Tổng doanh thu quý 4"
• "Phân tích chi phí theo loại"
• "So sánh tháng này với tháng trước"
```

#### 3️⃣ **Tính toán số tiền**
```
• "Tổng tiền hóa đơn tuần này"
• "Chi bao nhiêu hôm nay?"
• "Trung bình chi phí mỗi tháng"
```

#### 4️⃣ **Xuất dữ liệu**
```
• "Xuất hóa đơn ra Excel"
• "Tạo báo cáo PDF tháng này"
• "Tải xuống CSV"
```

### 🎯 **Lựa chọn nhanh:**

👉 [Xem tất cả hóa đơn] - Hỏi: "Có bao nhiêu hóa đơn?"
👉 [Thống kê tháng này] - Hỏi: "Thống kê tháng này"
👉 [Tìm hóa đơn] - Hỏi: "Tìm hóa đơn [tên công ty]"
👉 [Xuất Excel] - Hỏi: "Xuất ra Excel"

💡 **Mẹo:** Bạn có thể hỏi bằng ngôn ngữ tự nhiên, tôi sẽ hiểu!"""

        return ChatResponse(
            response=help_message,
            conversation_id=conversation_id,
            tokens_used=0
        )
