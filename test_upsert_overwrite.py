import os
from dotenv import load_dotenv
load_dotenv()
from services.pg_sync import fetch_claims_from_postgres, upsert_claim_to_postgres, _get_connection

cur = _get_connection().cursor()
cur.execute("UPDATE claims SET status = 'Registered', follow_up___notes = '' WHERE claim_id = 'CLM-1782805735'")
_get_connection().commit()

print("Initial DB status: Registered, Notes: ''")

# the row as it comes from sheets on FIRST edit (typing remarks)
row1 = {
    'Claim ID': 'CLM-1782805735',
    'REMARKS': 'First remark',
    'STATUS': 'Registered'
}

print("Running upsert 1 (typing remarks)...")
upsert_claim_to_postgres(row1)

cur = _get_connection().cursor()
cur.execute("SELECT status, follow_up___notes FROM claims WHERE claim_id = 'CLM-1782805735'")
res = cur.fetchone()
print("After Upsert 1 DB Row Status:", res[0])
print("After Upsert 1 DB Row Notes:", repr(res[1]))

# the row as it comes from sheets on SECOND edit (typing something else, or multiple onEdit triggers)
row2 = {
    'Claim ID': 'CLM-1782805735',
    'REMARKS': 'First remark',
    'STATUS': 'Registered'
}

print("Running upsert 2 (subsequent sync)...")
upsert_claim_to_postgres(row2)

cur = _get_connection().cursor()
cur.execute("SELECT status, follow_up___notes FROM claims WHERE claim_id = 'CLM-1782805735'")
res2 = cur.fetchone()
print("After Upsert 2 DB Row Status:", res2[0])
print("After Upsert 2 DB Row Notes:", repr(res2[1]))
