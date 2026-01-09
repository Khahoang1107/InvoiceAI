# Sơ đồ Pipeline với Confidence Threshold

## 1. Dual OCR Pipeline

```mermaid
flowchart TD
    A[📄 Hình ảnh hóa đơn] --> B[🔧 Image Preprocessing]
    B --> C[📝 Tesseract OCR]
    C --> D{Confidence ≥ 70%?}
    
    D -->|✅ Yes| E[Sử dụng kết quả Tesseract]
    D -->|❌ No| F[🧠 EasyOCR Processing]
    
    F --> G{So sánh kết quả}
    G --> H[Chọn kết quả tốt hơn]
    
    E --> I[📊 NER Extraction]
    H --> I
    
    I --> J{Field Confidence?}
    J -->|≥80%| K[✅ HIGH - Tự động xử lý]
    J -->|60-79%| L[⚠️ MEDIUM - Cần xem xét]
    J -->|<60%| M[❌ LOW - Yêu cầu review]
    
    K --> N[(💾 Lưu vào Database)]
    L --> N
    M --> O[👤 Manual Review]
    O --> N
    
    style A fill:#e1f5fe
    style D fill:#fff3e0
    style J fill:#fff3e0
    style K fill:#c8e6c9
    style L fill:#fff9c4
    style M fill:#ffcdd2
    style N fill:#e8f5e9
```

## 2. Chi tiết Confidence Thresholds

### OCR Level (Tesseract vs EasyOCR)

| Threshold | Hành động | Tỷ lệ trigger |
|-----------|-----------|---------------|
| **≥ 70%** | Dùng Tesseract (fast path) | 83% |
| **< 70%** | Trigger EasyOCR fallback | 17% |

### Field Extraction Level

| Confidence | Icon | Trạng thái | Hành động |
|------------|------|------------|-----------|
| **≥ 80%** | ✅ | HIGH | Tự động chấp nhận |
| **60-79%** | ⚠️ | MEDIUM | Cảnh báo, cần xem xét |
| **< 60%** | ❌ | LOW | Yêu cầu review thủ công |

## 3. End-to-End Pipeline với Confidence Scoring

```mermaid
flowchart LR
    subgraph INPUT["📥 Input"]
        A1[Image Upload]
    end
    
    subgraph OCR["🔍 OCR Processing"]
        B1[Tesseract] --> B2{Conf ≥70%?}
        B2 -->|No| B3[EasyOCR]
        B2 -->|Yes| B4[OCR Result]
        B3 --> B4
    end
    
    subgraph NER["🏷️ NER Extraction"]
        C1[Field Detection]
        C2[Confidence Scoring]
    end
    
    subgraph VALIDATION["✔️ Validation"]
        D1{Conf ≥80%}
        D2[Auto Accept]
        D3[Manual Review]
    end
    
    subgraph OUTPUT["📤 Output"]
        E1[(Database)]
        E2[User Response]
    end
    
    A1 --> B1
    B4 --> C1 --> C2
    C2 --> D1
    D1 -->|Yes| D2
    D1 -->|No| D3
    D2 --> E1
    D3 --> E1
    E1 --> E2
```

## 4. Confidence Score Calculation

```mermaid
flowchart TD
    A[Raw OCR Output] --> B[Field Extraction]
    
    B --> C1[invoice_code]
    B --> C2[buyer_name]
    B --> C3[seller_name]
    B --> C4[total_amount]
    B --> C5[invoice_date]
    
    C1 --> D1[Pattern Match Score]
    C2 --> D2[NER Entity Score]
    C3 --> D3[NER Entity Score]
    C4 --> D4[Number Format Score]
    C5 --> D5[Date Format Score]
    
    D1 --> E[Weighted Average]
    D2 --> E
    D3 --> E
    D4 --> E
    D5 --> E
    
    E --> F{Final Confidence}
    F --> G["0.0 - 1.0 Score"]
    
    style E fill:#e3f2fd
    style F fill:#fff3e0
```

## 5. RAG Pipeline Chi Tiết

### 5.1. RAG Indexing Pipeline (Khi Upload Hóa Đơn)

