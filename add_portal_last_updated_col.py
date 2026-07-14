"""
add_portal_last_updated_col.py
Adds the portal_last_updated column to the claims table.
This is used by the race condition guard in pg_sync.py.
"""
import os
from dotenv import load_dotenv
load_dotenv()
import psycopg2

conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
cur = conn.cursor()

# Check if column already exists
cur.execute("""
    SELECT column_name FROM information_schema.columns 
    WHERE table_name='claims' AND column_name='portal_last_updated'
""")
exists = cur.fetchone()

if exists:
    print("[SKIP] Column 'portal_last_updated' already exists.")
else:
    cur.execute("ALTER TABLE claims ADD COLUMN portal_last_updated TIMESTAMP;")
    conn.commit()
    print("[OK] Column 'portal_last_updated' added to claims table.")

# Also ensure follow_up_notes exists (in case it doesn't)
cur.execute("""
    SELECT column_name FROM information_schema.columns 
    WHERE table_name='claims' AND column_name='follow_up_notes'
""")
exists2 = cur.fetchone()
if not exists2:
    cur.execute("ALTER TABLE claims ADD COLUMN follow_up_notes TEXT;")
    conn.commit()
    print("[OK] Column 'follow_up_notes' added.")
else:
    print("[SKIP] Column 'follow_up_notes' already exists.")

conn.close()
print("\nDone. DB schema is ready for race condition guard.")
