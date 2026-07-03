"""
import_osid_feb2026_full.py
----------------------------
Reads all rows from:
  Onsitego OSID updated upto FEB 2026.xlsx
and bulk-inserts them into a NEW PostgreSQL table: osid_data

Run from project root:
    python import_osid_feb2026_full.py
"""

import os
import sys
import re
import logging
import pandas as pd
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── Config ─────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.abspath(os.path.dirname(__file__))
EXCEL_PATH = os.path.join(BASE_DIR, "Onsitego OSID updated upto FEB 2026.xlsx")
TABLE_NAME = "osid_data"
SHEET_NAME = 0   # first sheet


# ── Helpers ────────────────────────────────────────────────────────────────
def pg_col(name: str) -> str:
    s = str(name).strip().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = s.strip("_")
    return s or "col"


def clean_value(val):
    if val is None:
        return None
    s = str(val).strip()
    if s.lower() in ("nan", "nat", "none", ""):
        return None
    return s


def get_connection():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        logger.error("DATABASE_URL not set in .env")
        sys.exit(1)
    return psycopg2.connect(db_url)


# ── Load Excel ──────────────────────────────────────────────────────────────
logger.info(f"Loading: {EXCEL_PATH}")
df = pd.read_excel(EXCEL_PATH, sheet_name=SHEET_NAME, dtype=str)
df.columns = [str(c).strip() for c in df.columns]
logger.info(f"  → {len(df)} rows | {len(df.columns)} columns")
logger.info(f"  → Columns: {list(df.columns)}")

# Build column map: original header → pg-safe name
col_map = {}
for c in df.columns:
    pg = pg_col(c)
    if pg in col_map.values():
        pg = pg + "_2"
    col_map[c] = pg

pg_cols = list(col_map.values())
logger.info(f"  → PG columns: {pg_cols}")


# ── Create table ────────────────────────────────────────────────────────────
def create_table(conn):
    col_defs = ",\n    ".join(f'"{c}" TEXT' for c in pg_cols)
    ddl = f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            id SERIAL PRIMARY KEY,
            {col_defs},
            imported_at TIMESTAMPTZ DEFAULT NOW()
        );
    """
    with conn.cursor() as cur:
        cur.execute(ddl)
    conn.commit()
    logger.info(f"[PG] Table `{TABLE_NAME}` ensured.")


# ── Bulk insert ─────────────────────────────────────────────────────────────
def bulk_insert(conn, df):
    rows = []
    for _, row in df.iterrows():
        rows.append(tuple(clean_value(row[orig]) for orig in col_map.keys()))

    col_identifiers = ", ".join(f'"{c}"' for c in pg_cols)
    placeholders    = ", ".join(["%s"] * len(pg_cols))
    sql = f'INSERT INTO {TABLE_NAME} ({col_identifiers}) VALUES ({placeholders})'

    total = len(rows)
    batch_size = 500
    inserted = 0

    with conn.cursor() as cur:
        for i in range(0, total, batch_size):
            batch = rows[i:i + batch_size]
            psycopg2.extras.execute_batch(cur, sql, batch, page_size=batch_size)
            inserted += len(batch)
            if inserted % 10000 == 0 or inserted == total:
                logger.info(f"  [{inserted}/{total}] rows inserted...")

    conn.commit()
    logger.info(f"[PG] Committed {inserted} rows into `{TABLE_NAME}`.")
    return inserted


# ── Main ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if df.empty:
        logger.warning("Excel has no data rows. Nothing to import.")
        sys.exit(0)

    conn = get_connection()
    try:
        create_table(conn)

        # Truncate if table already has rows (idempotent re-run)
        with conn.cursor() as cur:
            cur.execute(f"SELECT COUNT(*) FROM {TABLE_NAME};")
            existing = cur.fetchone()[0]
        if existing > 0:
            logger.info(f"Table already has {existing} rows — truncating before re-import...")
            with conn.cursor() as cur:
                cur.execute(f"TRUNCATE TABLE {TABLE_NAME} RESTART IDENTITY;")
            conn.commit()

        inserted = bulk_insert(conn, df)

        logger.info("=" * 60)
        logger.info(f"✅ Import complete: {inserted} rows in `{TABLE_NAME}`")
        logger.info("=" * 60)

    except Exception as e:
        conn.rollback()
        logger.error(f"Import failed: {e}", exc_info=True)
        sys.exit(1)
    finally:
        conn.close()
