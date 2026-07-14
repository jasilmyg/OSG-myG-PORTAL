import os
import collections
from dotenv import load_dotenv
load_dotenv()
from services.pg_sync import _get_connection, PG_COLS

def run_diagnostics():
    print("=== DATA DIAGNOSTICS REPORT ===")
    
    try:
        conn = _get_connection()
        cur = conn.cursor()
    except Exception as e:
        print(f"Failed to connect to DB: {e}")
        return

    # Check total rows
    cur.execute("SELECT COUNT(*) FROM claims;")
    total_rows = cur.fetchone()[0]
    print(f"\nTotal claims in database: {total_rows}")

    if total_rows == 0:
        print("No data found to diagnose.")
        return

    # Check for empty claim_ids
    cur.execute("SELECT COUNT(*) FROM claims WHERE claim_id IS NULL OR TRIM(claim_id) = '';")
    empty_claims = cur.fetchone()[0]
    if empty_claims > 0:
        print(f"[!] WARNING: Found {empty_claims} claims with EMPTY claim_id.")
    else:
        print("[OK] No empty claim_ids found.")

    # Check for duplicate claim_ids
    cur.execute("SELECT claim_id, COUNT(*) FROM claims GROUP BY claim_id HAVING COUNT(*) > 1;")
    duplicates = cur.fetchall()
    if duplicates:
        print(f"[!] WARNING: Found {len(duplicates)} DUPLICATE claim_ids!")
        for row in duplicates[:5]:
            print(f"    - {row[0]} occurs {row[1]} times")
    else:
        print("[OK] No duplicate claim_ids found.")

    # Check date column formats and anomalies
    cur.execute("SELECT claim_id, date FROM claims WHERE date IS NOT NULL AND date != '';")
    dates = cur.fetchall()
    
    date_formats = collections.defaultdict(int)
    invalid_dates = []
    
    for row in dates:
        d_str = str(row[1]).strip()
        # Basic heuristic for format
        if len(d_str) >= 19 and '-' in d_str and ':' in d_str:
            date_formats["YYYY-MM-DD HH:MM:SS"] += 1
        elif len(d_str) == 10 and d_str[4] == '-':
            date_formats["YYYY-MM-DD"] += 1
        elif len(d_str) == 10 and d_str[2] == '-':
            date_formats["DD-MM-YYYY"] += 1
        elif len(d_str) == 10 and d_str[2] == '/':
            date_formats["DD/MM/YYYY"] += 1
        elif len(d_str) == 10 and d_str[4] == '/':
            date_formats["YYYY/MM/DD"] += 1
        else:
            date_formats["OTHER/INVALID"] += 1
            invalid_dates.append((row[0], d_str))

    print("\n--- Date Format Analysis (column: 'date') ---")
    if date_formats:
        for fmt, count in date_formats.items():
            print(f"Format '{fmt}': {count} entries")
            
        if len(date_formats) > 1:
            print("[!] WARNING: Multiple different date formats detected in the database. This causes sorting and parsing failures.")
    else:
        print("No date data found.")
        
    if invalid_dates:
        print(f"[!] WARNING: Found {len(invalid_dates)} highly irregular date formats.")
        for row in invalid_dates[:5]:
            print(f"    - Claim {row[0]}: '{row[1]}'")

    # Check for empty critical fields
    print("\n--- Critical Field Check ---")
    critical_fields = ['customer_name', 'status', 'mobile_number']
    
    # Check what columns exist actually
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'claims';")
    existing_cols = [row[0] for row in cur.fetchall()]
    
    for field in critical_fields:
        if field in existing_cols:
            cur.execute(f"SELECT COUNT(*) FROM claims WHERE {field} IS NULL OR TRIM({field}) = '' OR {field} = 'nan' OR {field} = 'None';")
            missing = cur.fetchone()[0]
            if missing > 0:
                print(f"[!] WARNING: '{field}' is completely missing or 'nan' in {missing} rows.")
            else:
                print(f"[OK] '{field}' is populated for all rows.")
        else:
            print(f"Field '{field}' does not exist in DB schema.")
            
    # Check for statuses
    if 'status' in existing_cols:
        cur.execute("SELECT status, COUNT(*) FROM claims GROUP BY status ORDER BY count DESC;")
        statuses = cur.fetchall()
        print("\n--- Status Distribution ---")
        for st in statuses:
            print(f" - '{st[0]}': {st[1]}")

    conn.close()

if __name__ == "__main__":
    run_diagnostics()
