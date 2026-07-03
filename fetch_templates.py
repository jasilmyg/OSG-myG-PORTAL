import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("TELFINY_API_KEY")
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "x-api-key": API_KEY
}

url = "https://hub.telinfy.com/unified/developer/api/v1/whatsapp/templates"
resp = requests.get(url, headers=headers)
print("GET templates status:", resp.status_code)
if resp.status_code == 200:
    print(json.dumps(resp.json(), indent=2))
else:
    print(resp.text)
