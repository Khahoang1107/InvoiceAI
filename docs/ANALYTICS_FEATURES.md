# 📊 Tính năng phân tích InvoiceAI

## Tổng quan

Hệ thống InvoiceAI đã được bổ sung các công cụ phân tích mạnh mẽ để giúp bạn:
- ✅ Tính tổng chi tiêu
- ✅ Phân tích xu hướng theo thời gian
- ✅ Phát hiện các hóa đơn bất thường

## 🎯 Các công cụ phân tích

### 1. Tính tổng chi tiêu (`get_total_spending`)

**Mô tả:** Tính tổng chi tiêu từ tất cả hóa đơn với khả năng lọc theo thời gian.

**Tham số:**
- `user_id` (optional): Lọc theo user
- `start_date` (optional): Ngày bắt đầu (YYYY-MM-DD)
- `end_date` (optional): Ngày kết thúc (YYYY-MM-DD)

**Kết quả:**
- Tổng chi tiêu
- Tổng số hóa đơn
- Trung bình mỗi hóa đơn
- Chi tiêu theo loại hóa đơn
- Top 10 nhà cung cấp
- Phân tích theo tháng

**Ví dụ câu hỏi:**
- "Tổng chi tiêu của tôi là bao nhiêu?"
- "Tôi đã chi bao nhiêu tiền tháng này?"
- "Chi tiêu từ ngày 1/1 đến 31/12 là bao nhiêu?"

**Ví dụ kết quả:**
```json
{
  "success": true,
  "total_spending": 15250000,
  "total_invoices": 45,
  "average_per_invoice": 338888.89,
  "spending_by_type": {
    "electricity": 2500000,
    "water": 1200000,
    "sale": 11550000
  },
  "top_vendors": [
    {"vendor": "Công ty Điện lực", "amount": 2500000},
    {"vendor": "Công ty Cấp nước", "amount": 1200000}
  ],
  "monthly_breakdown": {
    "2025-10": 5200000,
    "2025-11": 6800000,
    "2025-12": 3250000
  }
}
```

---

### 2. Phân tích xu hướng (`analyze_spending_trends`)

**Mô tả:** Phân tích xu hướng chi tiêu theo thời gian để xác định chi tiêu tăng hay giảm.

**Tham số:**
- `user_id` (optional): Lọc theo user
- `months` (optional): Số tháng phân tích (mặc định 6)

**Kết quả:**
- Hướng xu hướng (tăng/giảm/ổn định)
- Phần trăm thay đổi
- Dữ liệu chi tiết theo tháng
- Tháng cao nhất/thấp nhất
- Trung bình chi tiêu hàng tháng

**Ví dụ câu hỏi:**
- "Xu hướng chi tiêu của tôi thế nào?"
- "Chi tiêu tăng hay giảm?"
- "Phân tích chi tiêu 3 tháng gần đây"

**Ví dụ kết quả:**
```json
{
  "success": true,
  "months_analyzed": 6,
  "trend_direction": "tăng",
  "change_percent": 15.5,
  "monthly_data": [
    {
      "month": "2025-07",
      "total": 4200000,
      "count": 12,
      "average": 350000,
      "by_type": {
        "electricity": 800000,
        "water": 400000,
        "sale": 3000000
      }
    },
    // ... more months
  ],
  "insights": {
    "highest_month": {"month": "2025-11", "total": 6800000},
    "lowest_month": {"month": "2025-07", "total": 4200000},
    "average_monthly_spending": 5200000,
    "total_invoices": 72
  }
}
```

---

### 3. Phát hiện bất thường (`detect_spending_anomalies`)

**Mô tả:** Phát hiện các hóa đơn có giá trị bất thường (cao hoặc thấp hơn bình thường).

**Tham số:**
- `user_id` (optional): Lọc theo user
- `threshold_multiplier` (optional): Hệ số ngưỡng (mặc định 2.0 = gấp đôi trung bình)

**Kết quả:**
- Danh sách hóa đơn bất thường
- Thống kê (trung bình, độ lệch chuẩn)
- Mức độ nghiêm trọng (high/medium/low)
- Phân loại theo mức độ

**Ví dụ câu hỏi:**
- "Có hóa đơn nào bất thường không?"
- "Phát hiện chi tiêu lạ"
- "Hóa đơn đáng ngờ"

