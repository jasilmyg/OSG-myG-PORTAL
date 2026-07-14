import os
from dotenv import load_dotenv
load_dotenv()
import psycopg2

conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
cur = conn.cursor()

print('=== GST INVOICE BILLED - REPLACEMENT APPROVED CLAIMS ===')

# Total replacement approved
cur.execute("SELECT COUNT(*) FROM claims WHERE LOWER(status) LIKE '%replace%'")
total_repl = cur.fetchone()[0]
print(f'\nTotal Replacement Approved claims: {total_repl}')

# Invoice Generated = Yes/YES - check both columns
cur.execute("""
    SELECT COUNT(*) FROM claims 
    WHERE LOWER(status) LIKE '%replace%'
    AND LOWER(COALESCE(replacement_invoice_generated, '')) IN ('yes', 'true', '1')
""")
inv_yes = cur.fetchone()[0]

cur.execute("""
    SELECT COUNT(*) FROM claims 
    WHERE LOWER(status) LIKE '%replace%'
    AND LOWER(COALESCE(invoice_generated_yes_no, '')) IN ('yes', 'true', '1')
""")
inv_yes2 = cur.fetchone()[0]

# Invoice = No or empty
cur.execute("""
    SELECT COUNT(*) FROM claims 
    WHERE LOWER(status) LIKE '%replace%'
    AND LOWER(COALESCE(replacement_invoice_generated, '')) NOT IN ('yes', 'true', '1')
""")
inv_no = cur.fetchone()[0]

print(f'GST Invoice Billed YES (replacement_invoice_generated): {inv_yes}')
print(f'GST Invoice Billed YES (invoice_generated_yes_no):       {inv_yes2}')
print(f'GST Invoice NOT Billed / NULL:                           {inv_no}')

# Show the NO/NULL ones — these are the ones still pending GST invoice
print('\n--- Claims where GST Invoice NOT yet billed ---')
cur.execute("""
    SELECT claim_id, customer_name, mobile_number, date,
           replacement_invoice_generated, invoice_generated_yes_no,
           replacement_settled_with_accounts, replacement_mail_to_store
    FROM claims 
    WHERE LOWER(status) LIKE '%replace%'
    AND LOWER(COALESCE(replacement_invoice_generated, '')) NOT IN ('yes', 'true', '1')
    ORDER BY date DESC
""")
rows = cur.fetchall()
print(f'Count: {len(rows)}\n')
print(f"{'CLM_ID':<20} {'CUSTOMER':<24} {'DATE':<12} {'INV_GEN':<10} {'INV_YES_NO':<12} {'SETTLED':<10} {'MAIL_STORE'}")
print('-'*100)
for r in rows:
    print(f"{r[0]:<20} {str(r[1])[:24]:<24} {str(r[3])[:10]:<12} {str(r[4]):<10} {str(r[5]):<12} {str(r[6]):<10} {str(r[7])}")

conn.close()
print('\nDone.')
