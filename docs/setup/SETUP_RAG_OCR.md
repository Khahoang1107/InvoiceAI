# 🚀 HƯỚNG DẪN SETUP RAG + OCR ĐẦY ĐỦ

## 📋 TỔNG QUAN
Hướng dẫn này sẽ giúp bạn setup:
1. ✅ Pinecone RAG (Vector Database)
2. ✅ Tesseract OCR (Text Recognition)
3. ✅ EasyOCR (Deep Learning OCR)
4. ✅ Embedding Service (Sentence Transformers)

**Thời gian ước tính:** 15-20 phút

---

## 1️⃣ SETUP PINECONE RAG

### Bước 1: Tạo tài khoản Pinecone (FREE)

1. Truy cập: https://www.pinecone.io/
2. Click "Start Free"
3. Đăng ký với email (hoặc Google/GitHub)
4. Xác nhận email

### Bước 2: Lấy API Key

1. Đăng nhập vào Pinecone Console: https://app.pinecone.io/
2. Vào **API Keys** (menu bên trái)
3. Copy API Key (dạng: `pcsk_xxx...`)
4. Copy Environment (thường là: `us-east-1-aws` hoặc `gcp-starter`)

### Bước 3: Tạo Index

1. Trong Pinecone Console, click **Indexes**
2. Click **Create Index**
3. Điền thông tin:
   - **Name**: `invoiceai-vectors`
   - **Dimensions**: `384` (cho all-MiniLM-L6-v2 model)
   - **Metric**: `cosine`
   - **Cloud**: `AWS` hoặc `GCP` (free tier)
4. Click **Create Index**
5. Đợi index được tạo (1-2 phút)

### Bước 4: Cấu hình trong .env

Mở file `.env` và thêm/cập nhật:

```env
# Pinecone Vector Database
PINECONE_API_KEY=pcsk_YOUR_API_KEY_HERE
PINECONE_ENVIRONMENT=us-east-1-aws
PINECONE_INDEX_NAME=invoiceai-vectors
```

### Bước 5: Cài đặt dependencies

```bash
cd backend
pip install pinecone-client sentence-transformers
```

---

## 2️⃣ SETUP TESSERACT OCR

### Bước 1: Download Tesseract

**Windows:**
1. Download installer: https://github.com/UB-Mannheim/tesseract/wiki
2. Chọn: `tesseract-ocr-w64-setup-5.3.3.20231005.exe` (latest version)
3. Chạy installer
4. **QUAN TRỌNG**: Chọn cài đặt language packs:
   - ✅ English
   - ✅ Vietnamese (vie)
   - ✅ Additional languages nếu cần

### Bước 2: Cấu hình PATH

Mặc định Tesseract cài vào: `C:\Program Files\Tesseract-OCR\tesseract.exe`

Thêm vào file `.env`:

```env
# Tesseract OCR Path
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
```

### Bước 3: Cài đặt Python wrapper

```bash
pip install pytesseract Pillow
```

### Bước 4: Test Tesseract

```bash
tesseract --version
```

Nếu thành công sẽ hiển thị version info.

---

## 3️⃣ FIX EASYOCR (NumPy Compatibility)

### Vấn đề hiện tại:
- NumPy 2.x không tương thích với opencv-python hiện tại
- EasyOCR cần NumPy 1.x

### Giải pháp:

#### Option 1: Downgrade NumPy (KHUYẾN NGHỊ)

```bash
pip uninstall numpy -y
pip install "numpy<2.0" --no-cache-dir
```

#### Option 2: Upgrade OpenCV (Nếu Option 1 không work)

```bash
pip uninstall opencv-python opencv-python-headless -y
pip install opencv-python-headless
pip install easyocr
```

### Cài đặt EasyOCR

```bash
pip install easyocr
```

---

## 4️⃣ SETUP EMBEDDING SERVICE

### Cài đặt Sentence Transformers

```bash
pip install sentence-transformers
```

Model sẽ tự động download khi chạy lần đầu (~80MB).

---

## 5️⃣ UPDATE CODE

### File: backend/services/ocr_service.py

**Bỏ comment dòng này để enable EasyOCR:**

Tìm dòng:
```python
logger.warning("EasyOCR disabled due to NumPy compatibility issues")
return False
```

