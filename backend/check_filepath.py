from dotenv import load_dotenv
import os
load_dotenv()

import psycopg2

conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()

cur.execute('SELECT id, filename, filepath FROM invoices WHERE user_id=2 ORDER BY created_at DESC LIMIT 3')
rows = cur.fetchall()

print('\n=== FILEPATH CHECK ===')
for row in rows:
    print(f'\nID: {row[0]}')
    print(f'Filename: {row[1]}')
    print(f'Filepath: {row[2]}')
    
    # Check if file exists
    if row[2]:
        # Try both paths
        path1 = row[2]
        path2 = f'backend/{row[2]}'
        path3 = f'uploads/{row[1]}' if row[1] else None
        
        print(f'Path in DB: {path1}')
        exists1 = os.path.exists(path1)
        exists2 = os.path.exists(path2)
        exists3 = os.path.exists(path3) if path3 else False
        
        print(f'Exists at "{path1}": {exists1}')
        print(f'Exists at "{path2}": {exists2}')
        if path3:
            print(f'Exists at "{path3}": {exists3}')

conn.close()
