"""
Investigate: Find ALL claims in DB that may have been wrongly reverted to 'Follow Up'
by the sync bug. Look for claims where:
1. Status = 'Follow Up' BUT workflow steps are partially/fully done
2. Notes contain auto-appended [REMARK] or [ONSITEGO STATUS] entries (sign the bug triggered)
3. Status = 'Follow Up' but complete_yes_no = 'Yes' (impossible if genuinely Follow Up)
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

with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
    cur.execute("SELECT * FROM claims ORDER BY synced_at DESC")
    rows = [dict(r) for r in cur.fetchall()]

conn.close()

print(f"Total claims in DB: {len(rows)}\n")

def is_yes(val):
    return str(val or '').strip().lower() in ('yes','true','1','y')

issues = []

for row in rows:
    claim_id = row.get('claim_id','')
    customer = row.get('customer_name','')
    mobile = row.get('mobile_number','') or row.get('mobile','')
    status = str(row.get('status') or '').strip()
    notes = str(row.get('follow_up___notes') or row.get('follow_up_notes') or '')
    complete_yn = row.get('complete_yes_no','')
    complete = row.get('complete','')

    # Workflow steps (check both old and new columns)
    cust_conf = is_yes(row.get('customer_confirmation')) or is_yes(row.get('replacement_confirmation_pending'))
    osg_appr  = is_yes(row.get('approval_mail_received_from_onsitego_yes_no')) or is_yes(row.get('replacement_osg_approval'))
    mail_store= is_yes(row.get('mail_sent_to_store_yes_no')) or is_yes(row.get('replacement_mail_to_store'))
    inv_gen   = is_yes(row.get('invoice_generated_yes_no')) or is_yes(row.get('replacement_invoice_generated'))
    inv_sent  = is_yes(row.get('invoice_sent_to_onsitego_yes_no')) or is_yes(row.get('replacement_invoice_sent_to_osg'))
    settle_ml = is_yes(row.get('settlement_mail_to_accounts_yes_no')) or is_yes(row.get('replacement_settlement_mail_to_accounts'))
    settled   = is_yes(row.get('settled_with_accounts_yes_no')) or is_yes(row.get('replacement_settled_with_accounts'))
    
    steps_done = sum([cust_conf, osg_appr, mail_store, inv_gen, inv_sent, settle_ml, settled])
    has_auto_note = '[REMARK]' in notes or '[ONSITEGO STATUS]' in notes

    # CASE 1: Status is Follow Up but has workflow steps done
    if status.lower() == 'follow up' and steps_done > 0:
        issues.append({
            'type': 'WRONG_FOLLOW_UP_WITH_WORKFLOW',
            'claim_id': claim_id,
            'customer': customer,
            'mobile': mobile,
            'status': status,
            'steps_done': steps_done,
            'workflow': f'CC={cust_conf} OSG={osg_appr} Mail={mail_store} Inv={inv_gen} ISent={inv_sent} SetMail={settle_ml} Settled={settled}',
            'has_auto_note': has_auto_note,
            'notes_snippet': notes[:120].replace('\n',' ')
        })

    # CASE 2: Status is Follow Up but complete_yes_no = Yes (contradictory)
    elif status.lower() == 'follow up' and (is_yes(complete_yn) or is_yes(complete)):
        issues.append({
            'type': 'FOLLOW_UP_BUT_COMPLETE',
            'claim_id': claim_id,
            'customer': customer,
            'mobile': mobile,
            'status': status,
            'steps_done': steps_done,
            'workflow': f'CC={cust_conf} OSG={osg_appr} Mail={mail_store} Inv={inv_gen}',
            'has_auto_note': has_auto_note,
            'notes_snippet': notes[:120].replace('\n',' ')
        })

    # CASE 3: Replacement Approved / Repair Completed but notes have auto-appended entries
    # These MAY have been reverted and re-set by the user
    elif status.lower() in ('replacement approved', 'repair completed', 'rejected') and has_auto_note:
        issues.append({
            'type': 'PROTECTED_WITH_AUTO_NOTE (was likely reverted, now restored)',
            'claim_id': claim_id,
            'customer': customer,
            'mobile': mobile,
            'status': status,
            'steps_done': steps_done,
            'workflow': f'CC={cust_conf} OSG={osg_appr} Mail={mail_store} Inv={inv_gen}',
            'has_auto_note': has_auto_note,
            'notes_snippet': notes[:120].replace('\n',' ')
        })

print(f"ISSUES FOUND: {len(issues)}\n")
print("="*70)

# Group by type
from collections import defaultdict
by_type = defaultdict(list)
for i in issues:
    by_type[i['type']].append(i)

for issue_type, records in by_type.items():
    print(f"\n{'='*70}")
    print(f"TYPE: {issue_type}")
    print(f"COUNT: {len(records)}")
    print(f"{'='*70}")
    for r in records:
        print(f"  {r['claim_id']:<20} | {r['customer']:<25} | {r['mobile']:<12} | Status: {r['status']}")
        print(f"  Steps Done: {r['steps_done']}/7 | {r['workflow']}")
        print(f"  Auto-Note: {r['has_auto_note']} | Notes: {r['notes_snippet'][:80]}")
        print()

# Summary
print("="*70)
print("SUMMARY:")
print(f"  WRONG_FOLLOW_UP_WITH_WORKFLOW (incorrectly stuck as Follow Up):   {len(by_type['WRONG_FOLLOW_UP_WITH_WORKFLOW'])}")
print(f"  FOLLOW_UP_BUT_COMPLETE (contradictory state):                     {len(by_type['FOLLOW_UP_BUT_COMPLETE'])}")
print(f"  PROTECTED_WITH_AUTO_NOTE (had auto-note, may have reverted+fixed): {len(by_type['PROTECTED_WITH_AUTO_NOTE (was likely reverted, now restored)'])}")
