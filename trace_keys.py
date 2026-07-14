import os
from dotenv import load_dotenv
load_dotenv()
import psycopg2
import psycopg2.extras

conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

# Simulate what fetch_claims_from_postgres() returns
from services.pg_sync import COL_MAP

reverse_map = {v: k for k, v in COL_MAP.items()}
reverse_map["claim_id"] = "Claim ID"

cur.execute("SELECT * FROM claims WHERE LOWER(status) LIKE '%replace%' LIMIT 1;")
row = dict(cur.fetchone())

print("=== RAW DB COLUMNS (postgres names) FOR A REPLACEMENT CLAIM ===")
for k, v in row.items():
    if v and str(v).strip() not in ('', 'None', 'nan', 'False'):
        print(f"  DB col: {k!r:55} | value: {str(v)[:40]!r}")

print("\n=== AFTER reverse_map (Sheet-header names seen by ClaimWrapper) ===")
mapped = {}
for pg_col, val in row.items():
    sheet_key = reverse_map.get(pg_col, pg_col)
    mapped[sheet_key] = val

replacement_keys = [k for k in mapped.keys() if any(x in k.lower() for x in ['replace', 'invoice', 'settl', 'mail', 'store', 'confirm', 'approval'])]
print(f"\n  Replacement-related keys visible to ClaimWrapper:")
for k in sorted(replacement_keys):
    print(f"  {k!r:60} = {str(mapped[k])[:30]!r}")

# Now simulate what ClaimWrapper properties actually read
print("\n=== WHAT ClaimWrapper PROPERTIES LOOK UP ===")
lookup_keys = {
    'mail_sent_to_store': ["Replacement: Mail to Store", "Mail Sent To Store (Yes/No)"],
    'invoice_generated': ["Replacement: Invoice Generated", "Invoice Generated (Yes/No)"],
    'invoice_sent_osg': ["Replacement: Invoice Sent to OSG", "Invoice Sent To Onsitego (Yes/No)"],
    'settled_with_accounts': ["Replacement: Settled with Accounts", "Settled With Accounts (Yes/No)"],
    'settlement_mail_accounts': ["Replacement: Settlement Mail to Accounts", "Settlement Mail to Accounts(Yes/No)", "Settlement Mail to Accounts (Yes/No)"],
    'cust_confirmation': ["Replacement: Confirmation Pending", "Customer Confirmation"],
    'approval_mail_received': ["Replacement: OSG Approval", "Approval Mail Received From Onsitego (Yes/No)"],
}

for prop, keys in lookup_keys.items():
    found = False
    for key in keys:
        val = mapped.get(key)
        if val is not None:
            v = str(val).strip().lower()
            result = v in ("yes", "true", "1")
            print(f"  {prop}: looks up '{key}' -> found='{val}' -> bool={result}")
            found = True
            break
    if not found:
        print(f"  {prop}: NONE OF THESE KEYS FOUND IN DATA! keys tried: {keys}")

conn.close()
