from services.pg_sync import fetch_claims_from_postgres, upsert_claim_to_postgres

claims = fetch_claims_from_postgres()
row = next((c for c in claims if c.get("Claim ID") == "CLM-1782801779"), None)
print("Before:", row.get("Follow Up - Notes"), "| Status:", row.get("Status"))

# simulate sheet data
row["Remarks"] = "Testing new remarks"
row["ONSITEGO - STATUS"] = "Testing new status"

print("Upserting...")
res = upsert_claim_to_postgres(row)
print("Result:", res)

claims = fetch_claims_from_postgres()
row2 = next((c for c in claims if c.get("Claim ID") == "CLM-1782801779"), None)
print("After:", row2.get("Follow Up - Notes"), "| Status:", row2.get("Status"))
