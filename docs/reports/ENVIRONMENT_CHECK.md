# Environment Verification Checklist

Run these commands to verify your setup is correct.

## 1. Check Python 3.12 Installation

```bash
py -3.12 --version
# Expected: Python 3.12.0 or higher
```

## 2. Check Virtual Environment

```bash
cd backend
dir venv312\Scripts\python.exe
# Should exist
```

## 3. Activate and Verify Packages

```bash
cd backend
venv312\Scripts\activate

# Check Python version in venv
python --version
# Expected: Python 3.12.x

# Check critical packages
python -c "import fastapi; print('FastAPI:', fastapi.__version__)"
python -c "import spacy; print('spaCy:', spacy.__version__)"
python -c "import pytesseract; print('pytesseract: OK')"
python -c "import groq; print('Groq: OK')"
python -c "import pinecone; print('Pinecone: OK')"
```

## 4. Check NER Model

```bash
cd backend
venv312\Scripts\activate

python -c "import spacy; nlp = spacy.load('models/invoice_ner'); print('NER Model: ✅ Loaded')"

# List entity types
python -c "import json; print(json.load(open('models/invoice_ner/entity_labels.json', encoding='utf-8')))"
```

## 5. Verify Environment Variables

```bash
# Check .env file exists
dir .env

# Verify critical keys (PowerShell)
Get-Content .env | Select-String "GROQ_API_KEY"
Get-Content .env | Select-String "PINECONE_API_KEY"
Get-Content .env | Select-String "TESSERACT_CMD"
```

## 6. Test Backend Startup

```bash
cd backend
start_py312.bat

# Backend should start on http://localhost:8000
# Check logs for:
# - ✅ NER service initialized
# - ✅ Tesseract available: True
# - ✅ Database connection established
```

## 7. Test API Endpoints

Open browser:
- http://localhost:8000/docs - Should show FastAPI docs
- http://localhost:8000/health - Should return {"status":"healthy"}

## 8. Test Frontend

```bash
cd frontend
npm install
npm run dev

# Frontend should start on http://localhost:5173
```

## 9. Full Integration Test

1. Start backend: `cd backend && start_py312.bat`
2. Start frontend: `cd frontend && npm run dev`
3. Login with test user
4. Upload invoice image
5. Check OCR extraction with NER entities
6. Chat with AI about the invoice

---

## Expected Results

### Backend Logs (with Python 3.12)
```
✅ NER service initialized - will use trained model for entity extraction
Tesseract available: True
NER available: True
Starting server on http://0.0.0.0:8000
```

### OCR Response (with NER)
```json
{
  "extracted_fields": {
    "invoice_number": "HD123456",
    "total_amount": "1.500.000",
    "currency": "VND",
    "date": "25/12/2024",
    "vendor_name": "Công ty ABC"
  },
  "confidence": 0.85,
  "ner_entities": [
    {"text": "HD123456", "label": "INVOICE_NUMBER"},
    {"text": "1.500.000", "label": "AMOUNT"}
  ]
}
```

---

## Troubleshooting

### ❌ "Python 3.12 not found"
→ Install from https://www.python.org/downloads/release/python-3120/

### ❌ "spaCy not installed"
→ `venv312\Scripts\activate && pip install spacy pyvi`

### ❌ "NER Model not found"
→ `cd backend && venv312\Scripts\activate && python train_ner_quick.py`

### ❌ "Module not found"
→ `venv312\Scripts\activate && pip install -r requirements_py312.txt`

### ❌ "Port 8000 already in use"
→ `netstat -ano | findstr :8000` then `taskkill /PID <pid> /F`

---

## Success Criteria

✅ Python 3.12 activated
✅ All packages installed
✅ NER model loaded
✅ Backend starts without errors
✅ Frontend runs on port 5173
✅ Can upload and process invoice
✅ OCR extracts fields with high confidence
✅ AI chatbot responds to queries

**If all checks pass, your environment is ready! 🎉**
