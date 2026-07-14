import os, psycopg2
from collections import defaultdict

env_path = r'c:\Users\jasil_myg\Desktop\OSG-myG-PORTAL-mainnnnn - Copy\.env'
DATABASE_URL = ''
with open(env_path) as f:
    for line in f:
        if line.startswith('DATABASE_URL'):
            DATABASE_URL = line.split('=',1)[1].strip().strip('"').strip("'")
            break

conn = psycopg2.connect(DATABASE_URL, sslmode='require')
cur = conn.cursor()
issues = []
warnings = []

print("="*65)
print("OSG PORTAL - FULL DATA INVESTIGATION REPORT")
print("="*65)

# 1. Total
cur.execute("SELECT COUNT(*) FROM claims")
total = cur.fetchone()[0]
print(f"\n[1] TOTAL CLAIMS IN DATABASE: {total}")

# 2. Status distribution
cur.execute("SELECT status, COUNT(*) FROM claims GROUP BY status ORDER BY COUNT(*) DESC")
rows = cur.fetchall()
print(f"\n[2] STATUS DISTRIBUTION:")
for status, cnt in rows:
    pct = round(cnt/total*100, 1)
    flag = " <<< MIXED CASE!" if status and status.upper() == status and len(status) > 4 else ""
    flag2 = " <<< EMPTY STATUS!" if status == '' or status is None else ""
    print(f"    {repr(str(status)):<40} {cnt:>5} ({pct}%){flag}{flag2}")
    if status and status.upper() == status and len(status) > 4:
        issues.append(f"MIXED CASE STATUS: '{status}' has {cnt} records - should be lowercase/title")
    if status == '' or status is None:
        issues.append(f"CRITICAL: {cnt} claims have empty/NULL status")

# 3. Exact mixed case variants
cur.execute("SELECT DISTINCT LOWER(status), COUNT(DISTINCT status) FROM claims WHERE status IS NOT NULL AND status != '' GROUP BY LOWER(status) HAVING COUNT(DISTINCT status)>1")
mixed = cur.fetchall()
print(f"\n[3] SAME STATUS DIFFERENT CASE (Data Inconsistency):")
if mixed:
    for norm, cnt in mixed:
        cur.execute("SELECT DISTINCT status FROM claims WHERE LOWER(status)=%s", (norm,))
        variants = [r[0] for r in cur.fetchall()]
        cur.execute("SELECT SUM(c) FROM (SELECT status, COUNT(*) as c FROM claims WHERE LOWER(status)=%s GROUP BY status) x", (norm,))
        total_for_status = cur.fetchone()[0]
        print(f"    '{norm}' -> variants: {variants}  (total: {total_for_status} records affected)")
        issues.append(f"MIXED CASE: '{norm}' has variants {variants}")
else:
    print("    None - CLEAN")

# 4. Duplicate column check (follow_up___dates vs follow_up_dates)
print(f"\n[4] DUPLICATE/REDUNDANT COLUMNS CHECK:")
cur.execute("SELECT COUNT(*) FROM claims WHERE follow_up___dates IS NOT NULL AND follow_up___dates != ''")
old_fu_dates = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM claims WHERE follow_up_dates IS NOT NULL AND follow_up_dates != ''")
new_fu_dates = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM claims WHERE substatus___workflow IS NOT NULL AND substatus___workflow != ''")
old_sub = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM claims WHERE substatus_workflow IS NOT NULL AND substatus_workflow != ''")
new_sub = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM claims WHERE mobile_number IS NOT NULL AND mobile_number != ''")
old_mob = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM claims WHERE mobile IS NOT NULL AND mobile != ''")
new_mob = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM claims WHERE follow_up___notes IS NOT NULL AND follow_up___notes != ''")
old_fn = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM claims WHERE follow_up_notes IS NOT NULL AND follow_up_notes != ''")
new_fn = cur.fetchone()[0]

print(f"    follow_up___dates  (old col): {old_fu_dates} records have data")
print(f"    follow_up_dates    (new col): {new_fu_dates} records have data")
print(f"    follow_up___notes  (old col): {old_fn} records have data")
print(f"    follow_up_notes    (new col): {new_fn} records have data")
print(f"    substatus___workflow (old)  : {old_sub} records have data")
print(f"    substatus_workflow   (new)  : {new_sub} records have data")
print(f"    mobile_number (old col)     : {old_mob} records have data")
print(f"    mobile        (new col)     : {new_mob} records have data")
if old_fu_dates > 0 and new_fu_dates > 0:
    issues.append(f"SCHEMA SPLIT: Both follow_up___dates ({old_fu_dates}) and follow_up_dates ({new_fu_dates}) have data - data split across 2 columns!")
