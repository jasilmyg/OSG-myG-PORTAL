import os, psycopg2, psycopg2.extras, sys

env_path = r'c:\Users\jasil_myg\Desktop\OSG-myG-PORTAL-mainnnnn - Copy\.env'
DATABASE_URL = ''
with open(env_path) as f:
    for line in f:
        if line.startswith('DATABASE_URL'):
            DATABASE_URL = line.split('=',1)[1].strip().strip('"').strip("'")
            break

sys.path.insert(0, r"c:\Users\jasil_myg\Desktop\OSG-myG-PORTAL-mainnnnn - Copy")

conn = psycopg2.connect(DATABASE_URL, sslmode='require')

with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
    cur.execute("SELECT * FROM claims WHERE mobile_number = '9895869979' OR mobile = '9895869979'")
    row = dict(cur.fetchone())

conn.close()

# Simulate the COL_MAP reverse mapping (same as pg_sync.py does)
def _pg_col(name):
    clean = name.strip().lower()
    return (clean.replace(" ","_").replace("-","_").replace("(","").replace(")","")
            .replace("/","_").replace(":","").replace(".","").replace(",","")
            .replace("'","").replace("?","").replace("!","").strip("_"))

SHEET_COLUMNS = [
    "Customer Confirmation","Approval Mail Received From Onsitego (Yes/No)",
    "Mail Sent To Store (Yes/No)","Invoice Generated (Yes/No)",
    "Invoice Sent To Onsitego (Yes/No)","Settlement Mail to Accounts(Yes/No)",
    "Settlement Mail to Accounts Date","Settled With Accounts (Yes/No)","Complete (Yes/No)",
    "Replacement: Confirmation Pending","Replacement: OSG Approval",
    "Replacement: Mail to Store","Replacement: Invoice Generated",
    "Replacement: Invoice Sent to OSG","Replacement: Settled with Accounts",
    "Replacement: Settlement Mail to Accounts",
]
COL_MAP = {col: _pg_col(col) for col in SHEET_COLUMNS}
reverse_map = {v: k for k, v in COL_MAP.items()}

# Build claim.data (same as fetch_claims_from_postgres does)
claim_data = {}
for pg_col, val in row.items():
    sheet_key = reverse_map.get(pg_col, pg_col)
    claim_data[sheet_key] = val

print("="*65)
print("CLAIM: CLM-1781257656 | AZCCO GLOBAL | 9895869979")
print("="*65)
print(f"\nCurrent Status in DB: {repr(row.get('status'))}")
print(f"Last Updated:         {row.get('last_updated_timestamp')}")
print(f"Synced At (UTC):      {row.get('synced_at')}")
print(f"Onsitego Status:      {repr(row.get('onsitego___status'))}")

print("\n--- WORKFLOW COLUMNS (both old & new) ---")
print(f"  customer_confirmation                     = {repr(row.get('customer_confirmation'))}")
print(f"  replacement_confirmation_pending          = {repr(row.get('replacement_confirmation_pending'))}")
print(f"  replacement_osg_approval                 = {repr(row.get('replacement_osg_approval'))}")
print(f"  approval_mail_received_from_onsitego_y_n = {repr(row.get('approval_mail_received_from_onsitego_yes_no'))}")
print(f"  replacement_mail_to_store                = {repr(row.get('replacement_mail_to_store'))}")
print(f"  mail_sent_to_store_yes_no                = {repr(row.get('mail_sent_to_store_yes_no'))}")
print(f"  replacement_invoice_generated            = {repr(row.get('replacement_invoice_generated'))}")
print(f"  invoice_generated_yes_no                 = {repr(row.get('invoice_generated_yes_no'))}")
print(f"  replacement_invoice_sent_to_osg          = {repr(row.get('replacement_invoice_sent_to_osg'))}")
print(f"  invoice_sent_to_onsitego_yes_no          = {repr(row.get('invoice_sent_to_onsitego_yes_no'))}")
print(f"  replacement_settlement_mail_to_accounts  = {repr(row.get('replacement_settlement_mail_to_accounts'))}")
print(f"  settlement_mail_to_accounts_yes_no       = {repr(row.get('settlement_mail_to_accounts_yes_no'))}")  # <-- MISMATCH?
print(f"  replacement_settled_with_accounts        = {repr(row.get('replacement_settled_with_accounts'))}")
print(f"  settled_with_accounts_yes_no             = {repr(row.get('settled_with_accounts_yes_no'))}")
print(f"  complete                                 = {repr(row.get('complete'))}")
print(f"  complete_yes_no                          = {repr(row.get('complete_yes_no'))}")

print("\n--- FOLLOW UP NOTES (timeline) ---")
notes = str(row.get('follow_up___notes') or row.get('follow_up_notes') or '')
print(notes[:2000])

print("\n--- WHAT TRIGGERED THE REVERT TO FOLLOW UP ---")
print()

# Simulate what the sync would have seen BEFORE today's re-fix
# The notes contain: "[09/07/2026, 09:35:57 am] [REMARK]: Field Executive Pickup Pending"
# This means on July 9, a NEW REMARK was detected → appended = True
# At that time, the Onsitego status was 'Approved for replacement'
# And the SHEET status was likely 'Registered' (old bug)

print("Trigger: New REMARK detected in Google Sheet on July 9:")
print("         'Field Executive Pickup Pending'")
print("         → appended = True")
print()
print("OLD BUGGY LOGIC:")
print("  1. current_incoming_status (from Sheet) = 'Registered'")
print("  2. 'registered' NOT in TERMINAL_STATUSES → True")
print("  3. claim_data['Status'] = 'Follow Up'  ← FORCED!")
print("  4. sheet_status read AFTER mutation = 'Follow Up'")
print("  5. 'follow up' NOT in DOWNGRADE_STATUSES → protection skipped")
print("  6. RESULT: Status reverted to 'Follow Up' silently")
print()
print("NEW FIXED LOGIC (in place now):")
print("  1. original_sheet_status captured BEFORE any change = 'Registered'")
print("  2. old_db_status = 'Replacement approved' → IS in PROTECTED_STATUSES")
print("  3. Rule 1 fires → claim_data['Status'] = 'Replacement approved' (kept)")
print("  4. RESULT: Status PROTECTED, only the note gets saved")
print()

# Check if settlement_mail mismatch
s_old = row.get('replacement_settlement_mail_to_accounts')
s_new = row.get('settlement_mail_to_accounts_yes_no')
if s_old != s_new:
    print(f"⚠️  SCHEMA SPLIT MISMATCH DETECTED!")
    print(f"   replacement_settlement_mail_to_accounts = {repr(s_old)} (old col)")
    print(f"   settlement_mail_to_accounts_yes_no      = {repr(s_new)} (new col)")
    print(f"   → Analytics reads: settlement_mail_accounts = {bool(s_new and s_new.lower() in ['yes','true','1'])}")
    print(f"   → ClaimWrapper reads: True (via fuzzy fallback on old col)")
    print(f"   → FIX NEEDED: align both columns")
