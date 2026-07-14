import os, psycopg2, psycopg2.extras
from dotenv import load_dotenv
load_dotenv()

conn = psycopg2.connect(os.getenv('DATABASE_URL'))
with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:

    # Try all possible mobile formats
    for search in ['7012899934', '07012899934', '+917012899934', '917012899934']:
        cur.execute("SELECT claim_id, customer_name, status, mobile_number, date, synced_at FROM claims WHERE mobile_number ILIKE %s", (f'%%{search}%%',))
        rows = cur.fetchall()
        if rows:
            print(f"Found with search '{search}': {len(rows)} record(s)")
            for r in rows:
                print(f"  {r['claim_id']} | {r['customer_name']} | {r['status']} | {r['mobile_number']} | {str(r['date'])[:10]}")
        else:
            print(f"Not found with: {search}")

    # Also check how many total claims exist
    cur.execute("SELECT COUNT(*) as cnt, MAX(date) as latest FROM claims")
    r = cur.fetchone()
    print(f"\nTotal claims in DB: {r['cnt']}, Latest date: {r['latest']}")

    # Check new claims submitted in last 2 weeks
    cur.execute("""
        SELECT claim_id, customer_name, mobile_number, status, date, synced_at
        FROM claims
        WHERE date >= '2026-07-01'
        ORDER BY date DESC
        LIMIT 20
    """)
    rows = cur.fetchall()
    print(f"\nRecent claims (July 2026):")
    for r in rows:
        print(f"  {r['claim_id']} | {r['customer_name']} | {r['mobile_number']} | {str(r['date'])[:10]} | {r['status']}")

conn.close()
