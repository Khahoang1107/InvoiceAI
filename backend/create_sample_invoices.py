"""
Tạo dữ liệu hóa đơn mẫu để train AI
"""
import os
import sys
from dotenv import load_dotenv
load_dotenv()

import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
import json

# Sample invoices data
SAMPLE_INVOICES = [
    {
        "invoice_number": "INV-2024-001",
        "vendor": "Công ty TNHH Điện máy Xanh",
        "tax_code": "0123456789",
        "customer_name": "Công ty CP Công nghệ ABC",
        "customer_email": "abc@company.com",
        "customer_address": "123 Đường Lê Lợi, Q1, TP.HCM",
        "issue_date": (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d"),
        "due_date": (datetime.now() + timedelta(days=20)).strftime("%Y-%m-%d"),
        "status": "completed",
        "items": [
            {"name": "Laptop Dell Inspiron 15", "quantity": 5, "price": 15000000, "total": 75000000},
            {"name": "Chuột không dây Logitech", "quantity": 10, "price": 350000, "total": 3500000},
            {"name": "Bàn phím cơ gaming", "quantity": 5, "price": 1200000, "total": 6000000}
        ],
        "notes": "Giao hàng trong 2 tuần. Bảo hành 24 tháng."
    },
    {
        "invoice_number": "INV-2024-002",
        "vendor": "Công ty TNHH Văn phòng phẩm Thiên Long",
        "tax_code": "0987654321",
        "customer_name": "Trường Đại học Khoa học Tự nhiên",
        "customer_email": "procurement@university.edu.vn",
        "customer_address": "227 Nguyễn Văn Cừ, Q5, TP.HCM",
        "issue_date": (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d"),
        "due_date": (datetime.now() + timedelta(days=25)).strftime("%Y-%m-%d"),
        "status": "processing",
        "items": [
            {"name": "Bút bi Thiên Long TL-079", "quantity": 500, "price": 3000, "total": 1500000},
            {"name": "Sổ tay A5 cao cấp", "quantity": 200, "price": 25000, "total": 5000000},
            {"name": "Giấy A4 80gsm (1 thùng)", "quantity": 20, "price": 85000, "total": 1700000}
        ],
        "notes": "Giao hàng từng đợt theo yêu cầu"
    },
    {
        "invoice_number": "INV-2024-003",
        "vendor": "Công ty CP Thực phẩm Vissan",
        "tax_code": "0111222333",
        "customer_name": "Nhà hàng Á Đông",
        "customer_email": "adong@restaurant.vn",
        "customer_address": "456 Hai Bà Trưng, Q3, TP.HCM",
        "issue_date": (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d"),
        "due_date": (datetime.now() + timedelta(days=13)).strftime("%Y-%m-%d"),
        "status": "pending",
        "items": [
            {"name": "Thịt heo ba chỉ (10kg)", "quantity": 5, "price": 850000, "total": 4250000},
            {"name": "Gà ta nguyên con (1kg)", "quantity": 20, "price": 180000, "total": 3600000},
            {"name": "Tôm sú size L (1kg)", "quantity": 10, "price": 320000, "total": 3200000}
        ],
        "notes": "Giao hàng tươi sống vào sáng sớm"
    },
    {
        "invoice_number": "INV-2024-004",
        "vendor": "Công ty TNHH Nội thất Hòa Phát",
        "tax_code": "0444555666",
        "customer_name": "Công ty CP Xây dựng Minh Phát",
        "customer_email": "minhphat@construction.vn",
        "customer_address": "789 Lê Văn Việt, Q9, TP.HCM",
        "issue_date": (datetime.now() - timedelta(days=15)).strftime("%Y-%m-%d"),
        "due_date": (datetime.now() + timedelta(days=15)).strftime("%Y-%m-%d"),
        "status": "completed",
        "items": [
            {"name": "Bàn làm việc 1m4", "quantity": 50, "price": 2500000, "total": 125000000},
            {"name": "Ghế xoay văn phòng", "quantity": 50, "price": 1800000, "total": 90000000},
            {"name": "Tủ hồ sơ 4 ngăn", "quantity": 30, "price": 3200000, "total": 96000000}
        ],
        "notes": "Lắp đặt tại văn phòng mới trong tháng 12"
    },
    {
        "invoice_number": "INV-2024-005",
        "vendor": "Công ty TNHH Dược phẩm Hà Tây",
        "tax_code": "0777888999",
        "customer_name": "Phòng khám Đa khoa Quốc tế",
        "customer_email": "info@internationalclinic.vn",
        "customer_address": "321 Cộng Hòa, Tân Bình, TP.HCM",
        "issue_date": datetime.now().strftime("%Y-%m-%d"),
        "due_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
        "status": "pending",
        "items": [
            {"name": "Paracetamol 500mg (100 viên)", "quantity": 50, "price": 45000, "total": 2250000},
            {"name": "Amoxicillin 500mg (100 viên)", "quantity": 30, "price": 120000, "total": 3600000},
            {"name": "Khẩu trang y tế 4 lớp (hộp 50 cái)", "quantity": 100, "price": 85000, "total": 8500000}
        ],
        "notes": "Cần giấy phép lưu hành thuốc"
    }
]

def create_sample_invoices():
    """Tạo hóa đơn mẫu vào database"""
    db_url = os.getenv('DATABASE_URL')
    
    if not db_url:
        print("❌ DATABASE_URL not found in .env")
        return
    
    print("🔗 Connecting to database...")
    conn = psycopg2.connect(db_url, cursor_factory=RealDictCursor)
    cursor = conn.cursor()
    
    user_id = 16  # Admin user
    created_count = 0
    skipped_count = 0
    
    print("\n📝 Creating sample invoices...\n")
    
    for invoice in SAMPLE_INVOICES:
        # Check if exists
        cursor.execute(
            "SELECT id FROM invoices WHERE invoice_number = %s",
            (invoice['invoice_number'],)
        )
        
        if cursor.fetchone():
            print(f"⏭️  Skipped: {invoice['invoice_number']} (already exists)")
            skipped_count += 1
            continue
        
        # Calculate totals
        items = invoice['items']
        amount = sum(item['total'] for item in items)
        tax = amount * 0.1  # 10% VAT
        total_amount = amount + tax
        
        # Prepare extracted_data
        extracted_data = {
            "customer": {
                "name": invoice['customer_name'],
                "email": invoice['customer_email'],
                "address": invoice['customer_address']
            },
            "vendor": {
                "name": invoice['vendor'],
                "tax_code": invoice['tax_code']
            },
            "items": items,
            "subtotal": amount,
            "tax": tax,
            "total": total_amount,
            "dates": {
                "issue": invoice['issue_date'],
                "due": invoice['due_date']
            }
        }
        
        # Insert invoice
        cursor.execute("""
            INSERT INTO invoices (
                user_id, invoice_number, vendor, tax_code,
                issue_date, due_date, amount, tax, total_amount_numeric,
                status, notes, items, extracted_data, created_at,
                filename, filepath, invoice_code, invoice_type
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            user_id,
            invoice['invoice_number'],
            invoice['vendor'],
            invoice['tax_code'],
            invoice['issue_date'],
            invoice['due_date'],
            amount,
            tax,
            total_amount,
            invoice['status'],
            invoice['notes'],
            json.dumps(items, ensure_ascii=False),
            json.dumps(extracted_data, ensure_ascii=False),
            datetime.now(),
            f"{invoice['invoice_number']}.json",  # filename
            f"/manual/{invoice['invoice_number']}.json",  # filepath
            invoice['invoice_number'],  # invoice_code
            'general'  # invoice_type
        ))
        
        result = cursor.fetchone()
        conn.commit()
        
        print(f"✅ Created: {invoice['invoice_number']} (ID: {result['id']}) - {invoice['customer_name']}")
        print(f"   💰 Total: ₫{total_amount:,.0f} ({len(items)} items)")
        created_count += 1
    
    conn.close()
    
    print(f"\n{'='*60}")
    print(f"✅ Created: {created_count} invoices")
    print(f"⏭️  Skipped: {skipped_count} invoices")
    print(f"📊 Total in database: {created_count + skipped_count}")
    print(f"{'='*60}\n")
    
    print("🤖 AI Training Summary:")
    print("- Các loại hóa đơn: Điện máy, Văn phòng phẩm, Thực phẩm, Nội thất, Dược phẩm")
    print("- Trạng thái: pending, processing, completed")
    print("- Tổng giá trị: ₫" + f"{sum(sum(item['total'] for item in inv['items']) * 1.1 for inv in SAMPLE_INVOICES):,.0f}")
    print("\n🎯 Test Chatbot với câu hỏi:")
    print("  1. 'Có bao nhiêu hóa đơn?'")
    print("  2. 'Tìm hóa đơn của Công ty ABC'")
    print("  3. 'Hóa đơn nào đang pending?'")
    print("  4. 'Tổng giá trị hóa đơn tháng này?'")
    print("  5. 'Hóa đơn của nhà cung cấp Điện máy Xanh'")

if __name__ == "__main__":
    create_sample_invoices()
