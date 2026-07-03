import os
import requests
from dotenv import load_dotenv

load_dotenv()
web_app_url = os.environ.get("WEB_APP_URL")
resp = requests.get(web_app_url, timeout=30)
sheet_data = resp.json()

from services.pg_sync import fetch_claims_from_postgres, upsert_claim_to_postgres
db_data = fetch_claims_from_postgres()
db_dict = {str(c.get("Claim ID", "")): c for c in db_data}

updates_made = False
for row in sheet_data:
    cid = str(row.get("Claim ID") or row.get("claim_id") or "")
    if not cid or not cid.startswith("CLM-"):
        continue
        
    db_row = db_dict.get(cid, {})
    
    # Extract sheet Remarks and Onsitego
    s_remarks = ""
    s_onsitego = ""
    for k, v in row.items():
        if str(k).strip().lower() == "remarks":
            s_remarks = str(v).strip()
        elif "onsitego" in str(k).lower() and "status" in str(k).lower():
            s_onsitego = str(v).strip()
            
    # Extract DB Remarks and Onsitego
    db_remarks = ""
    db_onsitego = ""
    for k, v in db_row.items():
        if str(k).strip().lower() == "remarks":
            db_remarks = str(v).strip()
        elif "onsitego" in str(k).lower() and "status" in str(k).lower():
            db_onsitego = str(v).strip()
            
    if s_remarks.lower() in ('nan', 'none', 'nat'): s_remarks = ""
    if s_onsitego.lower() in ('nan', 'none', 'nat'): s_onsitego = ""
    if db_remarks.lower() in ('nan', 'none', 'nat'): db_remarks = ""
    if db_onsitego.lower() in ('nan', 'none', 'nat'): db_onsitego = ""

    print(f"[{cid}] Sheet Remarks: '{s_remarks}', DB Remarks: '{db_remarks}'")
    print(f"[{cid}] Sheet Onsitego: '{s_onsitego}', DB Onsitego: '{db_onsitego}'")

    if (s_remarks and s_remarks.lower() != db_remarks.lower()) or \
       (s_onsitego and s_onsitego.lower() != db_onsitego.lower()):
        print(">>> DETECTED CHANGE!")
        upsert_claim_to_postgres(row)
        updates_made = True

if updates_made:
    print("Updates made!")
else:
    print("No updates made.")
