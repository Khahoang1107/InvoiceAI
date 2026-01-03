#!/usr/bin/env python3
"""
Simple user creation script for Docker container
"""
import sys
sys.path.insert(0, '/app')

from sqlalchemy import create_engine, text
import os

# Get DATABASE_URL from environment
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:GMwwQpAoEifdnriKhrfzPEkCtGmmabQb@shinkansen.proxy.rlwy.net:16775/railway')

engine = create_engine(DATABASE_URL)

# Use bcrypt directly with simple hash
import bcrypt

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    # Truncate password to 72 bytes if needed
    password_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

def create_user(email: str, password: str, name: str, is_admin: bool = False):
    """Create a new user"""
    with engine.connect() as conn:
        # Check if user exists
        result = conn.execute(
            text("SELECT id FROM users WHERE email = :email"),
            {"email": email}
        )
        if result.fetchone():
            print(f"⚠️  User {email} already exists")
            return False
        
        # Hash password
        hashed_password = hash_password(password)
        
        # Insert user
        conn.execute(
            text("""
                INSERT INTO users (email, name, hashed_password, is_active, is_admin, role, created_at)
                VALUES (:email, :name, :password, :is_active, :is_admin, :role, NOW())
            """),
            {
                "email": email,
                "name": name,
                "password": hashed_password,
                "is_active": True,
                "is_admin": is_admin,
                "role": "admin" if is_admin else "user"
            }
        )
        conn.commit()
        print(f"✅ User created: {email} / {password}")
        print(f"   Name: {name}")
        print(f"   Role: {'admin' if is_admin else 'user'}")
        return True

if __name__ == "__main__":
    print("🔧 Creating default users for Docker...")
    
    # Create regular user
    create_user("user@test.com", "test123", "Test User", is_admin=False)
    
    # Create admin user
    create_user("admin@test.com", "admin123", "Admin User", is_admin=True)
    
    print("\n✅ Default users created!")
    print("   Regular: user@test.com / test123")
    print("   Admin: admin@test.com / admin123")
