from services.pg_sync import _get_connection
from dotenv import load_dotenv
load_dotenv()

def fix_claims():
    conn = _get_connection()
    cur = conn.cursor()
    
    # Check claims
    cur.execute("SELECT claim_id, customer_name, status FROM claims WHERE date = '2026-07-07' AND status = 'Submitted'")
    rows = cur.fetchall()
    
    print(f"Found {len(rows)} claims to update:")
    for r in rows:
        print(f" - {r[0]} ({r[1]}): {r[2]}")
        
    if rows:
        # Update them
        cur.execute("UPDATE claims SET status = 'Registered', last_notified_status = 'REGISTERED' WHERE date = '2026-07-07' AND status = 'Submitted'")
        conn.commit()
        print("Updated successfully!")
            
    conn.close()

if __name__ == '__main__':
    fix_claims()
