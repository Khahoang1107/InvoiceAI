# 🤖 Hướng Dẫn: Chatbot Hiểu Sâu Về Hóa Đơn

## 📋 Tổng Quan

Để chatbot có thể trả lời các câu hỏi và hiểu sâu về hóa đơn trong ứng dụng, bạn cần:

1. **Thêm các tools chuyên sâu** để phân tích hóa đơn
2. **Cung cấp context đầy đủ** về cấu trúc dữ liệu
3. **Train prompt** để Groq hiểu các trường hợp sử dụng
4. **Thêm semantic search** cho các câu hỏi phức tạp

---

## ✅ Những Gì Đã Có

### 1. Groq Database Tools (7 tools cơ bản)

```python
# Trong backend/groq_tools.py
- get_all_invoices()        # Lấy danh sách
- search_invoices()         # Tìm kiếm
- get_invoice_by_id()       # Chi tiết 1 hóa đơn
- get_statistics()          # Thống kê tổng quát
- filter_by_date()          # Lọc theo ngày
- get_invoices_by_type()    # Lọc theo loại
- get_high_value_invoices() # Hóa đơn giá trị cao
```

### 2. Schema Hóa Đơn Hiện Tại

Mỗi hóa đơn có **38 trường dữ liệu**:

```
Thông tin cơ bản:
- id, invoice_number, invoice_code
- invoice_type (electricity, water, sale, service)
- status (pending, paid, overdue)

Thông tin người bán:
- seller_name, seller_address, seller_tax_id

Thông tin người mua:
- buyer_name, buyer_address, buyer_tax_id

Thông tin tài chính:
- subtotal, tax_percentage, tax_amount, tax
- total_amount, total_amount_value, total_amount_numeric
- amount, currency

Thông tin thời gian:
- date, date_string, issue_date, due_date
- created_at, updated_at

Metadata:
- filename, filepath, file_id
- confidence_score (độ tin cậy OCR)
- ocr_text, extracted_data
- items (danh sách sản phẩm)
- notes, description
```

---

## 🎯 Những Gì Cần Thêm

### 1. Tools Phân Tích Chuyên Sâu

#### A. Phân tích chi tiết một hóa đơn

```python
def analyze_invoice_details(self, invoice_id: int) -> Dict[str, Any]:
    """
    Phân tích chi tiết một hóa đơn bao gồm:
    - Tất cả thông tin cơ bản
    - Items (nếu có)
    - Tình trạng thanh toán
    - Cảnh báo (overdue, high value, etc)
    - So sánh với hóa đơn tương tự
    """
    invoice = self.db_tools.get_invoice_by_id(invoice_id)
    
    # Parse items nếu là JSON
    items = []
    if invoice.get('items'):
        try:
            items = json.loads(invoice['items'])
        except:
            items = []
    
    # Tính toán insights
    analysis = {
        "invoice": invoice,
        "items_breakdown": items,
        "payment_status": self._analyze_payment_status(invoice),
        "warnings": self._get_warnings(invoice),
        "similar_invoices": self._find_similar_invoices(invoice),
        "insights": {
            "is_high_value": invoice.get('total_amount_numeric', 0) > 10000000,
            "is_overdue": self._check_overdue(invoice),
            "days_until_due": self._calculate_days_until_due(invoice)
        }
    }
    
    return analysis
```

#### B. So sánh hóa đơn

```python
def compare_invoices(self, invoice_ids: List[int]) -> Dict[str, Any]:
    """
    So sánh nhiều hóa đơn với nhau
    - Giá trị
    - Nhà cung cấp
    - Thời gian
    - Xu hướng
    """
    invoices = [self.db_tools.get_invoice_by_id(id) for id in invoice_ids]
    
    return {
        "invoices": invoices,
        "comparison": {
            "total_values": [inv.get('total_amount_numeric') for inv in invoices],
            "vendors": [inv.get('vendor') or inv.get('seller_name') for inv in invoices],
            "dates": [inv.get('issue_date') or inv.get('date') for inv in invoices],
            "average_value": sum(inv.get('total_amount_numeric', 0) for inv in invoices) / len(invoices),
            "highest_value": max(invoices, key=lambda x: x.get('total_amount_numeric', 0)),
            "lowest_value": min(invoices, key=lambda x: x.get('total_amount_numeric', 0))
        }
    }
```