if old_mob > 0 and new_mob > 0:
    issues.append(f"SCHEMA SPLIT: Both mobile_number ({old_mob}) and mobile ({new_mob}) have data - split mobile data!")

# 5. Specific mobiles from June investigation
print(f"\n[5] JUNE INVESTIGATION - MISSING CLAIMS CHECK:")
for mob in ['9061319169', '8113856077', '7012899934']:
    cur.execute("SELECT claim_id, customer_name, mobile_number, date, status FROM claims WHERE mobile_number=%s OR mobile=%s", (mob, mob))
    rows = cur.fetchall()
    if rows:
        for r in rows:
            print(f"    FOUND  {mob}: {r[0]} | {str(r[1])[:25]} | {r[3]} | {r[4]}")
    else:
        print(f"    MISSING {mob}: NOT IN DATABASE!")
        issues.append(f"MISSING CLAIM: Mobile {mob} not found in database")

# 6. Monthly claim counts
print(f"\n[6] MONTHLY CLAIM COUNTS (Apr-Jul 2026):")
cur.execute("""
    SELECT 
        SUBSTRING(date,1,7) as month,
        COUNT(*) as total,
        COUNT(CASE WHEN LOWER(status) LIKE '%replacement%' THEN 1 END) as replacement,
        COUNT(CASE WHEN LOWER(status) LIKE '%repair%' THEN 1 END) as repair,
        COUNT(CASE WHEN LOWER(status) = 'rejected' THEN 1 END) as rejected,
        COUNT(CASE WHEN LOWER(status) = 'cancelled' THEN 1 END) as cancelled
    FROM claims 
    WHERE date >= '2026-04'
    GROUP BY SUBSTRING(date,1,7)
    ORDER BY 1
""")
print(f"    {'Month':<10} {'Total':>6} {'Replace':>9} {'Repair':>8} {'Rejected':>9} {'Cancelled':>10}")
for r in cur.fetchall():
    print(f"    {str(r[0]):<10} {r[1]:>6} {r[2]:>9} {r[3]:>8} {r[4]:>9} {r[5]:>10}")

# 7. Claims with REPAIR COMPLETED but no feedback (data gap)
print(f"\n[7] 'REPAIR COMPLETED' CLAIMS MISSING FEEDBACK:")
cur.execute("""
    SELECT COUNT(*) FROM claims 
    WHERE LOWER(status) = 'repair completed'
    AND (repair_feedback_completed_yes_no IS NULL OR repair_feedback_completed_yes_no = '')
""")
no_feedback = cur.fetchone()[0]
print(f"    Repair Completed but no feedback recorded: {no_feedback}")
if no_feedback > 0:
    warnings.append(f"INFO: {no_feedback} Repair Completed claims have no feedback")

# 8. Replacement Approved with missing workflow steps
print(f"\n[8] 'REPLACEMENT APPROVED' - MISSING WORKFLOW STEPS:")
cur.execute("""
    SELECT 
        COUNT(*) as total,
        COUNT(CASE WHEN customer_confirmation IS NULL OR customer_confirmation = '' THEN 1 END) as no_cust_confirm,
        COUNT(CASE WHEN replacement_osg_approval IS NULL OR replacement_osg_approval = '' THEN 1 END) as no_osg_approval,
        COUNT(CASE WHEN replacement_mail_to_store IS NULL OR replacement_mail_to_store = '' THEN 1 END) as no_mail_store,
        COUNT(CASE WHEN replacement_invoice_generated IS NULL OR replacement_invoice_generated = '' THEN 1 END) as no_invoice,
        COUNT(CASE WHEN replacement_settled_with_accounts IS NULL OR replacement_settled_with_accounts = '' THEN 1 END) as no_settle
    FROM claims 
    WHERE LOWER(status) LIKE '%replacement approved%'
""")
r = cur.fetchone()
print(f"    Total Replacement Approved: {r[0]}")
print(f"    Missing Customer Confirmation: {r[1]}")
print(f"    Missing OSG Approval          : {r[2]}")
print(f"    Missing Mail to Store         : {r[3]}")
print(f"    Missing Invoice Generated     : {r[4]}")
print(f"    Missing Settled with Accounts : {r[5]}")
if r[5] > 50:
    warnings.append(f"INFO: {r[5]} Replacement Approved claims not settled with accounts yet")

