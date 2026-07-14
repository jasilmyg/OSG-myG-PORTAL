import sys
sys.path.append('.')
from dotenv import load_dotenv
load_dotenv()
from services.pg_sync import _get_connection

conn = _get_connection()
with conn.cursor() as cur:
    cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'osid_data';")
    cols = cur.fetchall()
    print('Columns in osid_data:')
    for c in cols:
        print(c)
        
    print('\nChecking osid_data for 9048915082:')
    cur.execute("SELECT * FROM osid_data WHERE mobile_no = '9048915082';")
    from psycopg2.extras import RealDictCursor
    with conn.cursor(cursor_factory=RealDictCursor) as dict_cur:
        dict_cur.execute("SELECT * FROM osid_data WHERE mobile_no = '9048915082';")
        rows = dict_cur.fetchall()
        for row in rows:
            print(row)
            print(row)
