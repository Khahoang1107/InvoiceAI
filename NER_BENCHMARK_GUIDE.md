# NER Benchmarking System - Setup Guide

## Overview

The NER (Named Entity Recognition) Benchmarking System tracks model performance metrics over time, enabling systematic performance tracking and improvement verification for the Invoice NER system.

## Current Status

✅ **Baseline Benchmark Saved**

```
Model: Invoice NER v1 (v1.0)
Dataset: invoice
Saved: 2025-12-29T00:00:00

Overall Performance:
  - Precision: 93.9%
  - Recall: 92.7%
  - F1-Score: 93.3%

Entity Performance:
  - Mã hóa đơn: P=92.5%, R=91.0%, F1=91.7%
  - Ngày phát hành: P=94.0%, R=93.2%, F1=93.6%
  - Tổng tiền: P=95.1%, R=94.0%, F1=94.5%
```

## System Architecture

### Services

**`NERBenchmarkService`** (`backend/services/ner_benchmark_service.py`)
- Handles all benchmark lifecycle operations
- Stores data in JSONL format for easy appending
- Location: `logs/benchmarks/ner_benchmarks.jsonl`

**API Endpoints** (`backend/routers/admin.py`)
- `GET /api/admin/benchmarks/ner/latest` - Get latest benchmark
- `GET /api/admin/benchmarks/ner/all` - Get all historical benchmarks
- `GET /api/admin/benchmarks/ner/comparison` - Track improvements over time
- `GET /api/admin/benchmarks/ner/report` - Formatted report
- `GET /api/admin/benchmarks/ner/entity-summary` - Per-entity averages

### Data Storage

**File: `logs/benchmarks/ner_benchmarks.jsonl`**

Format: One JSON object per line (JSONL)

```json
{
  "timestamp": "2025-12-29T00:00:00",
  "model_name": "Invoice NER v1",
  "version": "1.0",
  "dataset": "invoice",
  "entities": {
    "Mã hóa đơn": {
      "precision": 92.5,
      "recall": 91.0,
      "f1": 91.7
    },
    "Ngày phát hành": {
      "precision": 94.0,
      "recall": 93.2,
      "f1": 93.6
    },
    "Tổng tiền": {
      "precision": 95.1,
      "recall": 94.0,
      "f1": 94.5
    }
  },
  "overall_metrics": {
    "precision": 93.9,
    "recall": 92.7,
    "f1": 93.3
  },
  "notes": "Baseline NER performance on invoice dataset"
}
```

## Usage Examples

### 1. Saving a New Benchmark

```python
from backend.services.ner_benchmark_service import NERBenchmarkService

service = NERBenchmarkService()

# When you train a new model, save the benchmark
service.save_ner_benchmark(
    model_name="Invoice NER v2",
    version="2.0",
    entities={
        "Mã hóa đơn": {"precision": 93.2, "recall": 92.1, "f1": 92.6},
        "Ngày phát hành": {"precision": 94.5, "recall": 94.0, "f1": 94.2},
        "Tổng tiền": {"precision": 95.8, "recall": 95.1, "f1": 95.4}
    },
    overall_metrics={"precision": 94.5, "recall": 93.7, "f1": 94.1},
    notes="Improved with additional training data"
)
```

### 2. Get Latest Benchmark

```python
latest = service.get_latest_ner_benchmark()
print(f"Latest model: {latest['model_name']} v{latest['version']}")
print(f"F1-Score: {latest['overall_metrics']['f1']}%")
```

### 3. View Improvement Tracking

```python
comparison = service.get_ner_benchmark_comparison()
for benchmark in comparison['benchmarks']:
    print(f"{benchmark['model']} v{benchmark['version']}: F1={benchmark['overall']['f1']}%")
```

### 4. Get Entity-Level Analysis

```python
summary = service.get_entity_performance_summary()
for entity, stats in summary.items():
    print(f"{entity}:")
    print(f"  Avg Precision: {stats['avg_precision']}%")
    print(f"  Avg Recall: {stats['avg_recall']}%")
    print(f"  Trend: {stats['trend']}")
```

### 5. Generate Report

```python
report = service.generate_ner_report()
print(report)
```

## API Usage Examples

### Get Latest Benchmark

```bash
curl http://localhost:8000/api/admin/benchmarks/ner/latest
```

Response:
```json
{
  "status": "ok",
  "data": {
    "timestamp": "2025-12-29T00:00:00",
    "model_name": "Invoice NER v1",
    "version": "1.0",
    "overall_metrics": {
      "precision": 93.9,
      "recall": 92.7,
      "f1": 93.3
    },
    ...
  }
}
```

### Get All Benchmarks (Historical)

```bash
curl http://localhost:8000/api/admin/benchmarks/ner/all
```

Response:
```json
{
  "status": "ok",
  "data": [
    { /* benchmark 1 */ },
    { /* benchmark 2 */ },
    { /* benchmark 3 */ }
  ],
  "count": 3
}
```

### Get Benchmark Comparison

