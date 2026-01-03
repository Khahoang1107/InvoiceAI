#!/usr/bin/env python3
"""
UBIAI Data Downloader and NER Training Script

This script downloads annotated data from UBIAI and trains a custom NER model
for invoice information extraction.
"""

import json
import os
import requests
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
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

try:
    import spacy
    from spacy.training import Example
    from spacy.util import minibatch, compounding
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    logger.warning("spaCy not available. Install with: pip install spacy")

try:
    from transformers import AutoTokenizer, AutoModelForTokenClassification, TrainingArguments, Trainer
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("transformers not available. Install with: pip install transformers torch")


class UBIAIDataLoader:
    """Class to download and process UBIAI annotated data"""

    def __init__(self, api_key: str, project_id: str):
        self.api_key = api_key
        self.project_id = project_id
        self.base_url = "https://api.ubi.ai"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    def download_project_data(self, output_dir: str = "data/ubi_ai") -> List[Dict]:
        """
        Download all annotated documents from UBIAI project

        Args:
            output_dir: Directory to save downloaded data

        Returns:
            List of annotated documents
        """
        try:
            # Create output directory
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            # Get project documents
            url = f"{self.base_url}/projects/{self.project_id}/documents"
            response = requests.get(url, headers=self.headers)

            if response.status_code != 200:
                logger.error(f"Failed to fetch documents: {response.status_code}")
                return []

            documents = response.json()
            logger.info(f"Found {len(documents)} documents in project")

            annotated_data = []

            for doc in documents:
                doc_id = doc.get('id')
                if not doc_id:
                    continue

                # Get annotations for this document
                annotations_url = f"{self.base_url}/projects/{self.project_id}/documents/{doc_id}/annotations"
                ann_response = requests.get(annotations_url, headers=self.headers)

                if ann_response.status_code == 200:
                    annotations = ann_response.json()

                    # Convert UBIAI format to spaCy format
                    spacy_format = self._convert_ubiai_to_spacy(doc, annotations)
                    if spacy_format:
                        annotated_data.append(spacy_format)

                        # Save individual document
                        doc_file = output_path / f"{doc_id}.json"
                        with open(doc_file, 'w', encoding='utf-8') as f:
                            json.dump(spacy_format, f, indent=2, ensure_ascii=False)

            # Save all data
            all_data_file = output_path / "all_annotated_data.json"
            with open(all_data_file, 'w', encoding='utf-8') as f:
                json.dump(annotated_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Downloaded and processed {len(annotated_data)} annotated documents")
            return annotated_data

        except Exception as e:
            logger.error(f"Error downloading UBIAI data: {e}")
            return []

    def _convert_ubiai_to_spacy(self, document: Dict, annotations: List[Dict]) -> Optional[Dict]:
        """
        Convert UBIAI annotation format to spaCy training format

        Args:
            document: UBIAI document object
            annotations: List of annotations

        Returns:
            spaCy format dictionary or None if conversion fails
        """
        try:
            text = document.get('text', '')
            if not text:
                return None

            entities = []

            for ann in annotations:
                label = ann.get('label')
                start = ann.get('start_offset', 0)
                end = ann.get('end_offset', 0)

                if label and start is not None and end is not None:
                    entities.append([start, end, label])

            return {
                "text": text,
                "entities": entities,
                "document_id": document.get('id'),
                "metadata": {
                    "source": "UBIAI",
                    "project_id": self.project_id,
                    "converted_at": datetime.now().isoformat()
                }
            }

        except Exception as e:
            logger.warning(f"Failed to convert document {document.get('id')}: {e}")
            return None


class NERTrainer:
    """Class to train NER models using spaCy or transformers"""

    def __init__(self, model_type: str = "spacy"):
        """
        Args:
            model_type: "spacy" or "transformers"
        """
        self.model_type = model_type
        self.model = None

    def train_spacy_model(self, training_data: List[Dict], output_dir: str,
                         base_model: str = "en_core_web_sm", n_iter: int = 100) -> str:
        """
        Train a spaCy NER model

        Args:
            training_data: List of training examples in spaCy format
            output_dir: Directory to save the trained model
            base_model: Base spaCy model to start with
            n_iter: Number of training iterations

        Returns:
            Path to saved model
        """
        if not SPACY_AVAILABLE:
            raise ImportError("spaCy is required for spaCy model training")

        try:
            # Load base model or create blank model
            if base_model and spacy.util.is_package(base_model):
                nlp = spacy.load(base_model)
                logger.info(f"Loaded base model: {base_model}")
            else:
                nlp = spacy.blank("en")
                logger.info("Created blank English model")

            # Add NER pipeline if not exists
            if "ner" not in nlp.pipe_names:
                ner = nlp.add_pipe("ner")
            else:
                ner = nlp.get_pipe("ner")

            # Add labels to NER
            for example in training_data:
                for ent in example.get("entities", []):
                    if len(ent) >= 3:
                        ner.add_label(ent[2])

            # Convert training data to Example objects
            examples = []
            for item in training_data:
                doc = nlp.make_doc(item["text"])
                example = Example.from_dict(doc, {"entities": item["entities"]})
                examples.append(example)

            # Training loop
            optimizer = nlp.initialize(lambda: examples)
            batch_sizes = compounding(4.0, 32.0, 1.001)

            for i in range(n_iter):
                losses = {}
                batches = minibatch(examples, size=batch_sizes)

                for batch in batches:
                    nlp.update(batch, losses=losses, drop=0.5)

                if i % 10 == 0:
                    logger.info(f"Iteration {i}, Losses: {losses}")

            # Save model
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            nlp.to_disk(output_path)

            logger.info(f"Model saved to: {output_path}")
            return str(output_path)

        except Exception as e:
            logger.error(f"Error training spaCy model: {e}")
            raise

    def train_transformers_model(self, training_data: List[Dict], output_dir: str,
                                model_name: str = "distilbert-base-uncased",
                                num_labels: int = 9) -> str:
        """
        Train a transformers NER model

        Args:
            training_data: List of training examples
            output_dir: Directory to save the trained model
            model_name: Base transformer model
            num_labels: Number of NER labels

        Returns:
            Path to saved model
        """
        if not TRANSFORMERS_AVAILABLE:
            raise ImportError("transformers is required for transformer model training")

        try:
            # This is a simplified implementation
            # In practice, you'd need to tokenize and format data properly
            logger.info("Transformer NER training not fully implemented yet")
            logger.info("Use spaCy training for now")

            return ""

        except Exception as e:
            logger.error(f"Error training transformer model: {e}")
            raise


class InvoiceNERPipeline:
    """Complete pipeline for invoice NER training"""

    def __init__(self, ubiai_api_key: str = None, ubiai_project_id: str = None):
        self.ubiai_loader = None
        if ubiai_api_key and ubiai_project_id:
            self.ubiai_loader = UBIAIDataLoader(ubiai_api_key, ubiai_project_id)

        self.trainer = NERTrainer(model_type="spacy")

    def download_and_train(self, output_dir: str = "models/invoice_ner",
                          model_type: str = "spacy") -> str:
        """
        Complete pipeline: download data from UBIAI and train NER model

        Args:
            output_dir: Directory to save model
            model_type: Type of model to train

        Returns:
            Path to trained model
        """
        # Download data
        if not self.ubiai_loader:
            logger.error("UBIAI credentials not provided")
            return ""

        logger.info("Downloading annotated data from UBIAI...")
        training_data = self.ubiai_loader.download_project_data()

        if not training_data:
            logger.error("No training data downloaded")
            return ""

        # Train model
        logger.info(f"Training {model_type} NER model...")
        if model_type == "spacy":
            model_path = self.trainer.train_spacy_model(training_data, output_dir)
        else:
            model_path = self.trainer.train_transformers_model(training_data, output_dir)

        logger.info(f"NER training completed. Model saved at: {model_path}")
        return model_path

    def load_trained_model(self, model_path: str):
        """Load a trained NER model"""
        if not SPACY_AVAILABLE:
            raise ImportError("spaCy required to load models")

        try:
            return spacy.load(model_path)
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return None


def main():
    """Main function for UBIAI data download and NER training"""
    print("UBIAI Data Downloader and NER Training Tool")
    print("=" * 50)

    # Check dependencies
    if not SPACY_AVAILABLE:
        print("ERROR: spaCy is required. Install with: pip install spacy")
        print("Also download a language model: python -m spacy download en_core_web_sm")
        return

    # UBIAI credentials (should be set via environment variables)
    api_key = os.getenv("UBIAI_API_KEY")
    project_id = os.getenv("UBIAI_PROJECT_ID")

    if not api_key or not project_id:
        print("ERROR: UBIAI credentials not found!")
        print("Set environment variables:")
        print("  UBIAI_API_KEY=your_api_key")
        print("  UBIAI_PROJECT_ID=your_project_id")
        return

    # Create pipeline
    pipeline = InvoiceNERPipeline(api_key, project_id)

    # Download and train
    try:
        model_path = pipeline.download_and_train()
        if model_path:
            print(f"\n✅ Training completed! Model saved at: {model_path}")

            # Test the model
            nlp = pipeline.load_trained_model(model_path)
            if nlp:
                test_text = "Invoice #12345 from ABC Corp, total amount $1,250.00"
                doc = nlp(test_text)
                print(f"\n🧪 Test Results for: '{test_text}'")
                for ent in doc.ents:
                    print(f"  {ent.text} -> {ent.label_}")
        else:
            print("\n❌ Training failed!")

    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()