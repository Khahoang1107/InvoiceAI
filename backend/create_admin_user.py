#!/usr/bin/env python3
"""
Create Admin User Script
========================

Script để tạo tài khoản admin đầu tiên cho hệ thống.
Support cả PostgreSQL và SQLite.
"""

import sys
import os
import sqlite3
from datetime import datetime
import bcrypt

# Password hashing with bcrypt directly
def get_password_hash(password: str) -> str:
    # Bcrypt requires bytes and has 72 byte limit
    password_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

def create_admin_user_sqlite():
    """Tạo admin user với SQLite"""
    print("🔧 Creating admin user with SQLite...")
    conn = None
    
    try:
        # Connect to SQLite database
        conn = sqlite3.connect('chatbot.db')
        cursor = conn.cursor()

        print("✅ SQLite database connection established")

        # Check if admin user already exists
        cursor.execute("SELECT id FROM users WHERE is_admin = 1 LIMIT 1")
        if cursor.fetchone():
            print("⚠️ Admin user already exists")
            return True

        # Create admin user
        admin_username = "admin"
        admin_email = "admin@example.com"
        admin_password = "admin123"  # Change this in production!

        password_hash = get_password_hash(admin_password)
        created_at = datetime.utcnow().isoformat()

        cursor.execute("""
            INSERT INTO users (email, name, hashed_password, is_admin, is_active, role, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            admin_email,
            "System Administrator",  # name
            password_hash,
            1,  # is_admin
            1,  # is_active
            'admin',  # role
            created_at
        ))

        admin_id = cursor.lastrowid
        conn.commit()

        print("✅ Admin user created successfully!")
        print(f"   Username: {admin_username}")
        print(f"   Email: {admin_email}")
        print(f"   Password: {admin_password}")
        print(f"   Role: Admin")
        print(f"   User ID: {admin_id}")
        print("\n🔐 Please change the default password after first login!")
        return True

    except Exception as e:
        print(f"❌ Error creating admin user: {str(e)}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def create_admin_user_postgres():
    """Tạo admin user với PostgreSQL"""
    print("🔧 Creating admin user with PostgreSQL...")
    conn = None
    admin_email = "admin@example.com"
    admin_password = "admin123"

    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        from dotenv import load_dotenv

        # Load environment variables
        load_dotenv()

        # Try to get DATABASE_URL first, then individual vars
        database_url = os.getenv('DATABASE_URL')
        if database_url:
            conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
        else:
            # Fallback to individual variables
            DB_HOST = os.getenv('DB_HOST', 'localhost')
            DB_PORT = os.getenv('DB_PORT', '5432')
            DB_NAME = os.getenv('DB_NAME', 'invoice_ai_db')
            DB_USER = os.getenv('DB_USER', 'postgres')
            DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')

            conn = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                cursor_factory=RealDictCursor
            )

        conn.autocommit = False
        print("✅ PostgreSQL database connection established")

    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {str(e)}")
        print("💡 Falling back to SQLite...")
        return create_admin_user_sqlite()

    try:
        with conn.cursor() as cursor:
            # Check if admin user already exists
            cursor.execute("SELECT id FROM users WHERE is_admin = %s LIMIT 1", (1,))
            if cursor.fetchone():
                print("⚠️ Admin user already exists")
                return True

            # Create admin user
            admin_username = "admin"

            # Hash password with bcrypt
            password_hash = get_password_hash(admin_password)

            cursor.execute("""
                INSERT INTO users (email, name, hashed_password, is_admin, is_active, role, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
                RETURNING id
            """, (
                admin_email,
                "System Administrator",  # name
                password_hash,
                1,  # is_admin
                1,  # is_active
                'admin',  # role
            ))

            result = cursor.fetchone()
            if result:
                # RealDictCursor returns dict-like row
                admin_id = result['id'] if isinstance(result, dict) else result[0]
                conn.commit()
                print("✅ Admin user created successfully!")
                print(f"   Email: {admin_email}")
                print(f"   Password: {admin_password}")
                print(f"   Role: Admin")
                print(f"   User ID: {admin_id}")
                print("\n🔐 Please change the default password after first login!")
                return True
            else:
                print("❌ Failed to create admin user")
                return False

    except psycopg2.IntegrityError as e:
        if "duplicate key" in str(e).lower():
            print("⚠️ Admin user already exists!")
            print(f"   Email: {admin_email}")
            print(f"   Password: {admin_password} (if you remember it)")
            print("\n💡 Try logging in with these credentials, or change the email in the script if needed.")
            return True
        else:
            if conn:
                conn.rollback()
            print(f"❌ Database integrity error: {str(e)}")
            return False
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"❌ Error creating admin user: {str(e)}")
        return False
    finally:
        if conn:
            conn.close()

def create_admin_user():
    """Tạo tài khoản admin - thử PostgreSQL trước, fallback to SQLite"""
    # Try PostgreSQL first
    try:
        return create_admin_user_postgres()
    except ImportError:
        print("⚠️ psycopg2 not available, using SQLite...")
        return create_admin_user_sqlite()

if __name__ == "__main__":
    success = create_admin_user()
    sys.exit(0 if success else 1)