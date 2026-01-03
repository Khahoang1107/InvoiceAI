#!/usr/bin/env python3
"""
Kiểm tra cấu trúc bảng users và hiển thị data
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')

conn = psycopg2.connect(DATABASE_URL)

with conn.cursor(cursor_factory=RealDictCursor) as cursor:
    # Lấy cấu trúc bảng users
    print("📋 Cấu trúc bảng USERS:")
    cursor.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'users'
        ORDER BY ordinal_position
    """)
    columns = cursor.fetchall()
    for col in columns:
        print(f"   - {col['column_name']}: {col['data_type']} (nullable: {col['is_nullable']})")
    
    # Lấy data users
    print("\n👥 Danh sách users:")
    cursor.execute("SELECT * FROM users LIMIT 5")
    users = cursor.fetchall()
    if users:
        for user in users:
            print(f"   - {dict(user)}")
    else:
        print("   (Không có user)")

conn.close()
