import os
from dotenv import load_dotenv
load_dotenv()
import psycopg2

conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
cur = conn.cursor()

print("=" * 70)
print("WATERFALL SIMULATION - What the dashboard actually counts")
print("=" * 70)

# Simulate exactly what the dashboard waterfall does
cur.execute("""
    SELECT 
        claim_id, customer_name, status,
        replacement_mail_to_store,
        replacement_invoice_generated,
        replacement_invoice_sent_to_osg,
        replacement_settled_with_accounts,
        replacement_settlement_mail_to_accounts
    FROM claims
    WHERE LOWER(status) LIKE '%replace%'
""")
rows = cur.fetchall()

def is_true(val):
    if val is None: return False
    return str(val).strip().lower() in ('yes', 'true', '1')

settled = 0
settlement_mail = 0
pending_osg = 0
gst_invoice = 0
mail_to_store = 0

for r in rows:
    _, _, _, mail_store, inv_gen, inv_osg, settled_accs, settl_mail = r
    
    if is_true(settled_accs):
        settled += 1
    elif is_true(settl_mail):
        settlement_mail += 1
    elif is_true(inv_osg):
        pending_osg += 1
    elif is_true(inv_gen):
        gst_invoice += 1
    else:
        mail_to_store += 1

total = settled + settlement_mail + pending_osg + gst_invoice + mail_to_store
print(f"\n  REPLACEMENT MAIL SENT TO STORE : {mail_to_store}")
print(f"  GST INVOICE BILLED             : {gst_invoice}")
print(f"  PENDING SETTLEMENT FROM OSG    : {pending_osg}")
print(f"  SETTLEMENT MAIL TO ACCOUNTS    : {settlement_mail}")
print(f"  SETTLED WITH ACCOUNTS          : {settled}")
print(f"  ─────────────────────────────────────")
print(f"  GRAND TOTAL                    : {total}")
print(f"\n  Expected from report: MAIL=30, GST=0, PENDING=0, MAIL_ACC=0, SETTLED=139, TOTAL=169")

# Now check what the report currently shows vs correct
print(f"\n[COMPARISON]:")
report_mail = 30
report_gst = 0
report_pending = 0
report_settl_mail = 0
report_settled = 139

if mail_to_store != report_mail:
    print(f"  ❌ MAIL TO STORE: report shows {report_mail}, should be {mail_to_store}")
if gst_invoice != report_gst:
    print(f"  ❌ GST INVOICE: report shows {report_gst}, should be {gst_invoice}")
if pending_osg != report_pending:
    print(f"  ❌ PENDING OSG: report shows {report_pending}, should be {pending_osg}")
if settlement_mail != report_settl_mail:
    print(f"  ❌ SETTL MAIL: report shows {report_settl_mail}, should be {settlement_mail}")
if settled != report_settled:
    print(f"  ❌ SETTLED: report shows {report_settled}, should be {settled}")

conn.close()
