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
    
    # Extract sheet Remarks, Onsitego, and SR No
    s_remarks = ""
    s_onsitego = ""
    s_sr_no = ""
    for k, v in row.items():
        if str(k).strip().lower() == "remarks":
            s_remarks = str(v).strip()
        elif "onsitego" in str(k).lower() and "status" in str(k).lower():
            s_onsitego = str(v).strip()
        elif str(k).strip().lower() == "sr no" or str(k).strip().lower() == "sr_no":
            s_sr_no = str(v).strip()
            
    # Extract DB Remarks, Onsitego, and SR No
    db_remarks = ""
    db_onsitego = ""
    db_sr_no = ""
    for k, v in db_row.items():
        if str(k).strip().lower() == "remarks":
            db_remarks = str(v).strip()
        elif "onsitego" in str(k).lower() and "status" in str(k).lower():
            db_onsitego = str(v).strip()
        elif str(k).strip().lower() == "sr no" or str(k).strip().lower() == "sr_no":
            db_sr_no = str(v).strip()
            
    if s_remarks.lower() in ('nan', 'none', 'nat'): s_remarks = ""
    if s_onsitego.lower() in ('nan', 'none', 'nat'): s_onsitego = ""
    if s_sr_no.lower() in ('nan', 'none', 'nat'): s_sr_no = ""
    if db_remarks.lower() in ('nan', 'none', 'nat'): db_remarks = ""
    if db_onsitego.lower() in ('nan', 'none', 'nat'): db_onsitego = ""
    if db_sr_no.lower() in ('nan', 'none', 'nat'): db_sr_no = ""

    print(f"[{cid}] Sheet Remarks: '{s_remarks}', DB Remarks: '{db_remarks}'")
    print(f"[{cid}] Sheet Onsitego: '{s_onsitego}', DB Onsitego: '{db_onsitego}'")
    print(f"[{cid}] Sheet SR No: '{s_sr_no}', DB SR No: '{db_sr_no}'")

    if (s_remarks and s_remarks.lower() != db_remarks.lower()) or \
       (s_onsitego and s_onsitego.lower() != db_onsitego.lower()) or \
       (s_sr_no and s_sr_no.lower() != db_sr_no.lower()):
        print(">>> DETECTED CHANGE!")
        
        # Build a partial dictionary with only the fields we want to pull from Google Sheets
        partial_row = {
            "Claim ID": cid
        }
        if s_remarks and s_remarks.lower() != db_remarks.lower():
            partial_row["Remarks"] = s_remarks
        if s_onsitego and s_onsitego.lower() != db_onsitego.lower():
            partial_row["ONSITEGO - STATUS"] = s_onsitego
        if s_sr_no and s_sr_no.lower() != db_sr_no.lower():
            partial_row["SR No"] = s_sr_no
            
        upsert_claim_to_postgres(partial_row)
        updates_made = True

if updates_made:
    print("Updates made!")
else:
    print("No updates made.")
