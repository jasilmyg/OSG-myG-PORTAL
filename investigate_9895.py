import os, psycopg2, psycopg2.extras

env_path = r'c:\Users\jasil_myg\Desktop\OSG-myG-PORTAL-mainnnnn - Copy\.env'
DATABASE_URL = ''
with open(env_path) as f:
    for line in f:
        if line.startswith('DATABASE_URL'):
            DATABASE_URL = line.split('=',1)[1].strip().strip('"').strip("'")
            break

conn = psycopg2.connect(DATABASE_URL, sslmode='require')

with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
    cur.execute("""
        SELECT claim_id, customer_name, mobile_number, mobile, status, 
               last_updated_timestamp, synced_at,
               customer_confirmation, replacement_confirmation_pending,
               replacement_osg_approval, approval_mail_received_from_onsitego_yes_no,
               replacement_mail_to_store, mail_sent_to_store_yes_no,
               replacement_invoice_generated, invoice_generated_yes_no,
               replacement_invoice_sent_to_osg, invoice_sent_to_onsitego_yes_no,
               replacement_settlement_mail_to_accounts, settlement_mail_to_accounts_yes_no,
               replacement_settled_with_accounts, settled_with_accounts_yes_no,
               complete, complete_yes_no,
               follow_up___notes, follow_up_notes,
               last_notified_status,
               onsitego___status
        FROM claims 
        WHERE mobile_number = '9895869979' OR mobile = '9895869979'
        ORDER BY synced_at DESC
    """)
    rows = cur.fetchall()

print(f"Found {len(rows)} claim(s) for mobile 9895869979\n")
for row in rows:
    print("="*65)
    for k, v in row.items():
        if v is not None and str(v).strip() not in ('', 'None', 'nan'):
            print(f"  {k:<50} = {repr(str(v))[:80]}")
        else:
            print(f"  {k:<50} = (null)")
    print()

conn.close()
