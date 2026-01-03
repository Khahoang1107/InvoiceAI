"""
Vector Store Interface for RAG System

Supports multiple vector database backends:
- ChromaDB (local, persistent)
- FAISS (in-memory, fast)
- Pinecone (cloud, scalable)
"""

import os
import json
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

class VectorStore(ABC):
    """Abstract base class for vector stores"""

    @abstractmethod
    def add_documents(self, documents: List[Dict[str, Any]], embeddings: List[List[float]]) -> List[str]:
        """Add documents with their embeddings to the store"""
        pass

    @abstractmethod
    def search(self, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents using embedding"""
        pass

    @abstractmethod
    def delete(self, document_ids: List[str]) -> bool:
        """Delete documents by IDs"""
        pass

    @abstractmethod
    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific document by ID"""
        pass

    @abstractmethod
    def count(self) -> int:
        """Get total number of documents"""
        pass

    @abstractmethod
    def clear(self) -> bool:
        """Clear all documents"""
        pass


class ChromaVectorStore(VectorStore):
    """ChromaDB implementation of VectorStore"""

    def __init__(self, collection_name: str = "invoice_documents", persist_directory: str = "./data/vector_db"):
        try:
            import chromadb
            from chromadb.config import Settings

            self.collection_name = collection_name
            self.persist_directory = persist_directory

            # Ensure directory exists
            os.makedirs(persist_directory, exist_ok=True)

            # Initialize ChromaDB client
            self.client = chromadb.PersistentClient(
                path=persist_directory,
                settings=Settings(anonymized_telemetry=False)
            )

            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"description": "Invoice documents for RAG"}
            )

            logger.info(f"ChromaDB initialized with collection: {collection_name}")

        except ImportError:
            raise ImportError("ChromaDB not installed. Install with: pip install chromadb")

    def add_documents(self, documents: List[Dict[str, Any]], embeddings: List[List[float]]) -> List[str]:
        """Add documents with embeddings to ChromaDB"""
        if len(documents) != len(embeddings):
            raise ValueError("Number of documents must match number of embeddings")

        # Generate IDs if not provided
        ids = []
        metadatas = []
        documents_text = []

        for i, doc in enumerate(documents):
            doc_id = doc.get('id', f"doc_{len(ids)}")
            ids.append(doc_id)

            # Prepare metadata (exclude text content)
            metadata = {k: v for k, v in doc.items() if k not in ['content', 'text']}
            metadata['document_type'] = doc.get('type', 'invoice')
            metadatas.append(metadata)

            # Get text content
            text_content = doc.get('content', doc.get('text', ''))
            documents_text.append(text_content)

        # Add to collection
        self.collection.add(
            embeddings=embeddings,
            documents=documents_text,
            metadatas=metadatas,
            ids=ids
        )

        logger.info(f"Added {len(documents)} documents to vector store")
        return ids

    def search(self, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents"""
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=['documents', 'metadatas', 'distances']
        )

        # Format results
        search_results = []
        if results['ids'] and len(results['ids']) > 0:
            for i, doc_id in enumerate(results['ids'][0]):
                result = {
                    'id': doc_id,
                    'content': results['documents'][0][i] if results['documents'] else '',
                    'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                    'score': 1 - results['distances'][0][i] if results['distances'] else 0  # Convert distance to similarity
                }
                search_results.append(result)

        return search_results

    def delete(self, document_ids: List[str]) -> bool:
        """Delete documents by IDs"""
        try:
            self.collection.delete(ids=document_ids)
            logger.info(f"Deleted {len(document_ids)} documents")
            return True
        except Exception as e:
            logger.error(f"Error deleting documents: {e}")
            return False

    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get document by ID"""
        try:
            result = self.collection.get(ids=[document_id], include=['documents', 'metadatas'])
            if result['ids']:
                return {
                    'id': result['ids'][0],
                    'content': result['documents'][0] if result['documents'] else '',
                    'metadata': result['metadatas'][0] if result['metadatas'] else {}
                }
        except Exception as e:
            logger.error(f"Error getting document {document_id}: {e}")
        return None

    def count(self) -> int:
        """Get total number of documents"""
        return self.collection.count()

    def clear(self) -> bool:
        """Clear all documents"""
        try:
            # ChromaDB doesn't have a direct clear method, so we recreate the collection
            self.client.delete_collection(self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "Invoice documents for RAG"}
            )
            logger.info("Cleared all documents from vector store")
            return True
        except Exception as e:
            logger.error(f"Error clearing vector store: {e}")
            return False


