import os
from dotenv import load_dotenv
load_dotenv()
from services.pg_sync import fetch_claims_from_postgres, upsert_claim_to_postgres

# the row as it comes from sheets
row = {
    'Claim ID': 'CLM-1782803825',
    'REMARKS': 'Demo testing from script',
    'ONSITEGO - STATUS': 'Demo testing from script status'
}

print("Running upsert...")
res = upsert_claim_to_postgres(row)
print("Upsert result:", res)

claims = fetch_claims_from_postgres()
db_row = next((c for c in claims if c.get('Claim ID') == 'CLM-1782803825'), None)
print("After Upsert DB Row Status:", db_row.get("Status"))
print("After Upsert DB Row Notes:", repr(db_row.get("Follow Up - Notes")))