```mermaid
flowchart TD
    subgraph UPLOAD["📥 File Upload"]
        A1[Hình ảnh/PDF hóa đơn]
    end
    
    subgraph OCR["🔍 OCR Processing"]
        B1[Dual OCR]
        B2[Text Extraction]
        B3[NER Field Extraction]
    end
    
    subgraph RAG_INDEX["🧠 RAG Indexing"]
        C1[Content Synthesis]
        C2[Text Chunking]
        C3["Embedding Generation<br/>(all-MiniLM-L6-v2)"]
        C4["Vector Storage<br/>(Pinecone/ChromaDB)"]
    end
    
    subgraph STORAGE["💾 Storage"]
        D1[(SQL Database)]
        D2[(Vector Database)]
    end
    
    A1 --> B1 --> B2 --> B3
    B3 --> C1 --> C2 --> C3 --> C4
    B3 --> D1
    C4 --> D2
    
    style A1 fill:#e3f2fd
    style C3 fill:#fff3e0
    style D1 fill:#e8f5e9
    style D2 fill:#fce4ec
```

### 5.2. RAG Query Pipeline (Khi Tra Cứu/Chat)

```mermaid
flowchart TD
    A[💬 User Query] --> B["🔢 Query Embedding<br/>(all-MiniLM-L6-v2)"]
    B --> C["🔍 Vector Search<br/>(Pinecone/ChromaDB)"]
    
    C --> D{Similarity Score}
    
    D -->|"≥ 0.7 (High)"| E[📄 Retrieved Documents<br/>Top-K Results]
    D -->|"0.5-0.7 (Medium)"| F[📄 Partial Match<br/>Lower Priority]
    D -->|"< 0.5 (Low)"| G[❌ No Relevant Context]
    
    E --> H[Context Preparation]
    F --> H
    G --> I[Fallback: SQL Query]
    
    H --> J["🧠 Enhanced Prompt<br/>Query + Context"]
    I --> J
    
    J --> K["🤖 Groq LLM<br/>(mixtral-8x7b-32768)"]
    K --> L[💬 Intelligent Response]
    
    style A fill:#e8eaf6
    style D fill:#fff3e0
    style E fill:#c8e6c9
    style F fill:#fff9c4
    style G fill:#ffcdd2
    style L fill:#c8e6c9
```

### 5.3. RAG Hybrid Search Flow

```mermaid
flowchart LR
    subgraph QUERY["Query Processing"]
        Q1[User Question]
        Q2[Query Embedding]
    end
    
    subgraph SEARCH["Hybrid Search"]
        S1["Semantic Search<br/>(Vector Similarity)"]
        S2["Keyword Search<br/>(BM25/SQL LIKE)"]
        S3[Result Fusion]
    end
    
    subgraph RANKING["Re-ranking"]
        R1{Score Threshold}
        R2[Top-K Selection]
    end
    
    subgraph OUTPUT["Context Output"]
        O1[Relevant Invoices]
        O2[Context for LLM]
    end
    
    Q1 --> Q2
    Q2 --> S1
    Q1 --> S2
    S1 --> S3
    S2 --> S3
    S3 --> R1
    R1 -->|≥0.7| R2
    R2 --> O1 --> O2
    
    style Q1 fill:#e8eaf6
    style R1 fill:#fff3e0
    style O2 fill:#c8e6c9
```

## 6. Kết quả thực tế

```
📊 Production Statistics (30 days)

OCR Processing:
├─ Total invoices:        8,547
├─ Tesseract only:       7,124 (83.4%)  ✅ Confidence ≥70%
├─ EasyOCR triggered:    1,423 (16.6%)  ⚠️ Confidence <70%
│  └─ Improved result:   1,178 (82.8%)
└─ Manual correction:      127 (1.5%)   ❌ Confidence <60%

Accuracy Metrics:
✅ CAR (Character Accuracy Rate): 97.3%
✅ Full automation rate:          98.5%
✅ Average processing time:       2.15s
```

---

**Threshold Configuration:**
- OCR Fallback Threshold: `70%`
- High Confidence: `≥80%`
- Medium Confidence: `60-79%`
- Low Confidence: `<60%`
- RAG Similarity Threshold: `0.7`
