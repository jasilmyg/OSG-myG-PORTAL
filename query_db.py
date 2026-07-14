import os, psycopg2, pandas as pd
from dotenv import load_dotenv
load_dotenv()
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
df = pd.read_sql_query("SELECT * FROM whatsapp_message_logs WHERE mobile_number LIKE '%9846552171%'", conn)
print(df.to_string())
conn.close()
