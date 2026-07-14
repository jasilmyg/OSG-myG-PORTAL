import os
import sys
sys.path.append('.')
from dotenv import load_dotenv
load_dotenv()
import requests

web_app_url = os.environ.get("WEB_APP_URL")
resp = requests.get(web_app_url, timeout=30)
sheet_data = resp.json()

mobiles = ['9037246466', '8139041007', '9539145403', '9847225317', '9744494347', '7507231711']

for row in sheet_data:
    mobile = str(row.get('Mobile Number') or row.get('Mobile') or "").strip()
    if mobile in mobiles:
        print(f"Mobile: {mobile} | Claim ID: {row.get('Claim ID')} | Submitted Date: {row.get('Submitted Date')} | DATE: {row.get('DATE')} | Date: {row.get('Date')}")
