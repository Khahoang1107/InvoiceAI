"""
Script embed invoice data vào RAG system (Pinecone)
Cho phép chatbot trả lời các query về hóa đơn
"""

import os
import sys
from datetime import datetime

# Add backend to path
sys.path.append('backend')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.models import Invoice
from pinecone import Pinecone
from groq import Groq

# ==================== CONFIG ====================

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost/invoiceai")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
PINECONE_INDEX_NAME = "invoiceai-rag"

# ==================== FUNCTIONS ====================

def create_invoice_document(invoice):
    """
    Tạo document text từ invoice data để embed
    """
    doc = f"""
Hóa đơn #{invoice.id}
Mã số: {invoice.invoice_number or 'N/A'}
Ngày: {invoice.invoice_date.strftime('%d/%m/%Y') if invoice.invoice_date else 'N/A'}
Đơn vị: {invoice.seller_name or 'N/A'}
Người mua: {invoice.buyer_name or 'N/A'}
Tổng tiền: {invoice.total_amount:,.0f} VND
Thuế: {invoice.tax_amount or 0:,.0f} VND
Thành tiền: {invoice.amount_in_words or 'N/A'}

Sản phẩm/Dịch vụ:
{invoice.items_description or 'Không có mô tả'}

Ghi chú: {invoice.notes or 'Không có'}
Trạng thái: {'Đã xử lý' if invoice.processed else 'Chưa xử lý'}
"""
    return doc.strip()


def get_embedding(text, groq_client):
    """
    Tạo embedding từ text sử dụng Groq
    (Thực tế nên dùng OpenAI embeddings hoặc sentence-transformers)
    """
    # Giả lập - trong thực tế dùng:
    # from sentence_transformers import SentenceTransformer
    # model = SentenceTransformer('all-MiniLM-L6-v2')
    # embedding = model.encode(text)
    
    # Mock embedding 768 dimensions
    import hashlib
    import numpy as np
    
    hash_obj = hashlib.sha256(text.encode())
    seed = int(hash_obj.hexdigest(), 16) % (2**32)
    np.random.seed(seed)
    embedding = np.random.rand(768).tolist()
    
    return embedding


def embed_invoices_to_pinecone():
    """
    Embed tất cả invoices vào Pinecone
    """
    print("=" * 80)
    print("🚀 EMBED INVOICE DATA VÀO RAG SYSTEM")
    print("=" * 80)
    print()
    
    # Connect to database
    print("📊 Kết nối database...")
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Get all invoices
    invoices = session.query(Invoice).all()
    print(f"✅ Tìm thấy {len(invoices)} hóa đơn")
    print()
    
    if len(invoices) == 0:
        print("⚠️ Không có dữ liệu hóa đơn để embed!")
        print("   Vui lòng upload hóa đơn trước hoặc tạo dữ liệu mẫu.")
        return
    
    # Initialize Pinecone
    print("🔧 Kết nối Pinecone...")
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index(PINECONE_INDEX_NAME)
    print(f"✅ Connected to index: {PINECONE_INDEX_NAME}")
    print()
    
    # Initialize Groq (for embedding generation)
    groq_client = Groq(api_key=GROQ_API_KEY)
    
    # Embed each invoice
    print("📝 Đang embed invoices...")
    vectors = []
    
    for i, invoice in enumerate(invoices, 1):
        # Create document text
        doc_text = create_invoice_document(invoice)
        
        # Generate embedding
        embedding = get_embedding(doc_text, groq_client)
        
        # Create metadata
        metadata = {
            "invoice_id": invoice.id,
            "invoice_number": invoice.invoice_number or "",
            "invoice_date": invoice.invoice_date.isoformat() if invoice.invoice_date else "",
            "seller_name": invoice.seller_name or "",
            "buyer_name": invoice.buyer_name or "",
            "total_amount": float(invoice.total_amount or 0),
            "tax_amount": float(invoice.tax_amount or 0),
            "processed": invoice.processed,
            "text": doc_text[:1000]  # Giới hạn 1000 ký tự
        }
        
        # Add to vectors
        vectors.append({
            "id": f"invoice_{invoice.id}",
            "values": embedding,
            "metadata": metadata
        })
        
        print(f"  [{i}/{len(invoices)}] Embedded invoice #{invoice.id}")
    
    # Upsert to Pinecone in batches
    print()
    print("💾 Uploading to Pinecone...")
    batch_size = 100
    for i in range(0, len(vectors), batch_size):
        batch = vectors[i:i+batch_size]
        index.upsert(vectors=batch)
        print(f"  Uploaded batch {i//batch_size + 1}/{(len(vectors)-1)//batch_size + 1}")
    
    print()
    print("=" * 80)
    print("✅ HOÀN THÀNH!")
    print("=" * 80)
    print(f"📊 Đã embed {len(invoices)} hóa đơn vào RAG system")
    print(f"🔍 Index: {PINECONE_INDEX_NAME}")
    print()
    print("🎯 Bây giờ chatbot có thể trả lời:")
    print("   • Tổng số tiền hóa đơn theo thời gian")
    print("   • Liệt kê hóa đơn theo giá trị/đơn vị")
    print("   • Tra cứu chi tiết hóa đơn")
    print("   • Thống kê theo tháng/nhà cung cấp")
    print()


