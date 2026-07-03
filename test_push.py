import os
import requests
from dotenv import load_dotenv

load_dotenv()

web_app_url = os.environ.get("WEB_APP_URL")

payload = {
    "SR No": "CLM-TEST-12345",
    "Submitted Dat": "2026-06-25",
    "Customer Name": "Test User",
    "Mobile": "1234567890",
    "Branch": "Test Branch",
    "Product": "Test Product",
    "Issue": "Test Issue",
    "STATUS": "Submitted"
}

print(f"Pushing to {web_app_url}")
response = requests.post(web_app_url, json=payload, timeout=15)
print(f"Status Code: {response.status_code}")
print(f"Response text: {response.text}")
