"""
Migration: Add chat_history table
Created: 2024-12-29
"""

from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost/invoiceai")

def upgrade():
    """Create chat_history table"""
    engine = create_engine(DATABASE_URL)
    metadata = MetaData()
    
    chat_history = Table(
        'chat_history',
        metadata,
        Column('id', Integer, primary_key=True, autoincrement=True),
        Column('user_id', Integer, ForeignKey('users.id'), nullable=False),
        Column('conversation_id', String(255), nullable=False, index=True),
        Column('role', String(50), nullable=False),  # 'user' or 'assistant'
        Column('message', Text, nullable=False),
        Column('tokens_used', Integer, default=0),
        Column('model', String(100)),
        Column('created_at', DateTime(timezone=True), server_default=func.now()),
        Column('is_deleted', Boolean, default=False)
    )
    
    # Create table
    metadata.create_all(engine)
    print("✅ Created chat_history table")
    
    # Create index
    from sqlalchemy import text
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_chat_history_user_conversation 
            ON chat_history(user_id, conversation_id, created_at DESC);
        """))
        conn.commit()
    print("✅ Created indexes")


def downgrade():
    """Drop chat_history table"""
    engine = create_engine(DATABASE_URL)
    metadata = MetaData()
    
    chat_history = Table('chat_history', metadata)
    chat_history.drop(engine, checkfirst=True)
    print("✅ Dropped chat_history table")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python add_chat_history_table.py [upgrade|downgrade]")
        sys.exit(1)
    
    action = sys.argv[1]
    
    if action == "upgrade":
        upgrade()
    elif action == "downgrade":
        downgrade()
    else:
        print("Invalid action. Use 'upgrade' or 'downgrade'")
        sys.exit(1)
