# 👑 Admin API - Hướng dẫn Quản trị Hệ thống

## 📋 Tổng quan

API dành riêng cho **Admin** để quản lý toàn bộ hệ thống InvoiceAI bao gồm:
- 👥 **Quản lý người dùng** - Tạo, xóa, cấp quyền
- 📋 **Giám sát OCR jobs** - Theo dõi tiến trình xử lý OCR
- 📄 **Quản lý hóa đơn** - Xem và quản lý toàn bộ database
- 📊 **Thống kê hệ thống** - Số liệu tổng hợp về hoạt động

---

## 🔑 Authentication

Tất cả endpoint Admin yêu cầu:
1. **Token hợp lệ** (JWT)
2. **Quyền Admin** (`is_admin = true`)

### Header yêu cầu:
```http
Authorization: Bearer <admin_jwt_token>
```

### Lấy Admin Token:
```bash
POST /auth/login
Content-Type: application/json

{
  "email": "admin@invoiceai.com",
  "password": "admin_password"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "admin@invoiceai.com",
    "is_admin": true
  }
}
```

---

## 👥 Quản lý Người dùng

### 1. Lấy danh sách tất cả người dùng

```http
GET /admin/users
Authorization: Bearer <admin_token>
```

**Response:**
```json
[
  {
    "id": 1,
    "username": "admin",
    "email": "admin@invoiceai.com",
    "full_name": "Administrator",
    "is_active": true,
    "is_admin": true,
    "created_at": "2025-01-01T00:00:00",
    "last_login": "2025-12-22T10:30:00"
  },
  {
    "id": 2,
    "username": "user1",
    "email": "user1@example.com",
    "full_name": "User One",
    "is_active": true,
    "is_admin": false,
    "created_at": "2025-01-15T00:00:00",
    "last_login": "2025-12-20T14:20:00"
  }
]
```

---

### 2. Cấp/Thu hồi quyền Admin

```http
PUT /admin/users/{user_id}/toggle-admin
Authorization: Bearer <admin_token>
```

**Example:**
```bash
curl -X PUT http://localhost:8000/admin/users/2/toggle-admin \
  -H "Authorization: Bearer <admin_token>"
```

**Response:**
```json
{
  "id": 2,
  "username": "user1",
  "email": "user1@example.com",
  "is_admin": true,
  "message": "User promoted to admin"
}
```

⚠️ **Lưu ý:** Không thể tự xóa quyền admin của chính mình

---

### 3. Kích hoạt/Vô hiệu hóa tài khoản

```http
PUT /admin/users/{user_id}/toggle-active
Authorization: Bearer <admin_token>
```

**Example:**
```bash
curl -X PUT http://localhost:8000/admin/users/3/toggle-active \
  -H "Authorization: Bearer <admin_token>"
```

**Response:**
```json
{
  "id": 3,
  "username": "user2",
  "is_active": false,
  "message": "User account deactivated"
}
```

---

### 4. Xóa người dùng

```http
DELETE /admin/users/{user_id}
Authorization: Bearer <admin_token>
```

**Example:**
```bash
curl -X DELETE http://localhost:8000/admin/users/3 \
  -H "Authorization: Bearer <admin_token>"
```

**Response:**
```json
{
  "message": "User user2 (user2@example.com) has been deleted successfully",
  "deleted_user_id": 3,
  "timestamp": "2025-12-22T10:35:00"
}
```

⚠️ **Giới hạn:**
- Không thể xóa tài khoản của chính mình
- Không thể xóa tài khoản admin khác

---

## 📋 Giám sát OCR Jobs

### 1. Xem tất cả OCR jobs

```http
GET /admin/ocr-jobs?status=<status>&limit=<limit>
Authorization: Bearer <admin_token>
```

**Query Parameters:**
- `status` (optional): `queued`, `processing`, `done`, `failed`
- `limit` (optional): Số lượng jobs tối đa (default: 50)

