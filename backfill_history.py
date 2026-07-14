from services.pg_sync import _get_connection
from dotenv import load_dotenv
import datetime

load_dotenv()
conn = _get_connection()
cur = conn.cursor()

cur.execute("SELECT claim_id, remarks, onsitego___status, follow_up___notes, date FROM claims")
rows = cur.fetchall()

updated_count = 0
for r in rows:
    claim_id, remarks, onsitego, notes, claim_date = r
    
    notes = str(notes or "").strip()
    remarks = str(remarks or "").strip()
    onsitego = str(onsitego or "").strip()
    
    original_notes = notes
    appended = False
    
    # Use claim_date or current date for timestamp
    ts = datetime.datetime.now().strftime('%d/%m/%Y, %I:%M:%S %p').lower()
    if claim_date:
        try:
            # format as DD/MM/YYYY, 12:00:00 am
            ts = claim_date.strftime('%d/%m/%Y, 12:00:00 am').lower()
        except:
            pass
            
    if remarks and remarks.lower() not in ('nan', 'none', 'nat'):
        if "[REMARK]" not in notes and remarks.lower() not in notes.lower():
            notes += f"\n[{ts}] [REMARK]: {remarks}"
            appended = True
            
    if onsitego and onsitego.lower() not in ('nan', 'none', 'nat'):
        if "[ONSITEGO STATUS]" not in notes and onsitego.lower() not in notes.lower():
            notes += f"\n[{ts}] [ONSITEGO STATUS]: {onsitego}"
            appended = True
            
    if appended:
        notes = notes.strip()
        cur.execute("UPDATE claims SET follow_up___notes = %s WHERE claim_id = %s", (notes, claim_id))
        updated_count += 1

conn.commit()
print(f"Backfilled {updated_count} claims with missing history.")
conn.close()
