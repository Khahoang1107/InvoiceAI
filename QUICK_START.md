# Quick Start Guide - InvoiceAI

## Lần đầu mở project

### 1. Setup Python 3.12 (one-time)
```bash
cd backend
setup_py312.bat
```

Hoặc thủ công:
```bash
py -3.12 -m venv venv312
venv312\Scripts\activate
pip install -r requirements_py312.txt
python train_ner_quick.py
```

---

## Mỗi lần chạy lại

### Backend (Python 3.12 + NER)
```bash
cd backend
start_py312.bat
```

Hoặc thủ công:
```bash
cd backend
venv312\Scripts\activate
python main_refactored.py
```

Backend: http://localhost:8000

### Frontend (Terminal khác)
```bash
cd frontend
npm install  # lần đầu
npm run dev
```

Frontend: http://localhost:5173

---

## Kiểm tra môi trường

```bash
cd backend
venv312\Scripts\activate
python --version  # Should be 3.12.x
python -c "import spacy; print('spaCy OK')"
python -c "import spacy; nlp=spacy.load('models/invoice_ner'); print('NER OK')"
```

---

## Cấu trúc thư mục

```
InvoiceAI/
├── backend/
│   ├── venv312/          ← Python 3.12 environment
│   ├── models/
│   │   └── invoice_ner/  ← Trained NER model
│   ├── setup_py312.bat   ← Setup script
│   ├── start_py312.bat   ← Start script
│   └── main_refactored.py
├── frontend/
│   └── src/
└── .env                  ← Configuration
```

---

## Nếu gặp lỗi

### Backend không chạy
```bash
# Check port 8000
netstat -ano | findstr :8000
taskkill /PID <pid> /F

# Restart
cd backend
start_py312.bat
```

### NER không hoạt động
```bash
cd backend
venv312\Scripts\activate
python train_ner_quick.py
```

### Module not found
```bash
venv312\Scripts\activate
pip install <module_name>
```

---

## Tóm tắt các lệnh

| Mục đích | Lệnh |
|----------|------|
| **Setup lần đầu** | `cd backend && setup_py312.bat` |
| **Start backend** | `cd backend && start_py312.bat` |
| **Start frontend** | `cd frontend && npm run dev` |
| **Train NER** | `cd backend && venv312\Scripts\activate && python train_ner_quick.py` |
| **Check Python** | `venv312\Scripts\activate && python --version` |

---

## URLs quan trọng

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- OpenAPI: http://localhost:8000/openapi.json

---

## Environment cần thiết

Kiểm tra file `.env` có đủ:
- ✅ `GROQ_API_KEY` - AI chatbot
- ✅ `PINECONE_API_KEY` - Vector database
- ✅ `TESSERACT_CMD` - OCR engine path
- ✅ `DATABASE_URL` - PostgreSQL connection

Xem chi tiết: [PYTHON312_SETUP.md](../PYTHON312_SETUP.md)