**Example:**
```bash
# Lấy tất cả jobs đang xử lý
curl http://localhost:8000/admin/ocr-jobs?status=processing \
  -H "Authorization: Bearer <admin_token>"

# Lấy 20 jobs mới nhất
curl http://localhost:8000/admin/ocr-jobs?limit=20 \
  -H "Authorization: Bearer <admin_token>"
```

**Response:**
```json
{
  "success": true,
  "count": 15,
  "jobs": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "filename": "invoice_001.jpg",
      "filepath": "/uploads/invoice_001.jpg",
      "status": "done",
      "progress": 100,
      "invoice_id": 42,
      "error_message": null,
      "user_id": "user123",
      "created_at": "2025-12-22T10:00:00",
      "started_at": "2025-12-22T10:00:05",
      "completed_at": "2025-12-22T10:00:15",
      "updated_at": "2025-12-22T10:00:15"
    },
    {
      "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
      "filename": "invoice_002.png",
      "filepath": "/uploads/invoice_002.png",
      "status": "failed",
      "progress": 0,
      "invoice_id": null,
      "error_message": "Tesseract OCR failed: Unable to read image",
      "user_id": "user456",
      "created_at": "2025-12-22T10:05:00",
      "started_at": "2025-12-22T10:05:02",
      "completed_at": "2025-12-22T10:05:05",
      "updated_at": "2025-12-22T10:05:05"
    }
  ],
  "timestamp": "2025-12-22T10:30:00"
}
```

---

### 2. Thống kê OCR Jobs

```http
GET /admin/ocr-jobs/statistics
Authorization: Bearer <admin_token>
```

**Example:**
```bash
curl http://localhost:8000/admin/ocr-jobs/statistics \
  -H "Authorization: Bearer <admin_token>"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "total_jobs": 150,
    "status_breakdown": {
      "queued": 5,
      "processing": 2,
      "done": 130,
      "failed": 13
    },
    "recent_24h": 45,
    "success_rate": 90.91,
    "avg_processing_time_seconds": 12.5,
    "queued": 5,
    "processing": 2,
    "done": 130,
    "failed": 13
  },
  "timestamp": "2025-12-22T10:30:00"
}
```

**Giải thích các trường:**
- `total_jobs`: Tổng số jobs trong hệ thống
- `status_breakdown`: Phân bố theo trạng thái
- `recent_24h`: Số jobs trong 24h qua
- `success_rate`: Tỷ lệ thành công (%)
- `avg_processing_time_seconds`: Thời gian xử lý trung bình (giây)

---

## 📄 Quản lý Hóa đơn

### 1. Xem tất cả hóa đơn

```http
GET /admin/invoices?limit=<limit>&offset=<offset>
Authorization: Bearer <admin_token>
```

**Query Parameters:**
- `limit` (optional): Số lượng hóa đơn tối đa (default: 100)
- `offset` (optional): Bỏ qua số hóa đơn (default: 0)

**Example:**
```bash
# Lấy 50 hóa đơn đầu tiên
curl http://localhost:8000/admin/invoices?limit=50 \
  -H "Authorization: Bearer <admin_token>"

# Lấy 20 hóa đơn, bỏ qua 100 hóa đơn đầu (pagination)
curl http://localhost:8000/admin/invoices?limit=20&offset=100 \
  -H "Authorization: Bearer <admin_token>"
```

**Response:**
```json
{
  "success": true,
  "total": 450,
  "count": 50,
  "limit": 50,
  "offset": 0,
  "invoices": [
    {
      "id": 42,
      "filename": "invoice_001.jpg",
      "filepath": "/uploads/invoice_001.jpg",
      "invoice_code": "INV-2025-001",
      "invoice_type": "sale",
      "buyer_name": "Công ty ABC",
      "seller_name": "Công ty XYZ",
      "invoice_date": "2025-12-20",
      "total_amount": "1,500,000 VND",
      "total_amount_value": 1500000.0,
      "confidence_score": 0.95,
      "buyer_tax_id": "0123456789",
      "seller_tax_id": "9876543210",
      "currency": "VND",
      "subtotal": 1363636.36,
      "tax_amount": 136363.64,
      "created_at": "2025-12-20T14:30:00",
      "updated_at": "2025-12-20T14:30:00"
    }
  ],
  "timestamp": "2025-12-22T10:30:00"
}
```

