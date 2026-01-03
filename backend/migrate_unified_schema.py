"""
Unified Schema Migration Script
Run this script to migrate database to unified schema.

Usage:
    python migrate_unified_schema.py [--check] [--migrate] [--rollback]
    
Options:
    --check     Check current database state without making changes
    --migrate   Run migration to unified schema
    --rollback  Rollback to previous schema (use with caution)
"""

import os
import sys
import logging
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_database_state():
    """Check current database state and report issues"""
    from dotenv import load_dotenv
    load_dotenv()
    
    database_url = os.getenv("DATABASE_URL", "")
    
    if database_url.startswith("postgresql"):
        return check_postgres_state(database_url)
    else:
        return check_sqlite_state()


def check_postgres_state(database_url: str):
    """Check PostgreSQL database state"""
    from sqlalchemy import create_engine, text
    
    logger.info("🔍 Checking PostgreSQL database state...")
    
    try:
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # Get all tables
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result]
            
            logger.info(f"📋 Found {len(tables)} tables: {tables}")
            
            # Check each table structure
            for table in tables:
                result = conn.execute(text(f"""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_name = '{table}'
                    ORDER BY ordinal_position
                """))
                columns = [(row[0], row[1], row[2]) for row in result]
                logger.info(f"  📊 {table}: {len(columns)} columns")
            
            # Check for unified schema indicators
            issues = []
            
            # Check if users has 'role' column
            if 'users' in tables:
                result = conn.execute(text("""
                    SELECT column_name FROM information_schema.columns
                    WHERE table_name = 'users' AND column_name = 'role'
                """))
                if not result.fetchone():
                    issues.append("❌ users table missing 'role' column")
                else:
                    logger.info("✅ users.role column exists")
            
            # Check if invoices has 'user_id' column
            if 'invoices' in tables:
                result = conn.execute(text("""
                    SELECT column_name FROM information_schema.columns
                    WHERE table_name = 'invoices' AND column_name = 'user_id'
                """))
                if not result.fetchone():
                    issues.append("❌ invoices table missing 'user_id' column")
                else:
                    logger.info("✅ invoices.user_id column exists")
                
                # Check for OCR fields in invoices
                result = conn.execute(text("""
                    SELECT column_name FROM information_schema.columns
                    WHERE table_name = 'invoices' AND column_name = 'ocr_text'
                """))
                if not result.fetchone():
                    issues.append("⚠️ invoices missing OCR fields (not unified)")
                else:
                    logger.info("✅ invoices has OCR fields (unified)")
            
            # Check images table
            if 'images' not in tables:
                issues.append("⚠️ images table does not exist")
            else:
                logger.info("✅ images table exists")
            
            # Check alembic version
            if 'alembic_version' in tables:
                result = conn.execute(text("SELECT version_num FROM alembic_version"))
                versions = [row[0] for row in result]
                logger.info(f"📌 Alembic versions: {versions}")
                
                if '002_unified' in versions:
                    logger.info("✅ Unified schema migration (002_unified) is applied")
                else:
                    issues.append("⚠️ Unified schema migration not applied")
            
            # Report data counts
            logger.info("\n📊 Data Statistics:")
            for table in tables:
                if not table.startswith('_') and table != 'alembic_version':
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.fetchone()[0]
                    logger.info(f"  {table}: {count} records")
            
            # Check for orphaned data
            if 'invoices' in tables:
                try:
                    result = conn.execute(text("""
                        SELECT COUNT(*) FROM invoices 
                        WHERE user_id IS NULL OR user_id NOT IN (SELECT id FROM users)
                    """))
                    orphaned = result.fetchone()[0]
                    if orphaned > 0:
                        issues.append(f"⚠️ {orphaned} orphaned invoices (no valid user_id)")
                except:
                    pass
            
            # Summary
            if issues:
                logger.warning("\n⚠️ Issues found:")
                for issue in issues:
                    logger.warning(f"  {issue}")
                return False
            else:
                logger.info("\n✅ Database is in good state!")
                return True
                
    except Exception as e:
        logger.error(f"❌ Error checking database: {e}")
        return False


