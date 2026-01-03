#!/usr/bin/env python3
"""
Script kiểm tra kết nối database cloud (PostgreSQL)
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')

print("="*60)
print("🔍 KIỂM TRA KẾT NỐI DATABASE CLOUD")
print("="*60)
print(f"\n📍 DATABASE_URL: {DATABASE_URL[:50]}..." if DATABASE_URL and len(DATABASE_URL) > 50 else f"\n📍 DATABASE_URL: {DATABASE_URL}")

if not DATABASE_URL:
    print("\n❌ Không tìm thấy DATABASE_URL trong file .env")
    sys.exit(1)

# Kiểm tra loại database
if DATABASE_URL.startswith('postgresql://') or DATABASE_URL.startswith('postgres://'):
    print("✅ Phát hiện PostgreSQL database")
    
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        
        print("\n🔌 Đang kết nối đến database...")
        
        # Kết nối
        conn = psycopg2.connect(DATABASE_URL)
        print("✅ Kết nối thành công!")
        
        # Kiểm tra tables
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            tables = cursor.fetchall()
            
            print(f"\n📊 Các bảng trong database: {len(tables)}")
            for table in tables:
                print(f"   - {table['table_name']}")
            
            # Kiểm tra users
            print("\n👥 Kiểm tra bảng USERS:")
            cursor.execute("SELECT COUNT(*) as count FROM users")
            user_count = cursor.fetchone()['count']
            print(f"   Tổng số users: {user_count}")
            
            if user_count > 0:
                cursor.execute("SELECT id, email, username, role FROM users LIMIT 5")
                users = cursor.fetchall()
                print("\n   Danh sách users:")
                for user in users:
                    print(f"   - ID: {user['id']}, Email: {user['email']}, Username: {user['username']}, Role: {user['role']}")
            else:
                print("   ⚠️ Chưa có user nào trong database")
            
            # Kiểm tra invoices
            print("\n📄 Kiểm tra bảng INVOICES:")
            cursor.execute("SELECT COUNT(*) as count FROM invoices")
            invoice_count = cursor.fetchone()['count']
            print(f"   Tổng số invoices: {invoice_count}")
        
        conn.close()
        print("\n✅ Kiểm tra hoàn tất!")
        
    except ImportError:
        print("\n❌ Thiếu thư viện psycopg2!")
        print("Cài đặt: pip install psycopg2-binary")
    except Exception as e:
        print(f"\n❌ Lỗi kết nối: {e}")
        
elif DATABASE_URL.startswith('sqlite'):
    print("⚠️ Đang dùng SQLite local, không phải cloud database")
    print("Vui lòng cập nhật DATABASE_URL trong file .env với URL cloud database của bạn")
else:
    print(f"❌ Không nhận diện được loại database: {DATABASE_URL[:30]}")

print("\n" + "="*60)
