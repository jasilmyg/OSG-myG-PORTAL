"""
import_osid_feb2026.py
----------------------
Reads all rows from:
  MYG India Pvt Ltd report for FEBRUARY 2026_FINAL_OSID (2).xlsx
and bulk-inserts them into a NEW PostgreSQL table: osid_feb2026

Columns auto-derived from Excel headers (converted to safe PG names).
Run from project root:
    python import_osid_feb2026.py
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
EXCEL_PATH = os.path.join(BASE_DIR, "MYG India Pvt Ltd report for FEBRUARY 2026_FINAL_OSID (2).xlsx")
TABLE_NAME = "osid_feb2026"
SHEET_NAME = "FEB 2026 UPDATED"


# ── Helpers ────────────────────────────────────────────────────────────────
def pg_col(name: str) -> str:
    """Convert column header to safe PostgreSQL identifier."""
    s = str(name).strip().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)   # replace any non-alphanumeric runs with _
    s = s.strip("_")
    return s or "col"


def clean_value(val):
    """Return None for blank/NaN; str for everything else."""
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
    # deduplicate if two headers normalise to same pg name
    if pg in col_map.values():
        pg = pg + "_2"
    col_map[c] = pg

pg_cols = list(col_map.values())
logger.info(f"  → PG column names: {pg_cols}")


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
    # Prepare rows as list of tuples (preserving column order)
    rows = []
    for _, row in df.iterrows():
        rows.append(tuple(clean_value(row[orig]) for orig in col_map.keys()))

    col_identifiers = ", ".join(f'"{c}"' for c in pg_cols)
    placeholders    = ", ".join(["%s"] * len(pg_cols))
    sql = f'INSERT INTO {TABLE_NAME} ({col_identifiers}) VALUES ({placeholders})'

    with conn.cursor() as cur:
        psycopg2.extras.execute_batch(cur, sql, rows, page_size=100)
    conn.commit()
    logger.info(f"[PG] Inserted {len(rows)} rows into `{TABLE_NAME}`.")
    return len(rows)


# ── Main ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if df.empty:
        logger.warning("Excel has no data rows. Nothing to import.")
        sys.exit(0)

    conn = get_connection()
    try:
        create_table(conn)

        # Optional: clear existing rows before re-import (idempotent re-run)
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
        logger.info(f"✅ Import complete: {inserted} rows inserted into `{TABLE_NAME}`")
        logger.info("=" * 60)

    except Exception as e:
        conn.rollback()
        logger.error(f"Import failed: {e}", exc_info=True)
        sys.exit(1)
    finally:
        conn.close()
