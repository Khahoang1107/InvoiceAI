"""Unified schema - Merge Alembic + Database Tools schemas

Revision ID: 002_unified
Revises: 001_initial
Create Date: 2024-12-25 00:00:00.000000

This migration:
1. Adds missing 'role' field to users table
2. Recreates invoices table with ALL fields from both schemas
3. Creates images table for binary storage
4. Adds proper FK constraints and indexes
5. Migrates existing data safely
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import DateTime, func, text

# revision identifiers, used by Alembic.
revision = '002_unified'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade():
    """Upgrade to unified schema"""
    
    # ============================================
    # PHASE 1: Update users table - add role field
    # ============================================
    
    # Check if role column exists, if not add it
    try:
        op.add_column('users', sa.Column('role', sa.String(50), server_default='user'))
    except Exception:
        pass  # Column might already exist
    
    # Add index on role if not exists
    try:
        op.create_index('ix_users_role', 'users', ['role'])
    except Exception:
        pass
    
    # ============================================
    # PHASE 2: Backup existing invoices data
    # ============================================
    
    # Create backup table for existing invoices
    op.execute(text("""
        CREATE TABLE IF NOT EXISTS _invoices_backup AS 
        SELECT * FROM invoices WHERE 1=1
    """))
    
    # ============================================
    # PHASE 3: Drop old invoices table
    # ============================================
    
    # Drop foreign key constraints if they exist
    try:
        op.drop_constraint('invoices_user_id_fkey', 'invoices', type_='foreignkey')
    except Exception:
        pass
    
    try:
        op.drop_constraint('invoices_ocr_job_id_fkey', 'invoices', type_='foreignkey')
    except Exception:
        pass
    
    # Drop indexes
    try:
        op.drop_index('ix_invoices_id', 'invoices')
        op.drop_index('ix_invoices_user_id', 'invoices')
        op.drop_index('ix_invoices_invoice_number', 'invoices')
    except Exception:
        pass
    
    # Drop old invoices table
    op.drop_table('invoices')
    
    # ============================================
    # PHASE 4: Create unified invoices table
    # ============================================
    
    op.create_table(
        'invoices',
        # Primary key
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        
        # Foreign keys - REQUIRED
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('ocr_job_id', sa.Integer(), nullable=True),
        sa.Column('file_id', sa.String(255), nullable=True),
        
        # File info (from Database Tools)
        sa.Column('filename', sa.String(255), nullable=True),
        sa.Column('filepath', sa.String(500), nullable=True),
        
        # Invoice identification (merged)
        sa.Column('invoice_number', sa.String(100), nullable=True),
        sa.Column('invoice_code', sa.String(255), nullable=True),
        sa.Column('invoice_type', sa.String(100), server_default='general'),
        
        # Dates (merged)
        sa.Column('invoice_date', sa.DateTime(), nullable=True),
        sa.Column('due_date', sa.DateTime(), nullable=True),
        sa.Column('date_string', sa.String(50), nullable=True),  # Original string from OCR
        
        # Seller info (from Database Tools)
        sa.Column('seller_name', sa.String(255), nullable=True),
        sa.Column('seller_address', sa.String(500), nullable=True),
        sa.Column('seller_tax_id', sa.String(100), nullable=True),
        
        # Buyer info (from Database Tools)
        sa.Column('buyer_name', sa.String(255), nullable=True),
        sa.Column('buyer_address', sa.String(500), nullable=True),
        sa.Column('buyer_tax_id', sa.String(100), nullable=True),
        
        # Financial fields (merged)
        sa.Column('amount', sa.Float(), nullable=True),  # From Alembic
        sa.Column('subtotal', sa.Float(), server_default='0'),
        sa.Column('tax_percentage', sa.Float(), server_default='0'),
        sa.Column('tax_amount', sa.Float(), server_default='0'),
        sa.Column('total_amount', sa.String(100), nullable=True),  # String display
        sa.Column('total_amount_value', sa.Float(), server_default='0'),  # Numeric value
        sa.Column('currency', sa.String(10), server_default='VND'),
        
        # Additional info (from Alembic)
        sa.Column('vendor', sa.String(255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        
        # OCR metadata (from Database Tools)
        sa.Column('confidence_score', sa.Float(), server_default='0'),
        sa.Column('ocr_text', sa.Text(), nullable=True),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=func.now(), onupdate=func.now()),
        
        # Constraints
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['ocr_job_id'], ['ocr_jobs.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['file_id'], ['uploaded_files.file_id'], ondelete='SET NULL'),
    )
    
    # Create indexes for unified invoices
    op.create_index('ix_invoices_id', 'invoices', ['id'])
    op.create_index('ix_invoices_user_id', 'invoices', ['user_id'])
    op.create_index('ix_invoices_ocr_job_id', 'invoices', ['ocr_job_id'])
    op.create_index('ix_invoices_file_id', 'invoices', ['file_id'])
    op.create_index('ix_invoices_invoice_number', 'invoices', ['invoice_number'])
    op.create_index('ix_invoices_invoice_code', 'invoices', ['invoice_code'])
    op.create_index('ix_invoices_invoice_type', 'invoices', ['invoice_type'])
    op.create_index('ix_invoices_invoice_date', 'invoices', ['invoice_date'])
    op.create_index('ix_invoices_created_at', 'invoices', ['created_at'])
    
    # ============================================
    # PHASE 5: Migrate data from backup
    # ============================================
    
    # Migrate existing data - handle both schema formats
    op.execute(text("""
        INSERT INTO invoices (
            id, user_id, invoice_number, amount, currency, vendor, description,
            invoice_date, due_date, ocr_job_id, created_at, updated_at
        )
        SELECT 
            id, user_id, invoice_number, amount, currency, vendor, description,
            invoice_date, due_date, ocr_job_id, created_at, updated_at
        FROM _invoices_backup
        WHERE user_id IS NOT NULL
    """))
    
    # ============================================
    # PHASE 6: Create images table
    # ============================================
    
    op.create_table(
        'images',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('invoice_id', sa.Integer(), nullable=True),
        sa.Column('uploaded_file_id', sa.Integer(), nullable=True),
        
        # File info
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('original_filename', sa.String(255), nullable=True),
        sa.Column('file_path', sa.String(500), nullable=True),
        sa.Column('file_data', sa.LargeBinary(), nullable=True),  # BYTEA for binary storage
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('mime_type', sa.String(100), nullable=True),
        sa.Column('storage_type', sa.String(20), server_default='filesystem'),  # 'filesystem' or 'database'
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=func.now(), onupdate=func.now()),
        
        # Constraints
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['uploaded_file_id'], ['uploaded_files.id'], ondelete='SET NULL'),
    )
    
    # Create indexes for images
    op.create_index('ix_images_id', 'images', ['id'])
    op.create_index('ix_images_user_id', 'images', ['user_id'])
    op.create_index('ix_images_invoice_id', 'images', ['invoice_id'])
    op.create_index('ix_images_uploaded_file_id', 'images', ['uploaded_file_id'])
    op.create_index('ix_images_created_at', 'images', ['created_at'])
    
    # ============================================
    # PHASE 7: Cleanup
    # ============================================
    
    # Keep backup table for safety - can be dropped manually after verification
    # op.execute(text("DROP TABLE IF EXISTS _invoices_backup"))


def downgrade():
    """Revert to original schema"""
    
    # Drop images table
    op.drop_index('ix_images_created_at', 'images')
    op.drop_index('ix_images_uploaded_file_id', 'images')
    op.drop_index('ix_images_invoice_id', 'images')
    op.drop_index('ix_images_user_id', 'images')
    op.drop_index('ix_images_id', 'images')
    op.drop_table('images')
    
    # Backup current invoices
    op.execute(text("""
        CREATE TABLE IF NOT EXISTS _invoices_unified_backup AS 
        SELECT * FROM invoices WHERE 1=1
    """))
    
    # Drop unified invoices indexes
    op.drop_index('ix_invoices_created_at', 'invoices')
    op.drop_index('ix_invoices_invoice_date', 'invoices')
    op.drop_index('ix_invoices_invoice_type', 'invoices')
    op.drop_index('ix_invoices_invoice_code', 'invoices')
    op.drop_index('ix_invoices_invoice_number', 'invoices')
    op.drop_index('ix_invoices_file_id', 'invoices')
    op.drop_index('ix_invoices_ocr_job_id', 'invoices')
    op.drop_index('ix_invoices_user_id', 'invoices')
    op.drop_index('ix_invoices_id', 'invoices')
    
    # Drop unified invoices table
    op.drop_table('invoices')
    
    # Recreate original invoices table
    op.create_table(
        'invoices',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('invoice_number', sa.String(100), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(3), server_default='USD'),
        sa.Column('vendor', sa.String(255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('invoice_date', sa.DateTime(), nullable=False),
        sa.Column('due_date', sa.DateTime(), nullable=True),
        sa.Column('ocr_job_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=func.now(), onupdate=func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_invoices_id', 'invoices', ['id'])
    op.create_index('ix_invoices_user_id', 'invoices', ['user_id'])
    op.create_index('ix_invoices_invoice_number', 'invoices', ['invoice_number'])
    
    # Restore data from backup
    op.execute(text("""
        INSERT INTO invoices (
            id, user_id, invoice_number, amount, currency, vendor, description,
            invoice_date, due_date, ocr_job_id, created_at, updated_at
        )
        SELECT 
            id, user_id, 
            COALESCE(invoice_number, invoice_code, 'N/A'),
            COALESCE(amount, total_amount_value, 0),
            COALESCE(currency, 'USD'),
            vendor, description,
            invoice_date, due_date, ocr_job_id, created_at, updated_at
        FROM _invoices_unified_backup
    """))
    
    # Remove role column from users
    try:
        op.drop_index('ix_users_role', 'users')
        op.drop_column('users', 'role')
    except Exception:
        pass
