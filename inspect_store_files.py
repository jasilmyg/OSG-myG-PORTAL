import pandas as pd, re

files = {
    'myg_all_store':    'myG All Store.xlsx',
    'rbm_bdm_branch':   'RBM,BDM,BRANCH.xlsx',
    'future_store_list':'Future Store List.xlsx',
}

def pg_col(name):
    s = re.sub(r'[^a-z0-9]+', '_', str(name).strip().lower()).strip('_')
    return s or 'col'

for tbl, fname in files.items():
    try:
        df = pd.read_excel(fname, nrows=3, dtype=str)
        cols = [pg_col(c) for c in df.columns]
        print(f"\n=== {tbl} ({fname}) ===")
        print(f"Rows (approx): {len(pd.read_excel(fname, dtype=str))}")
        print(f"Columns: {cols}")
    except Exception as e:
        print(f"\n=== {tbl} ({fname}) === ERROR: {e}")
