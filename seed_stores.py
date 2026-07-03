import os, psycopg2, psycopg2.extras, pandas as pd
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

# 1. myG All Store
cur.execute('''
CREATE TABLE IF NOT EXISTS myg_all_store (
    id SERIAL PRIMARY KEY,
    store TEXT
)
''')
cur.execute('TRUNCATE myg_all_store')
df1 = pd.read_excel('myG All Store.xlsx', dtype=str).dropna(how='all')
if not df1.empty:
    col = df1.columns[0]
    psycopg2.extras.execute_batch(cur, 'INSERT INTO myg_all_store (store) VALUES (%s)', [(str(row[col]).strip() if pd.notna(row[col]) else None,) for _, row in df1.iterrows()])

# 2. Future Store List
cur.execute('''
CREATE TABLE IF NOT EXISTS future_store_list (
    id SERIAL PRIMARY KEY,
    store TEXT
)
''')
cur.execute('TRUNCATE future_store_list')
df2 = pd.read_excel('Future Store List.xlsx', dtype=str).dropna(how='all')
if not df2.empty:
    col = df2.columns[0]
    psycopg2.extras.execute_batch(cur, 'INSERT INTO future_store_list (store) VALUES (%s)', [(str(row[col]).strip() if pd.notna(row[col]) else None,) for _, row in df2.iterrows()])

# 3. RBM, BDM, BRANCH
cur.execute('''
CREATE TABLE IF NOT EXISTS rbm_bdm_branch (
    id SERIAL PRIMARY KEY,
    rbm TEXT,
    bdm TEXT,
    branch TEXT
)
''')
cur.execute('TRUNCATE rbm_bdm_branch')
df3 = pd.read_excel('RBM,BDM,BRANCH.xlsx', dtype=str).dropna(how='all')
if not df3.empty:
    cols = []
    for c in df3.columns:
        if 'rbm' in str(c).lower(): cols.append('rbm')
        elif 'bdm' in str(c).lower(): cols.append('bdm')
        elif 'branch' in str(c).lower(): cols.append('branch')
        else: cols.append(c)
    df3.columns = cols
    psycopg2.extras.execute_batch(cur, 'INSERT INTO rbm_bdm_branch (rbm, bdm, branch) VALUES (%s, %s, %s)', 
        [(str(row.get('rbm','')).strip() if pd.notna(row.get('rbm')) else None,
          str(row.get('bdm','')).strip() if pd.notna(row.get('bdm')) else None,
          str(row.get('branch','')).strip() if pd.notna(row.get('branch')) else None) 
         for _, row in df3.iterrows()])


conn.commit()
conn.close()
print("Tables created and seeded successfully.")
