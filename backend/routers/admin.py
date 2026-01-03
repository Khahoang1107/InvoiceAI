"""
Admin API Router
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from datetime import datetime
from services.metrics_service import MetricsService
from services.ner_benchmark_service import NERBenchmarkService

router = APIRouter(prefix="/api/admin", tags=["admin"])

# Initialize services
metrics_service = MetricsService()
ner_benchmark_service = NERBenchmarkService()

@router.get("/health")
async def admin_health():
    """Admin health check"""
    return JSONResponse({
        "status": "ok",
        "service": "admin",
        "timestamp": datetime.now().isoformat()
    })

@router.get("/stats")
async def admin_stats():
    """Admin statistics"""
    return JSONResponse({
        "message": "Admin stats not implemented yet",
        "timestamp": datetime.now().isoformat()
    })

@router.get("/metrics/summary")
async def metrics_summary(hours: int = Query(24, ge=1, le=168)):
    """
    Get metrics summary for last N hours
    
    Args:
        hours: Number of hours to look back (default: 24, max: 168 = 1 week)
    
    Returns:
        Metrics summary with retrieval, function calling, response quality stats
    """
    try:
        summary = metrics_service.get_metrics_summary(hours=hours)
        return JSONResponse({
            "status": "ok",
            "data": summary,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")

@router.get("/metrics/performance")
async def metrics_performance():
    """
    Get detailed performance report
    
    Returns:
        Performance metrics grouped by tool
    """
    try:
        report = metrics_service.get_performance_report()
        return JSONResponse({
            "status": "ok",
            "data": report,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance report: {str(e)}")

@router.post("/metrics/export")
async def metrics_export():
    """
    Export metrics to CSV for analysis
    
    Returns:
        Export status
    """
    try:
        metrics_service.export_metrics_to_csv()
        return JSONResponse({
            "status": "ok",
            "message": "Metrics exported to logs/metrics_export.csv",
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export metrics: {str(e)}")


# ==================== NER BENCHMARK ENDPOINTS ====================

@router.get("/benchmarks/ner/latest")
async def ner_benchmark_latest():
    """
    Get the latest NER model benchmark
    
    Returns:
        Latest NER benchmark with all metrics
    """
    try:
        benchmark = ner_benchmark_service.get_latest_ner_benchmark()
        if not benchmark:
            raise HTTPException(status_code=404, detail="No NER benchmark found")
        
        return JSONResponse({
            "status": "ok",
            "data": benchmark,
            "timestamp": datetime.now().isoformat()
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get NER benchmark: {str(e)}")


@router.get("/benchmarks/ner/all")
async def ner_benchmarks_all():
    """
    Get all NER model benchmarks (historical)
    
    Returns:
        List of all NER benchmarks with timestamps
    """
    try:
        benchmarks = ner_benchmark_service.get_all_ner_benchmarks()
        return JSONResponse({
            "status": "ok",
            "data": benchmarks,
            "count": len(benchmarks),
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get NER benchmarks: {str(e)}")


@router.get("/benchmarks/ner/comparison")
async def ner_benchmark_comparison():
    """
    Get NER benchmark comparison across all versions
    
    Returns:
        Improvement trends and summary statistics
    """
    try:
        comparison = ner_benchmark_service.get_ner_benchmark_comparison()
        return JSONResponse({
            "status": "ok",
            "data": comparison,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get NER comparison: {str(e)}")


@router.get("/benchmarks/ner/report")
async def ner_benchmark_report():
    """
    Get formatted NER benchmark report
    
    Returns:
        Human-readable benchmark report as text
    """
    try:
        report = ner_benchmark_service.generate_ner_report()
        return JSONResponse({
            "status": "ok",
            "data": report,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate NER report: {str(e)}")


@router.get("/benchmarks/ner/entity-summary")
async def ner_entity_performance():
    """
    Get per-entity performance summary across all benchmarks
    
    Returns:
        Average metrics for each entity type
    """
    try:
        summary = ner_benchmark_service.get_entity_performance_summary()
        return JSONResponse({
            "status": "ok",
            "data": summary,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get entity performance: {str(e)}")