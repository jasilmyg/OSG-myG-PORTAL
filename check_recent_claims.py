from services.pg_sync import _get_connection
from dotenv import load_dotenv
load_dotenv()
conn = _get_connection()
cur = conn.cursor()
cur.execute("SELECT claim_id, date, status, last_notified_status FROM claims WHERE date >= '2026-07-08'")
rows = cur.fetchall()
for r in rows:
    print(r)
conn.close()
