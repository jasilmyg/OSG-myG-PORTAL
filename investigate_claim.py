import os, psycopg2

env_path = r'c:\Users\jasil_myg\Desktop\OSG-myG-PORTAL-mainnnnn - Copy\.env'
DATABASE_URL = ''
with open(env_path) as f:
    for line in f:
        if line.startswith('DATABASE_URL'):
            DATABASE_URL = line.split('=',1)[1].strip().strip('"').strip("'")
            break

conn = psycopg2.connect(DATABASE_URL, sslmode='require')
cur = conn.cursor()

# Fetch ALL columns for this specific claim
cur.execute("SELECT * FROM claims WHERE claim_id = 'CLM-1782380107'")
row = cur.fetchone()
col_names = [desc[0] for desc in cur.description]

print("="*65)
print("CLAIM INVESTIGATION: CLM-1782380107 (MOHAMMEDYASIR P)")
print("="*65)

if not row:
    print("CLAIM NOT FOUND IN DATABASE!")
else:
    for col, val in zip(col_names, row):
        if val is not None and str(val).strip() not in ('', 'None', 'nan'):
            print(f"  {col:<45} = {repr(str(val))[:80]}")
        else:
            print(f"  {col:<45} = (empty/null)")

print("\n" + "="*65)
print("REPLACEMENT WORKFLOW COLUMNS SPECIFICALLY:")
print("="*65)
workflow_cols = [
    'customer_confirmation',
    'replacement_osg_approval',
    'replacement_confirmation_pending',
    'replacement_osg_approval',
    'replacement_mail_to_store',
    'replacement_invoice_generated',
    'replacement_invoice_sent_to_osg',
    'replacement_settled_with_accounts',
    'replacement_settlement_mail_to_accounts',
    'approval_mail_received_from_onsitego_yes_no',
    'mail_sent_to_store_yes_no',
    'invoice_generated_yes_no',
    'invoice_sent_to_onsitego_yes_no',
    'settlement_mail_to_accounts_yes_no',
    'settled_with_accounts_yes_no',
    'complete_yes_no',
    'complete',
    'status',
    'substatus_workflow',
    'substatus___workflow',
    'last_notified_status',
]
if row:
    for col in workflow_cols:
        if col in col_names:
            idx = col_names.index(col)
            val = row[idx]
            print(f"  {col:<50} = {repr(str(val))}")

cur.close()
conn.close()
