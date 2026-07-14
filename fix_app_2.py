with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

replacement = """        from services.pg_sync import _get_connection
        import pandas as pd
        
        # Feature Store List
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

        future_df = future_df.loc[:, ~future_df.columns.duplicated()]
"""

new_lines = lines[:2824] + [replacement] + lines[2832:]

with open('app.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
