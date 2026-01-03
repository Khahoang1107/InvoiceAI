#!/usr/bin/env python3
"""
OCR Engine Benchmarking Script

This script benchmarks Tesseract and EasyOCR engines on real invoice data
to determine which engine provides better accuracy for invoice processing.
"""

import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add backend to path
import sys
sys.path.append(str(Path(__file__).parent))

from services.ocr_service import OCRService


class OCRBenchmark:
    """OCR Engine Benchmarking Class"""

    def __init__(self, invoice_dir: str = "backend/uploads"):
        self.invoice_dir = Path(invoice_dir)
        self.ocr_service = OCRService()
        self.results = []

    def find_invoice_images(self) -> List[Path]:
        """Find all invoice image files"""
        image_extensions = {'.png', '.jpg', '.jpeg', '.tiff', '.bmp'}
        invoice_files = []

        if self.invoice_dir.exists():
            for file_path in self.invoice_dir.rglob('*'):
                if file_path.is_file() and file_path.suffix.lower() in image_extensions:
                    invoice_files.append(file_path)

        logger.info(f"Found {len(invoice_files)} invoice images")
        return invoice_files

    def run_benchmark(self) -> Dict[str, Any]:
        """Run OCR benchmark on all invoice images"""
        logger.info("Starting OCR engine benchmark...")

        invoice_files = self.find_invoice_images()
        if not invoice_files:
            logger.warning("No invoice images found for benchmarking")
            return {"error": "No invoice images found"}

        total_files = len(invoice_files)
        processed = 0
        errors = 0

        for file_path in invoice_files:
            try:
                logger.info(f"Processing {file_path.name} ({processed + 1}/{total_files})")

                # Compare engines
                comparison = self.ocr_service.compare_engines(str(file_path))

                # Add file info
                comparison["file"] = str(file_path.name)
                comparison["file_size"] = file_path.stat().st_size

                self.results.append(comparison)
                processed += 1

            except Exception as e:
                logger.error(f"Failed to process {file_path.name}: {e}")
                errors += 1

        # Generate summary
        summary = self._generate_summary()

        logger.info(f"Benchmark completed. Processed: {processed}, Errors: {errors}")
        logger.info(f"Summary: {summary}")

        return {
            "summary": summary,
            "results": self.results,
            "total_files": total_files,
            "processed": processed,
            "errors": errors,
            "timestamp": datetime.now().isoformat()
        }

    def _generate_summary(self) -> Dict[str, Any]:
        """Generate benchmark summary"""
        if not self.results:
            return {"error": "No results to summarize"}

        tess_wins = 0
        easy_wins = 0
        tess_total_conf = 0
        easy_total_conf = 0
        tess_total_time = 0
        easy_total_time = 0
        valid_comparisons = 0

        for result in self.results:
            tess = result.get("tesseract", {})
            easy = result.get("easyocr", {})

            if tess.get("available") and easy.get("available"):
                valid_comparisons += 1

                tess_conf = tess.get("confidence", 0)
                easy_conf = easy.get("confidence", 0)

                tess_total_conf += tess_conf
                easy_total_conf += easy_conf
                tess_total_time += tess.get("time", 0)
                easy_total_time += easy.get("time", 0)

                if tess_conf > easy_conf:
                    tess_wins += 1
                elif easy_conf > tess_conf:
                    easy_wins += 1

        if valid_comparisons == 0:
            return {"error": "No valid comparisons available"}

        avg_tess_conf = tess_total_conf / valid_comparisons
        avg_easy_conf = easy_total_conf / valid_comparisons
        avg_tess_time = tess_total_time / valid_comparisons
        avg_easy_time = easy_total_time / valid_comparisons

        # Determine recommendation
        if avg_tess_conf > avg_easy_conf:
            recommendation = "tesseract"
        elif avg_easy_conf > avg_tess_conf:
            recommendation = "easyocr"
        else:
            # If confidence similar, prefer faster engine
            recommendation = "tesseract" if avg_tess_time <= avg_easy_time else "easyocr"

        return {
            "total_comparisons": valid_comparisons,
            "tesseract_wins": tess_wins,
            "easyocr_wins": easy_wins,
            "tesseract_avg_confidence": round(avg_tess_conf, 2),
            "easyocr_avg_confidence": round(avg_easy_conf, 2),
            "tesseract_avg_time": round(avg_tess_time, 3),
            "easyocr_avg_time": round(avg_easy_time, 3),
            "recommended_engine": recommendation,
            "confidence_improvement": round(abs(avg_tess_conf - avg_easy_conf), 2),
            "time_difference": round(avg_tess_time - avg_easy_time, 3)
        }

    def save_results(self, output_file: str = "ocr_benchmark_results.json"):
        """Save benchmark results to file"""
        results = self.run_benchmark()

        output_path = Path(output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        logger.info(f"Results saved to {output_path}")
        return str(output_path)


def main():
    """Main benchmark function"""
    print("OCR Engine Benchmarking Tool")
    print("=" * 40)

    # Check OCR availability
    ocr_service = OCRService()
    print(f"Tesseract available: {ocr_service.tesseract_available}")
    print(f"EasyOCR available: {ocr_service.easyocr_available}")
    print()

    if not (ocr_service.tesseract_available or ocr_service.easyocr_available):
        print("ERROR: No OCR engines available!")
        print("\nTo install OCR engines:")
        print("1. For Tesseract: Download from https://github.com/UB-Mannheim/tesseract/wiki")
        print("2. For EasyOCR: pip install easyocr (requires compatible NumPy version)")
        print("\nNote: Current environment has NumPy compatibility issues with EasyOCR.")
        print("Consider using Python 3.8-3.11 for better compatibility.")
        return

    # Run benchmark
    benchmark = OCRBenchmark()
    results = benchmark.run_benchmark()

    # Display summary
    if "error" not in results.get("summary", {}):
        summary = results["summary"]
        print("BENCHMARK SUMMARY")
        print("-" * 20)
        print(f"Files processed: {results['processed']}")
        print(f"Valid comparisons: {summary['total_comparisons']}")
        print()
        print("Accuracy Results:")
        print(f"  Tesseract wins: {summary['tesseract_wins']}")
        print(f"  EasyOCR wins: {summary['easyocr_wins']}")
        print(f"  Tesseract avg confidence: {summary['tesseract_avg_confidence']}%")
        print(f"  EasyOCR avg confidence: {summary['easyocr_avg_confidence']}%")
        print()
        print("Performance Results:")
        print(f"  Tesseract avg time: {summary['tesseract_avg_time']}s")
        print(f"  EasyOCR avg time: {summary['easyocr_avg_time']}s")
        print()
        print(f"RECOMMENDED ENGINE: {summary['recommended_engine'].upper()}")
        print(f"Confidence improvement: {summary['confidence_improvement']}%")
        print(f"Time difference: {summary['time_difference']}s")
    else:
        print(f"ERROR: {results['summary']['error']}")

    # Save results
    output_file = benchmark.save_results()
    print(f"\nDetailed results saved to: {output_file}")


if __name__ == "__main__":
    main()