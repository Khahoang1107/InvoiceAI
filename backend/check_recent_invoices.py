"""
Check recent invoices in database
"""
from utils.database_tools_postgres import get_database_tools
from datetime import datetime, timedelta

db = get_database_tools()

print("=" * 60)
print("🔍 CHECKING RECENT INVOICES")
print("=" * 60)

# Get all invoices (no user filter)
print("\n📊 ALL INVOICES (no user filter):")
all_invoices = db.get_all_invoices(limit=50)
print(f"Total: {len(all_invoices)} invoices\n")

# Group by user
by_user = {}
for inv in all_invoices:
    user_id = inv.get('user_id', 'UNKNOWN')
    if user_id not in by_user:
        by_user[user_id] = []
    by_user[user_id].append(inv)

# Show by user
for user_id, invs in sorted(by_user.items()):
    print(f"\n👤 User ID: {user_id}")
    print(f"   Invoices: {len(invs)}")
    
    # Show most recent 3
    recent = sorted(invs, key=lambda x: x.get('created_at', ''), reverse=True)[:3]
    for inv in recent:
        print(f"   - {inv.get('invoice_code', 'N/A')}: {inv.get('seller_name', 'N/A')} → {inv.get('buyer_name', 'N/A')} ({inv.get('created_at', 'N/A')})")

print("\n" + "=" * 60)
print("🔍 RECENT 10 INVOICES:")
print("=" * 60)

recent_10 = sorted(all_invoices, key=lambda x: x.get('created_at', ''), reverse=True)[:10]
for i, inv in enumerate(recent_10, 1):
    print(f"\n{i}. ID: {inv.get('id')}")
    print(f"   User ID: {inv.get('user_id', 'UNKNOWN')}")
    print(f"   Code: {inv.get('invoice_code')}")
    print(f"   Seller: {inv.get('seller_name')}")
    print(f"   Buyer: {inv.get('buyer_name')}")
    print(f"   Amount: {inv.get('total_amount')}")
    print(f"   Created: {inv.get('created_at')}")

print("\n" + "=" * 60)
