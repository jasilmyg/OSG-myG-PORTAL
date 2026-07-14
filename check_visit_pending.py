from services.pg_sync import _get_connection
from dotenv import load_dotenv
load_dotenv()
conn = _get_connection()
cur = conn.cursor()
cur.execute("SELECT claim_id, remarks, onsitego___status, follow_up___notes FROM claims WHERE onsitego___status = 'Visit Pending' LIMIT 5")
rows = cur.fetchall()
for r in rows:
    print(r)
conn.close()
