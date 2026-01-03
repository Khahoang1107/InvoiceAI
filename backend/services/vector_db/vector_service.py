"""
Vector Service - Main RAG Service

Orchestrates the entire RAG (Retrieval-Augmented Generation) pipeline:
1. Document ingestion and embedding
2. Vector storage and indexing
3. Query processing and retrieval
4. Context preparation for LLM
"""

import os
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import logging

from .vector_store import ChromaVectorStore, FAISSVectorStore
from .embedding_service import EmbeddingService, create_embedding_service
from .retrieval_service import RetrievalService

logger = logging.getLogger(__name__)

class VectorService:
    """Main service for RAG operations"""

    def __init__(self,
                 vector_store_type: str = "faiss",  # Changed from "chroma" to "faiss"
                 embedding_service_type: str = "sentence-transformers",
                 embedding_model: str = "all-MiniLM-L6-v2",
                 persist_directory: str = "./data/vector_db",
                 collection_name: str = "invoice_documents"):
        """
        Initialize Vector Service

        Args:
            vector_store_type: Type of vector store ('chroma', 'faiss')
            embedding_service_type: Type of embedding service ('sentence-transformers', 'openai')
            embedding_model: Name of embedding model
            persist_directory: Directory for persistent storage
            collection_name: Name of vector collection
        """
        self.vector_store_type = vector_store_type
        self.persist_directory = persist_directory
        self.collection_name = collection_name

        # Initialize embedding service
        self.embedding_service = create_embedding_service(
            embedding_service_type,
            model_name=embedding_model
        )

        # Initialize vector store
        self.vector_store = self._create_vector_store()

        # Initialize retrieval service
        self.retrieval_service = RetrievalService(
            self.vector_store,
            self.embedding_service
        )

        logger.info(f"VectorService initialized with {vector_store_type} store and {embedding_service_type} embeddings")

    def _create_vector_store(self):
        """Create vector store instance"""
        if self.vector_store_type == "chroma":
            return ChromaVectorStore(
                collection_name=self.collection_name,
                persist_directory=self.persist_directory
            )
        elif self.vector_store_type == "faiss":
            return FAISSVectorStore()
        else:
            raise ValueError(f"Unsupported vector store type: {self.vector_store_type}")

    def add_invoice_documents(self, invoices: List[Dict[str, Any]]) -> List[str]:
        """
        Add invoice documents to vector store

        Args:
            invoices: List of invoice dictionaries

        Returns:
            List of document IDs
        """
        if not invoices:
            return []

        # Prepare documents for vectorization
        documents = []
        texts_to_embed = []

        for invoice in invoices:
            # Create document representation
            doc = self._prepare_invoice_document(invoice)
            documents.append(doc)

            # Extract text for embedding
            text_content = self._extract_invoice_text(invoice)
            texts_to_embed.append(text_content)

        # Generate embeddings
        embeddings = self.embedding_service.encode_batch(texts_to_embed)

        # Add to vector store
        document_ids = self.vector_store.add_documents(documents, embeddings)

        logger.info(f"Added {len(invoices)} invoice documents to vector store")
        return document_ids

    def _prepare_invoice_document(self, invoice: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare invoice data for document storage"""
        doc_id = invoice.get('id', f"invoice_{invoice.get('invoice_number', 'unknown')}")

        # Extract metadata
        metadata = {
            'document_type': 'invoice',
            'invoice_number': invoice.get('invoice_number', ''),
            'customer_name': invoice.get('customer_name', ''),
            'total_amount': invoice.get('total_amount', 0),
            'currency': invoice.get('currency', 'VND'),
            'issue_date': invoice.get('issue_date', ''),
            'due_date': invoice.get('due_date', ''),
            'status': invoice.get('status', 'unknown'),
            'created_at': datetime.now().isoformat(),
            'source': 'database'
        }

        # Add custom fields if available
        if 'custom_fields' in invoice:
            for key, value in invoice['custom_fields'].items():
                metadata[f'custom_{key}'] = str(value)

        return {
            'id': doc_id,
            'type': 'invoice',
            'metadata': metadata
        }

    def _extract_invoice_text(self, invoice: Dict[str, Any]) -> str:
        """Extract searchable text from invoice"""
        text_parts = []

        # Basic invoice info
        if invoice.get('invoice_number'):
            text_parts.append(f"Invoice Number: {invoice['invoice_number']}")
        if invoice.get('customer_name'):
            text_parts.append(f"Customer: {invoice['customer_name']}")
        if invoice.get('total_amount'):
            text_parts.append(f"Total Amount: {invoice['total_amount']} {invoice.get('currency', 'VND')}")

        # Dates
        if invoice.get('issue_date'):
            text_parts.append(f"Issue Date: {invoice['issue_date']}")
        if invoice.get('due_date'):
            text_parts.append(f"Due Date: {invoice['due_date']}")

        # Items
        if 'items' in invoice and invoice['items']:
            text_parts.append("Items:")
            for item in invoice['items']:
                item_text = f"- {item.get('description', '')}"
                if item.get('quantity'):
                    item_text += f" (Qty: {item['quantity']})"
                if item.get('unit_price'):
                    item_text += f" (Unit Price: {item['unit_price']})"
                if item.get('total'):
                    item_text += f" (Total: {item['total']})"
                text_parts.append(item_text)

        # Additional fields
        if invoice.get('notes'):
            text_parts.append(f"Notes: {invoice['notes']}")
        if invoice.get('payment_terms'):
            text_parts.append(f"Payment Terms: {invoice['payment_terms']}")

        return "\n".join(text_parts)

    def search_invoices(self, query: str, top_k: int = 5, search_type: str = "semantic") -> List[Dict[str, Any]]:
        """
        Search for relevant invoices

        Args:
            query: Search query
            top_k: Number of results to return
            search_type: Type of search ('semantic', 'hybrid', 'keyword')

        Returns:
            List of relevant invoice documents
        """
        if search_type == "semantic":
            return self.retrieval_service.retrieve_relevant_documents(query, top_k=top_k)
        elif search_type == "hybrid":
            return self.retrieval_service.hybrid_search(query, top_k=top_k)
        else:
            # For keyword search, we'd need to implement a different approach
            # For now, fall back to semantic search
            logger.warning(f"Search type '{search_type}' not fully implemented, using semantic search")
            return self.retrieval_service.retrieve_relevant_documents(query, top_k=top_k)

    def get_invoice_context(self, query: str, max_context_length: int = 4000) -> str:
        """
        Get context from relevant invoices for LLM

        Args:
            query: User query
            max_context_length: Maximum context length

        Returns:
            Formatted context string
        """
        # Search for relevant documents
        relevant_docs = self.search_invoices(query, top_k=3)

        # Prepare context
        context = self.retrieval_service.prepare_context(relevant_docs, max_context_length)

        return context

    def update_invoice_document(self, invoice_id: str, updated_invoice: Dict[str, Any]) -> bool:
        """
        Update an existing invoice document

        Args:
            invoice_id: ID of invoice to update
            updated_invoice: Updated invoice data

        Returns:
            Success status
        """
        try:
            # Delete old document
            self.vector_store.delete([invoice_id])

            # Add updated document
            self.add_invoice_documents([updated_invoice])

            logger.info(f"Updated invoice document: {invoice_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating invoice document {invoice_id}: {e}")
            return False

    def delete_invoice_documents(self, invoice_ids: List[str]) -> bool:
        """
        Delete invoice documents

        Args:
            invoice_ids: List of invoice IDs to delete

        Returns:
            Success status
        """
        return self.vector_store.delete(invoice_ids)

    def get_statistics(self) -> Dict[str, Any]:
        """Get vector store statistics"""
        return {
            'total_documents': self.vector_store.count(),
            'vector_store_type': self.vector_store_type,
            'embedding_model': self.embedding_service.model_name if hasattr(self.embedding_service, 'model_name') else 'unknown',
            'embedding_dimension': self.embedding_service.get_dimension(),
            'collection_name': getattr(self.vector_store, 'collection_name', 'unknown')
        }

    def clear_all_documents(self) -> bool:
        """Clear all documents from vector store"""
        return self.vector_store.clear()

    def export_documents(self, file_path: str) -> bool:
        """
        Export all documents to JSON file

        Args:
            file_path: Path to export file

        Returns:
            Success status
        """
        try:
            # This is a simplified export - in practice you'd need to implement
            # proper export functionality in the vector store
            stats = self.get_statistics()
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'metadata': stats,
                    'export_date': datetime.now().isoformat(),
                    'note': 'Full document export not implemented yet'
                }, f, indent=2, ensure_ascii=False)

            logger.info(f"Exported vector store metadata to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error exporting documents: {e}")
            return False

    def import_documents(self, file_path: str) -> bool:
        """
        Import documents from JSON file

        Args:
            file_path: Path to import file

        Returns:
            Success status
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # This is a placeholder - actual import would depend on file format
            logger.info(f"Imported data from {file_path} (placeholder implementation)")
            return True
        except Exception as e:
            logger.error(f"Error importing documents: {e}")
            return False