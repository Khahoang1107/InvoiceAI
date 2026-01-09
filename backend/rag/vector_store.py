"""
Vector Store Service using Pinecone for RAG functionality.
Stores and retrieves invoice embeddings for semantic search.
"""
import os
import hashlib
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from pinecone import Pinecone
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class VectorStoreService:
    """
    Service for managing invoice vectors in Pinecone.
    Uses sentence-transformers for embedding generation.
    """
    
    def __init__(self):
        """Initialize Pinecone connection and embedding model."""
        self.api_key = os.getenv("PINECONE_API_KEY")
        self.index_name = os.getenv("PINECONE_INDEX_NAME", "invoiceai-vectors")
        self.dimension = 1024  # Match Pinecone index dimension
        
        self.pc: Optional[Pinecone] = None
        self.index = None
        self.model: Optional[SentenceTransformer] = None
        self._initialized = False
        
    async def initialize(self) -> bool:
        """
        Initialize Pinecone and embedding model.
        Returns True if successful.
        """
        if self._initialized:
            return True
            
        try:
            # Check API key
            if not self.api_key:
                logger.warning("PINECONE_API_KEY not set - vector store disabled")
                return False
            
            # Initialize Pinecone client (new SDK syntax)
            self.pc = Pinecone(api_key=self.api_key)
            
            # Check if index exists
            indexes = self.pc.list_indexes().names()
            if self.index_name not in indexes:
                logger.warning(f"Pinecone index '{self.index_name}' not found")
                return False
            
            # Connect to index
            self.index = self.pc.Index(self.index_name)
            
            # Initialize embedding model (1024 dimensions)
            # Using a model that produces 1024-dim embeddings
            logger.info("Loading embedding model...")
            self.model = SentenceTransformer('BAAI/bge-large-en-v1.5')  # 1024 dimensions
            
            self._initialized = True
            logger.info(f"✅ Vector store initialized with index '{self.index_name}'")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            return False
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding vector for text."""
        if not self.model:
            raise RuntimeError("Embedding model not initialized")
        
        # Encode text to embedding
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def _create_document_id(self, invoice_id: int, chunk_index: int = 0) -> str:
        """Create unique document ID for Pinecone."""
        return f"invoice_{invoice_id}_chunk_{chunk_index}"
    
    async def store_invoice(
        self, 
        invoice_id: int,
        invoice_data: Dict[str, Any]
    ) -> bool:
        """
        Store invoice data as vectors in Pinecone.
        
        Args:
            invoice_id: Database ID of the invoice
            invoice_data: Invoice details to vectorize
            
        Returns:
            True if successful
        """
        if not self._initialized:
            if not await self.initialize():
                return False
        
        try:
            # Create searchable text from invoice data
            text_content = self._create_searchable_text(invoice_data)
            
            # Generate embedding
            embedding = self._generate_embedding(text_content)
            
            # Prepare metadata
            metadata = {
                "invoice_id": invoice_id,
                "invoice_number": str(invoice_data.get("invoice_number", "")),
                "client_name": str(invoice_data.get("client_name", "")),
                "vendor_name": str(invoice_data.get("vendor_name", "")),
                "amount": float(invoice_data.get("amount", 0)) if invoice_data.get("amount") else 0.0,
                "date": str(invoice_data.get("date", "")),
                "status": str(invoice_data.get("status", "")),
                "created_at": datetime.utcnow().isoformat()
            }
            
            # Create document ID
            doc_id = self._create_document_id(invoice_id)
            
            # Upsert to Pinecone
            self.index.upsert(
                vectors=[{
                    "id": doc_id,
                    "values": embedding,
                    "metadata": metadata
                }]
            )
            
            logger.info(f"✅ Stored invoice {invoice_id} in vector store")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store invoice {invoice_id}: {e}")
            return False
    
    def _create_searchable_text(self, invoice_data: Dict[str, Any]) -> str:
        """Create searchable text from invoice data."""
        parts = []
        
        if invoice_data.get("invoice_number"):
            parts.append(f"Invoice number: {invoice_data['invoice_number']}")
        
        if invoice_data.get("client_name"):
            parts.append(f"Client: {invoice_data['client_name']}")
            
        if invoice_data.get("vendor_name"):
            parts.append(f"Vendor: {invoice_data['vendor_name']}")
            
        if invoice_data.get("amount"):
            parts.append(f"Amount: {invoice_data['amount']}")
            
        if invoice_data.get("date"):
            parts.append(f"Date: {invoice_data['date']}")
            
        if invoice_data.get("description"):
            parts.append(f"Description: {invoice_data['description']}")
            
        if invoice_data.get("items"):
            items_text = ", ".join([str(item) for item in invoice_data['items']])
            parts.append(f"Items: {items_text}")
            
        if invoice_data.get("notes"):
            parts.append(f"Notes: {invoice_data['notes']}")
        
        return " | ".join(parts) if parts else "Invoice document"
    
    async def search(
        self,
        query: str,
        top_k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Semantic search for invoices.
        
        Args:
            query: Search query text
            top_k: Number of results to return
            filter_dict: Optional metadata filters
            
        Returns:
            List of matching invoice data with scores
        """
        if not self._initialized:
            if not await self.initialize():
                return []
        
        try:
            # Generate query embedding
            query_embedding = self._generate_embedding(query)
            
            # Search Pinecone
            results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                filter=filter_dict
            )
            
            # Format results
            formatted_results = []
            for match in results.get('matches', []):
                formatted_results.append({
                    "invoice_id": match['metadata'].get('invoice_id'),
                    "invoice_number": match['metadata'].get('invoice_number'),
                    "client_name": match['metadata'].get('client_name'),
                    "vendor_name": match['metadata'].get('vendor_name'),
                    "amount": match['metadata'].get('amount'),
                    "date": match['metadata'].get('date'),
                    "status": match['metadata'].get('status'),
                    "score": match['score']
                })
            
            logger.info(f"Found {len(formatted_results)} results for query: {query[:50]}...")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    async def delete_invoice(self, invoice_id: int) -> bool:
        """Delete invoice vectors from Pinecone."""
        if not self._initialized:
            if not await self.initialize():
                return False
        
        try:
            doc_id = self._create_document_id(invoice_id)
            self.index.delete(ids=[doc_id])
            logger.info(f"Deleted invoice {invoice_id} from vector store")
            return True
        except Exception as e:
            logger.error(f"Failed to delete invoice {invoice_id}: {e}")
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics."""
        if not self._initialized:
            if not await self.initialize():
                return {"error": "Not initialized"}
        
        try:
            stats = self.index.describe_index_stats()
            return {
                "total_vectors": stats.get('total_vector_count', 0),
                "dimension": stats.get('dimension', 0),
                "index_fullness": stats.get('index_fullness', 0)
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {"error": str(e)}


# Global instance
_vector_store: Optional[VectorStoreService] = None


def get_vector_store() -> VectorStoreService:
    """Get global vector store instance."""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStoreService()
    return _vector_store
