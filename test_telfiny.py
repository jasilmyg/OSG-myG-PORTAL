import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("TELFINY_API_KEY")
BASE_URL = "https://hub.telinfy.com/unified/developer/api/v1/whatsapp/reports"

def test_api():
    print("Requesting download...")
    res = requests.post(
        f"{BASE_URL}/request-download",
        headers={"x-api-key": API_KEY, "Content-Type": "application/json"},
        json={"fromDate": "2026-07-01", "toDate": "2026-07-09"}
    )
    print("Response:", res.status_code, res.text)
    data = res.json()
    if not data.get("success"):
        print("Failed to request download.")
        return
        
    file_id = data.get("fileID")
    print(f"Got fileID: {file_id}. Polling...")
    
    for _ in range(10):
        time.sleep(3)
        res = requests.get(
            f"{BASE_URL}/file/{file_id}",
            headers={"x-api-key": API_KEY}
        )
        print("Poll Response:", res.status_code)
        
        # Depending on content type, it might be the file or a JSON processing status
        content_type = res.headers.get("Content-Type", "")
        if "application/json" in content_type:
            poll_data = res.json()
            print("Status:", poll_data)
            if poll_data.get("status") == "processing":
                continue
            elif poll_data.get("success") == False:
                print("Error:", poll_data)
                return
        else:
            print("Got the file!")
            with open("test_report.csv", "wb") as f:
                f.write(res.content)
            print("Saved as test_report.csv")
            return

if __name__ == "__main__":
    test_api()
