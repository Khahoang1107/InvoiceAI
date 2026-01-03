# 🤖 HƯỚNG DẪN TRAIN & TEST AI CHATBOT

## ✅ ĐÃ HOÀN THÀNH

### 1. Dữ liệu mẫu (5 hóa đơn)
- **INV-2024-001**: Điện máy - Laptop Dell, Chuột, Bàn phím (₫92,950,000)
- **INV-2024-002**: Văn phòng phẩm - Bút, Sổ tay, Giấy A4 (₫9,020,000)
- **INV-2024-003**: Thực phẩm - Thịt heo, Gà, Tôm (₫12,155,000)
- **INV-2024-004**: Nội thất - Bàn, Ghế, Tủ (₫342,100,000)
- **INV-2024-005**: Dược phẩm - Paracetamol, Amoxicillin, Khẩu trang (₫15,785,000)

**Tổng giá trị: ₫472,010,000**

### 2. Cấu trúc dữ liệu
```json
{
  "invoice_number": "INV-2024-001",
  "vendor": "Công ty TNHH Điện máy Xanh",
  "tax_code": "0123456789",
  "customer_name": "Công ty CP Công nghệ ABC",
  "customer_email": "abc@company.com",
  "customer_address": "123 Đường Lê Lợi, Q1, TP.HCM",
  "issue_date": "2025-12-15",
  "due_date": "2026-01-14",
  "amount": 84500000,
  "tax": 8450000,
  "total_amount_numeric": 92950000,
  "status": "completed",
  "items": [
    {"name": "Laptop Dell Inspiron 15", "quantity": 5, "price": 15000000, "total": 75000000},
    {"name": "Chuột không dây Logitech", "quantity": 10, "price": 350000, "total": 3500000}
  ],
  "notes": "Giao hàng trong 2 tuần. Bảo hành 24 tháng."
}
```

### 3. System Prompt đã cấu hình
- Hiểu cấu trúc hóa đơn (invoice_number, vendor, customer, items, status, etc.)
- Biết cách sử dụng tools để query database
- Có ví dụ hỏi đáp cụ thể
- Trả lời bằng Tiếng Việt với emoji

---

## 🎯 CÁC CÂU HỎI TEST

### Mức độ CƠ BẢN
```
1. "Có bao nhiêu hóa đơn?"
   → AI gọi get_invoice_statistics()
   → "Hiện có 58 hóa đơn trong hệ thống"

2. "Liệt kê 5 hóa đơn gần nhất"
   → AI gọi get_all_invoices(limit=5)
   → Hiển thị danh sách

3. "Tìm hóa đơn INV-2024-001"
   → AI gọi search_invoices(query="INV-2024-001")
   → Hiển thị chi tiết hóa đơn
```

### Mức độ TRUNG BÌNH
```
4. "Hóa đơn nào đang pending?"
   → AI gọi get_all_invoices(limit=20)
   → Lọc theo status="pending"
   → Liệt kê kết quả

5. "Tìm hóa đơn của Công ty ABC"
   → AI gọi search_invoices(query="Công ty ABC")
   → Hiển thị hóa đơn liên quan

6. "Hóa đơn của nhà cung cấp Điện máy Xanh"
   → AI gọi search_invoices(query="Điện máy Xanh")
   → Hiển thị hóa đơn từ vendor đó

7. "Tổng giá trị tất cả hóa đơn?"
   → AI gọi get_invoice_statistics()
   → Tính tổng total_amount
```

### Mức độ NÂNG CAO
```
8. "Phân tích hóa đơn tháng 12"
   → AI gọi get_all_invoices(limit=100)
   → Lọc theo issue_date tháng 12
   → Thống kê số lượng, tổng giá trị

9. "So sánh hóa đơn completed vs pending"
   → AI gọi get_all_invoices(limit=100)
   → Group by status
   → So sánh số lượng và giá trị

10. "Khách hàng nào mua nhiều nhất?"
    → AI gọi get_all_invoices(limit=100)
    → Group by customer_name
    → Sort theo total_amount
```

---

## 🧪 CÁCH TEST

### 1. Khởi động backend (nếu chưa chạy)
```bash
cd d:\110122008\InvoiceAI\backend
python main.py
```
Backend chạy tại: http://localhost:8000