# 9. Claims with empty/missing customer_name
print(f"\n[9] MISSING CUSTOMER NAMES:")
cur.execute("SELECT COUNT(*) FROM claims WHERE customer_name IS NULL OR customer_name = ''")
no_name = cur.fetchone()[0]
print(f"    Claims with no customer name: {no_name}")
if no_name > 0:
    cur.execute("SELECT claim_id, mobile_number, date, status FROM claims WHERE customer_name IS NULL OR customer_name = '' LIMIT 10")
    for r in cur.fetchall():
        print(f"    {r[0]} | mobile={r[1]} | {r[2]} | {r[3]}")
    issues.append(f"WARNING: {no_name} claims have no customer name")

# 10. Claims with suspicious date values
print(f"\n[10] DATE FORMAT ISSUES:")
cur.execute("""
    SELECT COUNT(*) FROM claims 
    WHERE date IS NOT NULL 
    AND date != ''
    AND date !~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}'
""")
bad_date = cur.fetchone()[0]
print(f"    Claims with non-standard date format: {bad_date}")
if bad_date > 0:
    cur.execute("""
        SELECT claim_id, date, customer_name FROM claims 
        WHERE date IS NOT NULL AND date != '' AND date !~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}'
        LIMIT 10
    """)
    for r in cur.fetchall():
        print(f"    {r[0]} | date='{r[1]}' | {r[2]}")
    issues.append(f"FORMAT: {bad_date} claims have non-standard date format")

# 11. Duplicate claim IDs
print(f"\n[11] DUPLICATE CLAIM IDs:")
cur.execute("SELECT claim_id, COUNT(*) FROM claims GROUP BY claim_id HAVING COUNT(*)>1 ORDER BY 2 DESC LIMIT 10")
dupes = cur.fetchall()
if dupes:
    for r in dupes:
        print(f"    claim_id '{r[0]}' appears {r[1]} times!")
        issues.append(f"DUPLICATE: claim_id '{r[0]}' appears {r[1]} times")
else:
    print("    None - CLEAN")

# 12. onsitego___status column - check for data
print(f"\n[12] ONSITEGO STATUS COLUMN:")
cur.execute("SELECT COUNT(*) FROM claims WHERE onsitego___status IS NOT NULL AND onsitego___status != ''")
onsitego_count = cur.fetchone()[0]
cur.execute("SELECT DISTINCT onsitego___status, COUNT(*) FROM claims WHERE onsitego___status IS NOT NULL AND onsitego___status != '' GROUP BY onsitego___status ORDER BY 2 DESC LIMIT 10")
onsitego_rows = cur.fetchall()
print(f"    Claims with Onsitego status data: {onsitego_count}")
for r in onsitego_rows:
    print(f"    '{r[0]}': {r[1]} claims")

# 13. last_notified_status inconsistency
print(f"\n[13] LAST_NOTIFIED_STATUS vs CURRENT STATUS MISMATCH:")
cur.execute("""
    SELECT COUNT(*) FROM claims
    WHERE last_notified_status IS NOT NULL
    AND last_notified_status != ''
    AND LOWER(last_notified_status) != LOWER(status)
""")
mismatch = cur.fetchone()[0]
print(f"    Claims where last_notified != current status: {mismatch}")
if mismatch > 0:
    cur.execute("""
        SELECT claim_id, customer_name, status, last_notified_status, date
        FROM claims
        WHERE last_notified_status IS NOT NULL
        AND last_notified_status != ''
        AND LOWER(last_notified_status) != LOWER(status)
        ORDER BY date DESC
        LIMIT 15
    """)
    for r in cur.fetchall():
        print(f"    {r[0]} | {str(r[1])[:22]:<22} | Status='{r[2]}' | LastNotified='{r[3]}' | {r[4]}")
    warnings.append(f"INFO: {mismatch} claims have different last_notified vs current status (normal if status changed)")

# 14. Claims with no branch
print(f"\n[14] CLAIMS WITH MISSING BRANCH:")
cur.execute("SELECT COUNT(*) FROM claims WHERE branch IS NULL OR branch = ''")
no_branch = cur.fetchone()[0]
print(f"    Claims with no branch: {no_branch}")
if no_branch > 5:
    warnings.append(f"WARNING: {no_branch} claims have no branch assigned")

# 15. Overall health score
print(f"\n{'='*65}")
print(f"FINAL INVESTIGATION SUMMARY")
print(f"{'='*65}")
print(f"\nTotal Claims Investigated: {total}")
print(f"\nCRITICAL ISSUES ({len([i for i in issues if 'CRITICAL' in i or 'MIXED CASE' in i or 'MISSING' in i or 'SCHEMA' in i])}):")
for i in issues:
    print(f"  => {i}")
print(f"\nWARNINGS ({len(warnings)}):")
for w in warnings:
    print(f"  => {w}")
if not issues:
    print("  No critical issues!")
if not warnings:
    print("  No warnings!")

cur.close()
conn.close()
print("\nInvestigation Complete.")
