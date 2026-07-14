"""
Final investigation: Trace EXACTLY what claim.data contains for CLM-1782380107
and simulate how ClaimWrapper evaluates each workflow property.
"""
import os, sys, psycopg2, psycopg2.extras
sys.path.insert(0, r"c:\Users\jasil_myg\Desktop\OSG-myG-PORTAL-mainnnnn - Copy")

env_path = r'c:\Users\jasil_myg\Desktop\OSG-myG-PORTAL-mainnnnn - Copy\.env'
DATABASE_URL = ''
with open(env_path) as f:
    for line in f:
        if line.startswith('DATABASE_URL'):
            DATABASE_URL = line.split('=',1)[1].strip().strip('"').strip("'")
            break

# Simulate pg_sync COL_MAP reverse mapping
def _pg_col(name):
    clean = name.strip().lower()
    return (clean.replace(" ","_").replace("-","_").replace("(","").replace(")","")
            .replace("/","_").replace(":","").replace(".","").replace(",","")
            .replace("'","").replace("?","").replace("!","").strip("_"))

SHEET_COLUMNS = [
    "Claim ID","Customer Name","Mobile Number","Address","Product","Invoice Number",
    "Serial Number","SR No","Model","OSID","Issue","Branch","Follow Up - Dates",
    "Follow Up - Notes","Claim Settled Date","Remarks","Status",
    "Replacement: Confirmation Pending","Replacement: OSG Approval",
    "Replacement: Mail to Store","Replacement: Invoice Generated",
    "Replacement: Invoice Sent to OSG","Replacement: Settled with Accounts",
    "Replacement: Settlement Mail to Accounts","Approval Mail Received Date",
    "Mail Sent To Store Date","Invoice Generated Date","Invoice Sent To Onsitego Date",
    "Complete","Settled Time (TAT)","Assigned Staff","Feedback Rating",
    "Repair Feedback Completed (Yes/No)","Settlement Mail to Accounts(Yes/No)",
    "Last Updated Timestamp","Last_Notified_Status",
    "Customer Confirmation","Approval Mail Received From Onsitego (Yes/No)",
    "Mail Sent To Store (Yes/No)","Invoice Generated (Yes/No)",
    "Invoice Sent To Onsitego (Yes/No)","Settlement Mail to Accounts(Yes/No)",
    "Settlement Mail to Accounts Date","Settled With Accounts (Yes/No)","Complete (Yes/No)",
]
COL_MAP = {col: _pg_col(col) for col in SHEET_COLUMNS}
reverse_map = {v: k for k, v in COL_MAP.items()}
reverse_map["claim_id"] = "Claim ID"

conn = psycopg2.connect(DATABASE_URL, sslmode='require')
conn.cursor_factory = psycopg2.extras.RealDictCursor

with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
    cur.execute("SELECT * FROM claims WHERE claim_id = 'CLM-1782380107'")
    row = cur.fetchone()

conn.close()

if not row:
    print("Claim not found!")
    exit()

# Build claim.data the same way pg_sync does
claim_data = {}
for pg_col, val in row.items():
    sheet_key = reverse_map.get(pg_col, pg_col)
    claim_data[sheet_key] = val

print("="*65)
print("SIMULATED claim.data for CLM-1782380107")
print("(Only workflow-related keys shown)")
print("="*65)

workflow_keys = [
    "Replacement: Confirmation Pending",
    "Customer Confirmation",
    "Replacement: OSG Approval",
    "Approval Mail Received From Onsitego (Yes/No)",
    "Replacement: Mail to Store",
    "Mail Sent To Store (Yes/No)",
    "Mail Sent To Store Date",
    "Replacement: Invoice Generated",
    "Invoice Generated (Yes/No)",
    "Replacement: Invoice Sent to OSG",
    "Invoice Sent To Onsitego (Yes/No)",
    "Settlement Mail to Accounts(Yes/No)",
    "Replacement: Settlement Mail to Accounts",
    "Settled With Accounts (Yes/No)",
    "Replacement: Settled with Accounts",
    "Complete","Complete (Yes/No)",
    "Status",
]

