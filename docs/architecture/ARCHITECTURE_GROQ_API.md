# 📊 PHÂN CHIA NHIỆM VỤ: GROQ vs API

## 🤖 GROQ AI (Trí tuệ nhân tạo)

### Vai trò:
- **Xử lý ngôn ngữ tự nhiên (NLP)**: Hiểu ý định người dùng
- **Function Calling**: Quyết định tool nào cần gọi
- **Phân tích dữ liệu**: Tổng hợp, phân tích kết quả từ database
- **Sinh response**: Tạo câu trả lời thân thiện bằng tiếng Việt

### Model: 
- `llama-3.3-70b-versatile` (70B parameters)

### Nhiệm vụ cụ thể:
1. **Chat thông minh** - Trả lời câu hỏi người dùng
2. **Phân tích intent** - Hiểu user muốn làm gì (xem/tìm/xuất/lưu hóa đơn)
3. **Gọi tools** - Chọn tool phù hợp để lấy data
4. **Xử lý kết quả** - Format và trình bày data đẹp

### Tools Groq có thể gọi:
```python
1. get_all_invoices()         # Lấy danh sách hóa đơn
2. search_invoices()           # Tìm kiếm hóa đơn
3. get_invoice_by_id()         # Chi tiết 1 hóa đơn
4. get_invoice_statistics()    # Thống kê tổng quan
5. save_invoice_from_ocr()     # Lưu hóa đơn từ OCR
6. export_to_excel()           # Xuất Excel
7. get_recent_invoices()       # Hóa đơn gần đây
```

### Ví dụ flow:
```
User: "Cho tôi xem 5 hóa đơn gần nhất"
  ↓
Groq phân tích → Tool: get_recent_invoices(limit=5)
  ↓
Database trả về data
  ↓
Groq format → "Đây là 5 hóa đơn gần nhất: [danh sách]"
```

---

## 🔌 API ENDPOINTS (FastAPI)

### Vai trò:
- **CRUD operations**: Tạo/Đọc/Sửa/Xóa dữ liệu
- **Authentication**: Đăng ký, đăng nhập, quản lý token
- **File handling**: Upload, OCR, lưu file
- **Direct database access**: Truy cập trực tiếp không qua AI

### Endpoints chính:

#### 1. **Authentication** (`/api/auth/`)
```
POST /api/auth/register     # Đăng ký user mới
POST /api/auth/login        # Đăng nhập
POST /api/auth/refresh      # Làm mới token
GET  /api/auth/me          # Thông tin user hiện tại
```

#### 2. **Chat** (`/api/chat/`)
```
POST /api/chat/            # Chat với Groq AI
                           # → Groq xử lý và gọi tools
```

#### 3. **Invoices** (`/api/invoices/`)
```
GET  /api/invoices/        # Lấy danh sách hóa đơn
GET  /api/invoices/stats   # Thống kê
POST /api/invoices/        # Tạo hóa đơn mới
PUT  /api/invoices/{id}    # Cập nhật
DELETE /api/invoices/{id}  # Xóa
```

#### 4. **Upload & OCR** (`/api/upload/`)
```
POST /api/upload/          # Upload ảnh hóa đơn
POST /api/upload/ocr/{id}  # Chạy OCR trên ảnh
GET  /api/upload/ocr/{id}  # Lấy kết quả OCR
```

#### 5. **Export** (`/api/export/`)
```
GET /api/export/invoices           # Xuất Excel tất cả
GET /api/export/invoices/summary   # Xuất summary
```

#### 6. **Admin** (`/api/admin/`)
```
GET /api/admin/health      # Health check
GET /api/admin/stats       # Admin statistics
```

---

## 🔄 LUỒNG HOẠT ĐỘNG

### Kịch bản 1: User chat với AI
```
Frontend → POST /api/chat/
  ↓
FastAPI nhận request
  ↓
Groq Handler xử lý message
  ↓
Groq phân tích → Quyết định gọi tool
  ↓
Tool thực thi → Database query
  ↓
Groq nhận kết quả → Sinh response
  ↓
Frontend nhận câu trả lời
```

### Kịch bản 2: User truy cập trực tiếp API
```
Frontend → GET /api/invoices/
  ↓
FastAPI router xử lý
  ↓
Database query trực tiếp
  ↓
Trả về JSON raw data
  ↓
Frontend render
```

### Kịch bản 3: Upload & OCR
```
Frontend → POST /api/upload/ (file)
  ↓
FastAPI lưu file
  ↓
POST /api/upload/ocr/{id}
  ↓
Tesseract OCR extract text
  ↓
Trả về structured data
  ↓
User: "Lưu hóa đơn này"
  ↓
POST /api/chat/ → Groq → save_invoice_from_ocr()
```

---

## 📝 TÓM TẮT

| Thành phần | Vai trò | Khi nào dùng |
|-----------|---------|--------------|
| **Groq AI** | Trí tuệ, hiểu ngôn ngữ, phân tích | Chat tự nhiên, hỏi đáp phức tạp |
| **API Endpoints** | CRUD, Authentication, File handling | Thao tác trực tiếp, không cần AI |
| **Database Tools** | Cầu nối giữa Groq và Database | Groq gọi để lấy/lưu data |

### Ưu điểm của kiến trúc này:
✅ **Linh hoạt**: User có thể dùng chat AI hoặc API trực tiếp  
✅ **Mạnh mẽ**: Groq xử lý ngôn ngữ phức tạp  
✅ **Nhanh**: API trực tiếp cho thao tác đơn giản  
✅ **An toàn**: Authentication ở cả 2 layer  