---

### 2. Thống kê Hóa đơn

```http
GET /admin/invoices/statistics
Authorization: Bearer <admin_token>
```

**Example:**
```bash
curl http://localhost:8000/admin/invoices/statistics \
  -H "Authorization: Bearer <admin_token>"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "total_invoices": 450,
    "total_amount": 125000000.0,
    "avg_confidence": 0.92,
    "type_breakdown": {
      "sale": 250,
      "service": 100,
      "electricity": 50,
      "water": 30,
      "other": 20
    },
    "recent_7days": 45,
    "recent_30days": 180
  },
  "timestamp": "2025-12-22T10:30:00"
}
```

**Giải thích:**
- `total_invoices`: Tổng số hóa đơn
- `total_amount`: Tổng giá trị (VND)
- `avg_confidence`: Độ tin cậy trung bình
- `type_breakdown`: Phân loại theo loại hóa đơn
- `recent_7days`: Hóa đơn trong 7 ngày qua
- `recent_30days`: Hóa đơn trong 30 ngày qua

---

### 3. Xóa hóa đơn

```http
DELETE /admin/invoices/{invoice_id}
Authorization: Bearer <admin_token>
```

**Example:**
```bash
curl -X DELETE http://localhost:8000/admin/invoices/42 \
  -H "Authorization: Bearer <admin_token>"
```

**Response:**
```json
{
  "success": true,
  "message": "Invoice INV-2025-001 (ID: 42) has been deleted successfully",
  "deleted_invoice_id": 42,
  "timestamp": "2025-12-22T10:35:00"
}
```

---

## 📊 Dashboard Admin - Use Cases

### Use Case 1: Kiểm tra hiệu suất OCR

```bash
# Bước 1: Lấy thống kê OCR
curl http://localhost:8000/admin/ocr-jobs/statistics \
  -H "Authorization: Bearer <admin_token>"

# Bước 2: Xem các job thất bại
curl http://localhost:8000/admin/ocr-jobs?status=failed&limit=10 \
  -H "Authorization: Bearer <admin_token>"

# Phân tích: Nếu success_rate < 85%, cần kiểm tra:
# - Tesseract configuration
# - Image quality
# - Error messages của failed jobs
```

---

### Use Case 2: Giám sát hệ thống real-time

```bash
# Kiểm tra jobs đang xử lý
curl http://localhost:8000/admin/ocr-jobs?status=processing \
  -H "Authorization: Bearer <admin_token>"

# Kiểm tra jobs đang chờ
curl http://localhost:8000/admin/ocr-jobs?status=queued \
  -H "Authorization: Bearer <admin_token>"

# Nếu có nhiều jobs queued lâu:
# → Khởi động thêm OCR worker: python backend/worker.py
```

---

### Use Case 3: Quản lý người dùng

```bash
# Bước 1: Xem danh sách người dùng
curl http://localhost:8000/admin/users \
  -H "Authorization: Bearer <admin_token>"

# Bước 2: Vô hiệu hóa user vi phạm
curl -X PUT http://localhost:8000/admin/users/5/toggle-active \
  -H "Authorization: Bearer <admin_token>"

# Bước 3: Cấp quyền admin cho user tin cậy
curl -X PUT http://localhost:8000/admin/users/7/toggle-admin \
  -H "Authorization: Bearer <admin_token>"
```

---

### Use Case 4: Audit & Cleanup

