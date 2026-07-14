from services.pg_sync import _get_connection
from dotenv import load_dotenv
load_dotenv()
conn = _get_connection()
cur = conn.cursor()

# Set last_notified_status to REGISTERED for all existing claims that don't have one
cur.execute("UPDATE claims SET last_notified_status = 'REGISTERED' WHERE last_notified_status IS NULL")
conn.commit()

print(f'Updated {cur.rowcount} row(s) to prevent duplicate registration messages.')
conn.close()
