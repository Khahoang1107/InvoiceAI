#!/usr/bin/env python3
"""Delete admin user to recreate"""
import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

database_url = os.getenv('DATABASE_URL')
if database_url:
    conn = psycopg2.connect(database_url)
else:
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '5432'),
        dbname=os.getenv('DB_NAME', 'invoice_ai_db'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'password')
    )

cur = conn.cursor()
cur.execute("DELETE FROM users WHERE email = %s", ('admin@example.com',))
conn.commit()
print(f'✅ Deleted {cur.rowcount} admin user(s)')
conn.close()
