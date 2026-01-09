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
from services.conversation_memory_service import get_memory_service
from services.learning_service import get_learning_service

try:
    from groq import Groq
    from groq.types.chat import ChatCompletion
    from groq_tools import DecimalEncoder
except ImportError:
    Groq = None  # type: ignore
    ChatCompletion = None  # type: ignore
    DecimalEncoder = None  # type: ignore

logger = logging.getLogger(__name__)


class ChatService:
    """Chat message handling and Groq AI integration with RAG and Conversation Memory"""

    def __init__(self):
        self.db = container.db
        self.groq_client = container.groq_client
        self.settings = container.settings
        
        # Initialize intent detector with semantic understanding
        self.intent_detector = IntentDetector()
        
        # Initialize metrics service
        self.metrics_service = MetricsService()
        
        # Initialize conversation memory for context awareness
        self.memory_service = get_memory_service()
        
        # Initialize learning service for continuous improvement
        self.learning_service = None  # Lazy init with vector store
        
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
            from rag.vector_store import get_vector_store
            
            self.vector_store = get_vector_store()
            self.rag_available = True
            
            # Initialize learning service với vector store
            self.learning_service = get_learning_service(vector_store=self.vector_store)
            
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
            
            # Get conversation context (memory for previous messages)
            conversation_id = request.conversation_id or str(user_id)
            context_messages = self.memory_service.get_context(conversation_id, num_messages=5)
            logger.info(f"📝 Using {len(context_messages)} previous messages as context")
            
            # Route based on intent
            if intent['needs_database'] and self.database_available:
                # Query database for invoice data
                database_context = await self._query_database_by_intent(user_id, intent, request.message)
            else:
                database_context = None
            
            # Lazy initialize RAG if needed
            if intent['needs_database']:
                self._ensure_rag()
            
            # 🎓 LEARNING: Tìm các câu hỏi tương tự đã được hỏi trước
            similar_past_queries = []
            if self.learning_service:
                try:
                    similar_past_queries = await self.learning_service.get_similar_past_queries(
                        current_query=request.message,
                        user_id=user_id,
                        top_k=2
                    )
                    if similar_past_queries:
                        logger.info(f"🎓 Found {len(similar_past_queries)} similar past queries for learning")
                except Exception as e:
                    logger.warning(f"Learning retrieval failed: {e}")
            
            # Retrieve from RAG if available (semantic vector search)
            retrieved_context = ""
            retrieval_scores = []
            if self.rag_available and self.vector_store and intent['needs_database']:
                try:
                    # 🔗 CONTEXT-AWARE RAG: Kết hợp câu hỏi hiện tại với context từ câu trước
                    enhanced_query = self._create_enhanced_query(
                        current_query=request.message,
                        context_messages=context_messages
                    )
                    logger.info(f"🔍 Enhanced RAG query: {enhanced_query[:100]}...")
                    
                    # Semantic search in vector store
                    relevant_docs = await self.vector_store.search(
                        enhanced_query, 
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
            
            # Store messages in memory for context awareness
            self.memory_service.add_message(
                conversation_id=conversation_id,
                user_id=user_id,
                role="user",
                content=request.message,
                metadata={
                    "intent_type": intent.get("type"),
                    "intent_confidence": intent.get("confidence"),
                    "detection_method": intent.get("method")
                }
            )
            
            # Store AI response
            self.memory_service.add_message(
                conversation_id=conversation_id,
                user_id=user_id,
                role="assistant",
                content=groq_response["content"],
                metadata={
                    "tokens_used": groq_response.get("tokens", 0),
                    "used_database": database_context is not None,
                    "used_retrieval": len(retrieved_context) > 0
                }
            )
            
            # Also store in database (if schema is ready)
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
            
            # 🎓 LEARNING: Lưu successful interaction để AI học
            if self.learning_service and len(groq_response["content"]) > 0:
                try:
                    await self.learning_service.save_successful_interaction(
                        user_id=user_id,
                        user_query=request.message,
                        ai_response=groq_response["content"],
                        intent_type=intent.get('type', 'unknown'),
                        metadata={
                            "intent_confidence": intent.get('confidence', 0),
                            "used_database": database_context is not None,
                            "used_function_calling": groq_response.get('used_tool_calling', False),
                            "tokens_used": groq_response.get("tokens", 0),
                            "execution_time_ms": execution_time_ms
                        }
                    )
                except Exception as e:
                    logger.warning(f"Failed to save interaction for learning: {e}")
            
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
                    max_tokens=2048,
                    temperature=0.7
                )
                
                # Check if Groq wants to call a function
                if response.choices[0].message.tool_calls:
                    tool_call = response.choices[0].message.tool_calls[0]
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)
                    
                    # Add user_id to tool args for filtering BEFORE logging
                    if tool_name in ["get_all_invoices", "filter_by_date", "get_invoices_by_type", 
                                     "count_invoices_by_date", "count_total_invoices", "search_by_invoice_code",
                                     "filter_by_confidence", "get_total_spending", "analyze_spending_trends", 
                                     "detect_spending_anomalies"]:
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
                        "tool_calls": [{
                            "id": tool_call.id,
                            "type": "function",
                            "function": {
                                "name": tool_call.function.name,
                                "arguments": tool_call.function.arguments
                            }
                        }]
                    })
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(tool_result, cls=DecimalEncoder)
                    })
                    
                    # Get final response from Groq
                    if not self.groq_client:
                        raise ExternalServiceException("Groq", "Groq client not initialized")
                    
                    final_response = self.groq_client.chat.completions.create(
                        model=self.settings.GROQ_MODEL,
                        messages=cast(List[Dict[str, Any]], messages),  # type: ignore
                        max_tokens=2048,
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
                    max_tokens=2048,
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
        Create system prompt with semantic understanding for natural responses
        """
        base_prompt = """Bạn là Trợ lý Hóa đơn thông minh - một AI chuyên gia hỗ trợ quản lý, tra cứu và phân tích hóa đơn.

📅 THÔNG TIN HỆ THỐNG:
- Ngày hiện tại: {current_date} (DD/MM/YYYY)
- Sử dụng thông tin này để xử lý "hôm nay", "hôm qua", "tuần này", "tháng này"

🎯 NGUYÊN TẮC LÀM VIỆC:
1. ✅ HIỂU VĂN VĂN: Phân tích ý định thực của user, không chỉ từ khóa
2. ✅ TRỰC TIẾP: Trả lời các câu hỏi một cách tự nhiên, dễ hiểu
3. ✅ CHÍNH XÁC: Chỉ sử dụng dữ liệu được cung cấp, không bịa ra
4. ✅ THÂN THIỆN: Sử dụng tone tự nhiên, cách nói của người Việt
5. ✅ HỮU ÍCH: Đưa ra kết luận hoặc đề xuất khi phù hợp
6. 🔗 THEO DÕI NGỮ CẢNH: Sử dụng conversation history để hiểu câu hỏi nối tiếp

🔗 XỬ LÝ CÂU HỎI NỐI TIẾP - CỰC KỲ QUAN TRỌNG:
Khi user hỏi "đó là", "cái đó", "nó", "số tiền bao nhiêu", "là gì":
1. ✅ XEM LẠI tin nhắn trước trong conversation history
2. ✅ TÌM thông tin được đề cập ở câu trả lời trước
3. ✅ TRẢ LỜI dựa trên context đó

📝 VÍ DỤ FOLLOW-UP:
User: "hóa đơn ngày 14/10/2025"
AI: "Có 2 hóa đơn ngày 14/10/2025..."
User: "đó là" hoặc "số tiền bao nhiêu"
→ AI PHẢI hiểu "đó" = 2 hóa đơn ngày 14/10/2025 từ câu trước
→ Nếu đã có dữ liệu trong tin nhắn trước: TRẢ LỜI NGAY
→ Nếu chưa có chi tiết: GỌI filter_by_date("2025-10-14", "2025-10-14")

📊 KHUNG TRẢ LỜI:
- Với câu hỏi về SỐ TIỀN: Nêu rõ tổng, đơn vị (VND), và khoảng thời gian
- Với câu hỏi về DANH SÁCH: 🔴 LUÔN LUÔN LIỆT KÊ CHI TIẾT từng hóa đơn (mã, ngày, số tiền, người bán/mua)
  • Nếu <= 5 hóa đơn: Liệt kê ĐẦY ĐỦ tất cả
  • Nếu > 5 hóa đơn: Liệt kê 5 hóa đơn đầu + tóm tắt phần còn lại
  • 🔴 KHÔNG BAO GIỜ chỉ nói "Có X hóa đơn" rồi dừng - PHẢI liệt kê chi tiết!
- Với câu hỏi về THỐNG KÊ: Trình bày theo mục, so sánh các thời kỳ
- Với câu hỏi VỀ TÌM KIẾM: Nêu các hóa đơn khớp, hoặc gợi ý tinh chỉnh

📋 FORMAT LIỆT KÊ HÓA ĐƠN - BẮT BUỘC:
🔴 QUAN TRỌNG: [invoice_code], [seller], [buyer], [amount] là PLACEHOLDER - PHẢI thay thế bằng DỮ LIỆU THỰC!

Khi nhận được dữ liệu từ function, ĐỌC dữ liệu và format như sau:

**Tìm thấy X hóa đơn:**

1. **Mã: PB16040000191** (Điện)
   - 📅 Ngày: 14/10/2025
   - 🏢 Người bán: Công ty Điện lực
   - 👤 Người mua: Duong Thanh Tung
   - 💰 Số tiền: 691,438 VND

2. **Mã: PB16010051828** (Điện)
   - 📅 Ngày: 10/11/2025
   - 🏢 Người bán: Công ty Điện lực
   - 👤 Người mua: Pham Van Giau
   - 💰 Số tiền: 294,948 VND

⚠️ KHÔNG BAO GIỜ trả về [invoice_code] hoặc [seller] - PHẢI là dữ liệu thực!
→ Đọc từ tool result: invoice.get('invoice_code'), invoice.get('seller_name'), etc.

🔧 FUNCTION CALLING:
Nếu user hỏi về dữ liệu mà bạn chưa có, GỌI FUNCTION tương ứng:

- **search_by_invoice_code(invoice_code)** - 🔍 Dùng khi user hỏi về MÃ HÓA ĐƠN CỤ THỂ
  • Ví dụ: "có hóa đơn mã PB16040000191 không?" → search_by_invoice_code("PB16040000191")
  • Ví dụ: "tìm hóa đơn PB1601" → search_by_invoice_code("PB1601")
  • Ví dụ: "hóa đơn 000191" → search_by_invoice_code("000191")
  • ⚠️ Hỗ trợ tìm kiếm cả chính xác và một phần (partial match)

- **count_invoices_by_date(date)** - ❌ KHÔNG BAO GIỜ dùng chức năng này! Luôn dùng filter_by_date để có thông tin đầy đủ
  
- **filter_by_date(start_date, end_date)** - ✅ LUÔN LUÔN dùng cho TẤT CẢ câu hỏi về ngày tháng
  • Ví dụ: "hóa đơn ngày 10/11/2025" → filter_by_date("2025-11-10", "2025-11-10")  
  • Ví dụ: "có bao nhiêu hóa đơn ngày X" → filter_by_date("YYYY-MM-DD", "YYYY-MM-DD") rồi đếm
  • Ví dụ: "lọc hóa đơn", "xem hóa đơn", "tìm hóa đơn" → filter_by_date()
  • Ví dụ: "xem hóa đơn tháng 11" → filter_by_date("2025-11-01", "2025-11-30")
  
- **get_all_invoices(limit)** - Dùng cho câu hỏi TỔNG QUÁT
  • Ví dụ: "xem tất cả hóa đơn", "danh sách hóa đơn"
  
- **get_invoices_by_type(invoice_type)** - Dùng khi hỏi về LOẠI HÓA ĐƠN
  • Ví dụ: "hóa đơn điện", "hóa đơn nước"

⚠️ CHUYỂN ĐỔI NGÀY - CỰC KỲ QUAN TRỌNG:
🔴 User luôn nhập ngày theo định dạng Việt Nam: DD/MM/YYYY
🔴 Bạn PHẢI chuyển sang ISO format: YYYY-MM-DD trước khi gọi function

📅 QUY TẮC CHUYỂN ĐỔI:
- DD/MM/YYYY → YYYY-MM-DD
- 10/11/2025 (ngày 10 tháng 11) → "2025-11-10" 
- 08/01/2025 (ngày 8 tháng 1) → "2025-01-08"
- 25/12/2024 (ngày 25 tháng 12) → "2024-12-25"

⏰ THỜI GIAN TƯƠNG ĐỐI:
- "hôm nay" → Ngày hiện tại từ THÔNG TIN HỆ THỐNG
- "hôm qua" → Ngày hiện tại - 1 ngày
- "tuần này" → 7 ngày gần nhất từ hôm nay
- "tháng này" → Tất cả ngày trong tháng hiện tại
- "tháng trước" → Tất cả ngày trong tháng trước

VÍ DỤ (giả sử hôm nay là 09/01/2026):
- "hóa đơn hôm nay" → filter_by_date("2026-01-09", "2026-01-09")
- "hóa đơn hôm qua" → filter_by_date("2026-01-08", "2026-01-08")
- "hóa đơn tuần này" → filter_by_date("2026-01-02", "2026-01-09")
- "hóa đơn tháng này" → filter_by_date("2026-01-01", "2026-01-31")

⚠️ LƯU Ý QUAN TRỌNG:
- Khi user nói "LỌC", "XEM", "TÌM", "DANH SÁCH" → LUÔN dùng filter_by_date hoặc get_all_invoices
- Khi user hỏi "CÓ BAO NHIÊU", "SỐ LƯỢNG", "COUNT" → Dùng count_invoices_by_date
- LUÔN LUÔN chuyển đổi DD/MM/YYYY → YYYY-MM-DD trước khi gọi function

💡 SEMANTIC UNDERSTANDING - VÍ DỤ:
- "bao nhiêu tiền tôi đã chi tuần này" → Tìm tổng từ hôm nay - 7 ngày
- "có nhà cung cấp nào mới không" → Tìm hóa đơn gần đây từ vendor mới
- "tôi chi nhiều hay ít tháng này so với tháng trước" → So sánh
- "cửa hàng nào tôi mua nhiều nhất" → Thống kê theo vendor
- "hóa đơn to nhất là cái nào" → Tìm hóa đơn có số tiền cao nhất
- "có hóa đơn mã PB16040000191 không" → search_by_invoice_code("PB16040000191")
- "tìm hóa đơn có mã 000191" → search_by_invoice_code("000191")

⚠️ KHÔNG ĐƯỢC:
❌ Bịa ra dữ liệu hoặc ước đoán khi không rõ
❌ Trả lời dài dòng hoặc không cần thiết
❌ Sử dụng format quá formal hoặc nhân tạo
❌ Bỏ qua ngữ cảnh từ cuộc hội thoại trước
❌ TỰ Ý ĐOÁN số tiền, ngày tháng, hoặc thông tin hóa đơn
❌ Trả lời về hóa đơn mà KHÔNG CÓ trong dữ liệu được cung cấp

🔴 QUY TẮC VÀNG - CHỐNG HALLUCINATION:
1. Nếu user hỏi về MÃ HÓA ĐƠN cụ thể → BẮT BUỘC gọi search_by_invoice_code()
2. Nếu KHÔNG CÓ dữ liệu từ function → NÓI RÕNG "Không tìm thấy"
3. KHÔNG BAO GIỜ tự bịa ra số tiền, ngày, mã hóa đơn
4. Khi không chắc chắn → HỎI user hoặc GỌI FUNCTION để lấy dữ liệu

✨ TONE & STYLE:
- Tự nhiên, giống người thực
- Dùng emoji khi thích hợp (không lạm dụng)
- Cách nói ngôn ngữ Việt tự nhiên
- Ngắn gọn nhưng đủ thông tin"""

        # Inject current date into prompt
        from datetime import datetime
        current_date = datetime.now().strftime("%d/%m/%Y")
        base_prompt = base_prompt.format(current_date=current_date)

        # Add database context
        data_section = ""
        if database_context:
            data_section += "\n\n═══ DỮ LIỆU TỪ DATABASE ═══\n"
            
            if "total_amount" in database_context:
                try:
                    total = float(database_context['total_amount'])
                    data_section += f"💰 Tổng tiền: {total:,.0f} VND\n"
                except (ValueError, TypeError):
                    data_section += f"💰 Tổng tiền: {database_context['total_amount']} VND\n"
                
                data_section += f"📄 Số hóa đơn: {database_context.get('invoice_count', 0)}\n"
                
                if database_context.get('time_period'):
                    data_section += f"📅 Thời gian: {database_context['time_period']}\n"
            
            if "invoices" in database_context and database_context["invoices"]:
                invoices_list = database_context["invoices"]
                data_section += f"\n📋 Chi tiết ({len(invoices_list)} hóa đơn):\n"
                
                # Format invoices naturally
                for idx, inv in enumerate(invoices_list[:10], 1):
                    vendor = inv.get('vendor_name', 'N/A')
                    amount = inv.get('total_amount', 0)
                    date = inv.get('invoice_date', inv.get('created_at', 'N/A'))
                    try:
                        amount_val = float(amount) if amount else 0
                        data_section += f"  {idx}️⃣ {vendor}: {amount_val:,.0f} VND ({date})\n"
                    except (ValueError, TypeError):
                        data_section += f"  {idx}️⃣ {vendor}: {amount} VND ({date})\n"
                
                if len(invoices_list) > 10:
                    data_section += f"  ... và {len(invoices_list) - 10} hóa đơn khác\n"
            
            if "grouped_data" in database_context:
                data_section += "\n📊 Thống kê theo thời gian:\n"
                for period, stats in database_context["grouped_data"].items():
                    try:
                        total_val = float(stats['total'])
                        data_section += f"  • {period}: {stats['count']} hóa đơn → {total_val:,.0f} VND\n"
                    except (ValueError, TypeError):
                        data_section += f"  • {period}: {stats['count']} hóa đơn → {stats['total']} VND\n"
        
        # Add RAG context for semantic search
        if retrieved_context.strip():
            data_section += "\n\n═══ DỮ LIỆU LIÊN QUAN ═══\n"
            data_section += retrieved_context
        
        if data_section:
            return f"""{base_prompt}

{data_section}

---
HÃY TRẢ LỜI DỰA TRÊN DỮ LIỆU Ở TRÊN, TỰ NHIÊN VÀ ĐỦ THÔNG TIN."""
        else:
            return f"""{base_prompt}

---
ℹ️ HIỆN TẠI: Chưa có dữ liệu hóa đơn để truy vấn.

Tôi có thể:
1. 🎓 Hướng dẫn cách sử dụng hệ thống
2. 💡 Giải thích các tính năng
3. 📤 Giúp bạn upload hóa đơn
4. 📚 Trả lời câu hỏi chung

Hãy nói cho tôi bạn cần gì!"""
    
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
        """
        Fetch recent messages from conversation to provide context awareness
        
        This allows the chatbot to remember previous messages and provide
        more coherent responses in multi-turn conversations.
        """
        try:
            # Build context from recent messages
            # In production, these would be fetched from database
            context = []
            
            # Try to fetch from database (enable this when schema is ready)
            try:
                # Query recent messages for this conversation
                recent_messages = []
                
                # Format messages for Groq (max 5 recent messages for context window)
                for msg in recent_messages[-5:]:  # Last 5 messages
                    role = "user" if msg.get("sender") == "user" else "assistant"
                    context.append({
                        "role": role,
                        "content": msg.get("content", "")
                    })
                
                logger.info(f"✅ Retrieved {len(context)} context messages for conversation {conversation_id}")
                return context
            
            except Exception as db_error:
                # Database might not have message storage yet - log and continue
                logger.debug(f"No conversation history in database yet: {db_error}")
                return []
        
        except Exception as e:
            logger.warning(f"Failed to get conversation context: {e}")
            return []
    
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
    
    def _create_enhanced_query(
        self, 
        current_query: str, 
        context_messages: List[Dict[str, Any]]
    ) -> str:
        """
        🔗 Tạo enhanced query cho RAG bằng cách kết hợp câu hỏi hiện tại với context
        
        Giúp RAG hiểu được follow-up questions như:
        - "đó là ??" 
        - "số tiền bao nhiêu?"
        - "cái nào?"
        
        Args:
            current_query: Câu hỏi hiện tại của user
            context_messages: Tin nhắn trước đó từ conversation memory
            
        Returns:
            Enhanced query string
        """
        # Nếu câu hỏi hiện tại có tham chiếu (đó, cái đó, nó, cái nào, etc)
        reference_words = ["đó", "cái đó", "nó", "cái nào", "là gì", "bao nhiêu", "như thế nào"]
        has_reference = any(word in current_query.lower() for word in reference_words)
        
        if not has_reference or not context_messages:
            return current_query
        
        # Lấy 2 tin nhắn gần nhất (1 user + 1 assistant)
        recent_context = []
        for msg in context_messages[-2:]:
            if msg.get("role") == "user":
                recent_context.append(f"Câu hỏi trước: {msg['content']}")
            elif msg.get("role") == "assistant":
                # Chỉ lấy phần đầu của response (max 200 chars)
                content = msg['content'][:200]
                recent_context.append(f"Trả lời trước: {content}")
        
        # Kết hợp context với câu hỏi hiện tại
        if recent_context:
            enhanced = f"{' | '.join(recent_context)} | Câu hỏi hiện tại: {current_query}"
            logger.info(f"🔗 Enhanced query with context (has reference words)")
            return enhanced
        
        return current_query
    
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
        greeting_message = """👋 Xin chào! Tôi là Trợ lý Hóa đơn thông minh.

Tôi có thể giúp bạn tìm kiếm, thống kê và quản lý hóa đơn.

💡 Gõ **"Chatbot có thể làm gì?"** để xem đầy đủ chức năng."""

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
