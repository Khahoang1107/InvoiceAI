# RAG System Guide for InvoiceAI

## Tổng quan

Hệ thống RAG (Retrieval-Augmented Generation) được tích hợp vào InvoiceAI để nâng cao khả năng hiểu và trả lời câu hỏi về hóa đơn. RAG kết hợp giữa tìm kiếm ngữ nghĩa (semantic search) và tạo văn bản (generation) để cung cấp câu trả lời chính xác và có ngữ cảnh.

## Kiến trúc RAG

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Query    │───►│  Embedding     │───►│  Vector Search  │
│                 │    │  Generation    │    │  (ChromaDB)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
┌─────────────────┐    ┌─────────────────┐             │
│   Context       │◄───│  Document      │◄────────────┘
│   Preparation   │    │  Retrieval     │
└─────────────────┘    └─────────────────┘
         │
         ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Enhanced      │───►│   Groq AI      │───►│   Smart         │
│   Prompt        │    │   Generation   │    │   Response      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Cài đặt và Setup

### 1. Cài đặt Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Khởi tạo RAG System

```bash
python setup_rag.py
```

Script này sẽ:
- Kết nối đến database hiện tại
- Trích xuất dữ liệu hóa đơn
- Tạo embeddings cho từng hóa đơn
- Lưu trữ vào vector database (ChromaDB)

### 3. Test RAG System

```bash
python test_rag_system.py
```

## Cách sử dụng

### Khởi tạo trong Code

```python
from services.vector_db import VectorService

# Khởi tạo Vector Service
vector_service = VectorService(
    vector_store_type="chroma",  # hoặc "faiss"
    embedding_service_type="sentence-transformers",
    persist_directory="./data/vector_db"
)

# Khởi tạo Groq Tools với RAG
from groq_tools import GroqTools
groq_tools = GroqTools(db_tools, vector_service)
```

### Tích hợp vào Chatbot

```python
# Trong chat handler
user_query = "Hóa đơn nào chưa thanh toán?"

# Lấy context từ RAG
context = vector_service.get_invoice_context(user_query)

# Tạo prompt enhanced
enhanced_prompt = f"""
Dựa trên thông tin hóa đơn sau:

{context}

Hãy trả lời câu hỏi: {user_query}
"""

# Gửi đến Groq AI
response = groq_client.chat.completions.create(
    model="mixtral-8x7b-32768",
    messages=[{"role": "user", "content": enhanced_prompt}]
)
```

## Các Tính năng RAG

### 1. Semantic Search
Tìm kiếm hóa đơn dựa trên ý nghĩa, không chỉ từ khóa chính xác.

```python
results = vector_service.search_invoices("hóa đơn nợ tiền", top_k=5)
```

### 2. Context Preparation
Chuẩn bị ngữ cảnh liên quan cho AI generation.

```python
context = vector_service.get_invoice_context("tình trạng thanh toán")
# Context sẽ chứa thông tin về các hóa đơn liên quan
```

### 3. Invoice Insights
Phân tích thông minh dữ liệu hóa đơn.

```python
insights = rag_tools.get_invoice_insights("tổng quan tài chính")
```

### 4. Hybrid Search
Kết hợp semantic search và keyword search.

```python
results = retrieval_service.hybrid_search("ABC company invoice", top_k=3)
```

## API Endpoints (Tùy chọn)

Nếu muốn expose RAG qua API:

```python
@app.post("/api/rag/search")
async def search_invoices(query: str, top_k: int = 5):
    results = vector_service.search_invoices(query, top_k=top_k)
    return {"results": results}

@app.post("/api/rag/context")
async def get_context(query: str):
    context = vector_service.get_invoice_context(query)
    return {"context": context}
```

## Cấu hình

### Vector Stores

#### ChromaDB (Khuyến nghị)
```python
vector_service = VectorService(
    vector_store_type="chroma",
    persist_directory="./data/vector_db",
    collection_name="invoice_documents"
)
```

#### FAISS (In-memory)
```python
vector_service = VectorService(
    vector_store_type="faiss"
)
```

### Embedding Models

#### Sentence Transformers (Local)
```python
embedding_service = EmbeddingService(
    model_name="all-MiniLM-L6-v2"  # Fast, good quality
    # model_name="paraphrase-multilingual-MiniLM-L12-v2"  # Multilingual
)
```

#### OpenAI Embeddings (API)
```python
embedding_service = OpenAIEmbeddingService(
    api_key="your-openai-key",
    model="text-embedding-ada-002"
)
```

## Performance Tuning

### Batch Processing
```python
# Process invoices in batches
batch_size = 100
for i in range(0, len(all_invoices), batch_size):
    batch = all_invoices[i:i + batch_size]
    vector_service.add_invoice_documents(batch)
```

### Memory Optimization
```python
# Use FAISS for large datasets
vector_service = VectorService(vector_store_type="faiss")

# Or configure ChromaDB for persistence
vector_service = VectorService(
    persist_directory="./data/large_vector_db"
)
```

### Search Optimization
```python
# Adjust search parameters
results = vector_service.search_invoices(
    query="overdue invoices",
    top_k=10,  # More results
    threshold=0.7  # Higher similarity threshold
)
```

## Monitoring và Maintenance

### Statistics
```python
stats = vector_service.get_statistics()
print(f"Total documents: {stats['total_documents']}")
```

### Backup/Restore
```python
# Export data
vector_service.export_documents("backup.json")

# Import data
vector_service.import_documents("backup.json")
```

