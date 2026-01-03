import os
from dotenv import load_dotenv
load_dotenv()

import psycopg2

conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cursor = conn.cursor()

cursor.execute("""
    SELECT column_name, data_type, character_maximum_length
    FROM information_schema.columns 
    WHERE table_name='invoices' 
    ORDER BY ordinal_position
""")

print("="*60)
print("📋 Invoices Table Schema:")
print("="*60)
for row in cursor.fetchall():
    col_name, data_type, max_len = row
    length = f"({max_len})" if max_len else ""
    print(f"  {col_name:20s} {data_type}{length}")

conn.close()
