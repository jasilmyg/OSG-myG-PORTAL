import os
from dotenv import load_dotenv
load_dotenv()
import psycopg2

conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
cur = conn.cursor()

cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name='claims' 
    AND column_name IN ('last_notified_status', 'last_notified_at')
    ORDER BY column_name
""")
cols = cur.fetchall()
print('Existing WA columns:', cols)

if not any(c[0] == 'last_notified_at' for c in cols):
    cur.execute("ALTER TABLE claims ADD COLUMN last_notified_at TIMESTAMP")
    conn.commit()
    print("Added: last_notified_at TIMESTAMP")
else:
    print("last_notified_at already exists")

if not any(c[0] == 'last_notified_status' for c in cols):
    cur.execute("ALTER TABLE claims ADD COLUMN last_notified_status TEXT")
    conn.commit()
    print("Added: last_notified_status TEXT")
else:
    print("last_notified_status already exists")

conn.close()
print("Done.")
