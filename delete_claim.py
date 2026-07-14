from services.pg_sync import _get_connection
from dotenv import load_dotenv
load_dotenv()
conn = _get_connection()
cur = conn.cursor()
cur.execute("DELETE FROM claims WHERE claim_id = 'CLM-1782810764'")
conn.commit()
print(f'Deleted {cur.rowcount} row(s)')
conn.close()
