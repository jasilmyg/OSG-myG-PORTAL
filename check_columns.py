import os, psycopg2, pandas as pd
from dotenv import load_dotenv
load_dotenv()
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
df = pd.read_sql_query("SELECT column_name FROM information_schema.columns WHERE table_name = 'claims'", conn)
print(df.to_string())
conn.close()
