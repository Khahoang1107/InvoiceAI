"""
PostgreSQL Database Tools for ChatBotAI - Railway Cloud
UNIFIED SCHEMA VERSION - Uses Alembic migrations for schema management
"""

import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from sqlalchemy import create_engine, text

logger = logging.getLogger(__name__)


class DatabaseToolsPostgres:
    """
    PostgreSQL database tools for Railway cloud
    
    IMPORTANT: This class NO LONGER creates tables independently.
    All schema management is done via Alembic migrations.
    Run 'alembic upgrade head' to initialize/update database schema.
    """

    def __init__(self, connection_string: str = None):
        """Initialize PostgreSQL database connection"""
        if connection_string is None:
            connection_string = os.getenv("DATABASE_URL", "")

        if not connection_string or not connection_string.startswith("postgresql"):
            raise Exception("❌ DATABASE_URL not set for PostgreSQL in .env file")

        logger.info(f"🔗 Connecting to PostgreSQL cloud...")
        try:
            self.engine = create_engine(connection_string, echo=False)
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                conn.commit()
            logger.info("✅ Successfully connected to PostgreSQL cloud!")
            
            # Verify tables exist (don't create - Alembic handles this)
            self._verify_schema()
        except Exception as e:
            logger.error(f"❌ Failed to connect to PostgreSQL: {e}")
            raise

    def _verify_schema(self):
        """
        Verify that required tables exist.
        Tables are created by Alembic migrations, not this class.
        """
        required_tables = ['users', 'invoices', 'images', 'messages', 'uploaded_files', 'ocr_jobs']
        
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """))
                existing_tables = [row[0] for row in result]
                
                missing_tables = [t for t in required_tables if t not in existing_tables]
                
                if missing_tables:
                    logger.warning(f"⚠️ Missing tables: {missing_tables}")
                    logger.warning("⚠️ Run 'alembic upgrade head' to create database schema")
                    # Auto-initialize for backward compatibility
                    self._initialize_tables_fallback()
                else:
                    logger.info("✅ All required tables exist")
                    
        except Exception as e:
            logger.error(f"❌ Error verifying schema: {e}")
            self._initialize_tables_fallback()

    def _initialize_tables_fallback(self):
        """
        Fallback table creation for backward compatibility.
        This ensures the app works even if Alembic hasn't been run.
        Uses the UNIFIED schema structure.
        """
        logger.info("🔄 Running fallback table initialization (unified schema)...")
        
        try:
            with self.engine.connect() as conn:
                # Create users table (unified - includes role)
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        email VARCHAR(255) UNIQUE NOT NULL,
                        name VARCHAR(255),
                        hashed_password VARCHAR(255) NOT NULL,
                        is_active BOOLEAN DEFAULT TRUE,
                        is_admin BOOLEAN DEFAULT FALSE,
                        role VARCHAR(50) DEFAULT 'user',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_login TIMESTAMP
                    )
                """))
                
                # Create messages table
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS messages (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL REFERENCES users(id),
                        sender VARCHAR(50) NOT NULL,
                        content TEXT NOT NULL,
                        conversation_id VARCHAR(255) NOT NULL,
                        tokens_used INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                
                # Create uploaded_files table
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS uploaded_files (
                        id SERIAL PRIMARY KEY,
                        file_id VARCHAR(255) UNIQUE NOT NULL,
                        user_id INTEGER NOT NULL REFERENCES users(id),
                        filename VARCHAR(255) NOT NULL,
                        file_size INTEGER NOT NULL,
                        file_path VARCHAR(500) NOT NULL,
                        file_type VARCHAR(50),
                        upload_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                
                # Create ocr_jobs table
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS ocr_jobs (
                        id SERIAL PRIMARY KEY,
                        file_id VARCHAR(255) UNIQUE NOT NULL REFERENCES uploaded_files(file_id),
                        user_id INTEGER NOT NULL REFERENCES users(id),
                        status VARCHAR(20) NOT NULL DEFAULT 'pending',
                        extracted_text TEXT,
                        confidence FLOAT,
                        processing_time FLOAT,
                        error_message TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        processed_at TIMESTAMP
                    )
                """))
                
                # Create UNIFIED invoices table (merged from both schemas)
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS invoices (
                        id SERIAL PRIMARY KEY,
                        
                        -- Foreign keys (REQUIRED user_id)
                        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
                        ocr_job_id INTEGER REFERENCES ocr_jobs(id) ON DELETE SET NULL,
                        file_id VARCHAR(255) REFERENCES uploaded_files(file_id) ON DELETE SET NULL,
                        
                        -- File info
                        filename VARCHAR(255),
                        filepath VARCHAR(500),
                        
                        -- Invoice identification (merged)
                        invoice_number VARCHAR(100),
                        invoice_code VARCHAR(255),
                        invoice_type VARCHAR(100) DEFAULT 'general',
                        
                        -- Dates
                        invoice_date TIMESTAMP,
                        due_date TIMESTAMP,
                        date_string VARCHAR(50),
                        
                        -- Seller info
                        seller_name VARCHAR(255),
                        seller_address VARCHAR(500),
                        seller_tax_id VARCHAR(100),
                        
                        -- Buyer info
                        buyer_name VARCHAR(255),
                        buyer_address VARCHAR(500),
                        buyer_tax_id VARCHAR(100),
                        
                        -- Financial fields
                        amount FLOAT,
                        subtotal FLOAT DEFAULT 0,
                        tax_percentage FLOAT DEFAULT 0,
                        tax_amount FLOAT DEFAULT 0,
                        total_amount VARCHAR(100),
                        total_amount_value FLOAT DEFAULT 0,
                        currency VARCHAR(10) DEFAULT 'VND',
                        
                        -- Additional info
                        vendor VARCHAR(255),
                        description TEXT,
                        
                        -- OCR metadata
                        confidence_score FLOAT DEFAULT 0,
                        ocr_text TEXT,
                        
                        -- Timestamps
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                
                # Create UNIFIED images table
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS images (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        invoice_id INTEGER REFERENCES invoices(id) ON DELETE SET NULL,
                        uploaded_file_id INTEGER REFERENCES uploaded_files(id) ON DELETE SET NULL,
                        
                        filename VARCHAR(255) NOT NULL,
                        original_filename VARCHAR(255),
                        file_path VARCHAR(500),
                        file_data BYTEA,
                        file_size INTEGER,
                        mime_type VARCHAR(100),
                        storage_type VARCHAR(20) DEFAULT 'filesystem',
                        
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                
                # Create indexes
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_users_email ON users(email)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_users_role ON users(role)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_messages_user_id ON messages(user_id)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_messages_conversation_id ON messages(conversation_id)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_uploaded_files_user_id ON uploaded_files(user_id)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_uploaded_files_file_id ON uploaded_files(file_id)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_ocr_jobs_user_id ON ocr_jobs(user_id)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_ocr_jobs_status ON ocr_jobs(status)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_invoices_user_id ON invoices(user_id)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_invoices_invoice_code ON invoices(invoice_code)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_invoices_invoice_type ON invoices(invoice_type)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_invoices_created_at ON invoices(created_at)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_images_user_id ON images(user_id)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_images_invoice_id ON images(invoice_id)"))
                
                conn.commit()
                logger.info("✅ Fallback table initialization completed (unified schema)")
                return True

        except Exception as e:
            logger.error(f"❌ Failed to initialize tables: {e}")
            return False

    def save_invoice(self, invoice_data: Dict[str, Any], user_id: int = None) -> Optional[int]:
        """
        Save invoice to database and return the invoice ID.
        
        IMPORTANT: user_id is now REQUIRED for unified schema.
        If not provided, will try to get from invoice_data or use default.
        """
        # Get user_id - required in unified schema
        effective_user_id = user_id or invoice_data.get('user_id')
        
        if not effective_user_id:
            # Try to get a default user (first admin or any user)
            effective_user_id = self._get_default_user_id()
            if not effective_user_id:
                logger.error("❌ Cannot save invoice: user_id is required in unified schema")
                return None
        
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    INSERT INTO invoices (
                        user_id, ocr_job_id, file_id,
                        filename, filepath, invoice_number, invoice_code, invoice_type,
                        date_string,
                        seller_name, seller_address, seller_tax_id,
                        buyer_name, buyer_address, buyer_tax_id,
                        amount, subtotal, tax_percentage, tax_amount,
                        total_amount, total_amount_value, currency,
                        vendor, description,
                        confidence_score, ocr_text
                    ) VALUES (
                        :user_id, :ocr_job_id, :file_id,
                        :filename, :filepath, :invoice_number, :invoice_code, :invoice_type,
                        :date_string,
                        :seller_name, :seller_address, :seller_tax_id,
                        :buyer_name, :buyer_address, :buyer_tax_id,
                        :amount, :subtotal, :tax_percentage, :tax_amount,
                        :total_amount, :total_amount_value, :currency,
                        :vendor, :description,
                        :confidence_score, :ocr_text
                    )
                    RETURNING id
                """), {
                    "user_id": effective_user_id,
                    "ocr_job_id": invoice_data.get('ocr_job_id'),
                    "file_id": invoice_data.get('file_id'),
                    "filename": invoice_data.get('filename'),
                    "filepath": invoice_data.get('filepath') or invoice_data.get('file_path'),
                    "invoice_number": invoice_data.get('invoice_number'),
                    "invoice_code": invoice_data.get('invoice_code'),
                    "invoice_type": invoice_data.get('invoice_type', 'general'),
                    "date_string": invoice_data.get('date') or invoice_data.get('date_string'),
                    "seller_name": invoice_data.get('seller_name'),
                    "seller_address": invoice_data.get('seller_address'),
                    "seller_tax_id": invoice_data.get('seller_tax_id'),
                    "buyer_name": invoice_data.get('buyer_name'),
                    "buyer_address": invoice_data.get('buyer_address'),
                    "buyer_tax_id": invoice_data.get('buyer_tax_id'),
                    "amount": invoice_data.get('amount'),
                    "subtotal": invoice_data.get('subtotal', 0),
                    "tax_percentage": invoice_data.get('tax_percentage', 0),
                    "tax_amount": invoice_data.get('tax_amount', 0),
                    "total_amount": invoice_data.get('total_amount'),
                    "total_amount_value": invoice_data.get('total_amount_value', 0),
                    "currency": invoice_data.get('currency', 'VND'),
                    "vendor": invoice_data.get('vendor'),
                    "description": invoice_data.get('description'),
                    "confidence_score": invoice_data.get('confidence_score', 0),
                    "ocr_text": invoice_data.get('ocr_text')
                })

                invoice_id = result.fetchone()[0]
                conn.commit()

                logger.info(f"✅ Invoice saved with ID: {invoice_id} (user_id: {effective_user_id})")
                return invoice_id

        except Exception as e:
            logger.error(f"❌ Failed to save invoice: {e}")
            return None

    def _get_default_user_id(self) -> Optional[int]:
        """Get default user ID for orphaned data"""
        try:
            with self.engine.connect() as conn:
                # Try to get first admin user
                result = conn.execute(text("""
                    SELECT id FROM users WHERE is_admin = TRUE ORDER BY id LIMIT 1
                """))
                row = result.fetchone()
                if row:
                    return row[0]
                
                # Fallback to any user
                result = conn.execute(text("SELECT id FROM users ORDER BY id LIMIT 1"))
                row = result.fetchone()
                if row:
                    return row[0]
                    
                return None
        except Exception:
            return None

    def save_image(self, filename: str, original_filename: str, file_data: bytes, 
                   file_size: int, mime_type: str, user_id: int = None, 
                   invoice_id: int = None, file_path: str = None,
                   storage_type: str = 'database') -> Optional[int]:
        """
        Save image file to database (unified schema).
        
        IMPORTANT: user_id is now REQUIRED.
        """
        effective_user_id = user_id
        
        if not effective_user_id:
            effective_user_id = self._get_default_user_id()
            if not effective_user_id:
                logger.error("❌ Cannot save image: user_id is required in unified schema")
                return None
        
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    INSERT INTO images (
                        user_id, invoice_id, filename, original_filename, 
                        file_path, file_data, file_size, mime_type, storage_type,
                        created_at, updated_at
                    )
                    VALUES (
                        :user_id, :invoice_id, :filename, :original_filename,
                        :file_path, :file_data, :file_size, :mime_type, :storage_type,
                        NOW(), NOW()
                    )
                    RETURNING id
                """), {
                    "user_id": effective_user_id,
                    "invoice_id": invoice_id,
                    "filename": filename,
                    "original_filename": original_filename,
                    "file_path": file_path,
                    "file_data": file_data,
                    "file_size": file_size,
                    "mime_type": mime_type,
                    "storage_type": storage_type
                })

                image_id = result.fetchone()[0]
                conn.commit()

                logger.info(f"✅ Image saved with ID: {image_id} (user_id: {effective_user_id})")
                return image_id

        except Exception as e:
            logger.error(f"❌ Failed to save image: {e}")
            return None

    def get_image(self, image_id: int) -> Optional[Dict]:
        """Get image from database by ID"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT id, user_id, invoice_id, filename, original_filename, 
                           file_path, file_data, file_size, mime_type, storage_type,
                           created_at, updated_at
                    FROM images WHERE id = :image_id
                """), {"image_id": image_id})

                row = result.fetchone()
                if row:
                    return {
                        'id': row[0],
                        'user_id': row[1],
                        'invoice_id': row[2],
                        'filename': row[3],
                        'original_filename': row[4],
                        'file_path': row[5],
                        'file_data': row[6],
                        'file_size': row[7],
                        'mime_type': row[8],
                        'storage_type': row[9],
                        'created_at': str(row[10]),
                        'updated_at': str(row[11])
                    }
                return None

        except Exception as e:
            logger.error(f"❌ Error getting image: {e}")
            return None

    def update_image_invoice_id(self, image_id: int, invoice_id: int) -> bool:
        """Update image record with invoice_id reference"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("""
                    UPDATE images 
                    SET invoice_id = :invoice_id, updated_at = NOW()
                    WHERE id = :image_id
                """), {
                    "image_id": image_id,
                    "invoice_id": invoice_id
                })
                
                conn.commit()
                logger.info(f"✅ Updated image {image_id} with invoice_id {invoice_id}")
                return True

        except Exception as e:
            logger.error(f"❌ Failed to update image invoice_id: {e}")
            return False

    def get_all_invoices(self, limit: int = 20, user_id: int = None) -> List[Dict]:
        """
        Get all invoices from database.
        Optional: filter by user_id
        """
        try:
            with self.engine.connect() as conn:
                if user_id:
                    query = """
                        SELECT id, user_id, filename, invoice_code, invoice_number, invoice_type, 
                               date_string, seller_name, buyer_name, 
                               total_amount, total_amount_value, amount,
                               confidence_score, created_at, filepath
                        FROM invoices 
                        WHERE user_id = :user_id
                        ORDER BY created_at DESC 
                        LIMIT :limit
                    """
                    result = conn.execute(text(query), {"user_id": user_id, "limit": limit})
                else:
                    query = """
                        SELECT id, user_id, filename, invoice_code, invoice_number, invoice_type, 
                               date_string, seller_name, buyer_name, 
                               total_amount, total_amount_value, amount,
                               confidence_score, created_at, filepath
                        FROM invoices 
                        ORDER BY created_at DESC 
                        LIMIT :limit
                    """
                    result = conn.execute(text(query), {"limit": limit})

                invoices = []
                for row in result:
                    # Convert Windows backslash to forward slash for URLs
                    filepath_value = row[14] if len(row) > 14 else None
                    if filepath_value:
                        filepath_value = filepath_value.replace('\\', '/')
                    
                    invoices.append({
                        'id': row[0],
                        'user_id': row[1],
                        'filename': row[2],
                        'invoice_code': row[3],
                        'invoice_number': row[4],
                        'invoice_type': row[5],
                        'date': row[6],  # date_string
                        'date_string': row[6],
                        'seller_name': row[7],
                        'buyer_name': row[8],
                        'total_amount': row[9],
                        'total_amount_value': float(row[10]) if row[10] else 0,
                        'amount': float(row[11]) if row[11] else 0,
                        'confidence': float(row[12]) if row[12] else 0.0,
                        'confidence_score': float(row[12]) if row[12] else 0.0,
                        'processed_at': str(row[13]),
                        'created_at': str(row[13]),
                        'file_path': filepath_value,
                        'filepath': filepath_value,
                        'status': 'completed'
                    })

                logger.info(f"✅ Retrieved {len(invoices)} invoices from PostgreSQL")
                return invoices

        except Exception as e:
            logger.error(f"❌ Error getting invoices: {e}")
            return []

    def search_invoices(self, query: str, limit: int = 20, user_id: int = None) -> List[Dict]:
        """Search invoices by query"""
        try:
            with self.engine.connect() as conn:
                search_pattern = f"%{query}%"
                
                base_query = """
                    SELECT id, user_id, filename, invoice_code, invoice_number, invoice_type, 
                           date_string, invoice_date, seller_name, buyer_name, 
                           total_amount, total_amount_value, amount,
                           confidence_score, created_at, filepath
                    FROM invoices 
                    WHERE (filename ILIKE :pattern OR invoice_code ILIKE :pattern 
                       OR invoice_number ILIKE :pattern
                       OR seller_name ILIKE :pattern OR buyer_name ILIKE :pattern)
                """
                
                if user_id:
                    base_query += " AND user_id = :user_id"
                    params = {"pattern": search_pattern, "user_id": user_id, "limit": limit}
                else:
                    params = {"pattern": search_pattern, "limit": limit}
                
                base_query += " ORDER BY created_at DESC LIMIT :limit"
                
                result = conn.execute(text(base_query), params)

                invoices = []
                for row in result:
                    filepath_value = row[15] if len(row) > 15 else None
                    if filepath_value:
                        filepath_value = filepath_value.replace('\\', '/')
                    
                    invoices.append({
                        'id': row[0],
                        'user_id': row[1],
                        'filename': row[2],
                        'invoice_code': row[3],
                        'invoice_number': row[4],
                        'invoice_type': row[5],
                        'date': row[6],
                        'date_string': row[6],
                        'invoice_date': str(row[7]) if row[7] else None,
                        'seller_name': row[8],
                        'buyer_name': row[9],
                        'total_amount': row[10],
                        'total_amount_value': float(row[11]) if row[11] else 0,
                        'amount': float(row[12]) if row[12] else 0,
                        'confidence': float(row[13]) if row[13] else 0.0,
                        'confidence_score': float(row[13]) if row[13] else 0.0,
                        'processed_at': str(row[14]),
                        'created_at': str(row[14]),
                        'file_path': filepath_value,
                        'filepath': filepath_value,
                        'status': 'completed'
                    })

                logger.info(f"✅ Found {len(invoices)} invoices matching '{query}'")
                return invoices

        except Exception as e:
            logger.error(f"❌ Error searching invoices: {e}")
            return []

    def get_invoice_by_id(self, invoice_id: int) -> Optional[Dict]:
        """Get invoice by ID"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT * FROM invoices WHERE id = :invoice_id
                """), {"invoice_id": invoice_id})

                row = result.fetchone()
                if row:
                    return self._row_to_invoice_dict(row)
                return None

        except Exception as e:
            logger.error(f"❌ Error getting invoice by ID: {e}")
            return None

    def get_invoice_by_filename(self, filename: str) -> Optional[Dict]:
        """Get invoice by filename"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT * FROM invoices WHERE filename = :filename
                """), {"filename": filename})

                row = result.fetchone()
                if row:
                    return self._row_to_invoice_dict(row)
                return None

        except Exception as e:
            logger.error(f"❌ Error getting invoice by filename: {e}")
            return None

    def _row_to_invoice_dict(self, row) -> Dict:
        """Convert database row to invoice dictionary"""
        return {
            'id': row[0],
            'user_id': row[1],
            'ocr_job_id': row[2],
            'file_id': row[3],
            'filename': row[4],
            'filepath': row[5],
            'invoice_number': row[6],
            'invoice_code': row[7],
            'invoice_type': row[8],
            'invoice_date': str(row[9]) if row[9] else None,
            'due_date': str(row[10]) if row[10] else None,
            'date_string': row[11],
            'date': row[11],  # Alias for compatibility
            'seller_name': row[12],
            'seller_address': row[13],
            'seller_tax_id': row[14],
            'buyer_name': row[15],
            'buyer_address': row[16],
            'buyer_tax_id': row[17],
            'amount': row[18],
            'subtotal': row[19],
            'tax_percentage': row[20],
            'tax_amount': row[21],
            'total_amount': row[22],
            'total_amount_value': row[23],
            'currency': row[24],
            'vendor': row[25],
            'description': row[26],
            'confidence_score': row[27],
            'ocr_text': row[28],
            'created_at': str(row[29]) if row[29] else None,
            'updated_at': str(row[30]) if row[30] else None
        }

    def get_statistics(self, user_id: int = None) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            with self.engine.connect() as conn:
                user_filter = ""
                params = {}
                if user_id:
                    user_filter = "WHERE user_id = :user_id"
                    params['user_id'] = user_id

                # Total invoices
                result = conn.execute(text(f"SELECT COUNT(*) FROM invoices {user_filter}"), params)
                total_invoices = result.fetchone()[0]

                # Average confidence
                result = conn.execute(text(f"SELECT AVG(confidence_score) FROM invoices {user_filter}"), params)
                avg_confidence = result.fetchone()[0] or 0

                # Invoice types distribution
                type_query = f"""
                    SELECT invoice_type, COUNT(*) as count 
                    FROM invoices {user_filter}
                    GROUP BY invoice_type
                """
                result = conn.execute(text(type_query), params)
                invoice_types = {row[0]: row[1] for row in result}

                # Recent 7 days
                recent_query = f"""
                    SELECT COUNT(*) FROM invoices 
                    WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
                    {"AND user_id = :user_id" if user_id else ""}
                """
                result = conn.execute(text(recent_query), params)
                recent_7days = result.fetchone()[0]

                # Total amount sum
                result = conn.execute(text(f"SELECT SUM(total_amount_value) FROM invoices {user_filter}"), params)
                total_amount_sum = result.fetchone()[0] or 0

                # User count (admin only)
                result = conn.execute(text("SELECT COUNT(*) FROM users"))
                total_users = result.fetchone()[0]

                return {
                    'total_invoices': total_invoices,
                    'avg_confidence': round(float(avg_confidence), 2),
                    'invoice_types': invoice_types,
                    'recent_7days': recent_7days,
                    'total_amount_sum': float(total_amount_sum),
                    'total_users': total_users
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
                    "is_active": user_data.get('is_active', True),
                    "is_admin": user_data.get('is_admin', False),
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

    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT * FROM users WHERE id = :user_id"), {"user_id": user_id})
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
                
                # Check table count
                result = conn.execute(text("""
                    SELECT COUNT(*) FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """))
                table_count = result.fetchone()[0]
                
                return {
                    "status": "healthy",
                    "message": "PostgreSQL connection successful",
                    "schema": "unified",
                    "table_count": table_count,
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
