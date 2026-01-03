#!/usr/bin/env python3
"""Check admin user info"""
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
cur.execute('SELECT id, email, name, role, is_admin, is_active FROM users WHERE email = %s', ('admin@example.com',))
row = cur.fetchone()
if row:
    print(f'📊 Admin User Info:')
    print(f'   ID: {row[0]}')
    print(f'   Email: {row[1]}')
    print(f'   Name: {row[2]}')
    print(f'   Role: {row[3]}')
    print(f'   Is_Admin: {row[4]}')
    print(f'   Is_Active: {row[5]}')
else:
    print('❌ User not found')
conn.close()