class FAISSVectorStore(VectorStore):
    """FAISS implementation for in-memory vector search"""

    def __init__(self):
        try:
            import faiss
            self.dimension = None
            self.index = None
            self.documents = []
            self.id_to_idx = {}
            logger.info("FAISS vector store initialized")
        except ImportError:
            raise ImportError("FAISS not installed. Install with: pip install faiss-cpu")

    def add_documents(self, documents: List[Dict[str, Any]], embeddings: List[List[float]]) -> List[str]:
        """Add documents with embeddings to FAISS"""
        if not embeddings:
            return []

        try:
            import faiss
        except ImportError:
            raise ImportError("FAISS not installed. Install with: pip install faiss-cpu")

        # Initialize FAISS index if not exists
        if self.index is None:
            self.dimension = len(embeddings[0])
            self.index = faiss.IndexFlatIP(self.dimension)  # Inner product for cosine similarity

        # Convert to numpy array
        embeddings_array = np.array(embeddings, dtype=np.float32)

        # Add to index
        start_idx = len(self.documents)
        self.index.add(embeddings_array)

        # Store documents
        ids = []
        for i, doc in enumerate(documents):
            doc_id = doc.get('id', f"doc_{start_idx + i}")
            ids.append(doc_id)
            self.id_to_idx[doc_id] = start_idx + i
            self.documents.append(doc)

        logger.info(f"Added {len(documents)} documents to FAISS store")
        return ids

    def search(self, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """Search using FAISS"""
        if self.index is None or self.index.ntotal == 0:
            return []

        query_array = np.array([query_embedding], dtype=np.float32)
        scores, indices = self.index.search(query_array, min(top_k, self.index.ntotal))

        results = []
        for i, idx in enumerate(indices[0]):
            if idx != -1:  # Valid index
                doc = self.documents[idx]
                results.append({
                    'id': doc.get('id', f"doc_{idx}"),
                    'content': doc.get('content', doc.get('text', '')),
                    'metadata': {k: v for k, v in doc.items() if k not in ['content', 'text']},
                    'score': float(scores[0][i])
                })

        return results

    def delete(self, document_ids: List[str]) -> bool:
        """FAISS doesn't support efficient deletion, return False"""
        logger.warning("FAISS doesn't support document deletion")
        return False

    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get document by ID"""
        if document_id in self.id_to_idx:
            idx = self.id_to_idx[document_id]
            doc = self.documents[idx]
            return {
                'id': document_id,
                'content': doc.get('content', doc.get('text', '')),
                'metadata': {k: v for k, v in doc.items() if k not in ['content', 'text']}
            }
        return None

    def count(self) -> int:
        """Get total number of documents"""
        return len(self.documents) if self.documents else 0

    def clear(self) -> bool:
        """Clear all documents"""
        self.index = None
        self.documents = []
        self.id_to_idx = {}
        logger.info("Cleared FAISS vector store")
        return True


class PineconeVectorStore(VectorStore):
    """Pinecone implementation for cloud-based vector search"""

    def __init__(self, index_name: str = "invoice-rag", api_key: str = None, environment: str = None):
        try:
            import pinecone
            from pinecone import Pinecone, ServerlessSpec

            self.index_name = index_name
            self.api_key = api_key or os.getenv("PINECONE_API_KEY")
            self.environment = environment or os.getenv("PINECONE_ENVIRONMENT", "gcp-starter")

            if not self.api_key:
                raise ValueError("Pinecone API key not provided. Set PINECONE_API_KEY environment variable.")

            # Initialize Pinecone
            self.pc = Pinecone(api_key=self.api_key)

            # Check if index exists, create if not
            if self.index_name not in self.pc.list_indexes().names():
                self.pc.create_index(
                    name=self.index_name,
                    dimension=384,  # Sentence Transformers dimension
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region="us-east-1"
                    )
                )
                logger.info(f"Created new Pinecone index: {self.index_name}")

            # Connect to index
            self.index = self.pc.Index(self.index_name)
            logger.info(f"Pinecone vector store initialized with index: {self.index_name}")

        except ImportError:
            raise ImportError("Pinecone not installed. Install with: pip install pinecone-client")
        except Exception as e:
            raise Exception(f"Failed to initialize Pinecone: {e}")

    def add_documents(self, documents: List[Dict[str, Any]], embeddings: List[List[float]]) -> List[str]:
        """Add documents with embeddings to Pinecone"""
        if len(documents) != len(embeddings):
            raise ValueError("Number of documents must match number of embeddings")

        vectors = []
        ids = []

        for i, (doc, embedding) in enumerate(zip(documents, embeddings)):
            doc_id = doc.get('id', f"doc_{len(ids)}")
            ids.append(doc_id)

            # Prepare metadata (exclude text content from metadata to save space)
            metadata = {k: v for k, v in doc.items() if k not in ['content', 'text']}
            metadata['document_type'] = doc.get('type', 'invoice')

            # Get text content
            text_content = doc.get('content', doc.get('text', ''))

            # Pinecone vector format
            vector = {
                'id': doc_id,
                'values': embedding,
                'metadata': {
                    **metadata,
                    'text': text_content  # Store text in metadata for retrieval
                }
            }
            vectors.append(vector)

        # Upsert in batches (Pinecone recommends batches of 100 or less)
        batch_size = 100
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i:i + batch_size]
            self.index.upsert(vectors=batch)
            logger.info(f"Upserted batch {i//batch_size + 1} with {len(batch)} vectors")

        logger.info(f"Added {len(documents)} documents to Pinecone index")
        return ids

    def search(self, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents in Pinecone"""
        try:
            # Query Pinecone
            response = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                include_values=False
            )

            results = []
            for match in response['matches']:
                result = {
                    'id': match['id'],
                    'content': match['metadata'].get('text', ''),
                    'metadata': {k: v for k, v in match['metadata'].items() if k != 'text'},
                    'score': match['score']
                }
                results.append(result)

            return results

        except Exception as e:
            logger.error(f"Pinecone search failed: {e}")
            return []

    def delete(self, document_ids: List[str]) -> bool:
        """Delete documents by IDs from Pinecone"""
        try:
            self.index.delete(ids=document_ids)
            logger.info(f"Deleted {len(document_ids)} documents from Pinecone")
            return True
        except Exception as e:
            logger.error(f"Error deleting documents from Pinecone: {e}")
            return False

    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific document by ID from Pinecone"""
        try:
            response = self.index.fetch(ids=[document_id])
            if document_id in response['vectors']:
                vector_data = response['vectors'][document_id]
                metadata = vector_data.get('metadata', {})
                return {
                    'id': document_id,
                    'content': metadata.get('text', ''),
                    'metadata': {k: v for k, v in metadata.items() if k != 'text'}
                }
        except Exception as e:
            logger.error(f"Error getting document {document_id} from Pinecone: {e}")
        return None

    def count(self) -> int:
        """Get total number of documents in Pinecone index"""
        try:
            stats = self.index.describe_index_stats()
            return stats['total_vector_count']
        except Exception as e:
            logger.error(f"Error getting Pinecone index stats: {e}")
            return 0

    def clear(self) -> bool:
        """Clear all documents from Pinecone index"""
        try:
            # Delete all vectors (this might take time for large indexes)
            # Note: Pinecone doesn't have a direct clear method, so we delete all
            self.index.delete(delete_all=True)
            logger.info("Cleared all documents from Pinecone index")
            return True
        except Exception as e:
            logger.error(f"Error clearing Pinecone index: {e}")
            return False