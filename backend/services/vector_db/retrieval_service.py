"""
Retrieval Service for RAG System

Handles document retrieval, ranking, and context preparation
for Retrieval-Augmented Generation.
"""

import re
from typing import List, Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class RetrievalService:
    """Service for retrieving relevant documents for RAG"""

    def __init__(self, vector_store, embedding_service, max_context_length: int = 4000):
        """
        Initialize retrieval service

        Args:
            vector_store: Vector store instance
            embedding_service: Embedding service instance
            max_context_length: Maximum context length in characters
        """
        self.vector_store = vector_store
        self.embedding_service = embedding_service
        self.max_context_length = max_context_length

    def retrieve_relevant_documents(self, query: str, top_k: int = 5, threshold: float = 0.0) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents for a query

        Args:
            query: Search query
            top_k: Number of top results to return
            threshold: Minimum similarity threshold

        Returns:
            List of relevant documents with scores
        """
        # Generate embedding for query
        query_embedding = self.embedding_service.encode_text(query)

        # Search vector store
        results = self.vector_store.search(query_embedding, top_k=top_k)

        # Filter by threshold
        filtered_results = [doc for doc in results if doc.get('score', 0) >= threshold]

        logger.info(f"Retrieved {len(filtered_results)} relevant documents for query: '{query[:50]}...'")
        return filtered_results

    def prepare_context(self, documents: List[Dict[str, Any]], max_length: Optional[int] = None) -> str:
        """
        Prepare context string from retrieved documents

        Args:
            documents: List of retrieved documents
            max_length: Maximum context length (overrides instance setting)

        Returns:
            Formatted context string
        """
        if not documents:
            return ""

        max_len = max_length or self.max_context_length
        context_parts = []
        current_length = 0

        for doc in documents:
            content = doc.get('content', '')
            if not content:
                continue

            # Add document header
            doc_header = self._create_document_header(doc)
            content_with_header = f"{doc_header}\n{content}\n"

            # Check if adding this document would exceed max length
            if current_length + len(content_with_header) > max_len:
                # Try to add partial content
                remaining_length = max_len - current_length - len(doc_header) - 2
                if remaining_length > 100:  # Minimum useful content length
                    truncated_content = content[:remaining_length] + "..."
                    context_parts.append(f"{doc_header}\n{truncated_content}\n")
                break

            context_parts.append(content_with_header)
            current_length += len(content_with_header)

        context = "".join(context_parts).strip()
        logger.info(f"Prepared context with {len(context)} characters from {len(context_parts)} documents")
        return context

    def _create_document_header(self, document: Dict[str, Any]) -> str:
        """Create a header for a document"""
        doc_id = document.get('id', 'unknown')
        doc_type = document.get('metadata', {}).get('document_type', 'document')
        score = document.get('score', 0)

        # Format score as percentage
        score_percent = f"{score:.1%}" if isinstance(score, (int, float)) else "N/A"

        return f"--- {doc_type.upper()} DOCUMENT (ID: {doc_id}, Relevance: {score_percent}) ---"

    def hybrid_search(self, query: str, keyword_boost: float = 0.1, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Perform hybrid search combining semantic and keyword search

        Args:
            query: Search query
            keyword_boost: Boost factor for keyword matches
            top_k: Number of results to return

        Returns:
            Ranked documents combining both search methods
        """
        # Get semantic search results
        semantic_results = self.retrieve_relevant_documents(query, top_k=top_k * 2)

        # Perform keyword search on the same documents
        keyword_results = self._keyword_search(query, semantic_results)

        # Combine scores
        combined_results = {}
        for doc in semantic_results:
            doc_id = doc['id']
            combined_results[doc_id] = {
                'document': doc,
                'semantic_score': doc.get('score', 0),
                'keyword_score': 0
            }

        for doc in keyword_results:
            doc_id = doc['id']
            if doc_id in combined_results:
                combined_results[doc_id]['keyword_score'] = doc.get('keyword_score', 0)

        # Calculate final scores and rank
        final_results = []
        for doc_id, scores in combined_results.items():
            semantic_score = scores['semantic_score']
            keyword_score = scores['keyword_score']

            # Combine scores (weighted average)
            final_score = semantic_score + (keyword_score * keyword_boost)
            doc = scores['document'].copy()
            doc['score'] = final_score
            doc['semantic_score'] = semantic_score
            doc['keyword_score'] = keyword_score

            final_results.append(doc)

        # Sort by final score and return top_k
        final_results.sort(key=lambda x: x['score'], reverse=True)
        return final_results[:top_k]

    def _keyword_search(self, query: str, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Perform keyword-based search on documents"""
        query_words = self._preprocess_query(query)
        results = []

        for doc in documents:
            content = doc.get('content', '').lower()
            score = self._calculate_keyword_score(query_words, content)
            if score > 0:
                result = doc.copy()
                result['keyword_score'] = score
                results.append(result)

        return results

    def _preprocess_query(self, query: str) -> List[str]:
        """Preprocess query for keyword search"""
        # Remove punctuation and split into words
        words = re.findall(r'\b\w+\b', query.lower())
        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were'}
        return [word for word in words if word not in stop_words and len(word) > 2]

    def _calculate_keyword_score(self, query_words: List[str], content: str) -> float:
        """Calculate keyword matching score"""
        if not query_words:
            return 0.0

        total_score = 0
        content_words = set(re.findall(r'\b\w+\b', content))

        for word in query_words:
            if word in content_words:
                # Exact match gets higher score
                total_score += 1.0
            else:
                # Partial match (word contained in content words)
                for content_word in content_words:
                    if word in content_word or content_word in word:
                        total_score += 0.5
                        break

        # Normalize by query length
        return total_score / len(query_words)

    def rerank_documents(self, query: str, documents: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Re-rank documents using more sophisticated scoring

        Args:
            query: Original query
            documents: Documents to rerank
            top_k: Number of top documents to return

        Returns:
            Re-ranked documents
        """
        if not documents:
            return []

        query_lower = query.lower()
        reranked = []

        for doc in documents:
            content = doc.get('content', '').lower()
            score = doc.get('score', 0)

            # Boost score based on various factors
            boost_factors = {
                'exact_match': 0.3 if query_lower in content else 0,
                'title_match': 0.2 if any(word in doc.get('metadata', {}).get('title', '').lower() for word in query_lower.split()) else 0,
                'recency': 0.1 if doc.get('metadata', {}).get('created_at') else 0,  # Boost recent documents
                'length_penalty': -0.1 if len(content) < 100 else 0  # Penalize very short documents
            }

            total_boost = sum(boost_factors.values())
            final_score = score + total_boost

            doc_copy = doc.copy()
            doc_copy['reranked_score'] = final_score
            doc_copy['boost_factors'] = boost_factors
            reranked.append(doc_copy)

        # Sort by reranked score
        reranked.sort(key=lambda x: x['reranked_score'], reverse=True)
        return reranked[:top_k]