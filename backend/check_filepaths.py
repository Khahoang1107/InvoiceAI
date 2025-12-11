"""
Check invoices filepath status
"""
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

# Get all invoices
cursor.execute("""
    SELECT id, filename, invoice_code, filepath, created_at 
    FROM invoices 
    ORDER BY created_at DESC
    LIMIT 20
""")

invoices = cursor.fetchall()
print(f"\nTotal invoices: {len(invoices)}\n")
print(f"{'ID':<5} {'Invoice Code':<20} {'Filename':<40} {'Filepath':<60}")
print("-" * 130)

for inv_id, filename, invoice_code, filepath, created_at in invoices:
    filepath_display = filepath if filepath else "❌ NO FILEPATH"
    print(f"{inv_id:<5} {invoice_code:<20} {filename:<40} {filepath_display:<60}")

# Count invoices with and without filepath
cursor.execute("SELECT COUNT(*) FROM invoices WHERE filepath IS NOT NULL AND filepath != ''")
with_path = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM invoices WHERE filepath IS NULL OR filepath = ''")
without_path = cursor.fetchone()[0]

print(f"\n✅ With filepath: {with_path}")
print(f"❌ Without filepath: {without_path}")

cursor.close()
conn.close()
