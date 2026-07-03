import os, psycopg2
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

# Enforce rule: if "Settled With Accounts (Yes/No)" is 'Yes', 
# set "Settlement Mail to Accounts(Yes/No)" to 'Yes'.
cur.execute("""
    UPDATE claims 
    SET "settlement_mail_to_accountsyes_no" = 'Yes'
    WHERE "settled_with_accounts_yes_no" = 'Yes' 
      AND ("settlement_mail_to_accountsyes_no" IS NULL OR "settlement_mail_to_accountsyes_no" != 'Yes')
""")

print(f"Updated {cur.rowcount} retroactive claims.")

conn.commit()
conn.close()
