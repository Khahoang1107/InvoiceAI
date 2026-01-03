"""
Add missing columns to invoices table for manual invoice creation
"""
import os
from dotenv import load_dotenv
load_dotenv()

import psycopg2

def add_missing_columns():
    db_url = os.getenv('DATABASE_URL')
    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()
    
    print("🔧 Adding missing columns to invoices table...\n")
    
    columns_to_add = [
        ("tax_code", "VARCHAR(100)", "Mã số thuế"),
        ("issue_date", "DATE", "Ngày phát hành"),
        ("status", "VARCHAR(50)", "Trạng thái hóa đơn"),
        ("notes", "TEXT", "Ghi chú"),
        ("items", "TEXT", "Danh sách sản phẩm (JSON)"),
        ("extracted_data", "TEXT", "Dữ liệu trích xuất (JSON)"),
        ("tax", "DOUBLE PRECISION", "Thuế VAT"),
        ("total_amount_numeric", "DOUBLE PRECISION", "Tổng tiền (số)"),
    ]
    
    for col_name, col_type, description in columns_to_add:
        try:
            # Check if column exists
            cursor.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name='invoices' AND column_name=%s
            """, (col_name,))
            
            if cursor.fetchone():
                print(f"⏭️  {col_name:25s} - Already exists")
            else:
                cursor.execute(f"ALTER TABLE invoices ADD COLUMN {col_name} {col_type}")
                conn.commit()
                print(f"✅ {col_name:25s} {col_type:20s} - {description}")
        
        except Exception as e:
            print(f"❌ {col_name:25s} - Error: {e}")
            conn.rollback()
    
    # Set defaults
    print("\n🔧 Setting default values...")
    try:
        cursor.execute("UPDATE invoices SET status = 'completed' WHERE status IS NULL")
        cursor.execute("UPDATE invoices SET tax = 0 WHERE tax IS NULL")
        cursor.execute("UPDATE invoices SET total_amount_numeric = total_amount_value WHERE total_amount_numeric IS NULL")
        conn.commit()
        print("✅ Default values set")
    except Exception as e:
        print(f"❌ Error setting defaults: {e}")
        conn.rollback()
    
    conn.close()
    print("\n✅ Schema update completed!")

if __name__ == "__main__":
    add_missing_columns()
