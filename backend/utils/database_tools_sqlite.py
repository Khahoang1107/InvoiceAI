"""
Simple SQLite Database Tools for ChatBotAI
"""

import sqlite3
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class DatabaseTools:
    """Simple SQLite database tools"""

    def __init__(self, connection_string: str = None):
        """Initialize SQLite database connection"""
        if connection_string is None:
            connection_string = os.getenv("DATABASE_URL", "sqlite:///./chatbot.db")

        # Convert from SQLAlchemy format to SQLite path
        if connection_string.startswith("sqlite:///"):
            self.db_path = connection_string.replace("sqlite:///", "")
        else:
            self.db_path = "chatbot.db"

        logger.info(f"Using SQLite database: {self.db_path}")

    def connect(self):
        """Get SQLite connection"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable column access by name
            return conn
        except Exception as e:
            logger.error(f"Failed to connect to SQLite: {e}")
            return None

    def initialize_tables(self):
        """Create necessary tables if they don't exist"""
        try:
            conn = self.connect()
            if not conn:
                return False

            cursor = conn.cursor()

            # Create invoices table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS invoices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    filepath TEXT,
                    invoice_code TEXT,
                    invoice_type TEXT DEFAULT 'general',
                    date TEXT,
                    seller_name TEXT,
                    seller_address TEXT,
                    seller_tax_id TEXT,
                    buyer_name TEXT,
                    buyer_address TEXT,
                    buyer_tax_id TEXT,
                    subtotal REAL DEFAULT 0,
                    tax_percentage REAL DEFAULT 0,
                    tax_amount REAL DEFAULT 0,
                    total_amount TEXT,
                    total_amount_value REAL DEFAULT 0,
                    currency TEXT DEFAULT 'VND',
                    confidence_score REAL DEFAULT 0,
                    ocr_text TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    name TEXT,
                    hashed_password TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    is_admin INTEGER DEFAULT 0,
                    role TEXT DEFAULT 'user',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP
                )
            """)

            conn.commit()
            conn.close()
            logger.info("✅ Database tables initialized successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to initialize tables: {e}")
            return False

    def save_invoice(self, invoice_data: Dict[str, Any]) -> Optional[int]:
        """Save invoice to database and return the invoice ID"""
        try:
            conn = self.connect()
            if not conn:
                return None

            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO invoices (
                    filename, filepath, invoice_code, invoice_type, date,
                    seller_name, seller_address, seller_tax_id,
                    buyer_name, buyer_address, buyer_tax_id,
                    subtotal, tax_percentage, tax_amount,
                    total_amount, total_amount_value, currency,
                    confidence_score, ocr_text
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                invoice_data.get('filename'),
                invoice_data.get('filepath'),
                invoice_data.get('invoice_code'),
                invoice_data.get('invoice_type', 'general'),
                invoice_data.get('date'),
                invoice_data.get('seller_name'),
                invoice_data.get('seller_address'),
                invoice_data.get('seller_tax_id'),
                invoice_data.get('buyer_name'),
                invoice_data.get('buyer_address'),
                invoice_data.get('buyer_tax_id'),
                invoice_data.get('subtotal', 0),
                invoice_data.get('tax_percentage', 0),
                invoice_data.get('tax_amount', 0),
                invoice_data.get('total_amount'),
                invoice_data.get('total_amount_value', 0),
                invoice_data.get('currency', 'VND'),
                invoice_data.get('confidence_score', 0),
                invoice_data.get('ocr_text')
            ))

            invoice_id = cursor.lastrowid
            conn.commit()
            conn.close()

            logger.info(f"✅ Invoice saved with ID: {invoice_id}")
            return invoice_id

        except Exception as e:
            logger.error(f"❌ Failed to save invoice: {e}")
            return None

    def get_all_invoices(self, limit: int = 20) -> List[Dict]:
        """Get all invoices from database"""
        try:
            conn = self.connect()
            if not conn:
                return []

            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM invoices 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (limit,))

            rows = cursor.fetchall()
            conn.close()

            invoices = [dict(row) for row in rows]
            logger.info(f"✅ Retrieved {len(invoices)} invoices from database")
            return invoices

        except Exception as e:
            logger.error(f"❌ Error getting invoices: {e}")
            return []

    def search_invoices(self, query: str, limit: int = 20) -> List[Dict]:
        """Search invoices by query"""
        try:
            conn = self.connect()
            if not conn:
                return []

            cursor = conn.cursor()
            search_pattern = f"%{query}%"
            
            cursor.execute("""
                SELECT * FROM invoices 
                WHERE filename LIKE ? OR invoice_code LIKE ? 
                   OR seller_name LIKE ? OR buyer_name LIKE ?
                ORDER BY created_at DESC 
                LIMIT ?
            """, (search_pattern, search_pattern, search_pattern, search_pattern, limit))

            rows = cursor.fetchall()
            conn.close()

            results = [dict(row) for row in rows]
            logger.info(f"✅ Found {len(results)} invoices matching '{query}'")
            return results

        except Exception as e:
            logger.error(f"❌ Error searching invoices: {e}")
            return []

    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            conn = self.connect()
            if not conn:
                return {}

            cursor = conn.cursor()

            # Total invoices
            cursor.execute("SELECT COUNT(*) as count FROM invoices")
            total_invoices = cursor.fetchone()['count']

            # Average confidence
            cursor.execute("SELECT AVG(confidence_score) as avg FROM invoices")
            avg_confidence = cursor.fetchone()['avg'] or 0

            # Invoice types distribution
            cursor.execute("SELECT invoice_type, COUNT(*) as count FROM invoices GROUP BY invoice_type")
            invoice_types = {row['invoice_type']: row['count'] for row in cursor.fetchall()}

            # Recent 7 days
            cursor.execute("""
                SELECT COUNT(*) as count FROM invoices 
                WHERE created_at >= datetime('now', '-7 days')
            """)
            recent_7days = cursor.fetchone()['count']

            # Total amount sum
            cursor.execute("SELECT SUM(total_amount_value) as sum FROM invoices")
            total_amount_sum = cursor.fetchone()['sum'] or 0

            conn.close()

            return {
                'total_invoices': total_invoices,
                'avg_confidence': round(avg_confidence, 2),
                'invoice_types': invoice_types,
                'recent_7days': recent_7days,
                'total_amount_sum': total_amount_sum
            }

        except Exception as e:
            logger.error(f"❌ Error getting statistics: {e}")
            return {}

    def save_user(self, user_data: Dict[str, Any]) -> Optional[int]:
        """Save user to database and return the user ID"""
        try:
            conn = self.connect()
            if not conn:
                return None

            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO users (
                    email, name, hashed_password, is_active, is_admin, role
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                user_data.get('email'),
                user_data.get('name'),
                user_data.get('hashed_password'),
                user_data.get('is_active', 1),
                user_data.get('is_admin', 0),
                user_data.get('role', 'user')
            ))

            user_id = cursor.lastrowid
            conn.commit()
            conn.close()

            logger.info(f"✅ User saved with ID: {user_id}")
            return user_id

        except sqlite3.IntegrityError:
            logger.error(f"❌ User already exists: {user_data.get('email')}")
            return None
        except Exception as e:
            logger.error(f"❌ Failed to save user: {e}")
            return None

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        try:
            conn = self.connect()
            if not conn:
                return None

            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            row = cursor.fetchone()
            conn.close()

            if row:
                return dict(row)
            return None

        except Exception as e:
            logger.error(f"❌ Error getting user: {e}")
            return None

    def update_user_last_login(self, email: str) -> bool:
        """Update user's last login timestamp"""
        try:
            conn = self.connect()
            if not conn:
                return False

            cursor = conn.cursor()
            cursor.execute("""
                UPDATE users 
                SET last_login = CURRENT_TIMESTAMP 
                WHERE email = ?
            """, (email,))
            
            conn.commit()
            conn.close()
            return True

        except Exception as e:
            logger.error(f"❌ Error updating last login: {e}")
            return False

    def health_check(self) -> Dict[str, Any]:
        """Database health check"""
        try:
            conn = self.connect()
            if conn:
                conn.close()
                return {
                    "status": "healthy",
                    "message": "SQLite connection successful",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "status": "unhealthy",
                    "message": "Cannot connect to SQLite",
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"SQLite health check failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }

# Global instance
_db_tools_instance = None

def get_database_tools() -> DatabaseTools:
    """Get or create DatabaseTools singleton"""
    global _db_tools_instance
    if _db_tools_instance is None:
        _db_tools_instance = DatabaseTools()
    return _db_tools_instance