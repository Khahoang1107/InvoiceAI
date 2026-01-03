#!/usr/bin/env python3
import sqlite3
from datetime import datetime
from passlib.context import CryptContext

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# Connect to database
conn = sqlite3.connect('chatbot.db')
cursor = conn.cursor()

# Create admin user
admin_email = "admin@example.com"
admin_username = "admin"
admin_password = "admin123"
admin_full_name = "Administrator"
admin_role = "admin"

password_hash = get_password_hash(admin_password)
created_at = datetime.utcnow().isoformat()

try:
    cursor.execute("""
        INSERT INTO users (username, email, password_hash, full_name, role, is_active, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (admin_username, admin_email, password_hash, admin_full_name, admin_role, 1, created_at))
    
    conn.commit()
    print("✅ Admin user created successfully!")
    print(f"Email: {admin_email}")
    print(f"Password: {admin_password}")
    print("\n⚠️ IMPORTANT: Change password after first login!")
    
except sqlite3.IntegrityError:
    print("⚠️ User already exists")
except Exception as e:
    print(f"❌ Error: {e}")
finally:
    conn.close()
