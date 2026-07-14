import psycopg2

env_path = r'c:\Users\jasil_myg\Desktop\OSG-myG-PORTAL-mainnnnn - Copy\.env'
DATABASE_URL = ''
with open(env_path) as f:
    for line in f:
        if line.startswith('DATABASE_URL'):
            DATABASE_URL = line.split('=',1)[1].strip().strip('"').strip("'")
            break

conn = psycopg2.connect(DATABASE_URL, sslmode='require')
cur = conn.cursor()

# Fix settlement mail mismatch + set complete column
cur.execute("""
    UPDATE claims SET 
        settlement_mail_to_accounts_yes_no = 'Yes',
        complete = 'Yes'
    WHERE claim_id = 'CLM-1781257656'
""")
print(f"Fixed {cur.rowcount} record(s)")
conn.commit()

# Verify
cur.execute("""SELECT claim_id, status, settlement_mail_to_accounts_yes_no, 
                      replacement_settlement_mail_to_accounts, complete, complete_yes_no
               FROM claims WHERE claim_id = 'CLM-1781257656'""")
r = cur.fetchone()
print(f"claim_id:                               {r[0]}")
print(f"status:                                 {r[1]}")
print(f"settlement_mail_to_accounts_yes_no:     {r[2]}")
print(f"replacement_settlement_mail_to_accounts:{r[3]}")
print(f"complete:                               {r[4]}")
print(f"complete_yes_no:                        {r[5]}")

cur.close()
conn.close()
print("\nDB fixed successfully.")
