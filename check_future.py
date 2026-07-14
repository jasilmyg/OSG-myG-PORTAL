from services.pg_sync import _get_connection
from dotenv import load_dotenv
load_dotenv()
conn = _get_connection()
cur = conn.cursor()
cur.execute("SELECT claim_id, date, customer_name FROM claims WHERE date > '2026-07-08' ORDER BY date DESC")
rows = cur.fetchall()
print(f"Total future claims: {len(rows)}")
for r in rows[:30]:
    print(r)
conn.close()