**Ví dụ kết quả:**
```json
{
  "success": true,
  "total_invoices": 45,
  "anomalies_found": 5,
  "statistics": {
    "mean_amount": 338888.89,
    "std_deviation": 150000,
    "threshold_used": 677777.78,
    "min_amount": 50000,
    "max_amount": 2500000
  },
  "anomalies": [
    {
      "invoice_id": 123,
      "invoice_number": "INV-001",
      "invoice_code": "PB16040000191",
      "amount": 2500000,
      "vendor": "Công ty ABC",
      "date": "14/10/2025",
      "anomaly_type": "high_value",
      "severity": "high",
      "deviation_percent": 637.5,
      "times_above_average": 7.38
    },
    // ... more anomalies
  ],
  "severity_breakdown": {
    "high": 2,
    "medium": 2,
    "low": 1
  }
}
```

---

## 💬 Cách sử dụng trong Chatbot

Hệ thống sẽ tự động gọi các công cụ này khi bạn hỏi:

### Tổng chi tiêu
```
User: "Tổng chi tiêu của tôi là bao nhiêu?"
AI: [Tự động gọi get_total_spending() và trả lời]
     "Tổng chi tiêu của bạn là 15,250,000 VND từ 45 hóa đơn..."
```

### Xu hướng
```
User: "Xu hướng chi tiêu thế nào?"
AI: [Tự động gọi analyze_spending_trends() và phân tích]
     "Chi tiêu của bạn đang có xu hướng tăng 15.5% so với các tháng trước..."
```

### Bất thường
```
User: "Có hóa đơn nào bất thường không?"
AI: [Tự động gọi detect_spending_anomalies() và báo cáo]
     "Tìm thấy 5 hóa đơn bất thường, trong đó 2 có mức độ nghiêm trọng cao..."
```

---

## 🔧 Gọi trực tiếp qua API

Bạn cũng có thể gọi các công cụ trực tiếp qua API:

### Endpoint
```
POST /api/groq/tools/call
```

### Request Body
```json
{
  "tool_name": "get_total_spending",
  "params": {
    "start_date": "2025-01-01",
    "end_date": "2025-12-31"
  }
}
```

### Response
```json
{
  "status": "success",
  "tool": "get_total_spending",
  "result": {
    "success": true,
    "total_spending": 15250000,
    // ... rest of result
  },
  "timestamp": "2025-01-09T10:30:00"
}
```

---

## 📈 Ứng dụng thực tế

### 1. Quản lý ngân sách
- Theo dõi tổng chi tiêu hàng tháng
- So sánh với ngân sách đề ra
- Xác định các khoản chi lớn

### 2. Phát hiện gian lận
- Phát hiện hóa đơn có giá trị bất thường
- Cảnh báo chi tiêu vượt ngưỡng
- Kiểm tra các hóa đơn đáng ngờ

### 3. Lập kế hoạch tài chính
- Phân tích xu hướng chi tiêu
- Dự đoán chi phí tương lai
- Tối ưu hóa chi tiêu

### 4. Báo cáo và thống kê
- Xuất báo cáo chi tiêu theo tháng
- Phân tích theo loại hóa đơn
- So sánh chi tiêu giữa các nhà cung cấp

---

## 🎓 Các tính năng nâng cao

### Lọc theo thời gian
Tất cả các công cụ đều hỗ trợ lọc theo khoảng thời gian:
```
"Tổng chi tiêu từ 1/1 đến 31/3"
"Xu hướng 3 tháng gần đây"
"Bất thường trong tháng này"
```

### Phân tích theo loại
Kết quả phân tích được chia theo loại hóa đơn:
- Điện (electricity)
- Nước (water)
- Bán hàng (sale)
- Dịch vụ (service)

### Insights tự động
Hệ thống tự động đưa ra các insights:
- Tháng chi tiêu cao nhất/thấp nhất
- Nhà cung cấp chi nhiều nhất
- Mức độ biến động chi tiêu
- Cảnh báo tự động

---

## ⚠️ Lưu ý

1. **Dữ liệu cần thiết:** Các công cụ cần có ít nhất vài hóa đơn để hoạt động hiệu quả
2. **Thời gian xử lý:** Với nhiều hóa đơn, thời gian xử lý có thể lâu hơn
3. **Ngưỡng bất thường:** Có thể điều chỉnh `threshold_multiplier` để thay đổi độ nhạy phát hiện
4. **Định dạng ngày:** Sử dụng định dạng YYYY-MM-DD cho các tham số ngày

---

## 🚀 Cập nhật tương lai

Các tính năng đang phát triển:
- [ ] Dự đoán chi tiêu tương lai bằng ML
- [ ] So sánh với người dùng khác (anonymous)
- [ ] Cảnh báo tự động qua email/notification
- [ ] Dashboard trực quan với biểu đồ
- [ ] Export báo cáo Excel/PDF tự động

---

## 📞 Hỗ trợ

Nếu có thắc mắc hoặc cần hỗ trợ, vui lòng liên hệ đội ngũ phát triển.

**Phiên bản:** 1.0.0
**Ngày cập nhật:** 09/01/2026
