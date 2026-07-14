import os, psycopg2, pandas as pd
from dotenv import load_dotenv
load_dotenv()
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
df = pd.read_sql_query("SELECT status, customer_confirmation, approval_mail_received_from_onsitego_yes_no, mail_sent_to_store_yes_no, invoice_generated_yes_no, invoice_sent_to_onsitego_yes_no, settlement_mail_to_accounts_yes_no FROM claims WHERE mobile_number LIKE '%7507231711%'", conn)
print(df.to_string())
conn.close()
