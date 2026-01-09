"""Quick data check using config"""
import sys
import os
sys.path.insert(0, 'd:\\110122008\\InvoiceAI\\backend')

from dotenv import load_dotenv
import psycopg2
import json

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')

print("Connecting to database...")
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# Count invoices by user
cur.execute("""
    SELECT user_id, COUNT(*) as count
    FROM invoices
    GROUP BY user_id
    ORDER BY user_id
""")
print("\n📊 INVOICES BY USER:")
for row in cur.fetchall():
    print(f"   User {row[0]}: {row[1]} hóa đơn")

# Get recent 5 invoices
cur.execute("""
    SELECT id, user_id, invoice_number, seller_name, buyer_name, total_amount, created_at
    FROM invoices
    ORDER BY created_at DESC
    LIMIT 5
""")
print("\n📋 5 HÓA ĐƠN MỚI NHẤT:")
for row in cur.fetchall():
    print(f"   ID:{row[0]} | User:{row[1]} | Mã:{row[2]} | Seller:{row[3]} | Buyer:{row[4]} | Amount:{row[5]} | {row[6]}")

# Check user 2 invoices
cur.execute("""
    SELECT COUNT(*) FROM invoices WHERE user_id = 2
""")
count = cur.fetchone()[0]
print(f"\n👤 User ID 2 (User01@gmail.com) có: {count} hóa đơn")

conn.close()
