"""
Restore the 3 workflow steps for CLM-1782380107 that were wiped by Google Sheets sync.
Based on the user's screenshot showing steps 1-3 were done.
"""
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

print("Restoring workflow steps for CLM-1782380107 (MOHAMMEDYASIR P)...")
print("Steps to restore: Customer Confirmation, OSG Approval, Mail Sent To Store\n")

# Restore the 3 confirmed steps
cur.execute("""
    UPDATE claims SET
        customer_confirmation = 'Yes',
        replacement_confirmation_pending = 'Yes',
        replacement_osg_approval = 'Yes',
        approval_mail_received_from_onsitego_yes_no = 'Yes',
        replacement_mail_to_store = 'Yes',
        mail_sent_to_store_yes_no = 'Yes'
    WHERE claim_id = 'CLM-1782380107'
""")
updated = cur.rowcount
conn.commit()
print(f"Updated {updated} record(s)")

# Verify
cur.execute("""
    SELECT 
        claim_id, customer_name,
        customer_confirmation,
        replacement_osg_approval,
        replacement_mail_to_store,
        mail_sent_to_store_yes_no,
        approval_mail_received_from_onsitego_yes_no,
        status
    FROM claims WHERE claim_id = 'CLM-1782380107'
""")
row = cur.fetchone()
if row:
    print(f"\nVerification:")
    print(f"  Claim ID              : {row[0]}")
    print(f"  Customer Name         : {row[1]}")
    print(f"  Customer Confirmation : {row[2]}")
    print(f"  OSG Approval          : {row[3]}")
    print(f"  Mail to Store (old)   : {row[4]}")
    print(f"  Mail to Store (new)   : {row[5]}")
    print(f"  OSG Approval (new)    : {row[6]}")
    print(f"  Status                : {row[7]}")
    print(f"\nWorkflow restored successfully!")
    print(f"The claim will now show 3/7 completed in analytics.")
    print(f"Going forward, pg_sync.py COALESCE fix prevents future overwrites.")

cur.close()
conn.close()
