"""
Script to update filepath for existing invoices in database
"""
import os
import psycopg2
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Get database URL
DATABASE_URL = os.getenv("DATABASE_URL")

# Connect to database
try:
    conn = psycopg2.connect(DATABASE_URL)
    print(f"✅ Connected to database")
except Exception as e:
    print(f"❌ Failed to connect: {e}")
    exit(1)

if conn:
    try:
        cursor = conn.cursor()
        
        # Get all invoices without filepath
        cursor.execute("""
            SELECT id, filename, invoice_code, created_at 
            FROM invoices 
            WHERE filepath IS NULL OR filepath = ''
            ORDER BY created_at DESC
        """)
        
        invoices = cursor.fetchall()
        print(f"Found {len(invoices)} invoices without filepath")
        
        # Check uploads directory
        uploads_dir = "uploads"
        if os.path.exists(uploads_dir):
            files = os.listdir(uploads_dir)
            print(f"Found {len(files)} files in uploads directory: {files}")
            
            # Update each invoice
            for invoice_id, filename, invoice_code, created_at in invoices:
                # Try to find matching file
                matched_file = None
                
                # Check if exact filename exists
                if filename in files:
                    matched_file = filename
                else:
                    # Try to match by invoice_code or filename pattern
                    for file in files:
                        if invoice_code and invoice_code.replace('-', '') in file:
                            matched_file = file
                            break
                        # Check if file contains part of original filename
                        base_name = os.path.splitext(filename)[0]
                        if base_name.lower() in file.lower():
                            matched_file = file
                            break
                
                if matched_file:
                    filepath = os.path.join(uploads_dir, matched_file)
                    cursor.execute("""
                        UPDATE invoices 
                        SET filepath = %s 
                        WHERE id = %s
                    """, (filepath, invoice_id))
                    print(f"✅ Updated invoice {invoice_id} ({invoice_code}) with filepath: {filepath}")
                else:
                    print(f"⚠️ No matching file found for invoice {invoice_id} ({filename})")
        
        conn.commit()
        print(f"✅ Database update complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
else:
    print("❌ Could not connect to database")