def test_rag_queries():
    """
    Test RAG với các query mẫu
    """
    print("=" * 80)
    print("🧪 TEST RAG QUERIES")
    print("=" * 80)
    print()
    
    # Initialize Pinecone & Groq
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index(PINECONE_INDEX_NAME)
    groq_client = Groq(api_key=GROQ_API_KEY)
    
    # Test queries
    test_queries = [
        "Tổng số tiền tất cả hóa đơn là bao nhiêu?",
        "Liệt kê các hóa đơn trong tháng 12/2024",
        "Hóa đơn nào có giá trị cao nhất?",
        "Thống kê hóa đơn theo nhà cung cấp",
        "Cho tôi biết chi tiết hóa đơn số ABC123",
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*80}")
        print(f"📝 Query {i}: {query}")
        print('='*80)
        
        # Generate query embedding
        query_embedding = get_embedding(query, groq_client)
        
        # Search Pinecone
        results = index.query(
            vector=query_embedding,
            top_k=3,
            include_metadata=True
        )
        
        # Build context from results
        context = "Dữ liệu hóa đơn:\n\n"
        for match in results['matches']:
            metadata = match['metadata']
            context += f"- Hóa đơn #{metadata['invoice_id']}: {metadata.get('seller_name', 'N/A')}, "
            context += f"Ngày: {metadata.get('invoice_date', 'N/A')}, "
            context += f"Tổng tiền: {metadata.get('total_amount', 0):,.0f} VND\n"
        
        # Generate answer with Groq
        prompt = f"""Bạn là trợ lý AI quản lý hóa đơn. Dựa vào dữ liệu sau:

{context}

Trả lời câu hỏi: {query}

Trả lời ngắn gọn, chính xác và hữu ích."""
        
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Bạn là trợ lý quản lý hóa đơn thông minh."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=500
        )
        
        answer = completion.choices[0].message.content
        
        print(f"\n💬 Câu trả lời:")
        print(answer)
        print()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Embed invoice data to RAG system')
    parser.add_argument('--embed', action='store_true', help='Embed invoices to Pinecone')
    parser.add_argument('--test', action='store_true', help='Test RAG queries')
    parser.add_argument('--all', action='store_true', help='Embed and test')
    
    args = parser.parse_args()
    
    if args.all or args.embed:
        embed_invoices_to_pinecone()
    
    if args.all or args.test:
        test_rag_queries()
    
    if not any(vars(args).values()):
        print("Usage:")
        print("  python embed_invoices_to_rag.py --embed   # Embed invoices")
        print("  python embed_invoices_to_rag.py --test    # Test queries")
        print("  python embed_invoices_to_rag.py --all     # Both")