```bash
# Kiểm tra tổng quan database
curl http://localhost:8000/admin/invoices/statistics \
  -H "Authorization: Bearer <admin_token>"

# Xóa hóa đơn test/spam
curl -X DELETE http://localhost:8000/admin/invoices/999 \
  -H "Authorization: Bearer <admin_token>"

# Xóa users không hoạt động
curl -X DELETE http://localhost:8000/admin/users/123 \
  -H "Authorization: Bearer <admin_token>"
```

---

## 🔒 Security Best Practices

### 1. Bảo vệ Admin Token
```bash
# ❌ KHÔNG làm vậy
export ADMIN_TOKEN="eyJhbGciOiJIUzI1NiIsInR..."  # exposed in shell history

# ✅ Làm thế này
# Lưu trong file .env (không commit vào git)
ADMIN_TOKEN=<token>

# Hoặc dùng password manager
```

---

### 2. Giới hạn quyền Admin

Chỉ cấp admin cho:
- ✅ Người có trách nhiệm quản lý hệ thống
- ✅ Tài khoản có xác thực 2FA (nếu có)
- ❌ KHÔNG cấp cho users thông thường

---

### 3. Audit Logs

Theo dõi hành động admin:
```python
# TODO: Implement admin audit logging
# Log mọi thao tác:
# - User deleted
# - Admin permission granted
# - Invoice deleted
```

---

## 🚨 Error Handling

### Error Response Format:
```json
{
  "detail": "Error message here",
  "status_code": 403
}
```

### Common Errors:

| Status Code | Error | Giải pháp |
|-------------|-------|-----------|
| 401 | Unauthorized | Token hết hạn hoặc không hợp lệ → Login lại |
| 403 | Forbidden | Không có quyền admin → Liên hệ admin |
| 404 | Not Found | User/Invoice không tồn tại → Kiểm tra ID |
| 500 | Server Error | Lỗi database → Kiểm tra logs |

---

## 📝 API Summary

### User Management (4 endpoints)
- `GET /admin/users` - Danh sách users
- `PUT /admin/users/{id}/toggle-admin` - Cấp/thu hồi admin
- `PUT /admin/users/{id}/toggle-active` - Kích hoạt/vô hiệu
- `DELETE /admin/users/{id}` - Xóa user

### OCR Monitoring (2 endpoints)
- `GET /admin/ocr-jobs` - Danh sách OCR jobs
- `GET /admin/ocr-jobs/statistics` - Thống kê OCR

### Invoice Management (3 endpoints)
- `GET /admin/invoices` - Danh sách hóa đơn
- `GET /admin/invoices/statistics` - Thống kê hóa đơn
- `DELETE /admin/invoices/{id}` - Xóa hóa đơn

**Tổng: 9 endpoints**

---

## 🎯 Next Steps

1. **Tạo Admin Dashboard UI** (Frontend)
   - Hiển thị thống kê real-time
   - Quản lý users trong bảng
   - Monitor OCR jobs

2. **Implement Audit Logs**
   - Log mọi hành động admin
   - Lưu vào database
   - Export logs ra file

3. **Add Notifications**
   - Email khi có OCR job failed
   - Alert khi success_rate giảm
   - Webhook cho external monitoring

4. **Performance Monitoring**
   - Track API response time
   - Database query optimization
   - Cache frequently accessed data

---

## 📚 Related Documentation

- [AUTH_API_TESTING_GUIDE.md](./AUTH_API_TESTING_GUIDE.md) - Hướng dẫn authentication
- [OCR_STATUS_REPORT.md](./OCR_STATUS_REPORT.md) - Báo cáo OCR workflow
- [GROQ_QUICK_START.md](./GROQ_QUICK_START.md) - Groq integration

---

**✅ Hoàn thành:** Tài liệu API Admin đầy đủ

**Author:** InvoiceAI Team  
**Last Updated:** 2025-12-22