### 2. Mở frontend
Frontend đang chạy tại: http://localhost:3000

### 3. Test trong UserDashboard
- Login với tài khoản user hoặc admin
- Vào phần Chat
- Gõ từng câu hỏi ở trên
- Kiểm tra:
  - AI có gọi đúng tool không?
  - Dữ liệu trả về có chính xác không?
  - Format câu trả lời có đẹp không?

### 4. Kiểm tra logs
**Backend logs:**
```
📊 Calling tool: get_all_invoices with params: {'limit': 20}
✅ Tool result: {'success': True, 'count': 5, 'invoices': [...]}
🤖 AI response: Hiện có 58 hóa đơn trong hệ thống...
```

**Browser Console:**
```
🔵 Sending message: Có bao nhiêu hóa đơn?
🟢 Received response: Hiện có 58 hóa đơn...
```

---

## 🔧 TÙY CHỈNH AI

### 1. Thêm câu hỏi mẫu vào system prompt
File: `backend/handlers/groq_chat_handler.py`

Thêm vào section "VÍ DỤ HỎI ĐÁP":
```python
User: "Hóa đơn nào sắp hết hạn?"
AI: Tôi sẽ lấy danh sách bằng tool: get_all_invoices(limit=50)
    → Lọc due_date < today + 7 days
    → Liệt kê các hóa đơn sắp đến hạn
```

### 2. Thêm tools mới
File: `backend/groq_tools.py`

Thêm method mới:
```python
def get_invoices_by_status(self, status: str, limit: int = 20) -> Dict[str, Any]:
    """Lấy hóa đơn theo trạng thái"""
    try:
        all_invoices = self.db_tools.get_all_invoices(limit=limit*2)
        filtered = [inv for inv in all_invoices if inv.get('status') == status]
        return {
            "success": True,
            "status": status,
            "count": len(filtered),
            "invoices": filtered[:limit]
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
```

Thêm vào tools description:
```python
{
    "name": "get_invoices_by_status",
    "description": "Lấy danh sách hóa đơn theo trạng thái (pending/processing/completed/failed)",
    "parameters": {
        "type": "object",
        "properties": {
            "status": {"type": "string", "description": "Trạng thái hóa đơn"},
            "limit": {"type": "integer", "description": "Số lượng tối đa"}
        },
        "required": ["status"]
    }
}
```

### 3. Fine-tune responses
Chỉnh format trả lời trong system prompt:
```
Khi liệt kê hóa đơn, format như sau:
📋 Danh sách hóa đơn:
1. INV-2024-001 | Công ty ABC | ₫92,950,000 | ✅ Completed
2. INV-2024-002 | Trường ĐH | ₫9,020,000 | ⏳ Processing
...
```

---

## 📈 KẾT QUẢ MONG ĐỢI

### AI đã học được:
- ✅ Cấu trúc dữ liệu hóa đơn (10 fields chính)
- ✅ Cách query database qua tools (5 tools)
- ✅ Phân tích & thống kê dữ liệu
- ✅ Trả lời bằng Tiếng Việt có format đẹp

### AI có thể:
- ✅ Trả lời câu hỏi về số lượng hóa đơn
- ✅ Tìm kiếm hóa đơn theo mã/tên/vendor
- ✅ Lọc hóa đơn theo trạng thái
- ✅ Tính tổng giá trị
- ✅ Phân tích theo thời gian
- ✅ So sánh & thống kê

---

## 🚀 BƯỚC TIẾP THEO

1. **Thêm dữ liệu thực**: Upload ảnh hóa đơn thật qua OCR
2. **Train contextual understanding**: Thêm domain knowledge về thuế, hợp đồng
3. **Personalization**: Học preferences của từng user
4. **Multi-turn conversation**: Chatbot nhớ context cuộc hội thoại
5. **Action automation**: AI tự động tạo/sửa/xóa hóa đơn theo lệnh

---

## 📞 SUPPORT

Nếu chatbot trả lời sai:
1. Check backend logs xem tool nào được gọi
2. Verify dữ liệu trong database
3. Điều chỉnh system prompt
4. Test lại với câu hỏi rõ ràng hơn

**Happy Training! 🎉**