Thay bằng:
```python
# Try to import and initialize EasyOCR
import easyocr
reader = easyocr.Reader(['en', 'vi'], gpu=False, verbose=False)
logger.info("EasyOCR initialized successfully")
return True
```

### File: .env (HOÀN CHỈNH)

```env
# Database
DATABASE_URL=sqlite:///./chatbot.db

# Security
SECRET_KEY=your-super-secret-key-change-this-in-production-make-it-long-and-random
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Groq AI
GROQ_API_KEY=your-groq-api-key-here
GROQ_MODEL=llama-3.1-8b-instant

# Pinecone Vector Database
PINECONE_API_KEY=pcsk_YOUR_API_KEY_HERE
PINECONE_ENVIRONMENT=us-east-1-aws
PINECONE_INDEX_NAME=invoiceai-vectors

# Tesseract OCR
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe

# File Upload
UPLOAD_DIR=uploads
MAX_FILE_SIZE=10485760
```

---

## 6️⃣ KHỞI ĐỘNG LẠI HỆ THỐNG

### Backend:

```bash
cd backend
python run.py
```

**Kiểm tra log:**
- ✅ `Tesseract available: True`
- ✅ `EasyOCR available: True`
- ✅ `RAG components initialized`

### Frontend:

```bash
cd frontend
npm run dev
```

---

## 7️⃣ TEST HỆ THỐNG

### Test OCR:

1. Upload một ảnh hóa đơn
2. Kiểm tra log backend có `✅ OCR processed successfully`
3. Xem kết quả extraction

### Test RAG:

```python
# Chạy trong backend directory
python test_rag_system.py
```

### Test Chat với Database:

1. Hỏi: "Tổng tiền hóa đơn tháng này?"
2. Kiểm tra log: `Detected intent: data_query`
3. Kiểm tra response có số liệu từ database

---

## 🎯 CHECKLIST HOÀN THÀNH

- [ ] Pinecone account created
- [ ] Pinecone API key added to .env
- [ ] Pinecone index created (384 dimensions)
- [ ] `pinecone-client` installed
- [ ] `sentence-transformers` installed
- [ ] Tesseract downloaded & installed
- [ ] Tesseract path configured in .env
- [ ] `pytesseract` installed
- [ ] NumPy downgraded to <2.0
- [ ] `easyocr` installed successfully
- [ ] OCR service code updated
- [ ] Backend restart successful
- [ ] All services showing as available

---

## 🐛 TROUBLESHOOTING

### Lỗi: "Pinecone not installed"
```bash
pip install pinecone-client
```

### Lỗi: "Tesseract not found"
- Kiểm tra path trong .env đúng
- Chạy `tesseract --version` trong cmd
- Thử restart terminal

### Lỗi: "NumPy compatibility"
```bash
pip uninstall numpy opencv-python easyocr -y
pip install "numpy<2.0"
pip install opencv-python-headless easyocr
```

### Lỗi: "Index not found in Pinecone"
- Đảm bảo index name trong .env khớp với Pinecone Console
- Đợi index fully initialized (có thể mất 2-3 phút)

---

## 📚 TÀI LIỆU THAM KHẢO

- Pinecone Docs: https://docs.pinecone.io/
- Tesseract Wiki: https://github.com/tesseract-ocr/tesseract/wiki
- EasyOCR: https://github.com/JaidedAI/EasyOCR
- Sentence Transformers: https://www.sbert.net/

---

## 💡 NOTES

- **Pinecone Free Tier**: 1 index, 100k vectors, đủ cho development
- **Tesseract**: Support 100+ languages, tốt cho văn bản rõ ràng
- **EasyOCR**: Deep learning, tốt cho chữ viết tay và ảnh kém chất lượng
- **RAG**: Cần training data (upload hóa đơn) để có kết quả tốt

---

## ✅ HOÀN THÀNH!

Sau khi làm xong các bước trên, hệ thống sẽ có:
- 🧠 RAG với Pinecone (tìm kiếm semantic)
- 📸 Tesseract OCR (text recognition)
- 🎨 EasyOCR (deep learning OCR)
- 💬 Smart chatbot (intent detection + database query)

**Chúc bạn thành công!** 🎉
