from services.pg_sync import _get_connection
from dotenv import load_dotenv
load_dotenv()
conn = _get_connection()
cur = conn.cursor()
cur.execute("SELECT * FROM claims WHERE claim_id = 'CLM-1782805735'")
row = cur.fetchone()
if row:
    colnames = [desc[0] for desc in cur.description]
    for col, val in zip(colnames, row):
        print(f'{col}: {val}')
else:
    print('Claim not found')
conn.close()
