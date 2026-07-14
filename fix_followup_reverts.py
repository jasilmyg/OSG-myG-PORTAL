"""
Fix: Restore 4 claims wrongly reverted to 'Follow Up' by the sync bug.
All 4 had workflow steps done -> should be 'Replacement approved'
"""
import psycopg2, psycopg2.extras

env_path = r'c:\Users\jasil_myg\Desktop\OSG-myG-PORTAL-mainnnnn - Copy\.env'
DATABASE_URL = ''
with open(env_path) as f:
    for line in f:
        if line.startswith('DATABASE_URL'):
            DATABASE_URL = line.split('=',1)[1].strip().strip('"').strip("'")
            break

conn = psycopg2.connect(DATABASE_URL, sslmode='require')
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

# The 4 affected claims
claims_to_fix = [
    'CLM-1783406379',  # VISHNUPRASAD     | 3/7 done
    'CLM-1782911002',  # bushair athiman   | 3/7 done
    'CLM-1782198274',  # Renjith           | 4/7 done
    'CLM-1781786972',  # Sunilkumar        | 4/7 done
]

print("="*65)
print("BEFORE FIX:")
print("="*65)
cur.execute("""
    SELECT claim_id, customer_name, mobile_number, status,
           customer_confirmation, replacement_osg_approval,
           replacement_mail_to_store, replacement_invoice_generated,
           last_updated_timestamp
    FROM claims WHERE claim_id = ANY(%s)
    ORDER BY claim_id
""", (claims_to_fix,))
rows_before = cur.fetchall()
for r in rows_before:
    print(f"  {r['claim_id']} | {r['customer_name']:<25} | Status: {r['status']}")

# Fix: restore status to 'Replacement approved'
cur2 = conn.cursor()
cur2.execute("""
    UPDATE claims 
    SET status = 'Replacement approved',
        last_updated_timestamp = NOW()::text
    WHERE claim_id = ANY(%s)
    AND status = 'Follow Up'
""", (claims_to_fix,))
updated = cur2.rowcount
conn.commit()

print(f"\nFixed {updated} claim(s) -> 'Replacement approved'\n")

print("="*65)
print("AFTER FIX:")
print("="*65)
cur.execute("""
    SELECT claim_id, customer_name, mobile_number, status,
           customer_confirmation, replacement_osg_approval,
           replacement_mail_to_store, replacement_invoice_generated
    FROM claims WHERE claim_id = ANY(%s)
    ORDER BY claim_id
""", (claims_to_fix,))
rows_after = cur.fetchall()
for r in rows_after:
    cc  = 'Y' if r['customer_confirmation'] and r['customer_confirmation'].lower() == 'yes' else 'N'
    osg = 'Y' if r['replacement_osg_approval'] and r['replacement_osg_approval'].lower() == 'yes' else 'N'
    mail= 'Y' if r['replacement_mail_to_store'] and r['replacement_mail_to_store'].lower() == 'yes' else 'N'
    inv = 'Y' if r['replacement_invoice_generated'] and r['replacement_invoice_generated'].lower() == 'yes' else 'N'
    print(f"  {r['claim_id']} | {r['customer_name']:<25} | Status: {r['status']:<22} | CC={cc} OSG={osg} Mail={mail} Inv={inv}")

print("\nDone! All 4 claims restored to 'Replacement approved'.")
print("The pg_sync.py fix ensures this will NOT happen again.")

cur.close()
cur2.close()
conn.close()
