"""
PostgreSQL Database Tools for ChatBotAI - Railway Cloud
"""

import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from sqlalchemy import create_engine, text

logger = logging.getLogger(__name__)

class DatabaseToolsPostgres:
    """PostgreSQL database tools for Railway cloud"""

    def __init__(self, connection_string: str = None):
        """Initialize PostgreSQL database connection"""
        if connection_string is None:
            connection_string = os.getenv("DATABASE_URL", "")

        if not connection_string or connection_string.startswith("sqlite"):
            raise Exception("❌ DATABASE_URL not set for PostgreSQL in .env file")

        logger.info(f"🔗 Connecting to PostgreSQL cloud...")
        try:
            self.engine = create_engine(connection_string, echo=False)
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                conn.commit()
            logger.info("✅ Successfully connected to PostgreSQL cloud!")
            self.initialize_tables()
        except Exception as e:
            logger.error(f"❌ Failed to connect to PostgreSQL: {e}")
            raise

    def initialize_tables(self):
        """Create necessary tables if they don't exist"""
        try:
            with self.engine.connect() as conn:
                # Create users table
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        email VARCHAR(255) UNIQUE NOT NULL,
                        name VARCHAR(255),
                        hashed_password VARCHAR(255) NOT NULL,
                        is_active INTEGER DEFAULT 1,
                        is_admin INTEGER DEFAULT 0,
                        role VARCHAR(50) DEFAULT 'user',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_login TIMESTAMP
                    )
                """))

                # Create invoices table
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS invoices (
                        id SERIAL PRIMARY KEY,
                        filename VARCHAR(255) NOT NULL,
                        filepath VARCHAR(500),
                        invoice_code VARCHAR(255),
                        invoice_type VARCHAR(100) DEFAULT 'general',
                        date VARCHAR(50),
                        seller_name VARCHAR(255),
                        seller_address VARCHAR(500),
                        seller_tax_id VARCHAR(100),
                        buyer_name VARCHAR(255),
                        buyer_address VARCHAR(500),
                        buyer_tax_id VARCHAR(100),
                        subtotal REAL DEFAULT 0,
                        tax_percentage REAL DEFAULT 0,
                        tax_amount REAL DEFAULT 0,
                        total_amount VARCHAR(100),
                        total_amount_value REAL DEFAULT 0,
                        currency VARCHAR(10) DEFAULT 'VND',
                        confidence_score REAL DEFAULT 0,
                        ocr_text TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))

                conn.commit()
                logger.info("✅ PostgreSQL tables initialized successfully")
                return True

        except Exception as e:
            logger.error(f"❌ Failed to initialize tables: {e}")
            return False

    def save_invoice(self, invoice_data: Dict[str, Any]) -> Optional[int]:
        """Save invoice to database and return the invoice ID"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    INSERT INTO invoices (
                        filename, filepath, invoice_code, invoice_type, date,
                        seller_name, seller_address, seller_tax_id,
                        buyer_name, buyer_address, buyer_tax_id,
                        subtotal, tax_percentage, tax_amount,
                        total_amount, total_amount_value, currency,
                        confidence_score, ocr_text
                    ) VALUES (
                        :filename, :filepath, :invoice_code, :invoice_type, :date,
                        :seller_name, :seller_address, :seller_tax_id,
                        :buyer_name, :buyer_address, :buyer_tax_id,
                        :subtotal, :tax_percentage, :tax_amount,
                        :total_amount, :total_amount_value, :currency,
                        :confidence_score, :ocr_text
                    )
                    RETURNING id
                """), {
                    "filename": invoice_data.get('filename'),
                    "filepath": invoice_data.get('filepath') or invoice_data.get('file_path'),
                    "invoice_code": invoice_data.get('invoice_code'),
                    "invoice_type": invoice_data.get('invoice_type', 'general'),
                    "date": invoice_data.get('date'),
                    "seller_name": invoice_data.get('seller_name'),
                    "seller_address": invoice_data.get('seller_address'),
                    "seller_tax_id": invoice_data.get('seller_tax_id'),
                    "buyer_name": invoice_data.get('buyer_name'),
                    "buyer_address": invoice_data.get('buyer_address'),
                    "buyer_tax_id": invoice_data.get('buyer_tax_id'),
                    "subtotal": invoice_data.get('subtotal', 0),
                    "tax_percentage": invoice_data.get('tax_percentage', 0),
                    "tax_amount": invoice_data.get('tax_amount', 0),
                    "total_amount": invoice_data.get('total_amount'),
                    "total_amount_value": invoice_data.get('total_amount_value', 0),
                    "currency": invoice_data.get('currency', 'VND'),
                    "confidence_score": invoice_data.get('confidence_score', 0),
                    "ocr_text": invoice_data.get('ocr_text')
                })

                invoice_id = result.fetchone()[0]
                conn.commit()

                logger.info(f"✅ Invoice saved with ID: {invoice_id}")
                return invoice_id

        except Exception as e:
            logger.error(f"❌ Failed to save invoice: {e}")
            return None

    def get_all_invoices(self, limit: int = 20) -> List[Dict]:
        """Get all invoices from database"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT id, filename, invoice_code, invoice_type, date,
                           seller_name, buyer_name, total_amount, total_amount_value, 
                           confidence_score, created_at, filepath
                    FROM invoices 
                    ORDER BY created_at DESC 
                    LIMIT :limit
                """), {"limit": limit})

                invoices = []
                for row in result:
                    # Convert Windows backslash to forward slash for URLs
                    filepath_value = row[11] if len(row) > 11 else None
                    if filepath_value:
                        filepath_value = filepath_value.replace('\\', '/')
                    
                    invoices.append({
                        'id': row[0],
                        'filename': row[1],
                        'invoice_code': row[2],
                        'invoice_type': row[3],
                        'date': row[4],
                        'seller_name': row[5],
                        'buyer_name': row[6],
                        'total_amount': row[7],
                        'total_amount_value': float(row[8]) if row[8] else 0,
                        'confidence': float(row[9]) if row[9] else 0.0,
                        'confidence_score': float(row[9]) if row[9] else 0.0,
                        'processed_at': str(row[10]),
                        'created_at': str(row[10]),
                        'file_path': filepath_value,
                        'filepath': filepath_value,
                        'status': 'completed'
                    })

                logger.info(f"✅ Retrieved {len(invoices)} invoices from PostgreSQL")
                return invoices

        except Exception as e:
            logger.error(f"❌ Error getting invoices: {e}")
            return []

    def search_invoices(self, query: str, limit: int = 20) -> List[Dict]:
        """Search invoices by query"""
        try:
            with self.engine.connect() as conn:
                search_pattern = f"%{query}%"
                
                result = conn.execute(text("""
                    SELECT id, filename, invoice_code, invoice_type, date,
                           seller_name, buyer_name, total_amount, total_amount_value, 
                           confidence_score, created_at, filepath
                    FROM invoices 
                    WHERE filename ILIKE :pattern OR invoice_code ILIKE :pattern 
                       OR seller_name ILIKE :pattern OR buyer_name ILIKE :pattern
                    ORDER BY created_at DESC 
                    LIMIT :limit
                """), {"pattern": search_pattern, "limit": limit})

                invoices = []
                for row in result:
                    # Convert Windows backslash to forward slash for URLs
                    filepath_value = row[11] if len(row) > 11 else None
                    if filepath_value:
                        filepath_value = filepath_value.replace('\\', '/')
                    
                    invoices.append({
                        'id': row[0],
                        'filename': row[1],
                        'invoice_code': row[2],
                        'invoice_type': row[3],
                        'date': row[4],
                        'seller_name': row[5],
                        'buyer_name': row[6],
                        'total_amount': row[7],
                        'total_amount_value': float(row[8]) if row[8] else 0,
                        'confidence': float(row[9]) if row[9] else 0.0,
                        'confidence_score': float(row[9]) if row[9] else 0.0,
                        'processed_at': str(row[10]),
                        'created_at': str(row[10]),
                        'file_path': filepath_value,
                        'filepath': filepath_value,
                        'status': 'completed'
                    })

                logger.info(f"✅ Found {len(invoices)} invoices matching '{query}'")
                return invoices

        except Exception as e:
            logger.error(f"❌ Error searching invoices: {e}")
            return []

    def get_invoice_by_filename(self, filename: str) -> Optional[Dict]:
        """Get invoice by filename"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT * FROM invoices WHERE filename = :filename
                """), {"filename": filename})

                row = result.fetchone()
                if row:
                    return {
                        'id': row[0],
                        'filename': row[1],
                        'filepath': row[2],
                        'invoice_code': row[3],
                        'invoice_type': row[4],
                        'date': row[5],
                        'seller_name': row[6],
                        'seller_address': row[7],
                        'seller_tax_id': row[8],
                        'buyer_name': row[9],
                        'buyer_address': row[10],
                        'buyer_tax_id': row[11],
                        'subtotal': row[12],
                        'tax_percentage': row[13],
                        'tax_amount': row[14],
                        'total_amount': row[15],
                        'total_amount_value': row[16],
                        'currency': row[17],
                        'confidence_score': row[18],
                        'ocr_text': row[19],
                        'created_at': str(row[20]),
                        'updated_at': str(row[21])
                    }
                return None

        except Exception as e:
            logger.error(f"❌ Error getting invoice by filename: {e}")
            return None

    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            with self.engine.connect() as conn:
                # Total invoices
                result = conn.execute(text("SELECT COUNT(*) as count FROM invoices"))
                total_invoices = result.fetchone()[0]

                # Average confidence
                result = conn.execute(text("SELECT AVG(confidence_score) as avg FROM invoices"))
                avg_confidence = result.fetchone()[0] or 0

                # Invoice types distribution
                result = conn.execute(text("SELECT invoice_type, COUNT(*) as count FROM invoices GROUP BY invoice_type"))
                invoice_types = {row[0]: row[1] for row in result}

                # Recent 7 days
                result = conn.execute(text("""
                    SELECT COUNT(*) as count FROM invoices 
                    WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
                """))
                recent_7days = result.fetchone()[0]

                # Total amount sum
                result = conn.execute(text("SELECT SUM(total_amount_value) as sum FROM invoices"))
                total_amount_sum = result.fetchone()[0] or 0

                return {
                    'total_invoices': total_invoices,
                    'avg_confidence': round(float(avg_confidence), 2),
                    'invoice_types': invoice_types,
                    'recent_7days': recent_7days,
                    'total_amount_sum': float(total_amount_sum)
                }

        except Exception as e:
            logger.error(f"❌ Error getting statistics: {e}")
            return {}

    def save_user(self, user_data: Dict[str, Any]) -> Optional[int]:
        """Save user to database and return the user ID"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    INSERT INTO users (
                        email, name, hashed_password, is_active, is_admin, role
                    ) VALUES (
                        :email, :name, :hashed_password, :is_active, :is_admin, :role
                    )
                    RETURNING id
                """), {
                    "email": user_data.get('email'),
                    "name": user_data.get('name'),
                    "hashed_password": user_data.get('hashed_password'),
                    "is_active": user_data.get('is_active', 1),
                    "is_admin": user_data.get('is_admin', 0),
                    "role": user_data.get('role', 'user')
                })

                user_id = result.fetchone()[0]
                conn.commit()

                logger.info(f"✅ User saved with ID: {user_id}")
                return user_id

        except Exception as e:
            logger.error(f"❌ Failed to save user: {e}")
            return None

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT * FROM users WHERE email = :email"), {"email": email})
                row = result.fetchone()

                if row:
                    return {
                        'id': row[0],
                        'email': row[1],
                        'name': row[2],
                        'hashed_password': row[3],
                        'is_active': row[4],
                        'is_admin': row[5],
                        'role': row[6],
                        'created_at': str(row[7]),
                        'updated_at': str(row[8]),
                        'last_login': str(row[9]) if row[9] else None
                    }
                return None

        except Exception as e:
            logger.error(f"❌ Error getting user: {e}")
            return None

    def update_user_last_login(self, email: str) -> bool:
        """Update user's last login timestamp"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("""
                    UPDATE users 
                    SET last_login = CURRENT_TIMESTAMP 
                    WHERE email = :email
                """), {"email": email})
                
                conn.commit()
                return True

        except Exception as e:
            logger.error(f"❌ Error updating last login: {e}")
            return False

    def health_check(self) -> Dict[str, Any]:
        """Database health check"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                return {
                    "status": "healthy",
                    "message": "PostgreSQL connection successful",
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"PostgreSQL health check failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }


# Global instance
_db_tools_instance = None

def get_database_tools() -> DatabaseToolsPostgres:
    """Get or create DatabaseToolsPostgres singleton"""
    global _db_tools_instance
    if _db_tools_instance is None:
        _db_tools_instance = DatabaseToolsPostgres()
    return _db_tools_instance
