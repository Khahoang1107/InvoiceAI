#!/usr/bin/env python3
"""
Setup and Populate RAG System for InvoiceAI

This script initializes the vector database and populates it with
invoice data from the existing database for RAG functionality.
"""

import sys
import os
import asyncio
from typing import List, Dict, Any

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.vector_db.vector_service import VectorService
from utils.database_tools import DatabaseTools

def get_invoices_from_database(db_tools) -> List[Dict[str, Any]]:
    """Extract invoices from database for RAG indexing"""
    try:
        # Get all invoices
        invoices_data = db_tools.get_all_invoices(limit=1000)  # Adjust limit as needed

        invoices = []
        for inv in invoices_data:
            # Transform database format to RAG format
            invoice = {
                "id": f"inv_{inv.get('id', inv.get('invoice_number', 'unknown'))}",
                "invoice_number": inv.get("invoice_number", ""),
                "customer_name": inv.get("customer_name", ""),
                "total_amount": float(inv.get("total_amount", 0)),
                "currency": inv.get("currency", "VND"),
                "issue_date": str(inv.get("issue_date", "")),
                "due_date": str(inv.get("due_date", "")),
                "status": inv.get("status", "unknown"),
                "items": inv.get("items", []),
                "notes": inv.get("notes", ""),
                "payment_terms": inv.get("payment_terms", "")
            }
            invoices.append(invoice)

        print(f"📄 Extracted {len(invoices)} invoices from database")
        return invoices

    except Exception as e:
        print(f"❌ Error extracting invoices from database: {e}")
        return []

async def setup_rag_system():
    """Setup and populate RAG system"""
    print("🚀 Setting up RAG System for InvoiceAI")
    print("=" * 50)

    try:
        # Initialize database tools
        print("🗄️  Initializing database connection...")
        db_tools = DatabaseTools()
        print("✅ Database connection established")

        # Extract invoices from database
        print("📊 Extracting invoice data...")
        invoices = get_invoices_from_database(db_tools)

        if not invoices:
            print("⚠️  No invoices found in database. Using sample data for testing...")
            # Create sample data if no real data exists
            invoices = [
                {
                    "id": "sample_001",
                    "invoice_number": "SAMPLE-001",
                    "customer_name": "Sample Customer",
                    "total_amount": 1000000,
                    "currency": "VND",
                    "issue_date": "2024-01-01",
                    "due_date": "2024-02-01",
                    "status": "paid",
                    "items": [{"description": "Sample service", "quantity": 1, "unit_price": 1000000, "total": 1000000}],
                    "notes": "Sample invoice for testing",
                    "payment_terms": "Net 30 days"
                }
            ]

        # Initialize vector service
        print("📚 Initializing Vector Service...")
        vector_service = VectorService(
            vector_store_type="chroma",
            embedding_service_type="sentence-transformers",
            embedding_model="all-MiniLM-L6-v2",
            persist_directory="./data/vector_db",
            collection_name="invoice_documents"
        )
        print("✅ Vector Service initialized")

        # Clear existing data (optional - comment out if you want to keep existing data)
        print("🧹 Clearing existing vector data...")
        vector_service.clear_all_documents()
        print("✅ Vector store cleared")

        # Add invoices to vector database
        print("📥 Adding invoices to vector database...")
        document_ids = vector_service.add_invoice_documents(invoices)
        print(f"✅ Added {len(document_ids)} documents to vector database")

        # Verify the setup
        print("🔍 Verifying setup...")
        stats = vector_service.get_statistics()
        print("📊 Vector Database Statistics:")
        print(f"   Total documents: {stats['total_documents']}")
        print(f"   Vector store type: {stats['vector_store_type']}")
        print(f"   Embedding model: {stats['embedding_model']}")
        print(f"   Embedding dimension: {stats['embedding_dimension']}")

        # Test search functionality
        print("🧪 Testing search functionality...")
        test_queries = [
            "hóa đơn chưa thanh toán",
            "khách hàng ABC",
            "tổng tiền lớn nhất"
        ]

        for query in test_queries:
            results = vector_service.search_invoices(query, top_k=2)
            print(f"   Query '{query}': {len(results)} results")

        print("\n🎉 RAG System setup completed successfully!")
        print("\n💡 Next steps:")
        print("   1. Update your main.py to initialize VectorService")
        print("   2. Integrate RAG into your GroqTools")
        print("   3. Test the enhanced chatbot functionality")
        print("   4. Run test_rag_system.py to verify everything works")

    except Exception as e:
        print(f"❌ Error during RAG setup: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main function"""
    print("🛠️  InvoiceAI RAG System Setup")
    print("=" * 40)

    # Run setup
    asyncio.run(setup_rag_system())

    print("\n🏁 Setup completed!")

if __name__ == "__main__":
    main()