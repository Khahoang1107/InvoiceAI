#!/usr/bin/env python3
"""
Migrate Vector Data to Pinecone

This script migrates existing vector data from FAISS or ChromaDB
to Pinecone for the chat service RAG system.
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Any

# Add backend to path
import sys
sys.path.append(str(Path(__file__).parent))

from services.vector_db.vector_store import FAISSVectorStore, ChromaVectorStore, PineconeVectorStore
from services.vector_db.embedding_service import EmbeddingService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class VectorMigrator:
    """Migrates vector data between different stores"""

    def __init__(self):
        self.embedding_service = EmbeddingService()

    def migrate_from_faiss(self, faiss_store_path: str = None) -> bool:
        """Migrate data from FAISS to Pinecone"""
        try:
            logger.info("Starting migration from FAISS to Pinecone...")

            # Initialize stores
            faiss_store = FAISSVectorStore()
            pinecone_store = PineconeVectorStore()

            # Check if FAISS has data
            if faiss_store.count() == 0:
                logger.warning("No data found in FAISS store")
                return False

            logger.info(f"Found {faiss_store.count()} documents in FAISS")

            # Get all documents from FAISS
            documents = []
            for i in range(faiss_store.count()):
                doc_id = f"doc_{i}"
                doc = faiss_store.get_document(doc_id)
                if doc:
                    documents.append(doc)

            if not documents:
                logger.warning("No documents retrieved from FAISS")
                return False

            # Generate embeddings for documents
            logger.info("Generating embeddings for documents...")
            texts = [doc['content'] for doc in documents]
            embeddings = self.embedding_service.encode_texts(texts)

            # Add to Pinecone
            logger.info("Adding documents to Pinecone...")
            pinecone_store.add_documents(documents, embeddings)

            logger.info(f"✅ Successfully migrated {len(documents)} documents to Pinecone")
            return True

        except Exception as e:
            logger.error(f"❌ Migration from FAISS failed: {e}")
            return False

    def migrate_from_chromadb(self, chroma_path: str = "./data/vector_db") -> bool:
        """Migrate data from ChromaDB to Pinecone"""
        try:
            logger.info("Starting migration from ChromaDB to Pinecone...")

            # Initialize stores
            chroma_store = ChromaVectorStore(persist_directory=chroma_path)
            pinecone_store = PineconeVectorStore()

            # Check if ChromaDB has data
            count = chroma_store.count()
            if count == 0:
                logger.warning("No data found in ChromaDB store")
                return False

            logger.info(f"Found {count} documents in ChromaDB")

            # Note: ChromaDB doesn't provide easy way to get all documents
            # This is a simplified migration - in practice, you'd need to
            # re-process the original invoice files
            logger.warning("ChromaDB migration requires re-processing original files")
            logger.info("Please use the upload API to re-index your invoices to Pinecone")

            return False

        except Exception as e:
            logger.error(f"❌ Migration from ChromaDB failed: {e}")
            return False

    def verify_migration(self) -> bool:
        """Verify that migration was successful"""
        try:
            pinecone_store = PineconeVectorStore()
            count = pinecone_store.count()

            if count > 0:
                logger.info(f"✅ Pinecone has {count} documents")
                return True
            else:
                logger.warning("❌ Pinecone appears to be empty")
                return False

        except Exception as e:
            logger.error(f"❌ Verification failed: {e}")
            return False


def main():
    """Main migration function"""
    print("🔄 Vector Data Migration Tool")
    print("=" * 40)
    print("This tool migrates existing vector data to Pinecone")
    print()

    # Check environment
    pinecone_key = os.getenv("PINECONE_API_KEY")
    pinecone_env = os.getenv("PINECONE_ENVIRONMENT")

    if not pinecone_key or not pinecone_env:
        print("❌ Pinecone credentials not found!")
        print("Please set PINECONE_API_KEY and PINECONE_ENVIRONMENT environment variables")
        return

    print("✅ Pinecone credentials found")

    migrator = VectorMigrator()

    # Try to migrate from FAISS
    print("\n1. Attempting migration from FAISS...")
    if migrator.migrate_from_faiss():
        print("✅ FAISS migration completed")
    else:
        print("⚠️  FAISS migration skipped or failed")

    # Try to migrate from ChromaDB
    print("\n2. Attempting migration from ChromaDB...")
    if migrator.migrate_from_chromadb():
        print("✅ ChromaDB migration completed")
    else:
        print("⚠️  ChromaDB migration skipped (requires re-processing)")

    # Verify
    print("\n3. Verifying migration...")
    if migrator.verify_migration():
        print("✅ Migration verification passed")
        print("\n🎉 Migration completed successfully!")
        print("You can now use the chat service with Pinecone RAG.")
    else:
        print("❌ Migration verification failed")
        print("Please check your Pinecone configuration and try again.")


if __name__ == "__main__":
    main()