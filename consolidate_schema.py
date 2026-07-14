"""
consolidate_schema.py
--------------------------------------
Fixes the Schema Split issue in the `claims` table:
1. Merges follow_up___dates   -> follow_up___dates (keep old) but copy to follow_up_dates
2. Merges follow_up___notes   -> follow_up___notes (keep old) but copy to follow_up_notes
3. Merges mobile              -> mobile_number
4. Reports what was merged.

SAFE: uses COALESCE so existing data in the target column is never overwritten.
"""
import os, re
from dotenv import load_dotenv
load_dotenv()
import psycopg2
import psycopg2.extras

DATABASE_URL = os.environ.get("DATABASE_URL")
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

print("=" * 65)
print("SCHEMA CONSOLIDATION - MERGE SPLIT COLUMNS")
print("=" * 65)

# ---------------------------------------------------------------
# Helper: get all column names in the claims table
# ---------------------------------------------------------------
def get_columns():
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='claims';")
    return {row[0] for row in cur.fetchall()}

existing_cols = get_columns()

# ---------------------------------------------------------------
# 1. Merge follow_up___dates → follow_up_dates
# ---------------------------------------------------------------
if 'follow_up___dates' in existing_cols and 'follow_up_dates' in existing_cols:
    cur.execute("""
        UPDATE claims
        SET follow_up_dates = COALESCE(NULLIF(TRIM(follow_up___dates), ''), follow_up_dates)
        WHERE (follow_up_dates IS NULL OR TRIM(follow_up_dates) = '')
          AND follow_up___dates IS NOT NULL
          AND TRIM(follow_up___dates) != '';
    """)
    affected = cur.rowcount
    print(f"[OK] Merged follow_up___dates -> follow_up_dates: {affected} rows updated")
elif 'follow_up___dates' in existing_cols and 'follow_up_dates' not in existing_cols:
    # Rename the column
    cur.execute('ALTER TABLE claims RENAME COLUMN follow_up___dates TO follow_up_dates;')
    print(f"[OK] Renamed follow_up___dates -> follow_up_dates")
else:
    print(f"[SKIP] follow_up___dates column not found or already consolidated")

# ---------------------------------------------------------------
# 2. Merge follow_up___notes → follow_up_notes
# ---------------------------------------------------------------
if 'follow_up___notes' in existing_cols and 'follow_up_notes' in existing_cols:
    cur.execute("""
        UPDATE claims
        SET follow_up_notes = COALESCE(NULLIF(TRIM(follow_up___notes), ''), follow_up_notes)
        WHERE (follow_up_notes IS NULL OR TRIM(follow_up_notes) = '')
          AND follow_up___notes IS NOT NULL
          AND TRIM(follow_up___notes) != '';
    """)
    affected = cur.rowcount
    print(f"[OK] Merged follow_up___notes -> follow_up_notes: {affected} rows updated")

    # Also merge in the OPPOSITE direction for rows that only have follow_up_notes but not follow_up___notes
    cur.execute("""
        UPDATE claims
        SET follow_up___notes = COALESCE(NULLIF(TRIM(follow_up_notes), ''), follow_up___notes)
        WHERE (follow_up___notes IS NULL OR TRIM(follow_up___notes) = '')
          AND follow_up_notes IS NOT NULL
          AND TRIM(follow_up_notes) != '';
    """)
    affected2 = cur.rowcount
    print(f"[OK] Back-filled follow_up_notes -> follow_up___notes: {affected2} rows updated")
elif 'follow_up___notes' in existing_cols and 'follow_up_notes' not in existing_cols:
    cur.execute('ALTER TABLE claims RENAME COLUMN follow_up___notes TO follow_up_notes;')
    print(f"[OK] Renamed follow_up___notes -> follow_up_notes")
else:
    print(f"[SKIP] follow_up___notes column not found or already consolidated")

# ---------------------------------------------------------------
# 3. Merge mobile → mobile_number
# ---------------------------------------------------------------
if 'mobile' in existing_cols and 'mobile_number' in existing_cols:
    cur.execute("""
        UPDATE claims
        SET mobile_number = COALESCE(NULLIF(TRIM(mobile), ''), mobile_number)
        WHERE (mobile_number IS NULL OR TRIM(mobile_number) = '')
          AND mobile IS NOT NULL
          AND TRIM(mobile) != '';
    """)
    affected = cur.rowcount
    print(f"[OK] Merged mobile -> mobile_number: {affected} rows updated")
elif 'mobile' in existing_cols and 'mobile_number' not in existing_cols:
    cur.execute('ALTER TABLE claims RENAME COLUMN mobile TO mobile_number;')
    print(f"[OK] Renamed mobile -> mobile_number")
else:
    print(f"[SKIP] mobile column not found or already consolidated")

conn.commit()

# ---------------------------------------------------------------
# 4. Standardize date formats - convert YYYY-MM-DD HH:MM:SS to YYYY-MM-DD
# ---------------------------------------------------------------
print("\n--- Standardizing date formats ---")
cur.execute("""
    SELECT claim_id, date FROM claims
    WHERE date IS NOT NULL AND date != ''
    AND LENGTH(date) > 10
    AND date ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}';
""")
long_dates = cur.fetchall()
updated_dates = 0
for row in long_dates:
    claim_id, dt_str = row
    standardized = str(dt_str).strip()[:10]
    cur.execute("UPDATE claims SET date = %s WHERE claim_id = %s", (standardized, claim_id))
    updated_dates += 1

conn.commit()
print(f"[OK] Standardized {updated_dates} dates to YYYY-MM-DD format")

# ---------------------------------------------------------------
# 5. Final Verification
# ---------------------------------------------------------------
print("\n--- Final Verification ---")
existing_cols = get_columns()

for col in ['follow_up___dates', 'follow_up_dates']:
    if col in existing_cols:
        cur.execute(f"SELECT COUNT(*) FROM claims WHERE {col} IS NOT NULL AND TRIM({col}) != ''")
        print(f"  '{col}': {cur.fetchone()[0]} rows have data")

for col in ['follow_up___notes', 'follow_up_notes']:
    if col in existing_cols:
        cur.execute(f"SELECT COUNT(*) FROM claims WHERE {col} IS NOT NULL AND TRIM({col}) != ''")
        print(f"  '{col}': {cur.fetchone()[0]} rows have data")

for col in ['mobile', 'mobile_number']:
    if col in existing_cols:
        cur.execute(f"SELECT COUNT(*) FROM claims WHERE {col} IS NOT NULL AND TRIM({col}) != ''")
        print(f"  '{col}': {cur.fetchone()[0]} rows have data")

cur.execute("SELECT COUNT(*), COUNT(CASE WHEN LENGTH(date)=10 THEN 1 END) FROM claims WHERE date IS NOT NULL AND date != ''")
total_dates, std_dates = cur.fetchone()
print(f"  Date format check: {std_dates}/{total_dates} dates now in YYYY-MM-DD format")

conn.close()
print("\n[DONE] Schema consolidation complete!")
