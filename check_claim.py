import os, psycopg2, pandas as pd
from dotenv import load_dotenv
load_dotenv()
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
df = pd.read_sql_query("SELECT status, replacement_customer_confirmation, replacement_onsitego_approval, replacement_mail_sent_to_store, replacement_invoice_generated, replacement_invoice_sent, replacement_settlement_mail FROM osg_claims WHERE mobile_number LIKE '%7507231711%'", conn)
print(df.to_string())
conn.close()