#### C. Phân tích xu hướng

```python
def analyze_trends(self, vendor: str = None, invoice_type: str = None, months: int = 6) -> Dict[str, Any]:
    """
    Phân tích xu hướng chi tiêu
    - Theo nhà cung cấp
    - Theo loại hóa đơn
    - Theo thời gian
    """
    # Lấy hóa đọn trong khoảng thời gian
    invoices = self.db_tools.get_all_invoices(limit=1000)
    
    # Lọc theo điều kiện
    if vendor:
        invoices = [inv for inv in invoices if vendor.lower() in str(inv.get('vendor', '')).lower()]
    if invoice_type:
        invoices = [inv for inv in invoices if inv.get('invoice_type') == invoice_type]
    
    # Phân tích theo tháng
    monthly_analysis = {}
    total_spent = 0
    
    for inv in invoices:
        # Group by month
        date = inv.get('issue_date') or inv.get('date_string')
        # Calculate stats
        
    return {
        "period": f"{months} months",
        "total_invoices": len(invoices),
        "total_spent": total_spent,
        "monthly_breakdown": monthly_analysis,
        "trends": {
            "increasing": True,  # Calculate trend
            "average_per_month": total_spent / months
        }
    }
```

#### D. Trả lời câu hỏi về items trong hóa đơn

```python
def analyze_invoice_items(self, invoice_id: int) -> Dict[str, Any]:
    """
    Phân tích chi tiết các items trong hóa đơn
    """
    invoice = self.db_tools.get_invoice_by_id(invoice_id)
    
    items = []
    if invoice.get('items'):
        try:
            items = json.loads(invoice['items'])
        except:
            pass
    
    return {
        "invoice_id": invoice_id,
        "invoice_number": invoice.get('invoice_number'),
        "total_items": len(items),
        "items_detail": items,
        "categories": self._categorize_items(items),
        "most_expensive_item": max(items, key=lambda x: x.get('amount', 0)) if items else None,
        "total_quantity": sum(item.get('quantity', 0) for item in items)
    }
```

#### E. Tìm hóa đơn trùng lặp

```python
def find_duplicate_invoices(self) -> Dict[str, Any]:
    """
    Tìm các hóa đơn có thể bị trùng lặp
    - Cùng invoice_number
    - Cùng vendor + amount + date
    """
    invoices = self.db_tools.get_all_invoices(limit=1000)
    
    duplicates = []
    seen = {}
    
    for inv in invoices:
        key = f"{inv.get('invoice_number')}_{inv.get('vendor')}_{inv.get('total_amount_numeric')}"
        if key in seen:
            duplicates.append({
                "original": seen[key],
                "duplicate": inv
            })
        else:
            seen[key] = inv
    
    return {
        "total_duplicates_found": len(duplicates),
        "duplicates": duplicates
    }
```

#### F. Báo cáo tài chính

```python
def generate_financial_report(self, start_date: str, end_date: str) -> Dict[str, Any]:
    """
    Tạo báo cáo tài chính tổng hợp
    """
    invoices = self.filter_by_date(start_date, end_date)['invoices']
    
    return {
        "period": f"{start_date} to {end_date}",
        "summary": {
            "total_invoices": len(invoices),
            "total_amount": sum(inv.get('total_amount_numeric', 0) for inv in invoices),
            "paid_count": len([inv for inv in invoices if inv.get('status') == 'paid']),
            "pending_count": len([inv for inv in invoices if inv.get('status') == 'pending']),
            "overdue_count": len([inv for inv in invoices if inv.get('status') == 'overdue'])
        },
        "by_vendor": self._group_by_vendor(invoices),
        "by_type": self._group_by_type(invoices),
        "by_month": self._group_by_month(invoices)
    }
```

---

## 🔧 Cách Implement

### Bước 1: Thêm Tools Mới vào `groq_tools.py`

