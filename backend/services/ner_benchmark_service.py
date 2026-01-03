"""
NER Benchmark Storage & Reporting
Lưu trữ và báo cáo performance metrics của NER (Named Entity Recognition) system
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional


class NERBenchmarkService:
    """Track NER model performance benchmarks"""

    def __init__(self):
        self.benchmark_dir = Path("logs/benchmarks")
        self.benchmark_dir.mkdir(parents=True, exist_ok=True)
        self.ner_benchmark_file = self.benchmark_dir / "ner_benchmarks.jsonl"

    def save_ner_benchmark(
        self,
        model_name: str,
        version: str,
        entities: Dict[str, Dict[str, float]],  # {entity_type: {precision, recall, f1}}
        overall_metrics: Dict[str, float],  # {precision, recall, f1}
        dataset: str = "invoice",
        notes: Optional[str] = None
    ):
        """
        Lưu NER benchmark results
        
        Args:
            model_name: Tên model (e.g., "SpaCy NER", "BERT NER")
            version: Version (e.g., "1.0", "1.1")
            entities: Dict của từng entity type với precision/recall/f1
            overall_metrics: Overall precision/recall/f1
            dataset: Dataset used (default: invoice)
            notes: Additional notes
        
        Example:
            >>> benchmark_service.save_ner_benchmark(
            ...     model_name="Invoice NER v1",
            ...     version="1.0",
            ...     entities={
            ...         "Mã hóa đơn": {"precision": 92.5, "recall": 91.0, "f1": 91.7},
            ...         "Ngày phát hành": {"precision": 94.0, "recall": 93.2, "f1": 93.6},
            ...         "Tổng tiền": {"precision": 95.1, "recall": 94.0, "f1": 94.5}
            ...     },
            ...     overall_metrics={"precision": 93.9, "recall": 92.7, "f1": 93.3}
            ... )
        """
        benchmark = {
            "timestamp": datetime.utcnow().isoformat(),
            "model_name": model_name,
            "version": version,
            "dataset": dataset,
            "entities": entities,
            "overall_metrics": overall_metrics,
            "notes": notes
        }

        try:
            with open(self.ner_benchmark_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(benchmark, ensure_ascii=False) + '\n')
            print(f"✅ Benchmark saved: {model_name} v{version}")
            return benchmark
        except Exception as e:
            print(f"❌ Failed to save benchmark: {e}")
            return None

    def get_latest_ner_benchmark(self) -> Optional[Dict[str, Any]]:
        """Get latest NER benchmark"""
        if not self.ner_benchmark_file.exists():
            return None

        try:
            with open(self.ner_benchmark_file, 'r', encoding='utf-8') as f:
                benchmarks = [json.loads(line) for line in f.readlines() if line.strip()]
            return benchmarks[-1] if benchmarks else None
        except Exception as e:
            print(f"Error reading benchmark: {e}")
            return None

    def get_all_ner_benchmarks(self) -> List[Dict[str, Any]]:
        """Get all NER benchmarks"""
        if not self.ner_benchmark_file.exists():
            return []

        try:
            with open(self.ner_benchmark_file, 'r', encoding='utf-8') as f:
                return [json.loads(line) for line in f.readlines() if line.strip()]
        except Exception as e:
            print(f"Error reading benchmarks: {e}")
            return []

    def get_ner_benchmark_comparison(self) -> Dict[str, Any]:
        """
        Get comparison of all NER benchmarks
        Useful for tracking improvement over time
        """
        benchmarks = self.get_all_ner_benchmarks()

        if not benchmarks:
            return {"status": "no_benchmarks"}

        comparison = {
            "total_benchmarks": len(benchmarks),
            "benchmarks": []
        }

        for benchmark in benchmarks:
            comparison["benchmarks"].append({
                "timestamp": benchmark.get("timestamp"),
                "model": benchmark.get("model_name"),
                "version": benchmark.get("version"),
                "overall": benchmark.get("overall_metrics"),
                "entities": benchmark.get("entities")
            })

        # Calculate improvement from first to latest
        if len(benchmarks) > 1:
            first = benchmarks[0].get("overall_metrics", {})
            latest = benchmarks[-1].get("overall_metrics", {})

            comparison["improvement"] = {
                "precision_improvement": latest.get("precision", 0) - first.get("precision", 0),
                "recall_improvement": latest.get("recall", 0) - first.get("recall", 0),
                "f1_improvement": latest.get("f1", 0) - first.get("f1", 0)
            }

        return comparison

    def get_entity_performance_summary(self) -> Dict[str, Dict[str, float]]:
        """
        Get average performance for each entity type across all benchmarks
        """
        benchmarks = self.get_all_ner_benchmarks()

        if not benchmarks:
            return {}

        entity_stats = {}

        for benchmark in benchmarks:
            entities = benchmark.get("entities", {})
            for entity_name, metrics in entities.items():
                if entity_name not in entity_stats:
                    entity_stats[entity_name] = {
                        "precision": [],
                        "recall": [],
                        "f1": []
                    }

                entity_stats[entity_name]["precision"].append(metrics.get("precision", 0))
                entity_stats[entity_name]["recall"].append(metrics.get("recall", 0))
                entity_stats[entity_name]["f1"].append(metrics.get("f1", 0))

        # Calculate averages
        result = {}
        for entity_name, metrics in entity_stats.items():
            result[entity_name] = {
                "avg_precision": sum(metrics["precision"]) / len(metrics["precision"]),
                "avg_recall": sum(metrics["recall"]) / len(metrics["recall"]),
                "avg_f1": sum(metrics["f1"]) / len(metrics["f1"]),
                "benchmarks_count": len(metrics["precision"])
            }

        return result

    def generate_ner_report(self) -> str:
        """
        Generate formatted NER benchmark report
        """
        latest = self.get_latest_ner_benchmark()

        if not latest:
            return "No NER benchmarks found"

        report = f"""
