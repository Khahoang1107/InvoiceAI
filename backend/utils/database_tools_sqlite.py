"""
SQLite Database Tools for ChatBotAI
UNIFIED SCHEMA VERSION - Matches Alembic/PostgreSQL schema
"""

import sqlite3
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import os

logger = logging.getLogger(__name__)


class DatabaseTools:
    """
    SQLite database tools for local development
    
    IMPORTANT: Uses UNIFIED schema that matches PostgreSQL/Alembic.
    All tables now have proper FK constraints and user_id is REQUIRED for invoices.
    """

    def __init__(self, connection_string: str = None):
        """Initialize SQLite database connection"""
        if connection_string is None:
            connection_string = os.getenv("DATABASE_URL", "sqlite:///./chatbot.db")

        # Convert from SQLAlchemy format to SQLite path
        if connection_string.startswith("sqlite:///"):
            self.db_path = connection_string.replace("sqlite:///", "")
        else:
            self.db_path = "chatbot.db"

        logger.info(f"📦 Using SQLite database: {self.db_path}")
        
        # Initialize tables with unified schema
        self._initialize_tables()

    def connect(self):
        """Get SQLite connection with foreign keys enabled"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable column access by name
            # Enable foreign keys
            conn.execute("PRAGMA foreign_keys = ON")
            return conn
        except Exception as e:
            logger.error(f"❌ Failed to connect to SQLite: {e}")
            return None

    def _initialize_tables(self):
        """Create UNIFIED schema tables if they don't exist"""
        try:
            conn = self.connect()
            if not conn:
                return False

            cursor = conn.cursor()
            
            # Enable foreign keys
            cursor.execute("PRAGMA foreign_keys = ON")

            # Create users table (unified - includes role)
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
            
            # Create messages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    sender TEXT NOT NULL,
                    content TEXT NOT NULL,
                    conversation_id TEXT NOT NULL,
                    tokens_used INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            
            # Create uploaded_files table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS uploaded_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_id TEXT UNIQUE NOT NULL,
                    user_id INTEGER NOT NULL,
                    filename TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    file_path TEXT NOT NULL,
                    file_type TEXT,
                    upload_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            
            # Create ocr_jobs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ocr_jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_id TEXT UNIQUE NOT NULL,
                    user_id INTEGER NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    extracted_text TEXT,
                    confidence REAL,
                    processing_time REAL,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed_at TIMESTAMP,
                    FOREIGN KEY (file_id) REFERENCES uploaded_files(file_id),
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)

            # Create UNIFIED invoices table (merged from both schemas)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS invoices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    
                    -- Foreign keys (REQUIRED user_id)
                    user_id INTEGER NOT NULL,
                    ocr_job_id INTEGER,
                    file_id TEXT,
                    
                    -- File info
                    filename TEXT,
                    filepath TEXT,
                    
                    -- Invoice identification (merged)
                    invoice_number TEXT,
                    invoice_code TEXT,
                    invoice_type TEXT DEFAULT 'general',
                    
                    -- Dates
                    invoice_date TEXT,
                    due_date TEXT,
                    date_string TEXT,
                    
                    -- Seller info
                    seller_name TEXT,
                    seller_address TEXT,
                    seller_tax_id TEXT,
                    
                    -- Buyer info
                    buyer_name TEXT,
                    buyer_address TEXT,
                    buyer_tax_id TEXT,
                    
                    -- Financial fields
                    amount REAL,
                    subtotal REAL DEFAULT 0,
                    tax_percentage REAL DEFAULT 0,
                    tax_amount REAL DEFAULT 0,
                    total_amount TEXT,
                    total_amount_value REAL DEFAULT 0,
                    currency TEXT DEFAULT 'VND',
                    
                    -- Additional info
                    vendor TEXT,
                    description TEXT,
                    
                    -- OCR metadata
                    confidence_score REAL DEFAULT 0,
                    ocr_text TEXT,
                    
                    -- Timestamps
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    -- Foreign key constraints
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (ocr_job_id) REFERENCES ocr_jobs(id),
                    FOREIGN KEY (file_id) REFERENCES uploaded_files(file_id)
                )
            """)
            
            # Create UNIFIED images table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS images (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    invoice_id INTEGER,
                    uploaded_file_id INTEGER,
                    
                    filename TEXT NOT NULL,
                    original_filename TEXT,
                    file_path TEXT,
                    file_data BLOB,
                    file_size INTEGER,
                    mime_type TEXT,
                    storage_type TEXT DEFAULT 'filesystem',
                    
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (invoice_id) REFERENCES invoices(id),
                    FOREIGN KEY (uploaded_file_id) REFERENCES uploaded_files(id)
                )
            """)
            
            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS ix_users_email ON users(email)")
            cursor.execute("CREATE INDEX IF NOT EXISTS ix_users_role ON users(role)")
            cursor.execute("CREATE INDEX IF NOT EXISTS ix_messages_user_id ON messages(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS ix_messages_conversation_id ON messages(conversation_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS ix_uploaded_files_user_id ON uploaded_files(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS ix_uploaded_files_file_id ON uploaded_files(file_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS ix_ocr_jobs_user_id ON ocr_jobs(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS ix_ocr_jobs_status ON ocr_jobs(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS ix_invoices_user_id ON invoices(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS ix_invoices_invoice_code ON invoices(invoice_code)")
            cursor.execute("CREATE INDEX IF NOT EXISTS ix_invoices_invoice_type ON invoices(invoice_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS ix_invoices_created_at ON invoices(created_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS ix_images_user_id ON images(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS ix_images_invoice_id ON images(invoice_id)")

            conn.commit()
            conn.close()
            logger.info("✅ SQLite tables initialized successfully (unified schema)")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to initialize tables: {e}")
            return False

    def _get_default_user_id(self) -> Optional[int]:
        """Get default user ID for orphaned data"""
        try:
            conn = self.connect()
            if not conn:
                return None
            
            cursor = conn.cursor()
            
            # Try to get first admin user
            cursor.execute("SELECT id FROM users WHERE is_admin = 1 ORDER BY id LIMIT 1")
            row = cursor.fetchone()
            if row:
                conn.close()
                return row[0]
            
            # Fallback to any user
            cursor.execute("SELECT id FROM users ORDER BY id LIMIT 1")
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return row[0]
            return None
            
        except Exception:
            return None

    def save_invoice(self, invoice_data: Dict[str, Any], user_id: int = None) -> Optional[int]:
        """
        Save invoice to database and return the invoice ID.
        
        IMPORTANT: user_id is now REQUIRED for unified schema.
        """
        # Get user_id - required in unified schema
        effective_user_id = user_id or invoice_data.get('user_id')
        
        if not effective_user_id:
            effective_user_id = self._get_default_user_id()
            if not effective_user_id:
                logger.error("❌ Cannot save invoice: user_id is required in unified schema")
                return None
        
        try:
            conn = self.connect()
            if not conn:
                return None

            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO invoices (
                    user_id, ocr_job_id, file_id,
                    filename, filepath, invoice_number, invoice_code, invoice_type,
                    invoice_date, due_date, date_string,
                    seller_name, seller_address, seller_tax_id,
                    buyer_name, buyer_address, buyer_tax_id,
                    amount, subtotal, tax_percentage, tax_amount,
                    total_amount, total_amount_value, currency,
                    vendor, description,
                    confidence_score, ocr_text
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                effective_user_id,
                invoice_data.get('ocr_job_id'),
                invoice_data.get('file_id'),
                invoice_data.get('filename'),
                invoice_data.get('filepath') or invoice_data.get('file_path'),
                invoice_data.get('invoice_number'),
                invoice_data.get('invoice_code'),
                invoice_data.get('invoice_type', 'general'),
                invoice_data.get('invoice_date'),
                invoice_data.get('due_date'),
                invoice_data.get('date') or invoice_data.get('date_string'),
                invoice_data.get('seller_name'),
                invoice_data.get('seller_address'),
                invoice_data.get('seller_tax_id'),
                invoice_data.get('buyer_name'),
                invoice_data.get('buyer_address'),
                invoice_data.get('buyer_tax_id'),
                invoice_data.get('amount'),
                invoice_data.get('subtotal', 0),
                invoice_data.get('tax_percentage', 0),
                invoice_data.get('tax_amount', 0),
                invoice_data.get('total_amount'),
                invoice_data.get('total_amount_value', 0),
                invoice_data.get('currency', 'VND'),
                invoice_data.get('vendor'),
                invoice_data.get('description'),
                invoice_data.get('confidence_score', 0),
                invoice_data.get('ocr_text')
            ))

            invoice_id = cursor.lastrowid
            conn.commit()
            conn.close()

            logger.info(f"✅ Invoice saved with ID: {invoice_id} (user_id: {effective_user_id})")
            return invoice_id

        except Exception as e:
            logger.error(f"❌ Failed to save invoice: {e}")
            return None

    def save_image(self, filename: str, original_filename: str, file_data: bytes,
                   file_size: int, mime_type: str, user_id: int = None,
                   invoice_id: int = None, file_path: str = None,
                   storage_type: str = 'database') -> Optional[int]:
        """Save image file to database (unified schema)."""
        effective_user_id = user_id
        
        if not effective_user_id:
            effective_user_id = self._get_default_user_id()
            if not effective_user_id:
                logger.error("❌ Cannot save image: user_id is required in unified schema")
                return None
        
        try:
            conn = self.connect()
            if not conn:
                return None
            
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO images (
                    user_id, invoice_id, filename, original_filename,
                    file_path, file_data, file_size, mime_type, storage_type
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                effective_user_id, invoice_id, filename, original_filename,
                file_path, file_data, file_size, mime_type, storage_type
            ))
            
            image_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Image saved with ID: {image_id} (user_id: {effective_user_id})")
            return image_id
            
        except Exception as e:
            logger.error(f"❌ Failed to save image: {e}")
            return None

    def get_image(self, image_id: int) -> Optional[Dict]:
        """Get image from database by ID"""
        try:
            conn = self.connect()
            if not conn:
                return None
            
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, user_id, invoice_id, filename, original_filename,
                       file_path, file_data, file_size, mime_type, storage_type,
                       created_at, updated_at
                FROM images WHERE id = ?
            """, (image_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return dict(row)
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting image: {e}")
            return None

    def get_all_invoices(self, limit: int = 20, user_id: int = None) -> List[Dict]:
        """Get all invoices from database"""
        try:
            conn = self.connect()
            if not conn:
                return []

            cursor = conn.cursor()
            
            if user_id:
                cursor.execute("""
                    SELECT id, user_id, filename, invoice_code, invoice_number, invoice_type,
                           date_string, invoice_date, seller_name, buyer_name,
                           total_amount, total_amount_value, amount,
                           confidence_score, created_at, filepath
                    FROM invoices 
                    WHERE user_id = ?
                    ORDER BY created_at DESC 
                    LIMIT ?
                """, (user_id, limit))
            else:
                cursor.execute("""
                    SELECT id, user_id, filename, invoice_code, invoice_number, invoice_type,
                           date_string, invoice_date, seller_name, buyer_name,
                           total_amount, total_amount_value, amount,
                           confidence_score, created_at, filepath
                    FROM invoices 
                    ORDER BY created_at DESC 
                    LIMIT ?
                """, (limit,))

            rows = cursor.fetchall()
            conn.close()

            invoices = []
            for row in rows:
                filepath_value = row['filepath']
                if filepath_value:
                    filepath_value = filepath_value.replace('\\', '/')
                
                invoices.append({
                    'id': row['id'],
                    'user_id': row['user_id'],
                    'filename': row['filename'],
                    'invoice_code': row['invoice_code'],
                    'invoice_number': row['invoice_number'],
                    'invoice_type': row['invoice_type'],
                    'date': row['date_string'],
                    'date_string': row['date_string'],
                    'invoice_date': row['invoice_date'],
                    'seller_name': row['seller_name'],
                    'buyer_name': row['buyer_name'],
                    'total_amount': row['total_amount'],
                    'total_amount_value': float(row['total_amount_value']) if row['total_amount_value'] else 0,
                    'amount': float(row['amount']) if row['amount'] else 0,
                    'confidence': float(row['confidence_score']) if row['confidence_score'] else 0.0,
                    'confidence_score': float(row['confidence_score']) if row['confidence_score'] else 0.0,
                    'created_at': row['created_at'],
                    'file_path': filepath_value,
                    'filepath': filepath_value,
                    'status': 'completed'
                })
            
            logger.info(f"✅ Retrieved {len(invoices)} invoices from SQLite")
            return invoices

        except Exception as e:
            logger.error(f"❌ Error getting invoices: {e}")
            return []

    def search_invoices(self, query: str, limit: int = 20, user_id: int = None) -> List[Dict]:
        """Search invoices by query"""
        try:
            conn = self.connect()
            if not conn:
                return []

            cursor = conn.cursor()
            search_pattern = f"%{query}%"
            
            if user_id:
                cursor.execute("""
                    SELECT id, user_id, filename, invoice_code, invoice_number, invoice_type,
                           date_string, invoice_date, seller_name, buyer_name,
                           total_amount, total_amount_value, amount,
                           confidence_score, created_at, filepath
                    FROM invoices 
                    WHERE user_id = ? AND (
                        filename LIKE ? OR invoice_code LIKE ? 
                        OR invoice_number LIKE ?
                        OR seller_name LIKE ? OR buyer_name LIKE ?
                    )
                    ORDER BY created_at DESC 
                    LIMIT ?
                """, (user_id, search_pattern, search_pattern, search_pattern, 
                      search_pattern, search_pattern, limit))
            else:
                cursor.execute("""
                    SELECT id, user_id, filename, invoice_code, invoice_number, invoice_type,
                           date_string, invoice_date, seller_name, buyer_name,
                           total_amount, total_amount_value, amount,
                           confidence_score, created_at, filepath
                    FROM invoices 
                    WHERE filename LIKE ? OR invoice_code LIKE ? 
                       OR invoice_number LIKE ?
                       OR seller_name LIKE ? OR buyer_name LIKE ?
                    ORDER BY created_at DESC 
                    LIMIT ?
                """, (search_pattern, search_pattern, search_pattern, 
                      search_pattern, search_pattern, limit))

            rows = cursor.fetchall()
            conn.close()

            results = []
            for row in rows:
                filepath_value = row['filepath']
                if filepath_value:
                    filepath_value = filepath_value.replace('\\', '/')
                
                results.append({
                    'id': row['id'],
                    'user_id': row['user_id'],
                    'filename': row['filename'],
                    'invoice_code': row['invoice_code'],
                    'invoice_number': row['invoice_number'],
                    'invoice_type': row['invoice_type'],
                    'date': row['date_string'],
                    'date_string': row['date_string'],
                    'invoice_date': row['invoice_date'],
                    'seller_name': row['seller_name'],
                    'buyer_name': row['buyer_name'],
                    'total_amount': row['total_amount'],
                    'total_amount_value': float(row['total_amount_value']) if row['total_amount_value'] else 0,
                    'amount': float(row['amount']) if row['amount'] else 0,
                    'confidence': float(row['confidence_score']) if row['confidence_score'] else 0.0,
                    'confidence_score': float(row['confidence_score']) if row['confidence_score'] else 0.0,
                    'created_at': row['created_at'],
                    'file_path': filepath_value,
                    'filepath': filepath_value,
                    'status': 'completed'
                })
            
            logger.info(f"✅ Found {len(results)} invoices matching '{query}'")
            return results

        except Exception as e:
            logger.error(f"❌ Error searching invoices: {e}")
            return []

    def get_invoice_by_id(self, invoice_id: int) -> Optional[Dict]:
        """Get invoice by ID"""
        try:
            conn = self.connect()
            if not conn:
                return None
            
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM invoices WHERE id = ?", (invoice_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return dict(row)
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting invoice by ID: {e}")
            return None

    def get_invoice_by_filename(self, filename: str) -> Optional[Dict]:
        """Get invoice by filename"""
        try:
            conn = self.connect()
            if not conn:
                return None
            
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM invoices WHERE filename = ?", (filename,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return dict(row)
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting invoice by filename: {e}")
            return None

    def get_statistics(self, user_id: int = None) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            conn = self.connect()
            if not conn:
                return {}

            cursor = conn.cursor()
            
            user_filter = ""
            params = ()
            if user_id:
                user_filter = "WHERE user_id = ?"
                params = (user_id,)

            # Total invoices
            cursor.execute(f"SELECT COUNT(*) as count FROM invoices {user_filter}", params)
            total_invoices = cursor.fetchone()['count']

            # Average confidence
            cursor.execute(f"SELECT AVG(confidence_score) as avg FROM invoices {user_filter}", params)
            avg_confidence = cursor.fetchone()['avg'] or 0

            # Invoice types distribution
            cursor.execute(f"SELECT invoice_type, COUNT(*) as count FROM invoices {user_filter} GROUP BY invoice_type", params)
            invoice_types = {row['invoice_type']: row['count'] for row in cursor.fetchall()}

            # Recent 7 days
            recent_query = f"""
                SELECT COUNT(*) as count FROM invoices 
                WHERE created_at >= datetime('now', '-7 days')
                {"AND user_id = ?" if user_id else ""}
            """
            cursor.execute(recent_query, params)
            recent_7days = cursor.fetchone()['count']

            # Total amount sum
            cursor.execute(f"SELECT SUM(total_amount_value) as sum FROM invoices {user_filter}", params)
            total_amount_sum = cursor.fetchone()['sum'] or 0

            # User count
            cursor.execute("SELECT COUNT(*) as count FROM users")
            total_users = cursor.fetchone()['count']

            conn.close()

            return {
                'total_invoices': total_invoices,
                'avg_confidence': round(avg_confidence, 2),
                'invoice_types': invoice_types,
                'recent_7days': recent_7days,
                'total_amount_sum': total_amount_sum,
                'total_users': total_users
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

    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        try:
            conn = self.connect()
            if not conn:
                return None

            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
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
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
                table_count = cursor.fetchone()[0]
                conn.close()
                
                return {
                    "status": "healthy",
                    "message": "SQLite connection successful",
                    "schema": "unified",
                    "table_count": table_count,
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