### Update Documents
```python
# Update existing invoice
vector_service.update_invoice_document(invoice_id, updated_data)

# Delete documents
vector_service.delete_invoice_documents([invoice_id])
```

## Troubleshooting

### Common Issues

1. **Model Download Issues**
   ```bash
   # Pre-download model
   python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
   ```

2. **Memory Issues**
   ```python
   # Use smaller model
   embedding_service = EmbeddingService(model_name="all-MiniLM-L6-v2")
   ```

3. **Slow Search**
   ```python
   # Reduce top_k
   results = vector_service.search_invoices(query, top_k=3)
   ```

### Debug Mode
```python
# Enable detailed logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Test individual components
embeddings = embedding_service.encode_text("test query")
print(f"Embedding dimension: {len(embeddings)}")
```

## Examples

### Basic Search
```python
query = "hóa đơn của khách hàng Nguyễn Văn A"
results = vector_service.search_invoices(query)

for result in results:
    print(f"Invoice: {result['metadata']['invoice_number']}")
    print(f"Amount: {result['metadata']['total_amount']}")
```

### Enhanced Chat Response
```python
def get_rag_enhanced_response(user_query):
    # Get relevant context
    context = vector_service.get_invoice_context(user_query)

    # Create enhanced prompt
    prompt = f"""
    Based on the following invoice information:

    {context}

    Please answer the user's question: {user_query}

    Provide a helpful, accurate response using the invoice data above.
    """

    # Get AI response
    response = groq_client.generate_response(prompt)
    return response
```

## Tích hợp RAG vào File Upload

### Workflow Tự động

Khi người dùng upload file hóa đơn, hệ thống sẽ tự động thực hiện RAG processing:

```
Upload File → OCR → RAG Processing → Vector Storage
     ↓            ↓          ↓            ↓
  File nhận    Text trích    Embedding    Semantic
 được từ       xuất từ       tạo ra từ    search
 người dùng    hình ảnh      text được    enabled
                                 trích xuất
```

### Implementation trong Code

#### 1. InvoiceService.process_invoice_file()

```python
# Trong invoice_service.py
def process_invoice_file(self, file_path: str, filename: str, user_id: Optional[str] = None):
    # 1. OCR - Trích xuất text
    ocr_result = self.ocr_service.process_file(file_path)
    
    # 2. Tạo comprehensive content
    comprehensive_content = self._create_comprehensive_content(filename, extracted_text, user_id)
    
    # 3. Generate embeddings
    invoice_data = self._prepare_invoice_for_rag(filename, extracted_text, comprehensive_content, user_id)
    document_ids = self.vector_service.add_invoice_documents([invoice_data])
    
    # 4. Return results
    return {
        "success": True,
        "document_id": document_ids[0],
        "rag_indexed": True
    }
```

#### 2. Upload Endpoint với RAG

```python
# Trong routers/upload.py
@router.post("/")
async def upload_file(file: UploadFile = File(...), current_user = Depends(get_current_user)):
    # Upload và OCR processing
    invoice_data = await upload_service.upload_and_process_ocr(user_id, temp_file, file.filename)
    
    # RAG Processing
    try:
        vector_service = VectorService(...)
        ocr_service = OCRService()
        invoice_service = InvoiceService(vector_service=vector_service, ocr_service=ocr_service)
        
        rag_result = invoice_service.process_invoice_file(str(temp_file), file.filename, str(user_id))
        
        if rag_result.get("success"):
            invoice_data["rag_indexed"] = True
            invoice_data["document_id"] = rag_result.get("document_id")
    except Exception as rag_error:
        invoice_data["rag_indexed"] = False
        invoice_data["rag_error"] = str(rag_error)
    
    return {"invoice": invoice_data}
```

### Response Format

Upload response bây giờ bao gồm thông tin RAG:

```json
{
  "invoice": {
    "id": "inv_123",
    "filename": "hoa_don_abc.pdf",
    "ocr_text": "...extracted text...",
    "rag_indexed": true,
    "document_id": "file_hoa_don_abc.pdf_20241227_143052",
    "processing_steps": [
      "OCR text extraction",
      "Content synthesis", 
      "Embedding generation",
      "Vector database storage"
    ]
  }
}
```

### Testing RAG Integration

Chạy demo script để test:

```bash
python test_rag_integration.py
```

Script này sẽ:
- Tạo file demo hóa đơn
- Process với RAG pipeline
- Test semantic search
- Generate context cho LLM

### Benefits

1. **Tự động**: RAG processing chạy tự động khi upload file
2. **Real-time**: File được index ngay lập tức
3. **Scalable**: Hỗ trợ nhiều file và users
4. **Fallback**: Nếu RAG fail, OCR vẫn hoạt động bình thường
5. **Logging**: Chi tiết logging cho debugging

### Error Handling

- RAG failure không ảnh hưởng đến OCR processing
- Response bao gồm `rag_indexed: false` và `rag_error` nếu có lỗi
- Logging chi tiết để debug issues

### Performance Considerations

- Embedding generation có thể mất 1-2 giây cho mỗi file
- Vector search rất nhanh (< 100ms)
- Sử dụng async processing nếu cần scale
- Cache embeddings cho files đã process

## Support

Nếu gặp vấn đề, kiểm tra:
1. Logs trong `logs/` directory
2. Test scripts: `test_rag_system.py`
3. Documentation: `docs/CHATBOT_INVOICE_UNDERSTANDING.md`

---

*Last updated: December 2025*