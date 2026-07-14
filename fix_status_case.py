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

print("Fixing mixed case status values in database...\n")

# Check before
cur.execute("SELECT status, COUNT(*) FROM claims GROUP BY status ORDER BY COUNT(*) DESC")
print("BEFORE FIX:")
for r in cur.fetchall():
    print(f"  {repr(r[0])}: {r[1]}")

# Fix 1: REPAIR COMPLETED -> Repair Completed
cur.execute("UPDATE claims SET status='Repair Completed' WHERE status='REPAIR COMPLETED'")
fixed_repair = cur.rowcount
print(f"\nFixed 'REPAIR COMPLETED' -> 'Repair Completed': {fixed_repair} records")

# Fix 2: REJECTED -> Rejected
cur.execute("UPDATE claims SET status='Rejected' WHERE status='REJECTED'")
fixed_rejected = cur.rowcount
print(f"Fixed 'REJECTED' -> 'Rejected': {fixed_rejected} records")

# Fix 3: empty status -> set to 'Registered' (find the blank one)
cur.execute("SELECT claim_id, customer_name, mobile_number, date FROM claims WHERE status IS NULL OR status = ''")
blanks = cur.fetchall()
if blanks:
    for r in blanks:
        print(f"\nEmpty status claim: {r[0]} | {r[1]} | {r[2]} | {r[3]}")
    cur.execute("UPDATE claims SET status='Registered' WHERE status IS NULL OR status = ''")
    print(f"Fixed empty status -> 'Registered': {cur.rowcount} records")

conn.commit()

# Verify after
cur.execute("SELECT status, COUNT(*) FROM claims GROUP BY status ORDER BY COUNT(*) DESC")
print("\nAFTER FIX:")
for r in cur.fetchall():
    print(f"  {repr(r[0])}: {r[1]}")

print(f"\nDone! Total fixed: {fixed_repair + fixed_rejected} records")
cur.close()
conn.close()
