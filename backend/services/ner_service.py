#!/usr/bin/env python3
"""
Invoice NER Service

This service provides Named Entity Recognition for invoice text extraction
using trained spaCy models.
"""

import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    import spacy
    from spacy.lang.en import English
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    logger.warning("spaCy not available for NER service")


class InvoiceNERService:
    """Service for invoice named entity recognition"""

    def __init__(self, model_path: Optional[str] = None):
        """
        Args:
            model_path: Path to trained spaCy NER model
        """
        self.model_path = model_path or "models/invoice_ner"
        self.nlp = None
        self._load_model()

    def _load_model(self):
        """Load the trained NER model"""
        if not SPACY_AVAILABLE:
            logger.error("spaCy not available")
            return

        try:
            model_path = Path(self.model_path)
            if model_path.exists():
                self.nlp = spacy.load(model_path)
                logger.info(f"Loaded NER model from {model_path}")
            else:
                # Fallback to blank model with basic patterns
                self.nlp = self._create_fallback_model()
                logger.warning(f"Model not found at {model_path}, using fallback model")

        except Exception as e:
            logger.error(f"Error loading NER model: {e}")
            self.nlp = self._create_fallback_model()

    def _create_fallback_model(self):
        """Create a basic fallback NER model with rule-based patterns"""
        if not SPACY_AVAILABLE:
            return None

        # Create basic English model
        nlp = English()

        # Add sentencizer
        nlp.add_pipe("sentencizer")

        # Add entity ruler with basic invoice patterns
        ruler = nlp.add_pipe("entity_ruler")

        patterns = [
            # Invoice numbers
            {"label": "INVOICE_NUMBER", "pattern": [
                {"TEXT": {"REGEX": r"(?i)invoice\s*#?\s*[\w\d\-]+"}},
                {"TEXT": {"REGEX": r"(?i)inv\s*#?\s*[\w\d\-]+"}},
                {"TEXT": {"REGEX": r"(?i)bill\s*#?\s*[\w\d\-]+"}}
            ]},

            # Amounts
            {"label": "AMOUNT", "pattern": [
                {"TEXT": {"REGEX": r"\$[\d,]+\.?\d*"}},
                {"TEXT": {"REGEX": r"[\d,]+\.?\d*\s*(?:USD|dollars?|€|EUR|euros?|£|GBP|pounds?)"}},
                {"TEXT": {"REGEX": r"(?i)total\s*:?\s*\$?[\d,]+\.?\d*"}}
            ]},

            # Dates
            {"label": "DATE", "pattern": [
                {"TEXT": {"REGEX": r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}"}},
                {"TEXT": {"REGEX": r"\d{2,4}[/-]\d{1,2}[/-]\d{1,2}"}},
                {"TEXT": {"REGEX": r"(?i)(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+\d{1,2},?\s+\d{2,4}"}}
            ]},

            # Company names (basic)
            {"label": "COMPANY", "pattern": [
                {"TEXT": {"REGEX": r"(?i)(?:from|to|company|corp|inc|llc|ltd)\s*:?\s*[A-Z][\w\s&]+"}},
                {"TEXT": {"REGEX": r"[A-Z][\w\s&]{2,}(?:\s+(?:Corp|Inc|LLC|Ltd|Company))"}}
            ]},

            # Addresses
            {"label": "ADDRESS", "pattern": [
                {"TEXT": {"REGEX": r"\d+\s+[A-Z][\w\s,]+(?:ST|AVE|RD|BLVD|DR|LN|WAY|PL)\.?,?\s+[A-Z]{2}\s+\d{5}"}},
                {"TEXT": {"REGEX": r"(?i)address\s*:?\s*[A-Z][\w\s,]+"}},
                {"TEXT": {"REGEX": r"(?i)billing\s+address\s*:?\s*[A-Z][\w\s,]+"}},
                {"TEXT": {"REGEX": r"(?i)shipping\s+address\s*:?\s*[A-Z][\w\s,]+"}}
            ]}
        ]

        ruler.add_patterns(patterns)
        logger.info("Created fallback NER model with rule-based patterns")

        return nlp

    def extract_entities(self, text: str) -> Dict[str, Any]:
        """
        Extract named entities from invoice text

        Args:
            text: Invoice text to analyze

        Returns:
            Dictionary containing extracted entities
        """
        if not self.nlp:
            return {"error": "NER model not available"}

        try:
            doc = self.nlp(text)

            entities = {}
            for ent in doc.ents:
                label = ent.label_
                if label not in entities:
                    entities[label] = []
                entities[label].append({
                    "text": ent.text,
                    "start": ent.start_char,
                    "end": ent.end_char,
                    "confidence": getattr(ent, '_.confidence', 1.0)  # For future use with transformers
                })

            # Extract key invoice information
            invoice_info = self._extract_invoice_info(text, entities)

            return {
                "entities": entities,
                "invoice_info": invoice_info,
                "processed_at": datetime.now().isoformat(),
                "text_length": len(text),
                "entity_count": len(doc.ents)
            }

        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
            return {"error": str(e)}

    def _extract_invoice_info(self, text: str, entities: Dict) -> Dict[str, Any]:
        """Extract structured invoice information from entities"""
        info = {
            "invoice_number": None,
            "total_amount": None,
            "date": None,
            "company": None,
            "address": None
        }

        # Extract invoice number
        if "INVOICE_NUMBER" in entities and entities["INVOICE_NUMBER"]:
            # Take the first match
            info["invoice_number"] = entities["INVOICE_NUMBER"][0]["text"]

        # Extract amount
        if "AMOUNT" in entities and entities["AMOUNT"]:
            # Take the last amount (usually total)
            amounts = entities["AMOUNT"]
            info["total_amount"] = amounts[-1]["text"]

        # Extract date
        if "DATE" in entities and entities["DATE"]:
            info["date"] = entities["DATE"][0]["text"]

        # Extract company
        if "COMPANY" in entities and entities["COMPANY"]:
            info["company"] = entities["COMPANY"][0]["text"]

        # Extract address
        if "ADDRESS" in entities and entities["ADDRESS"]:
            info["address"] = entities["ADDRESS"][0]["text"]

        return info

    def compare_ocr_results(self, tesseract_text: str, easyocr_text: str) -> Dict[str, Any]:
        """
        Compare entity extraction results from two OCR engines

        Args:
            tesseract_text: Text from Tesseract OCR
            easyocr_text: Text from EasyOCR

        Returns:
            Comparison results
        """
        tess_entities = self.extract_entities(tesseract_text)
        easy_entities = self.extract_entities(easyocr_text)

        comparison = {
            "tesseract": tess_entities,
            "easyocr": easy_entities,
            "recommendation": self._recommend_engine(tess_entities, easy_entities),
            "comparison": {
                "tesseract_entity_count": tess_entities.get("entity_count", 0),
                "easyocr_entity_count": easy_entities.get("entity_count", 0),
                "common_entities": self._find_common_entities(tess_entities, easy_entities)
            }
        }

        return comparison

    def _recommend_engine(self, tess_result: Dict, easy_result: Dict) -> str:
        """Recommend which OCR engine to use based on entity extraction quality"""
        tess_count = tess_result.get("entity_count", 0)
        easy_count = easy_result.get("entity_count", 0)

        # Simple heuristic: prefer engine with more entities extracted
        if easy_count > tess_count:
            return "easyocr"
        elif tess_count > easy_count:
            return "tesseract"
        else:
            return "both"  # Similar performance

    def _find_common_entities(self, result1: Dict, result2: Dict) -> Dict[str, List[str]]:
        """Find common entities between two extraction results"""
        common = {}

        entities1 = result1.get("entities", {})
        entities2 = result2.get("entities", {})

        for label in set(entities1.keys()) | set(entities2.keys()):
            ents1 = entities1.get(label, [])
            ents2 = entities2.get(label, [])

            ents1_texts = {ent["text"].lower().strip() for ent in ents1}
            ents2_texts = {ent["text"].lower().strip() for ent in ents2}

            common[label] = list(ents1_texts & ents2_texts)

        return common


# Global NER service instance
_ner_service = None

def get_ner_service() -> InvoiceNERService:
    """Get global NER service instance"""
    global _ner_service
    if _ner_service is None:
        _ner_service = InvoiceNERService()
    return _ner_service