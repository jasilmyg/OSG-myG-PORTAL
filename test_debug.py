import requests
import os
from dotenv import load_dotenv

load_dotenv()
url = os.environ.get("WEB_APP_URL")
if not url:
    print("NO URL")
else:
    sheet = requests.get(url).json()
    row = next((r for r in sheet if r.get('Claim ID') == 'CLM-1782883825'), None)
    print("Google Sheet Row:", row)

from services.pg_sync import fetch_claims_from_postgres
db_claims = fetch_claims_from_postgres()
db_row = next((c for c in db_claims if c.get('Claim ID') == 'CLM-1782883825'), None)
print("DB Row:", db_row)
