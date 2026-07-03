import os
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

cur.execute("SELECT * FROM claims ORDER BY synced_at DESC LIMIT 1")
row = cur.fetchone()
if row:
    print(dict(row))
else:
    print("No claims found in database.")
