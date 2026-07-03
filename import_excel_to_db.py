"""
import_excel_to_db.py
---------------------
Reads every row from myG_OSG_Portal_Data1234.xlsx and upserts them
into the PostgreSQL `claims` table using the existing pg_sync service.

Run from the project root:
    python import_excel_to_db.py
"""

import os
import sys
import logging
import pandas as pd
from dotenv import load_dotenv

# ── Load .env so DATABASE_URL is available ───────────────────────────────────
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── Resolve paths ─────────────────────────────────────────────────────────────
BASE_DIR  = os.path.abspath(os.path.dirname(__file__))
EXCEL_PATH = os.path.join(BASE_DIR, "myG_OSG_Portal_Data1234.xlsx")

if not os.path.exists(EXCEL_PATH):
    logger.error(f"Excel file not found: {EXCEL_PATH}")
    sys.exit(1)

# ── Import upsert function ────────────────────────────────────────────────────
try:
    from services.pg_sync import upsert_claim_to_postgres, ensure_table_exists, _get_connection
except ImportError as e:
    logger.error(f"Cannot import pg_sync: {e}")
    sys.exit(1)

if not os.environ.get("DATABASE_URL"):
    logger.error("DATABASE_URL is not set in .env — cannot connect to PostgreSQL.")
    sys.exit(1)


def clean_value(val):
    """Convert NaN / NaT / None to None; everything else to string."""
    if val is None:
        return None
    s = str(val).strip()
    if s.lower() in ("nan", "nat", "none", ""):
        return None
    return s


def load_excel(path: str) -> pd.DataFrame:
    """Load the Excel file, using the first sheet."""
    logger.info(f"Loading Excel: {path}")
    df = pd.read_excel(path, sheet_name=0, dtype=str)
    # Strip whitespace from column headers
    df.columns = [str(c).strip() for c in df.columns]
    logger.info(f"  → {len(df)} rows | {len(df.columns)} columns")
    logger.info(f"  → Columns: {list(df.columns)}")
    return df


def run_import(df: pd.DataFrame):
    """Upsert every row in the DataFrame into PostgreSQL."""
    # Ensure the table exists before bulk insert
    try:
        conn = _get_connection()
        ensure_table_exists(conn)
        conn.close()
    except Exception as e:
        logger.error(f"Could not ensure table exists: {e}")
        sys.exit(1)

    total   = len(df)
    success = 0
    failed  = 0
    skipped = 0

    for i, row in df.iterrows():
        # Build a plain dict: {SheetHeader: value_or_None}
        claim_data = {col: clean_value(row[col]) for col in df.columns}

        # Determine the Claim ID column — try common names
        claim_id = (
            claim_data.get("Claim ID")
            or claim_data.get("claim_id")
            or claim_data.get("ClaimID")
            or claim_data.get("CLAIM ID")
        )

        if not claim_id:
            logger.warning(f"Row {i+2}: No Claim ID found — skipping. Row data: { {k:v for k,v in claim_data.items() if v} }")
            skipped += 1
            continue

        result = upsert_claim_to_postgres(claim_data)

        if result.get("success"):
            success += 1
            if success % 25 == 0 or success == 1:
                logger.info(f"  [{success}/{total}] Upserted claim_id={claim_id}")
        else:
            failed += 1
            logger.error(f"  Row {i+2} (claim_id={claim_id}) FAILED: {result.get('error')}")

    logger.info("=" * 60)
    logger.info(f"Import complete: {success} succeeded | {failed} failed | {skipped} skipped")
    logger.info("=" * 60)
    return success, failed, skipped


if __name__ == "__main__":
    df = load_excel(EXCEL_PATH)

    if df.empty:
        logger.warning("Excel file has no data rows. Nothing to import.")
        sys.exit(0)

    run_import(df)
