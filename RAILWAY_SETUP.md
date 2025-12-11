# 🚀 Hướng dẫn chuyển sang PostgreSQL Cloud (Railway)

## Bước 1: Lấy Connection String từ Railway

1. Đăng nhập vào https://railway.app
2. Vào project PostgreSQL của bạn
3. Click tab **"Variables"**
4. Bạn sẽ thấy các biến:
   - `PGHOST`: containers-us-west-XXX.railway.app
   - `PGPORT`: 5432
   - `PGDATABASE`: railway
   - `PGUSER`: postgres
   - `PGPASSWORD`: <your-password>

## Bước 2: Tạo DATABASE_URL

Format:
```
postgresql://USERNAME:PASSWORD@HOST:PORT/DATABASE
```

Ví dụ:
```
postgresql://postgres:abc123xyz@containers-us-west-123.railway.app:5432/railway
```

## Bước 3: Cập nhật file .env

```bash
# Mở file .env và thay đổi dòng DATABASE_URL:

# Cũ (SQLite):
# DATABASE_URL=sqlite:///./chatbot.db

# Mới (PostgreSQL):
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@containers-us-west-XXX.railway.app:5432/railway
```

## Bước 4: Khởi động backend

```powershell
cd "g:\110122008\ChatBotAI\backend"
python main.py
```

Nếu thấy:
```
✅ Successfully connected to PostgreSQL cloud!
✅ PostgreSQL tables initialized successfully
INFO:     Uvicorn running on http://0.0.0.0:8000
```

→ **Thành công!** 🎉

## Bước 5: Test

1. Mở http://localhost:3000
2. Đăng ký tài khoản mới → Dữ liệu lưu trên Railway
3. Upload hóa đơn → Dữ liệu lưu trên Railway
4. Restart server → Dữ liệu vẫn còn ✅

## Lợi ích PostgreSQL Cloud

✅ **Chia sẻ dữ liệu:** Tất cả dev trong team dùng chung database
✅ **Không mất dữ liệu:** Restart server không ảnh hưởng
✅ **Backup tự động:** Railway tự backup
✅ **Clone dễ dàng:** Clone project → Cập nhật .env → Chạy ngay

## Team member khác sử dụng

```powershell
# Clone project
git clone <your-repo>
cd ChatBotAI/backend

# Tạo .env với Railway connection string
echo "DATABASE_URL=postgresql://postgres:password@host:port/railway" > .env

# Cài đặt dependencies
pip install -r requirements.txt

# Chạy backend (tự động kết nối Railway)
python main.py
```

## Troubleshooting

### Lỗi: "Failed to connect to PostgreSQL"
- Kiểm tra Railway database có đang chạy không
- Kiểm tra connection string trong .env có đúng không
- Kiểm tra firewall/network

### Lỗi: "DATABASE_URL not set"
- Tạo file .env trong folder backend
- Copy connection string từ Railway Variables tab
- Format: postgresql://user:pass@host:port/db

### Muốn quay lại SQLite
```bash
# Trong .env, đổi lại:
DATABASE_URL=sqlite:///./chatbot.db
```
