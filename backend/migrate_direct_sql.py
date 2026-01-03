"""
Direct SQL Migration for Existing Database
This script adds missing columns to existing tables without recreating them.
"""

import os
import sys
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def migrate_existing_database():
    """Add missing columns to existing database"""
    from sqlalchemy import create_engine, text
    
    database_url = os.getenv("DATABASE_URL", "")
    
    if not database_url.startswith("postgresql"):
        logger.error("❌ This script is for PostgreSQL only")
        return False
    
    logger.info("🔄 Migrating existing PostgreSQL database to unified schema...")
    
    try:
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # ========================================
            # STEP 1: Add user_id to invoices
            # ========================================
            logger.info("📝 Step 1: Adding user_id to invoices...")
            
            # Check if column exists
            result = conn.execute(text("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'invoices' AND column_name = 'user_id'
            """))
            
            if not result.fetchone():
                # Get default user (first admin or first user)
                result = conn.execute(text("""
                    SELECT id FROM users WHERE is_admin = 1 ORDER BY id LIMIT 1
                """))
                row = result.fetchone()
                
                if not row:
                    result = conn.execute(text("SELECT id FROM users ORDER BY id LIMIT 1"))
                    row = result.fetchone()
                
                if not row:
                    logger.error("❌ No users found! Please create a user first.")
                    return False
                
                default_user_id = row[0]
                logger.info(f"  Using default user_id: {default_user_id}")
                
                # Add user_id column with default value
                conn.execute(text(f"""
                    ALTER TABLE invoices 
                    ADD COLUMN user_id INTEGER DEFAULT {default_user_id}
                """))
                conn.commit()
                logger.info("  ✅ Added user_id column to invoices")
                
                # Make it NOT NULL after setting default
                conn.execute(text("""
                    ALTER TABLE invoices 
                    ALTER COLUMN user_id SET NOT NULL
                """))
                conn.commit()
                logger.info("  ✅ Set user_id as NOT NULL")
                
                # Add foreign key constraint
                try:
                    conn.execute(text("""
                        ALTER TABLE invoices 
                        ADD CONSTRAINT fk_invoices_user_id 
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT
                    """))
                    conn.commit()
                    logger.info("  ✅ Added FK constraint for user_id")
                except Exception as e:
                    logger.warning(f"  ⚠️ Could not add FK constraint: {e}")
                
                # Create index
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS ix_invoices_user_id ON invoices(user_id)
                """))
                conn.commit()
                logger.info("  ✅ Created index on user_id")
            else:
                logger.info("  ✅ user_id column already exists")
            
            # ========================================
            # STEP 2: Add other missing columns to invoices
            # ========================================
            logger.info("📝 Step 2: Adding other missing columns to invoices...")
            
            columns_to_add = [
                ("ocr_job_id", "INTEGER"),
                ("file_id", "VARCHAR(255)"),
                ("invoice_number", "VARCHAR(100)"),
                ("amount", "FLOAT"),
                ("vendor", "VARCHAR(255)"),
                ("description", "TEXT"),
                ("due_date", "TIMESTAMP"),
                ("date_string", "VARCHAR(50)")
            ]
            
            for col_name, col_type in columns_to_add:
                result = conn.execute(text(f"""
                    SELECT column_name FROM information_schema.columns
                    WHERE table_name = 'invoices' AND column_name = '{col_name}'
                """))
                
                if not result.fetchone():
                    conn.execute(text(f"ALTER TABLE invoices ADD COLUMN {col_name} {col_type}"))
                    conn.commit()
                    logger.info(f"  ✅ Added column: {col_name}")
            
            # ========================================
            # STEP 3: Add missing columns to images
            # ========================================
            logger.info("📝 Step 3: Updating images table...")
            
            # Check if images.user_id has NOT NULL constraint
            result = conn.execute(text("""
                SELECT is_nullable FROM information_schema.columns
                WHERE table_name = 'images' AND column_name = 'user_id'
            """))
            row = result.fetchone()
            
            if row:
                # Get default user for images without user_id
                result = conn.execute(text("""
                    SELECT id FROM users WHERE is_admin = 1 ORDER BY id LIMIT 1
                """))
                default_row = result.fetchone()
                if default_row:
                    default_user_id = default_row[0]
                    
                    # Update null user_ids
                    conn.execute(text(f"""
                        UPDATE images SET user_id = {default_user_id} WHERE user_id IS NULL
                    """))
                    conn.commit()
                    logger.info(f"  ✅ Updated images with null user_id to {default_user_id}")
            
            # Add storage_type if missing
            result = conn.execute(text("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'images' AND column_name = 'storage_type'
            """))
            if not result.fetchone():
                conn.execute(text("""
                    ALTER TABLE images ADD COLUMN storage_type VARCHAR(20) DEFAULT 'database'
                """))
                conn.commit()
                logger.info("  ✅ Added storage_type column")
            
            # Add file_path if missing
            result = conn.execute(text("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'images' AND column_name = 'file_path'
            """))
            if not result.fetchone():
                conn.execute(text("ALTER TABLE images ADD COLUMN file_path VARCHAR(500)"))
                conn.commit()
                logger.info("  ✅ Added file_path column")
            
            # ========================================
            # STEP 4: Create missing tables
            # ========================================
            logger.info("📝 Step 4: Creating missing tables...")
            
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
            conn.commit()
            logger.info("  ✅ messages table ready")
            
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
            conn.commit()
            logger.info("  ✅ uploaded_files table ready")
            
            # Create ocr_jobs table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS ocr_jobs (
                    id SERIAL PRIMARY KEY,
                    file_id VARCHAR(255) UNIQUE NOT NULL,
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
            conn.commit()
            logger.info("  ✅ ocr_jobs table ready")
            
            # ========================================
            # STEP 5: Create all indexes
            # ========================================
            logger.info("📝 Step 5: Creating indexes...")
            
            indexes = [
                "CREATE INDEX IF NOT EXISTS ix_users_email ON users(email)",
                "CREATE INDEX IF NOT EXISTS ix_users_role ON users(role)",
                "CREATE INDEX IF NOT EXISTS ix_messages_user_id ON messages(user_id)",
                "CREATE INDEX IF NOT EXISTS ix_messages_conversation_id ON messages(conversation_id)",
                "CREATE INDEX IF NOT EXISTS ix_uploaded_files_user_id ON uploaded_files(user_id)",
                "CREATE INDEX IF NOT EXISTS ix_uploaded_files_file_id ON uploaded_files(file_id)",
                "CREATE INDEX IF NOT EXISTS ix_ocr_jobs_user_id ON ocr_jobs(user_id)",
                "CREATE INDEX IF NOT EXISTS ix_ocr_jobs_status ON ocr_jobs(status)",
                "CREATE INDEX IF NOT EXISTS ix_invoices_invoice_code ON invoices(invoice_code)",
                "CREATE INDEX IF NOT EXISTS ix_invoices_invoice_type ON invoices(invoice_type)",
                "CREATE INDEX IF NOT EXISTS ix_invoices_created_at ON invoices(created_at)",
                "CREATE INDEX IF NOT EXISTS ix_images_user_id ON images(user_id)",
                "CREATE INDEX IF NOT EXISTS ix_images_invoice_id ON images(invoice_id)",
            ]
            
            for idx_sql in indexes:
                try:
                    conn.execute(text(idx_sql))
                    conn.commit()
                except Exception as e:
                    pass  # Index might already exist
            
            logger.info("  ✅ All indexes created")
            
            # ========================================
            # STEP 6: Verify final state
            # ========================================
            logger.info("📝 Step 6: Verifying final state...")
            
            result = conn.execute(text("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result]
            logger.info(f"  Tables: {tables}")
            
            # Count records
            for table in ['users', 'invoices', 'images', 'messages', 'uploaded_files', 'ocr_jobs']:
                if table in tables:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.fetchone()[0]
                    logger.info(f"  {table}: {count} records")
            
            logger.info("\n✅ Migration completed successfully!")
            return True
            
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("🔧 InvoiceAI - Direct SQL Migration")
    print("=" * 60)
    
    migrate_existing_database()
