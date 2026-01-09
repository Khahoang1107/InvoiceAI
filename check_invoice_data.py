from sqlalchemy import create_engine, text
import os

# Direct import
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
import config as backend_config

engine = create_engine(backend_config.Config.DATABASE_URL)

with engine.connect() as conn:
    result = conn.execute(text('SELECT id, filename, filepath FROM invoices WHERE user_id = 2 LIMIT 3'))
    for row in result:
        print(f'ID: {row[0]}')
        print(f'  filename: {row[1]}')
        print(f'  filepath: {row[2]}')
        print()