╔════════════════════════════════════════════════════════╗
║          NER BENCHMARK REPORT                          ║
╚════════════════════════════════════════════════════════╝

Model: {latest.get('model_name')}
Version: {latest.get('version')}
Dataset: {latest.get('dataset')}
Timestamp: {latest.get('timestamp')}

┌─────────────────────────────────────────────────────┐
│ ENTITY PERFORMANCE METRICS                           │
├──────────────────┬───────────┬────────┬────────────┤
│ Entity Type      │ Precision │ Recall │ F1-Score   │
├──────────────────┼───────────┼────────┼────────────┤
"""

        entities = latest.get("entities", {})
        for entity_name, metrics in entities.items():
            precision = metrics.get("precision", 0)
            recall = metrics.get("recall", 0)
            f1 = metrics.get("f1", 0)
            report += f"│ {entity_name:<16} │ {precision:>7.1f}% │ {recall:>6.1f}% │ {f1:>8.1f}%   │\n"

        # Overall metrics
        overall = latest.get("overall_metrics", {})
        precision = overall.get("precision", 0)
        recall = overall.get("recall", 0)
        f1 = overall.get("f1", 0)

        report += f"""├──────────────────┼───────────┼────────┼────────────┤
│ **Trung bình**   │ {precision:>7.1f}% │ {recall:>6.1f}% │ {f1:>8.1f}%   │
└──────────────────┴───────────┴────────┴────────────┘
"""

        # Notes
        notes = latest.get("notes")
        if notes:
            report += f"\nNotes: {notes}\n"

        return report

    def compare_benchmarks(self, benchmark1_idx: int, benchmark2_idx: int) -> Dict[str, Any]:
        """
        Compare two benchmarks and show improvement
        """
        benchmarks = self.get_all_ner_benchmarks()

        if len(benchmarks) < 2:
            return {"status": "not_enough_benchmarks"}

        b1 = benchmarks[benchmark1_idx]
        b2 = benchmarks[benchmark2_idx]

        comparison = {
            "benchmark1": {
                "model": b1.get("model_name"),
                "version": b1.get("version"),
                "metrics": b1.get("overall_metrics")
            },
            "benchmark2": {
                "model": b2.get("model_name"),
                "version": b2.get("version"),
                "metrics": b2.get("overall_metrics")
            },
            "improvement": {
                "precision": (b2.get("overall_metrics", {}).get("precision", 0) - 
                             b1.get("overall_metrics", {}).get("precision", 0)),
                "recall": (b2.get("overall_metrics", {}).get("recall", 0) - 
                          b1.get("overall_metrics", {}).get("recall", 0)),
                "f1": (b2.get("overall_metrics", {}).get("f1", 0) - 
                      b1.get("overall_metrics", {}).get("f1", 0))
            }
        }

        return comparison
