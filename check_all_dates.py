import os
import sys
sys.path.append('.')
from dotenv import load_dotenv
load_dotenv()
from services.pg_sync import _get_connection
import psycopg2.extras

conn = _get_connection()
with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
    cur.execute("SELECT claim_id, date, mobile_number FROM claims ORDER BY claim_id DESC LIMIT 20;")
    rows = cur.fetchall()
    for row in rows:
        print(row)