```bash
curl http://localhost:8000/api/admin/benchmarks/ner/comparison
```

Response shows improvement trends and statistics.

### Get Entity Performance Summary

```bash
curl http://localhost:8000/api/admin/benchmarks/ner/entity-summary
```

Shows average metrics for each entity across all benchmarks.

### Get Formatted Report

```bash
curl http://localhost:8000/api/admin/benchmarks/ner/report
```

Returns formatted ASCII table report.

## Workflow

### Model Training & Benchmarking Cycle

1. **Train New Model**
   ```python
   # Your training code
   model = train_ner_model(data)
   ```

2. **Evaluate on Test Set**
   ```python
   # Your evaluation code
   metrics = evaluate_model(model, test_data)
   # metrics = {"precision": 94.5, "recall": 93.7, "f1": 94.1, ...}
   ```

3. **Extract Entity-Level Metrics**
   ```python
   entity_metrics = {
       "Mã hóa đơn": extract_entity_metrics("Mã hóa đơn"),
       "Ngày phát hành": extract_entity_metrics("Ngày phát hành"),
       "Tổng tiền": extract_entity_metrics("Tổng tiền")
   }
   ```

4. **Save Benchmark**
   ```python
   service.save_ner_benchmark(
       model_name="Invoice NER v2",
       version="2.0",
       entities=entity_metrics,
       overall_metrics=overall_metrics,
       notes="Description of improvements"
   )
   ```

5. **Review Progress**
   ```python
   comparison = service.get_ner_benchmark_comparison()
   # Check improvement percentage
   ```

## Testing

### Run Report Test

```bash
python test_ner_benchmark_report.py
```

Output shows:
- Formatted benchmark table
- Raw metric values
- Entity-level breakdown
- Baseline status or improvement trends

### Test Service Methods

```python
from backend.services.ner_benchmark_service import NERBenchmarkService

service = NERBenchmarkService()

# Test getting latest
latest = service.get_latest_ner_benchmark()
assert latest is not None

# Test getting all
all_benchmarks = service.get_all_ner_benchmarks()
assert len(all_benchmarks) >= 1

# Test generating report
report = service.generate_ner_report()
assert "Invoice NER v1" in report
```

## Integration Points

### With Admin Dashboard

The NER benchmarking endpoints are integrated into the admin API:
- Navigate to `/api/admin/benchmarks/ner/*` routes
- Can be displayed in admin dashboard for monitoring
- Real-time comparison views possible

### With Metrics System

The NER benchmarking is separate from the general metrics system but complementary:
- **Metrics System**: Tracks system-wide performance during chat operations
- **NER Benchmarking**: Tracks NER model quality on curated test sets
- Both accessible via `/api/admin/*` routes

## Key Metrics Explained

### Precision
"Of the entities the model identified as [Type], how many were correct?"
- Formula: `TP / (TP + FP)`
- Higher is better

### Recall
"Of the actual [Type] entities, how many did the model find?"
- Formula: `TP / (TP + FN)`
- Higher is better

### F1-Score
Harmonic mean of Precision and Recall
- Formula: `2 * (Precision * Recall) / (Precision + Recall)`
- Balances both metrics
- Range: 0-100%

### Current Baseline

| Entity | Precision | Recall | F1-Score |
|--------|-----------|--------|----------|
| Mã hóa đơn | 92.5% | 91.0% | 91.7% |
| Ngày phát hành | 94.0% | 93.2% | 93.6% |
| Tổng tiền | 95.1% | 94.0% | 94.5% |
| **Average** | **93.9%** | **92.7%** | **93.3%** |

## Next Steps

1. **Train improved models** and save benchmarks
2. **Monitor trends** via comparison endpoint
3. **Identify weak entities** from entity summary
4. **Implement improvements** and measure impact
5. **Track improvement percentage** over versions

## Files Involved

```
backend/
  services/
    ner_benchmark_service.py       # NER benchmark service
  routers/
    admin.py                        # API endpoints
  
logs/
  benchmarks/
    ner_benchmarks.jsonl            # Benchmark data storage

test_ner_benchmark_report.py        # Report generation test
```

## Troubleshooting

### "No NER benchmark found"
- Check `logs/benchmarks/ner_benchmarks.jsonl` exists
- Verify file has content
- Check file encoding (should be UTF-8)

### API Returns 404
- Ensure `NERBenchmarkService` is initialized in `admin.py`
- Check endpoint paths match documentation

### Encoding Issues
- Service now uses UTF-8 encoding explicitly
- Handles Vietnamese characters (Mã, Ngày, Tiền) properly

## Performance Targets

Based on baseline (v1.0):

| Milestone | Target | Timeline |
|-----------|--------|----------|
| v1.0 | Current (93.3% F1) | ✅ Baseline |
| v2.0 | 94.5% F1 | Q1 2025 |
| v3.0 | 95.5% F1 | Q2 2025 |
| v4.0 | 96.5% F1 | Q3 2025 |

Monitor progress via `/api/admin/benchmarks/ner/comparison`