for key in workflow_keys:
    val = claim_data.get(key)
    print(f"  {key:<55} = {repr(val)}")

# Now simulate the _bool method
def _bool(data, key):
    val = data.get(key)
    if val is None: return False
    return str(val).strip().lower() in ("yes","true","1","y","checked","on")

# Simulate each property
print("\n" + "="*65)
print("SIMULATED ClaimWrapper PROPERTY EVALUATION:")
print("="*65)

cust_conf = _bool(claim_data,"Replacement: Confirmation Pending") or _bool(claim_data,"Customer Confirmation")
print(f"  cust_confirmation_pending  = {cust_conf}")

osg_approval = _bool(claim_data,"Replacement: OSG Approval") or _bool(claim_data,"Approval Mail Received From Onsitego (Yes/No)")
print(f"  approval_mail_received     = {osg_approval}")

# mail_sent_to_store with fuzzy fallback
mail_store = False
for key in ["Replacement: Mail to Store","Mail Sent To Store (Yes/No)"]:
    if _bool(claim_data, key):
        mail_store = True
        break
if not mail_store:
    for k, v in claim_data.items():
        if isinstance(k,str) and "mail" in k.lower() and "store" in k.lower():
            if str(v or '').strip().lower() in ("yes","true","1"):
                mail_store = True
                print(f"  mail_sent_to_store FUZZY MATCH on key: '{k}' = {repr(v)}")
                break
print(f"  mail_sent_to_store         = {mail_store}")

inv_gen = _bool(claim_data,"Replacement: Invoice Generated") or _bool(claim_data,"Invoice Generated (Yes/No)")
print(f"  invoice_generated          = {inv_gen}")

# Now simulate analytics-data mapping
print("\n" + "="*65)
print("SIMULATED /api/analytics-data MAPPING (what analytics reads):")
print("="*65)

def parse_bool(val):
    if val is None or val == '': return False
    return str(val).strip().lower() in ['yes','true','1']

repl_conf_analytics = parse_bool(claim_data.get("Customer Confirmation") or claim_data.get("customer_confirmation"))
osg_analytics = parse_bool(claim_data.get("Approval Mail Received From Onsitego (Yes/No)") or claim_data.get("approval_mail_received_from_onsitego_yes_no"))
mail_analytics = parse_bool(claim_data.get("Mail Sent To Store (Yes/No)") or claim_data.get("mail_sent_to_store_yes_no"))

print(f"  replacement_confirmation    = {repl_conf_analytics}")
print(f"  replacement_osg_approval   = {osg_analytics}")
print(f"  replacement_mail_store     = {mail_analytics}")

print("\n" + "="*65)
print("ROOT CAUSE SUMMARY:")
print("="*65)

if cust_conf != repl_conf_analytics:
    print(f"  MISMATCH FOUND!")
    print(f"  Dashboard (ClaimWrapper.cust_confirmation_pending) = {cust_conf}")
    print(f"  Analytics (/api/analytics-data replacement_confirmation) = {repl_conf_analytics}")
    print(f"\n  => Dashboard and Analytics read DIFFERENT COLUMNS!")
    print(f"     Dashboard reads: 'Replacement: Confirmation Pending' (old) + 'Customer Confirmation' (new)")
    print(f"     Analytics reads: 'Customer Confirmation' + 'customer_confirmation' ONLY")
    print(f"\n  => If data is ONLY in 'Replacement: Confirmation Pending' column,")
    print(f"     Analytics MISSES it!")
else:
    print(f"  Both Dashboard and Analytics read the SAME value: {cust_conf}")
    print(f"\n  => The claim genuinely has no Customer Confirmation checked in DB.")
    print(f"  => The 3-of-7 shown in Edit Claim modal was from STALE CACHE.")
    print(f"     Google Sheets sync likely OVERWROTE the workflow data after it was saved.")
