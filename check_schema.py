import os, psycopg2

env_path = r'c:\Users\jasil_myg\Desktop\OSG-myG-PORTAL-mainnnnn - Copy\.env'
DATABASE_URL = ''
with open(env_path) as f:
    for line in f:
        if line.startswith('DATABASE_URL'):
            DATABASE_URL = line.split('=',1)[1].strip().strip('"').strip("'")
            break

conn = psycopg2.connect(DATABASE_URL, sslmode='require')
cur = conn.cursor()

# Get columns
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name='claims' 
    ORDER BY ordinal_position
""")
print("CLAIMS TABLE COLUMNS:")
cols = cur.fetchall()
for col, dtype in cols:
    print(f"  {col:<35} {dtype}")

# Also check a sample row
print("\nSAMPLE ROW (first claim):")
cur.execute("SELECT * FROM claims LIMIT 1")
row = cur.fetchone()
col_names = [desc[0] for desc in cur.description]
for i, (cn, val) in enumerate(zip(col_names, row)):
    print(f"  {cn:<35} = {repr(val)[:80]}")

conn.close()