```python
# File: backend/groq_tools.py

class GroqDatabaseTools:
    
    # ... existing methods ...
    
    def analyze_invoice_details(self, invoice_id: int) -> Dict[str, Any]:
        # Implementation như trên
        pass
    
    def compare_invoices(self, invoice_ids: List[int]) -> Dict[str, Any]:
        # Implementation như trên
        pass
    
    def analyze_trends(self, vendor: str = None, invoice_type: str = None, months: int = 6) -> Dict[str, Any]:
        # Implementation như trên
        pass
    
    def analyze_invoice_items(self, invoice_id: int) -> Dict[str, Any]:
        # Implementation như trên
        pass
    
    def find_duplicate_invoices(self) -> Dict[str, Any]:
        # Implementation như trên
        pass
    
    def generate_financial_report(self, start_date: str, end_date: str) -> Dict[str, Any]:
        # Implementation như trên
        pass
    
    # Update get_tools_description() để thêm tools mới
    def get_tools_description(self) -> List[Dict[str, Any]]:
        existing_tools = [...]  # Tools cũ
        
        new_tools = [
            {
                "name": "analyze_invoice_details",
                "description": "Phân tích chi tiết một hóa đơn bao gồm items, warnings, similar invoices",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "invoice_id": {"type": "integer", "description": "ID của hóa đơn"}
                    },
                    "required": ["invoice_id"]
                }
            },
            {
                "name": "compare_invoices",
                "description": "So sánh nhiều hóa đơn với nhau về giá trị, vendor, thời gian",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "invoice_ids": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "Danh sách ID các hóa đơn cần so sánh"
                        }
                    },
                    "required": ["invoice_ids"]
                }
            },
            # ... các tools khác
        ]
        
        return existing_tools + new_tools
```

### Bước 2: Update Prompt trong `groq_chat_handler.py`

```python
# File: backend/handlers/groq_chat_handler.py

SYSTEM_PROMPT = """
BẠN LÀ INVOICE AI ASSISTANT - CHUYÊN GIA PHÂN TÍCH HÓA ĐƠN

Bạn có quyền truy cập vào database hóa đơn với các khả năng:

1. TRUY VẤN CỞ BẢN:
   - Xem danh sách hóa đơn
   - Tìm kiếm theo keyword
   - Lọc theo ngày, loại, giá trị

2. PHÂN TÍCH CHUYÊN SÂU:
   - Phân tích chi tiết từng hóa đơn (items, cảnh báo, tương tự)
   - So sánh nhiều hóa đơn
   - Phân tích xu hướng chi tiêu
   - Tìm hóa đơn trùng lặp
   - Tạo báo cáo tài chính

3. CÁC CÂU HỎI BẠN CÓ THỂ TRẢ LỜI:
   ✅ "Hóa đơn số INV-001 có những gì?"
   ✅ "So sánh hóa đơn 1, 2 và 3"
   ✅ "Xu hướng chi tiêu điện nước 6 tháng qua?"
   ✅ "Có hóa đơn nào bị trùng không?"
   ✅ "Tổng chi tiêu tháng 12/2025?"
   ✅ "Hóa đơn nào sắp đến hạn?"
   ✅ "Vendor nào tôi chi nhiều nhất?"

CẤU TRÚC HÓA ĐƠN:
- Mỗi hóa đơn có 38 trường dữ liệu
- Items được lưu dưới dạng JSON string
- Status: pending/paid/overdue
- Invoice types: electricity/water/sale/service

CÁCH SỬ DỤNG TOOLS:
1. Với câu hỏi CƠ BẢN → dùng tools cơ bản (get_all, search, filter)
2. Với câu hỏi PHÂN TÍCH → dùng analyze_invoice_details, compare_invoices
3. Với câu hỏi XU HƯỚNG → dùng analyze_trends, generate_financial_report
4. Với câu hỏi CHI TIẾT ITEMS → dùng analyze_invoice_items

LƯU Ý:
- LUÔN parse items từ JSON string nếu có
- Tính toán days_until_due cho cảnh báo
- Format số tiền với đơn vị VND
- Đề xuất hành động nếu phát hiện vấn đề
"""
```

### Bước 3: Cải Thiện Response Format

