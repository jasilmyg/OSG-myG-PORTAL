import os, psycopg2, psycopg2.extras, time
from dotenv import load_dotenv
load_dotenv()

conn = psycopg2.connect(os.getenv('DATABASE_URL'))

try:
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        # Fetch full existing claim
        cur.execute("SELECT * FROM claims WHERE claim_id = 'CLM-1782382237'")
        existing = dict(cur.fetchone())
        print("=== EXISTING CLAIM (before changes) ===")
        print(f"  claim_id : {existing['claim_id']}")
        print(f"  date     : {existing['date']}")
        print(f"  status   : {existing['status']}")
        print(f"  osid     : {existing.get('osid')}")
        print(f"  sr_no    : {existing['sr_no']}")

        # STEP 1: Update existing claim to Cancelled with OSID 3F23000018525470
        cur.execute("""
            UPDATE claims
            SET status = 'Cancelled',
                osid   = '3F23000018525470',
                synced_at = NOW()
            WHERE claim_id = 'CLM-1782382237'
        """)
        print("\n[OK] STEP 1: Updated CLM-1782382237 -> status=Cancelled, osid=3F23000018525470")

        # STEP 2: Create NEW claim for replacement case (2026-07-03)
        new_claim_id = f"CLM-{int(time.time())}"

        # Get invoice/serial from osid_data for the active OSID
        cur.execute("SELECT invoice_no, serial_no FROM osid_data WHERE osid = '3F23000018525469' LIMIT 1")
        osid_row = cur.fetchone()
        new_invoice = osid_row['invoice_no'] if osid_row else existing.get('invoice_number', '')
        new_serial  = osid_row['serial_no']  if osid_row else existing.get('serial_number', '')

        cur.execute("""
            INSERT INTO claims (
                claim_id, date, customer_name, mobile_number, address,
                product, invoice_number, serial_number, model,
                osid, issue, branch, status,
                follow_up___notes,
                approval_mail_received_from_onsitego_yes_no,
                mail_sent_to_store_yes_no,
                invoice_generated_yes_no,
                invoice_sent_to_onsitego_yes_no,
                customer_confirmation,
                settled_with_accounts_yes_no,
                settlement_mail_to_accounts_yes_no,
                claim_settled_date,
                approval_mail_received_date,
                mail_sent_to_store_date,
                synced_at
            ) VALUES (
                %s, '2026-07-03', %s, %s, %s,
                %s, %s, %s, %s,
                '3F23000018525469', %s, %s, 'Replacement approved',
                %s,
                %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s,
                NOW()
            )
        """, (
            new_claim_id,
            existing['customer_name'],
            existing['mobile_number'],
            existing['address'],
            existing['product'],
            new_invoice,
            new_serial,
            existing['model'],
            existing['issue'],
            existing['branch'],
            existing.get('follow_up___notes', ''),
            existing.get('approval_mail_received_from_onsitego_yes_no'),
            existing.get('mail_sent_to_store_yes_no'),
            existing.get('invoice_generated_yes_no'),
            existing.get('invoice_sent_to_onsitego_yes_no'),
            existing.get('customer_confirmation'),
            existing.get('settled_with_accounts_yes_no'),
            existing.get('settlement_mail_to_accounts_yes_no'),
            existing.get('claim_settled_date'),
            existing.get('approval_mail_received_date'),
            existing.get('mail_sent_to_store_date'),
        ))
        print(f"\n[OK] STEP 2: Created NEW claim {new_claim_id} -> date=2026-07-03, status=Replacement approved, osid=3F23000018525469")
        print(f"             invoice={new_invoice}, serial={new_serial}")

    conn.commit()
    print("\n[SUCCESS] ALL CHANGES COMMITTED")

except Exception as e:
    conn.rollback()
    print(f"\n[ERROR] {e}")
    import traceback; traceback.print_exc()
finally:
    conn.close()
