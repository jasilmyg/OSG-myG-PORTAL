import os
from dotenv import load_dotenv
load_dotenv()
import psycopg2
import psycopg2.extras

conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
cur = conn.cursor()

print("=" * 70)
print("REPLACEMENT WORKFLOW - DETAILED INVESTIGATION")
print("=" * 70)

# 1. What are ALL distinct replacement-related statuses?
cur.execute("""
    SELECT status, COUNT(*) 
    FROM claims 
    WHERE LOWER(status) LIKE '%replace%'
    GROUP BY status ORDER BY COUNT(*) DESC
""")
rows = cur.fetchall()
print("\n[1] ALL REPLACEMENT STATUSES:")
for r in rows:
    print(f"  '{r[0]}': {r[1]}")

# 2. Check what columns exist for replacement workflow
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='claims' AND column_name LIKE '%replace%' OR column_name LIKE '%invoice%' OR column_name LIKE '%settl%' ORDER BY column_name;")
cols = [r[0] for r in cur.fetchall()]
print(f"\n[2] REPLACEMENT-RELATED COLUMNS IN DB:")
for c in cols:
    print(f"  {c}")

# 3. Check the actual data in those workflow columns
print("\n[3] WORKFLOW COLUMN DATA COUNTS (for replacement claims):")
workflow_cols = [
    ('customer_confirmation', 'Customer Confirmation'),
    ('replacement_confirmation_pending', 'Replacement: Confirmation Pending'),
    ('replacement_osg_approval', 'Replacement: OSG Approval'),
    ('replacement_mail_to_store', 'Replacement: Mail to Store'),
    ('replacement_invoice_generated', 'Replacement: Invoice Generated'),
    ('invoice_generated_yes_no', 'Invoice Generated (Yes/No)'),
    ('replacement_invoice_sent_to_osg', 'Replacement: Invoice Sent to OSG'),
    ('replacement_settled_with_accounts', 'Replacement: Settled with Accounts'),
    ('settled_with_accounts_yes_no', 'Settled With Accounts (Yes/No)'),
    ('replacement_settlement_mail_to_accounts', 'Replacement: Settlement Mail to Accounts'),
    ('settlement_mail_to_accountsyes_no', 'Settlement Mail to Accounts(Yes/No)'),
]

for col, label in workflow_cols:
    try:
        cur.execute(f"SELECT COUNT(*) FROM claims WHERE LOWER(status) LIKE '%replace%' AND {col} IS NOT NULL AND TRIM({col}) != '' AND LOWER({col}) NOT IN ('false', 'none', 'nan', '0')")
        has_data = cur.fetchone()[0]
        cur.execute(f"SELECT DISTINCT {col} FROM claims WHERE LOWER(status) LIKE '%replace%' AND {col} IS NOT NULL AND TRIM({col}) != '' LIMIT 5")
        vals = [r[0] for r in cur.fetchall()]
        print(f"  {col}: {has_data} records with data | sample values: {vals}")
    except Exception as e:
        print(f"  {col}: [column not found or error: {e}]")

# 4. Check settled_with_accounts specifically - why is it 139?
print("\n[4] 'SETTLED WITH ACCOUNTS' BREAKDOWN:")
for col in ['replacement_settled_with_accounts', 'settled_with_accounts_yes_no']:
    try:
        cur.execute(f"SELECT {col}, COUNT(*) FROM claims WHERE LOWER(status) LIKE '%replace%' GROUP BY {col} ORDER BY 2 DESC")
        rows = cur.fetchall()
        print(f"  Column '{col}':")
        for r in rows:
            print(f"    '{r[0]}': {r[1]}")
    except Exception as e:
        print(f"  Column '{col}': [not found: {e}]")

# 5. Check invoice_generated specifically - why is it 0?
print("\n[5] 'INVOICE GENERATED / GST BILLED' BREAKDOWN:")
for col in ['replacement_invoice_generated', 'invoice_generated_yes_no']:
    try:
        cur.execute(f"SELECT {col}, COUNT(*) FROM claims WHERE LOWER(status) LIKE '%replace%' GROUP BY {col} ORDER BY 2 DESC")
        rows = cur.fetchall()
        print(f"  Column '{col}':")
        for r in rows:
            print(f"    '{r[0]}': {r[1]}")
    except Exception as e:
        print(f"  Column '{col}': [not found: {e}]")

# 6. Check mail_to_store - shows 30 in report
print("\n[6] 'MAIL TO STORE' BREAKDOWN (report shows 30):")
for col in ['replacement_mail_to_store', 'mail_sent_to_store_yes_no']:
    try:
        cur.execute(f"SELECT {col}, COUNT(*) FROM claims WHERE LOWER(status) LIKE '%replace%' GROUP BY {col} ORDER BY 2 DESC")
        rows = cur.fetchall()
        print(f"  Column '{col}':")
        for r in rows:
            print(f"    '{r[0]}': {r[1]}")
    except Exception as e:
        print(f"  Column '{col}': [not found: {e}]")

# 7. Sample 5 replacement claims with all their workflow data
print("\n[7] SAMPLE 5 REPLACEMENT CLAIMS (raw workflow data):")
cur.execute("""
    SELECT claim_id, customer_name, status,
           replacement_confirmation_pending,
           replacement_osg_approval,
           replacement_mail_to_store,
           replacement_invoice_generated,
           replacement_invoice_sent_to_osg,
           replacement_settled_with_accounts,
           replacement_settlement_mail_to_accounts
    FROM claims
    WHERE LOWER(status) LIKE '%replace%'
    LIMIT 5
""")
rows = cur.fetchall()
cols_display = ['claim_id','customer','status','confirm','osg_appr','mail_store','inv_gen','inv_osg','settled','settl_mail']
for r in rows:
    print(f"\n  {r[0]} | {str(r[1])[:20]} | {r[2]}")
    for i, c in enumerate(cols_display[3:], 3):
        print(f"    {c}: '{r[i]}'")

conn.close()
print("\nDone.")
