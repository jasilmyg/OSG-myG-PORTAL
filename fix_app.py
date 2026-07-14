with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re

# Fix syntax error in generate_report_2
content = re.sub(
    r'        # Feature Store List\n        future_path = os.path.join\(BASE_DIR, "Future Store List\.xlsx"\)\n        except:\n            future_df = timed_excel_read\(future_path, engine=\'openpyxl\'\)\n\n        future_df = future_df\.loc\[:, ~future_df\.columns\.duplicated\(\)\]',
    '''        # Feature Store List
        future_path = os.path.join(BASE_DIR, "Future Store List.xlsx")
        try:
            conn = _get_connection()
            future_df = pd.read_sql('SELECT store as "Store" FROM future_store_list', conn)
            if future_df.empty: raise Exception("Empty DB table future_store_list")
        except Exception as e:
            if not os.path.exists(future_path):
                 flash("Future Store List.xlsx not found on server or DB.", "error")
                 return redirect(url_for('reports_tools'))
            try:
                future_df = timed_excel_read(future_path, "Future Store List", engine='openpyxl')
            except:
                future_df = timed_excel_read(future_path, engine='openpyxl')

        future_df = future_df.loc[:, ~future_df.columns.duplicated()]''',
    content
)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