```python
# File: backend/handlers/groq_chat_handler.py

async def _format_response(self, groq_response: str, tool_results: List) -> Dict[str, Any]:
    """Format response với rich data"""
    
    response = {
        "message": groq_response,
        "type": "text",
        "data": None,
        "visualizations": None
    }
    
    # Nếu có tool results, thêm structured data
    if tool_results:
        last_result = tool_results[-1]
        
        # Nếu là phân tích chi tiết → trả thêm structured data
        if "invoice" in last_result and "items_breakdown" in last_result:
            response["type"] = "invoice_details"
            response["data"] = last_result
        
        # Nếu là comparison → trả chart data
        elif "comparison" in last_result:
            response["type"] = "comparison"
            response["data"] = last_result
            response["visualizations"] = {
                "chart_type": "bar",
                "data": last_result["comparison"]["total_values"]
            }
        
        # Nếu là financial report → trả summary + charts
        elif "summary" in last_result and "by_month" in last_result:
            response["type"] = "financial_report"
            response["data"] = last_result
            response["visualizations"] = {
                "chart_type": "line",
                "data": last_result["by_month"]
            }
    
    return response
```

---

## 📊 Ví Dụ Sử Dụng

### 1. Phân tích chi tiết hóa đơn

```bash
POST /chat/groq
{
  "message": "Phân tích chi tiết hóa đơn số 5",
  "user_id": "user1"
}

Response:
{
  "message": "📋 Hóa đơn #5 (INV-2025-005)
  
  🏢 Nhà cung cấp: Công ty Điện Lực Hà Nội
  💰 Tổng tiền: 2,500,000 VND
  📅 Ngày phát hành: 01/12/2025
  ⏰ Hạn thanh toán: 15/12/2025 (còn 5 ngày)
  
  📦 Chi tiết items:
  1. Điện sinh hoạt: 250 kWh x 2,500 VND = 625,000 VND
  2. Điện sản xuất: 150 kWh x 3,200 VND = 480,000 VND
  3. Thuế VAT 10%: 110,500 VND
  
  ⚠️ Cảnh báo:
  - Sắp đến hạn thanh toán
  - Giá trị cao hơn trung bình 15%
  
  🔍 Hóa đơn tương tự:
  - INV-2025-003: 2,300,000 VND (tháng trước)
  - INV-2025-001: 2,100,000 VND (2 tháng trước)",
  
  "type": "invoice_details",
  "data": {
    "invoice": {...},
    "items_breakdown": [...],
    "warnings": [...],
    "similar_invoices": [...]
  }
}
```

### 2. So sánh hóa đơn

```bash
POST /chat/groq
{
  "message": "So sánh hóa đơn 1, 2 và 3",
  "user_id": "user1"
}

Response:
{
  "message": "📊 So sánh 3 hóa đơn:
  
  Hóa đơn #1:
  - Vendor: Công ty A
  - Giá trị: 1,500,000 VND
  - Ngày: 01/10/2025
  
  Hóa đơn #2:
  - Vendor: Công ty B  
  - Giá trị: 3,200,000 VND
  - Ngày: 15/10/2025
  
  Hóa đơn #3:
  - Vendor: Công ty A
  - Giá trị: 1,800,000 VND
  - Ngày: 01/11/2025
  
  📈 Insights:
  - Trung bình: 2,166,667 VND
  - Cao nhất: Hóa đơn #2 (3,200,000 VND)
  - Thấp nhất: Hóa đơn #1 (1,500,000 VND)
  - Công ty A chiếm 2/3 hóa đơn",
  
  "type": "comparison",
  "visualizations": {
    "chart_type": "bar",
    "data": [1500000, 3200000, 1800000]
  }
}
```

### 3. Xu hướng chi tiêu

```bash
POST /chat/groq
{
  "message": "Xu hướng chi tiêu điện nước 6 tháng qua",
  "user_id": "user1"
}

Response:
{
  "message": "📈 Xu hướng chi tiêu ĐIỆN & NƯỚC (6 tháng):
  
  Tổng chi: 45,000,000 VND
  Số hóa đơn: 24
  Trung bình/tháng: 7,500,000 VND
  
  Chi tiết theo tháng:
  - 07/2025: 6,500,000 VND
  - 08/2025: 7,200,000 VND  
  - 09/2025: 7,800,000 VND
  - 10/2025: 8,100,000 VND
  - 11/2025: 8,400,000 VND
  - 12/2025: 7,000,000 VND
  
  📊 Phân tích:
  - Xu hướng: TĂNG nhẹ (+15% so với đầu kỳ)
  - Tháng cao nhất: 11/2025 (8,400,000 VND)
  - Tháng thấp nhất: 07/2025 (6,500,000 VND)
  
  💡 Gợi ý:
  - Cân nhắc tiết kiệm năng lượng
  - Chi phí tăng đều qua các tháng",
  
  "type": "trends",
  "visualizations": {
    "chart_type": "line",
    "data": [6500000, 7200000, 7800000, 8100000, 8400000, 7000000]
  }
}
```

