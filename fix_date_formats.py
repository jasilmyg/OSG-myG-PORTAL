import os, psycopg2, psycopg2.extras, datetime
from dotenv import load_dotenv
load_dotenv()

conn = psycopg2.connect(os.getenv('DATABASE_URL'))

# Date columns that might have DD-MM-YYYY format stored
date_cols = [
    'approval_mail_received_date',
    'mail_sent_to_store_date',
    'invoice_generated_date',
    'invoice_sent_to_onsitego_date',
    'settlement_mail_to_accounts_date',
    'claim_settled_date',
]

def try_parse(s):
    s = str(s).strip()[:10]
    # Try DD-MM-YYYY
    try:
        dt = datetime.datetime.strptime(s, '%d-%m-%Y')
        return dt.strftime('%Y-%m-%d'), True  # returns converted value + flag it was wrong format
    except: pass
    # Try YYYY-MM-DD (already correct)
    try:
        datetime.datetime.strptime(s, '%Y-%m-%d')
        return s, False  # already correct
    except: pass
    return None, False

try:
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        total_fixed = 0
        for col in date_cols:
            cur.execute(f"SELECT claim_id, {col} FROM claims WHERE {col} IS NOT NULL AND {col} != ''")
            rows = cur.fetchall()
            col_fixed = 0
            for row in rows:
                raw = row[col]
                if not raw: continue
                converted, was_wrong = try_parse(str(raw))
                if was_wrong and converted:
                    cur.execute(f"UPDATE claims SET {col} = %s WHERE claim_id = %s", (converted, row['claim_id']))
                    col_fixed += 1
            if col_fixed > 0:
                print(f"[FIXED] {col}: {col_fixed} records converted from DD-MM-YYYY to YYYY-MM-DD")
            else:
                print(f"[OK]    {col}: no bad formats found")
            total_fixed += col_fixed

    conn.commit()
    print(f"\nTotal records fixed: {total_fixed}")
    print("Done.")

except Exception as e:
    conn.rollback()
    print(f"[ERROR] {e}")
    import traceback; traceback.print_exc()
finally:
    conn.close()
