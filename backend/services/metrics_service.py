"""
Metrics Tracking Service
Ghi nhận và phân tích chất lượng retrieval, function calling, và response quality
"""

import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
from pathlib import Path

logger = logging.getLogger(__name__)


class MetricsService:
    """Track system performance metrics"""

    def __init__(self):
        self.metrics_file = Path("logs/metrics.jsonl")
        self.metrics_file.parent.mkdir(parents=True, exist_ok=True)
        self.session_metrics = defaultdict(list)

    def log_retrieval_metrics(
        self,
        user_id: int,
        query: str,
        retrieved_count: int,
        top_k: int,
        relevant_count: Optional[int] = None,
        scores: Optional[List[float]] = None
    ):
        """
        Ghi nhận metrics cho retrieval từ vector store
        
        Args:
            user_id: User ID
            query: Query string
            retrieved_count: Số kết quả được retrieve
            top_k: K value (top K results)
            relevant_count: Số kết quả relevant (tùy chọn, dùng nếu có feedback)
            scores: List similarity scores
        """
        metric = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": "retrieval",
            "user_id": user_id,
            "query": query,
            "retrieved_count": retrieved_count,
            "top_k": top_k,
            "relevant_count": relevant_count,
            "avg_score": sum(scores) / len(scores) if scores else None,
            "max_score": max(scores) if scores else None,
            "min_score": min(scores) if scores else None,
        }
        
        # Tính Precision@K (nếu có relevant count)
        if relevant_count is not None:
            metric["precision_at_k"] = min(relevant_count, top_k) / top_k
        
        self._save_metric(metric)
        logger.info(f"📊 Retrieval: top_k={top_k}, retrieved={retrieved_count}, "
                   f"avg_score={metric['avg_score']:.2f if metric['avg_score'] else 'N/A'}")

    def log_function_calling_metrics(
        self,
        user_id: int,
        tool_name: str,
        tool_args: Dict[str, Any],
        success: bool,
        execution_time: float,
        result_count: Optional[int] = None,
        error: Optional[str] = None
    ):
        """
        Ghi nhận metrics cho Groq function calling
        
        Args:
            user_id: User ID
            tool_name: Tên function được gọi
            tool_args: Arguments truyền vào
            success: Có thành công không
            execution_time: Thời gian thực hiện (ms)
            result_count: Số kết quả trả về
            error: Error message nếu có
        """
        metric = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": "function_calling",
            "user_id": user_id,
            "tool_name": tool_name,
            "tool_args": tool_args,
            "success": success,
            "execution_time_ms": execution_time,
            "result_count": result_count,
            "error": error,
        }
        
        self._save_metric(metric)
        status = "✅" if success else "❌"
        logger.info(f"{status} Function: {tool_name}, Time: {execution_time:.2f}ms, "
                   f"Results: {result_count}")

    def log_response_quality_metrics(
        self,
        user_id: int,
        conversation_id: str,
        intent_type: str,
        intent_confidence: float,
        used_database: bool,
        used_retrieval: bool,
        used_function_calling: bool,
        response_length: int,
        tokens_used: int,
        execution_time: float
    ):
        """
        Ghi nhận metrics cho response quality
        
        Args:
            user_id: User ID
            conversation_id: Conversation ID
            intent_type: Loại intent được detect
            intent_confidence: Độ tin cậy của intent detection
            used_database: Có dùng database không
            used_retrieval: Có dùng retrieval không
            used_function_calling: Có gọi function không
            response_length: Độ dài response
            tokens_used: Số tokens sử dụng
            execution_time: Tổng thời gian xử lý
        """
        metric = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": "response_quality",
            "user_id": user_id,
            "conversation_id": conversation_id,
            "intent_type": intent_type,
            "intent_confidence": intent_confidence,
            "pipeline": {
                "used_database": used_database,
                "used_retrieval": used_retrieval,
                "used_function_calling": used_function_calling,
            },
            "response_length": response_length,
            "tokens_used": tokens_used,
            "execution_time_ms": execution_time,
            "efficiency_score": self._calculate_efficiency_score(
                tokens_used, execution_time, response_length
            ),
        }
        
        self._save_metric(metric)
        logger.info(f"📈 Response: intent={intent_type} ({intent_confidence:.2f}), "
                   f"tokens={tokens_used}, time={execution_time:.2f}ms, "
                   f"efficiency={metric['efficiency_score']:.2f}")

    def log_user_feedback(
        self,
        user_id: int,
        conversation_id: str,
        tool_name: Optional[str],
        feedback: str,  # "good", "bad", "partial"
        comment: Optional[str] = None
    ):
        """
        Ghi nhận user feedback (thumbs up/down)
        
        Args:
            user_id: User ID
            conversation_id: Conversation ID
            tool_name: Nếu feedback là cho function result
            feedback: "good", "bad", "partial"
            comment: Bình luận của user
        """
        metric = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": "user_feedback",
            "user_id": user_id,
            "conversation_id": conversation_id,
            "tool_name": tool_name,
            "feedback": feedback,
            "comment": comment,
        }
        
        self._save_metric(metric)
        logger.info(f"👤 Feedback: {feedback} on {tool_name if tool_name else 'response'}")

    def get_metrics_summary(self, hours: int = 24) -> Dict[str, Any]:
        """
        Lấy tóm tắt metrics trong khoảng thời gian
        
        Args:
            hours: Số giờ quay lại từ hiện tại
            
        Returns:
            Dict với thống kê metrics
        """
        cutoff_time = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
        metrics = self._read_recent_metrics(cutoff_time)

        if not metrics:
            return {
                "period_hours": hours,
                "total_events": 0,
                "message": "No metrics found in this period"
            }

        summary = {
            "period_hours": hours,
            "total_events": len(metrics),
            "retrieval": self._summarize_retrieval(metrics),
            "function_calling": self._summarize_function_calling(metrics),
            "response_quality": self._summarize_response_quality(metrics),
            "user_feedback": self._summarize_user_feedback(metrics),
        }

        return summary

    def get_performance_report(self) -> Dict[str, Any]:
        """
        Tạo performance report chi tiết
        """
        all_metrics = self._read_all_metrics()

        if not all_metrics:
            return {"status": "no_data"}

        # Group by tool
        tool_stats = defaultdict(list)
        for m in all_metrics:
            if m.get("type") == "function_calling":
                tool_name = m.get("tool_name")
                tool_stats[tool_name].append(m)

        report = {
            "generated_at": datetime.utcnow().isoformat(),
            "total_metrics": len(all_metrics),
            "tools": {}
        }

        for tool_name, metrics in tool_stats.items():
            successful = sum(1 for m in metrics if m.get("success", False))
            failed = len(metrics) - successful
            execution_times = [m.get("execution_time_ms", 0) for m in metrics]

            report["tools"][tool_name] = {
                "calls": len(metrics),
                "successful": successful,
                "failed": failed,
                "success_rate": successful / len(metrics) if metrics else 0,
                "avg_execution_time_ms": sum(execution_times) / len(execution_times) if execution_times else 0,
                "min_execution_time_ms": min(execution_times) if execution_times else 0,
                "max_execution_time_ms": max(execution_times) if execution_times else 0,
            }

        return report

    def _save_metric(self, metric: Dict[str, Any]):
        """Lưu metric vào file JSONL"""
        try:
            with open(self.metrics_file, 'a') as f:
                f.write(json.dumps(metric) + '\n')
        except Exception as e:
            logger.error(f"Failed to save metric: {e}")

    def _read_recent_metrics(self, after_timestamp: str) -> List[Dict]:
        """Đọc metrics sau một timestamp"""
        metrics = []
        if not self.metrics_file.exists():
            return metrics

        try:
            with open(self.metrics_file, 'r') as f:
                for line in f:
                    try:
                        metric = json.loads(line)
                        if metric.get("timestamp", "") >= after_timestamp:
                            metrics.append(metric)
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            logger.error(f"Failed to read metrics: {e}")

        return metrics

    def _read_all_metrics(self) -> List[Dict]:
        """Đọc tất cả metrics"""
        metrics = []
        if not self.metrics_file.exists():
            return metrics

        try:
            with open(self.metrics_file, 'r') as f:
                for line in f:
                    try:
                        metric = json.loads(line)
                        metrics.append(metric)
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            logger.error(f"Failed to read metrics: {e}")

        return metrics

    def _summarize_retrieval(self, metrics: List[Dict]) -> Dict[str, Any]:
        """Tóm tắt retrieval metrics"""
        retrieval_metrics = [m for m in metrics if m.get("type") == "retrieval"]

        if not retrieval_metrics:
            return {"total": 0}

        scores = [m.get("avg_score") for m in retrieval_metrics if m.get("avg_score")]
        precisions = [m.get("precision_at_k") for m in retrieval_metrics if m.get("precision_at_k")]

        return {
            "total": len(retrieval_metrics),
            "avg_score": sum(scores) / len(scores) if scores else None,
            "avg_precision_at_k": sum(precisions) / len(precisions) if precisions else None,
            "retrieval_events": retrieval_metrics,
        }

    def _summarize_function_calling(self, metrics: List[Dict]) -> Dict[str, Any]:
        """Tóm tắt function calling metrics"""
        function_metrics = [m for m in metrics if m.get("type") == "function_calling"]

        if not function_metrics:
            return {"total": 0}

        successful = sum(1 for m in function_metrics if m.get("success", False))
        failed = len(function_metrics) - successful

        execution_times = [m.get("execution_time_ms", 0) for m in function_metrics]

        return {
            "total": len(function_metrics),
            "successful": successful,
            "failed": failed,
            "success_rate": successful / len(function_metrics) if function_metrics else 0,
            "avg_execution_time_ms": sum(execution_times) / len(execution_times) if execution_times else 0,
            "tools_called": list(set(m.get("tool_name") for m in function_metrics if m.get("tool_name"))),
        }

    def _summarize_response_quality(self, metrics: List[Dict]) -> Dict[str, Any]:
        """Tóm tắt response quality metrics"""
        quality_metrics = [m for m in metrics if m.get("type") == "response_quality"]

        if not quality_metrics:
            return {"total": 0}

        tokens = [m.get("tokens_used", 0) for m in quality_metrics]
        execution_times = [m.get("execution_time_ms", 0) for m in quality_metrics]
        efficiency_scores = [m.get("efficiency_score", 0) for m in quality_metrics]

        return {
            "total": len(quality_metrics),
            "avg_tokens_used": sum(tokens) / len(tokens) if tokens else 0,
            "avg_execution_time_ms": sum(execution_times) / len(execution_times) if execution_times else 0,
            "avg_efficiency_score": sum(efficiency_scores) / len(efficiency_scores) if efficiency_scores else 0,
            "intents": list(set(m.get("intent_type") for m in quality_metrics if m.get("intent_type"))),
        }

    def _summarize_user_feedback(self, metrics: List[Dict]) -> Dict[str, Any]:
        """Tóm tắt user feedback"""
        feedback_metrics = [m for m in metrics if m.get("type") == "user_feedback"]

        if not feedback_metrics:
            return {"total": 0}

        feedback_counts = defaultdict(int)
        for m in feedback_metrics:
            feedback_counts[m.get("feedback", "unknown")] += 1

        return {
            "total": len(feedback_metrics),
            "breakdown": dict(feedback_counts),
            "positive_rate": feedback_counts.get("good", 0) / len(feedback_metrics) if feedback_metrics else 0,
        }

    @staticmethod
    def _calculate_efficiency_score(tokens_used: int, execution_time: float, response_length: int) -> float:
        """
        Tính efficiency score
        Cao hơn = tốt hơn (ít tokens, nhanh, response dài)
        """
        # Normalize values
        token_score = max(0, 10 - (tokens_used / 100))  # Penalize high tokens
        time_score = max(0, 10 - (execution_time / 100))  # Penalize slow response
        length_score = min(10, response_length / 100)  # Reward longer (more detailed) responses

        # Weighted average
        efficiency = (token_score * 0.3 + time_score * 0.3 + length_score * 0.4)
        return max(0, min(10, efficiency))

    def export_metrics_to_csv(self, output_path: str = "logs/metrics_export.csv"):
        """Export metrics to CSV for analysis"""
        import csv

        metrics = self._read_all_metrics()
        if not metrics:
            logger.warning("No metrics to export")
            return

        # Flatten metrics for CSV
        fieldnames = set()
        for m in metrics:
            fieldnames.update(m.keys())

        fieldnames = sorted(list(fieldnames))

        try:
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()

                for metric in metrics:
                    # Flatten nested dicts
                    flat_metric = {}
                    for key, value in metric.items():
                        if isinstance(value, dict):
                            for sub_key, sub_value in value.items():
                                flat_metric[f"{key}.{sub_key}"] = sub_value
                        else:
                            flat_metric[key] = value
                    writer.writerow(flat_metric)

            logger.info(f"✅ Metrics exported to {output_path}")
        except Exception as e:
            logger.error(f"Failed to export metrics: {e}")