def check_sqlite_state():
    """Check SQLite database state"""
    logger.info("🔍 Checking SQLite database state...")
    
    import sqlite3
    
    db_path = os.getenv("DATABASE_URL", "sqlite:///./chatbot.db")
    if db_path.startswith("sqlite:///"):
        db_path = db_path.replace("sqlite:///", "")
    
    if not os.path.exists(db_path):
        logger.warning(f"⚠️ Database file not found: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]
        
        logger.info(f"📋 Found {len(tables)} tables: {tables}")
        
        # Report data counts
        logger.info("\n📊 Data Statistics:")
        for table in tables:
            if not table.startswith('_') and table != 'alembic_version' and table != 'sqlite_sequence':
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                logger.info(f"  {table}: {count} records")
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Error checking database: {e}")
        return False


def run_alembic_migration():
    """Run Alembic migration to unified schema"""
    logger.info("🚀 Running Alembic migration...")
    
    try:
        import subprocess
        
        # Change to backend directory
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Run alembic upgrade
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            cwd=backend_dir,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            logger.info("✅ Alembic migration completed successfully!")
            logger.info(result.stdout)
            return True
        else:
            logger.error(f"❌ Alembic migration failed:")
            logger.error(result.stderr)
            return False
            
    except FileNotFoundError:
        logger.warning("⚠️ Alembic not found, running fallback migration...")
        return run_fallback_migration()
    except Exception as e:
        logger.error(f"❌ Migration error: {e}")
        return False


def run_fallback_migration():
    """Run fallback migration without Alembic"""
    from dotenv import load_dotenv
    load_dotenv()
    
    database_url = os.getenv("DATABASE_URL", "")
    
    if database_url.startswith("postgresql"):
        logger.info("🔄 Running PostgreSQL fallback migration...")
        from utils.database_tools_postgres import DatabaseToolsPostgres
        try:
            db = DatabaseToolsPostgres(database_url)
            logger.info("✅ PostgreSQL unified schema initialized!")
            return True
        except Exception as e:
            logger.error(f"❌ PostgreSQL migration failed: {e}")
            return False
    else:
        logger.info("🔄 Running SQLite fallback migration...")
        from utils.database_tools_sqlite import DatabaseTools
        try:
            db = DatabaseTools()
            logger.info("✅ SQLite unified schema initialized!")
            return True
        except Exception as e:
            logger.error(f"❌ SQLite migration failed: {e}")
            return False


def migrate_orphaned_data():
    """Migrate orphaned invoices to have a valid user_id"""
    from dotenv import load_dotenv
    load_dotenv()
    
    database_url = os.getenv("DATABASE_URL", "")
    
    if not database_url.startswith("postgresql"):
        logger.info("⏭️ Skipping orphaned data migration (SQLite)")
        return True
    
    from sqlalchemy import create_engine, text
    
    logger.info("🔄 Migrating orphaned data...")
    
    try:
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # Check for orphaned invoices
            result = conn.execute(text("""
                SELECT COUNT(*) FROM invoices 
                WHERE user_id IS NULL
            """))
            orphaned_count = result.fetchone()[0]
            
            if orphaned_count == 0:
                logger.info("✅ No orphaned invoices found")
                return True
            
            logger.info(f"⚠️ Found {orphaned_count} orphaned invoices")
            
            # Get or create system user
            result = conn.execute(text("""
                SELECT id FROM users WHERE email = 'system@invoiceai.local'
            """))
            row = result.fetchone()
            
            if row:
                system_user_id = row[0]
            else:
                # Create system user
                result = conn.execute(text("""
                    INSERT INTO users (email, name, hashed_password, is_admin, role)
                    VALUES ('system@invoiceai.local', 'OCR System', 'disabled', TRUE, 'system')
                    RETURNING id
                """))
                system_user_id = result.fetchone()[0]
                conn.commit()
                logger.info(f"✅ Created system user with ID: {system_user_id}")
            
            # Update orphaned invoices
            conn.execute(text("""
                UPDATE invoices SET user_id = :user_id WHERE user_id IS NULL
            """), {"user_id": system_user_id})
            conn.commit()
            
            logger.info(f"✅ Assigned {orphaned_count} orphaned invoices to system user")
            return True
            
    except Exception as e:
        logger.error(f"❌ Error migrating orphaned data: {e}")
        return False


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Unified Schema Migration Tool")
    parser.add_argument("--check", action="store_true", help="Check database state")
    parser.add_argument("--migrate", action="store_true", help="Run migration")
    parser.add_argument("--fix-orphans", action="store_true", help="Fix orphaned data")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🔧 InvoiceAI - Unified Schema Migration Tool")
    print("=" * 60)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    if args.check or (not args.migrate and not args.fix_orphans):
        check_database_state()
    
    if args.migrate:
        print("\n" + "=" * 60)
        print("🚀 Running Migration")
        print("=" * 60)
        
        success = run_alembic_migration()
        
        if success:
            # Also fix orphans after migration
            migrate_orphaned_data()
            
            print("\n" + "=" * 60)
            print("✅ Migration completed! Verifying...")
            print("=" * 60)
            check_database_state()
    
    if args.fix_orphans:
        print("\n" + "=" * 60)
        print("🔄 Fixing Orphaned Data")
        print("=" * 60)
        migrate_orphaned_data()


if __name__ == "__main__":
    main()
