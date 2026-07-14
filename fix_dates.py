from services.pg_sync import _get_connection
from dotenv import load_dotenv
load_dotenv()
conn = _get_connection()
cur = conn.cursor()

# Get the future dates
cur.execute("SELECT claim_id, date, customer_name FROM claims WHERE date > '2026-07-08' ORDER BY date DESC")
rows = cur.fetchall()
print(f"Total future claims: {len(rows)}")

for r in rows:
    claim_id = r[0]
    old_date = r[1][:10]  # Get YYYY-MM-DD
    # Split YYYY-MM-DD
    parts = old_date.split('-')
    if len(parts) == 3:
        year, month, day = parts
        # Swap month and day
        new_date = f"{year}-{day}-{month}"
        
        print(f"Fixing {claim_id}: {old_date} -> {new_date}")
        cur.execute("UPDATE claims SET date = %s WHERE claim_id = %s", (new_date, claim_id))

conn.commit()
print("Dates fixed successfully!")
conn.close()
