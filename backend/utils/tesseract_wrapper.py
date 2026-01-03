"""
Tesseract OCR Wrapper - Bypasses pytesseract compatibility issues with Python 3.14
Uses subprocess to call Tesseract directly
"""
import subprocess
import tempfile
import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from PIL import Image

logger = logging.getLogger(__name__)

# Get Tesseract path from environment
TESSERACT_CMD = os.getenv("TESSERACT_CMD", r"C:\Program Files\Tesseract-OCR\tesseract.exe")


class TesseractWrapper:
    """
    Direct wrapper for Tesseract OCR that bypasses pytesseract.
    Compatible with Python 3.14+
    """
    
    def __init__(self, tesseract_cmd: Optional[str] = None):
        """Initialize with Tesseract path."""
        self.tesseract_cmd = tesseract_cmd or TESSERACT_CMD
        self._verify_tesseract()
    
    def _verify_tesseract(self):
        """Verify Tesseract is available."""
        if not Path(self.tesseract_cmd).exists():
            raise FileNotFoundError(f"Tesseract not found at: {self.tesseract_cmd}")
        
        # Test version
        try:
            result = subprocess.run(
                [self.tesseract_cmd, "--version"],
                capture_output=True,
                text=True
            )
            version_line = result.stdout.split('\n')[0] if result.stdout else ""
            logger.info(f"Tesseract initialized: {version_line}")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Tesseract: {e}")
    
    def get_version(self) -> str:
        """Get Tesseract version."""
        result = subprocess.run(
            [self.tesseract_cmd, "--version"],
            capture_output=True,
            text=True
        )
        return result.stdout.split('\n')[0] if result.stdout else "Unknown"
    
    def get_languages(self) -> list:
        """Get available languages."""
        result = subprocess.run(
            [self.tesseract_cmd, "--list-langs"],
            capture_output=True,
            text=True
        )
        if result.stdout:
            lines = result.stdout.strip().split('\n')
            # Skip first line (header)
            return [l.strip() for l in lines[1:] if l.strip()]
        return []
    
    def image_to_string(
        self, 
        image: Image.Image, 
        lang: str = "eng",
        config: str = ""
    ) -> str:
        """
        Extract text from PIL Image.
        
        Args:
            image: PIL Image object
            lang: Language(s) to use (e.g., "eng", "eng+vie")
            config: Additional Tesseract config
            
        Returns:
            Extracted text
        """
        # Save image to temp file
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp_path = tmp.name
            image.save(tmp_path)
        
        try:
            # Run Tesseract
            result = subprocess.run(
                [self.tesseract_cmd, tmp_path, "stdout", "-l", lang] + 
                (config.split() if config else []),
                capture_output=True,
                text=True
            )
            return result.stdout.strip()
        finally:
            # Cleanup temp file
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    
    def image_to_data(
        self, 
        image: Image.Image, 
        lang: str = "eng",
        output_type: str = "dict"
    ) -> Dict[str, Any]:
        """
        Extract text with confidence data from PIL Image.
        
        Args:
            image: PIL Image object
            lang: Language(s) to use
            output_type: Output format (dict)
            
        Returns:
            Dictionary with text and confidence data
        """
        # Save image to temp file
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp_path = tmp.name
            image.save(tmp_path)
        
        try:
            # Run Tesseract with TSV output
            result = subprocess.run(
                [self.tesseract_cmd, tmp_path, "stdout", "-l", lang, "tsv"],
                capture_output=True,
                text=True
            )
            
            # Parse TSV output
            lines = result.stdout.strip().split('\n')
            if len(lines) < 2:
                return {
                    "text": [],
                    "conf": [],
                    "level": [],
                    "page_num": [],
                    "block_num": [],
                    "par_num": [],
                    "line_num": [],
                    "word_num": [],
                    "left": [],
                    "top": [],
                    "width": [],
                    "height": []
                }
            
            # Parse header and data
            header = lines[0].split('\t')
            data = {col: [] for col in header}
            
            for line in lines[1:]:
                values = line.split('\t')
                for i, col in enumerate(header):
                    if i < len(values):
                        data[col].append(values[i])
            
            return data
            
        finally:
            # Cleanup temp file
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    
    def image_to_string_from_path(
        self,
        image_path: str,
        lang: str = "eng",
        config: str = ""
    ) -> str:
        """
        Extract text directly from image file path.
        
        Args:
            image_path: Path to image file
            lang: Language(s) to use
            config: Additional Tesseract config
            
        Returns:
            Extracted text
        """
        if not Path(image_path).exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        result = subprocess.run(
            [self.tesseract_cmd, image_path, "stdout", "-l", lang] +
            (config.split() if config else []),
            capture_output=True,
            text=True
        )
        return result.stdout.strip()
    
    def get_confidence(self, image: Image.Image, lang: str = "eng") -> float:
        """
        Get average OCR confidence score.
        
        Args:
            image: PIL Image object
            lang: Language to use
            
        Returns:
            Average confidence score (0-100)
        """
        data = self.image_to_data(image, lang)
        
        if "conf" in data and data["conf"]:
            # Filter out -1 values (which indicate no confidence)
            confidences = [
                float(c) for c in data["conf"] 
                if c and c != "-1" and c.strip()
            ]
            if confidences:
                return sum(confidences) / len(confidences)
        
        return 0.0


# Global instance
_tesseract: Optional[TesseractWrapper] = None


def get_tesseract() -> TesseractWrapper:
    """Get global Tesseract instance."""
    global _tesseract
    if _tesseract is None:
        _tesseract = TesseractWrapper()
    return _tesseract


# Compatibility functions (mimicking pytesseract API)
def image_to_string(image, lang="eng", config="") -> str:
    """Extract text from image (pytesseract compatible)."""
    return get_tesseract().image_to_string(image, lang, config)


def image_to_data(image, lang="eng", output_type="dict") -> Dict:
    """Get OCR data with confidence (pytesseract compatible)."""
    return get_tesseract().image_to_data(image, lang, output_type)


def get_tesseract_version() -> str:
    """Get Tesseract version (pytesseract compatible)."""
    return get_tesseract().get_version()


def get_languages() -> list:
    """Get available languages (pytesseract compatible)."""
    return get_tesseract().get_languages()
