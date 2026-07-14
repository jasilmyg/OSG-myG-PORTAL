import os
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("TELFINY_API_KEY")

for dates in [("2026-07-08", "2026-07-09"), ("2026-06-01", "2026-06-30"), ("2025-01-01", "2025-01-21")]:
    res = requests.post(
        "https://hub.telinfy.com/unified/developer/api/v1/whatsapp/reports/request-download",
        headers={"x-api-key": API_KEY, "Content-Type": "application/json"},
        json={"fromDate": dates[0], "toDate": dates[1]}
    )
    print(dates, res.status_code, res.text)
