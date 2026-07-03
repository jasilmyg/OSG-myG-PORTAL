import os
import requests
from dotenv import load_dotenv

load_dotenv()

web_app_url = os.environ.get("WEB_APP_URL")
resp = requests.get(web_app_url, timeout=30)
sheet_data = resp.json()
for row in sheet_data:
    s_remarks = ""
    for k, v in row.items():
        if str(k).strip().lower() == "remarks":
            s_remarks = str(v).strip()
    if s_remarks.lower() == "demo testing":
        print("FOUND ROW WITH DEMO TESTING:", row)