---

## 🎨 Frontend Integration

### Component hiển thị Invoice Details

```typescript
// InvoiceDetailsView.tsx
function InvoiceDetailsView({ data }) {
  return (
    <div className="invoice-details">
      <h3>{data.invoice.invoice_number}</h3>
      
      {/* Basic Info */}
      <div className="info-section">
        <p>Vendor: {data.invoice.vendor}</p>
        <p>Amount: {formatCurrency(data.invoice.total_amount_numeric)}</p>
        <p>Date: {formatDate(data.invoice.issue_date)}</p>
      </div>
      
      {/* Items Breakdown */}
      <div className="items-section">
        <h4>Items</h4>
        {data.items_breakdown.map(item => (
          <div key={item.id}>
            <span>{item.name}</span>
            <span>{item.quantity} x {formatCurrency(item.price)}</span>
          </div>
        ))}
      </div>
      
      {/* Warnings */}
      {data.warnings.length > 0 && (
        <div className="warnings">
          {data.warnings.map(warning => (
            <Alert key={warning.id} type="warning">
              {warning.message}
            </Alert>
          ))}
        </div>
      )}
      
      {/* Similar Invoices */}
      <div className="similar-section">
        <h4>Similar Invoices</h4>
        {data.similar_invoices.map(inv => (
          <InvoiceCard key={inv.id} invoice={inv} />
        ))}
      </div>
    </div>
  );
}
```

### Component hiển thị Charts

```typescript
// TrendsChart.tsx
import { Line, Bar } from 'react-chartjs-2';

function TrendsChart({ visualizations, data }) {
  if (visualizations.chart_type === 'line') {
    return <Line data={data.by_month} />;
  }
  
  if (visualizations.chart_type === 'bar') {
    return <Bar data={data.comparison} />;
  }
  
  return null;
}
```

---

## 🚀 Testing

```bash
# Test phân tích chi tiết
curl -X POST http://localhost:8000/chat/groq \
  -H "Content-Type: application/json" \
  -d '{"message":"Phân tích chi tiết hóa đơn 5","user_id":"test"}'

# Test so sánh
curl -X POST http://localhost:8000/chat/groq \
  -H "Content-Type: application/json" \
  -d '{"message":"So sánh hóa đơn 1, 2, 3","user_id":"test"}'

# Test xu hướng
curl -X POST http://localhost:8000/chat/groq \
  -H "Content-Type: application/json" \
  -d '{"message":"Xu hướng chi tiêu 6 tháng","user_id":"test"}'

# Test báo cáo tài chính
curl -X POST http://localhost:8000/chat/groq \
  -H "Content-Type: application/json" \
  -d '{"message":"Báo cáo tài chính tháng 12/2025","user_id":"test"}'
```

---

## 📝 Checklist Implementation

- [ ] Thêm 6 tools mới vào `groq_tools.py`
- [ ] Update `get_tools_description()` 
- [ ] Update `call_tool()` để handle tools mới
- [ ] Cải thiện system prompt trong `groq_chat_handler.py`
- [ ] Thêm response formatting
- [ ] Test từng tool riêng lẻ
- [ ] Test qua chat endpoint
- [ ] Tạo frontend components để hiển thị
- [ ] Thêm visualizations (charts)
- [ ] Document các use cases

---

## 🎯 Kết Quả Mong Đợi

Sau khi implement, chatbot sẽ có thể:

✅ Trả lời chi tiết về từng hóa đơn  
✅ Phân tích items trong hóa đơn  
✅ So sánh nhiều hóa đơn  
✅ Phát hiện xu hướng chi tiêu  
✅ Cảnh báo hóa đơn sắp đến hạn  
✅ Tìm hóa đơn trùng lặp  
✅ Tạo báo cáo tài chính tự động  
✅ Gợi ý tiết kiệm chi phí  

---

**Bắt đầu từ đâu?**  
👉 Implement `analyze_invoice_details()` trước - đây là tool quan trọng nhất!
