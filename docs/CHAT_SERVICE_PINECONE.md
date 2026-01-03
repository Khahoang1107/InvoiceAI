# Chat Service với Pinecone RAG

## Tổng quan

Chat Service được thiết kế để cung cấp khả năng trò chuyện thông minh với người dùng về dữ liệu hóa đơn, sử dụng hệ thống RAG (Retrieval-Augmented Generation) với Pinecone làm vector database.

## Kiến trúc

```
User Query → Embedding → Pinecone Search → Context Filtering → Groq AI → Response
```

## Cấu hình Pinecone

### 1. Tạo tài khoản Pinecone
- Truy cập [pinecone.io](https://pinecone.io)
- Đăng ký tài khoản miễn phí
- Tạo API key và environment

### 2. Cài đặt biến môi trường

Thêm vào file `.env`:

```bash
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_ENVIRONMENT=gcp-starter  # hoặc aws, azure tùy region
```

### 3. Cấu hình Index

Chat service sẽ tự động tạo index `invoice-rag` với:
- Dimension: 384 (phù hợp với Sentence Transformers)
- Metric: cosine similarity
- Cloud: AWS us-east-1

## Cách hoạt động

### 1. Xử lý câu hỏi
Khi người dùng gửi câu hỏi:
1. **Embedding**: Chuyển câu hỏi thành vector 384 chiều
2. **Retrieval**: Tìm kiếm 3-5 tài liệu liên quan nhất trong Pinecone
3. **Filtering**: Lọc kết quả có độ tin cậy > 0.7
4. **Context**: Ghép ngữ cảnh vào prompt cho AI

### 2. Tính năng an toàn
- ✅ Chỉ trả lời dựa trên dữ liệu có sẵn
- ✅ Thừa nhận khi không tìm thấy thông tin
- ✅ Không bịa đặt hoặc ước đoán
- ✅ Luôn giải thích nguồn gốc dữ liệu

### 3. Quản lý hội thoại
- Lưu lịch sử chat trong database
- Nhớ ngữ cảnh cuộc trò chuyện
- Hỗ trợ multiple conversations per user

## API Endpoints

### POST /api/chat/
Gửi tin nhắn chat và nhận phản hồi từ AI.

**Request:**
```json
{
  "message": "Tổng tiền hóa đơn tháng này là bao nhiêu?",
  "conversation_id": "optional_conversation_id"
}
```

**Response:**
```json
{
  "response": "Dựa trên dữ liệu hóa đơn, tổng tiền tháng này là 2.500.000đ",
  "conversation_id": "conv_123",
  "success": true,
  "type": "rag_response",
  "metadata": {
    "tokens_used": 150
  }
}
```

## Testing

Chạy test script để kiểm tra chức năng:

```bash
cd backend
python test_chat_pinecone.py
```

## Migration từ FAISS/ChromaDB

Nếu bạn có dữ liệu cũ trong FAISS hoặc ChromaDB, có thể migrate sang Pinecone:

```python
from services.vector_db.vector_store import FAISSVectorStore, PineconeVectorStore
from services.vector_db.embedding_service import EmbeddingService

# Load dữ liệu cũ
old_store = FAISSVectorStore()
embedding_service = EmbeddingService()

# Migrate từng document
documents = []  # Load từ old store
embeddings = [embedding_service.encode_text(doc['content']) for doc in documents]

# Add to Pinecone
pinecone_store = PineconeVectorStore()
pinecone_store.add_documents(documents, embeddings)
```

## Troubleshooting

### Lỗi kết nối Pinecone
- Kiểm tra API key và environment variables
- Đảm bảo network connectivity
- Kiểm tra quota và billing

### Không tìm thấy tài liệu
- Kiểm tra có dữ liệu trong Pinecone index chưa
- Verify embedding model consistency
- Kiểm tra threshold filtering

### AI trả lời sai
- Review system prompt
- Kiểm tra context formatting
- Adjust retrieval parameters (top_k, threshold)

## Performance Tuning

### Retrieval Parameters
- `top_k`: Số lượng tài liệu lấy về (3-5 recommended)
- `threshold`: Ngưỡng độ tin cậy (0.7 recommended)
- `max_context_length`: Độ dài tối đa context (4000 tokens)

### Embedding Model
- Hiện tại dùng: `sentence-transformers/all-MiniLM-L6-v2`
- Dimension: 384
- Performance: Tốt cho tiếng Việt và tiếng Anh

### Pinecone Index
- Metric: cosine (recommended cho text similarity)
- Dimension: 384 (phải match với embedding model)
- Pod type: p1 (cho starter tier)