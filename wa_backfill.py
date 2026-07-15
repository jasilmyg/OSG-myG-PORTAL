"""
wa_backfill.py
One-time script: sends WhatsApp notifications to all claims updated
on or after 2026-07-09 that haven't received a notification yet.

Usage:
  python wa_backfill.py --dry-run   # preview only, no messages sent
  python wa_backfill.py             # actually send messages
"""
import os, sys, time, datetime, logging
from dotenv import load_dotenv
load_dotenv()
import psycopg2
import psycopg2.extras

DRY_RUN = '--dry-run' in sys.argv
CUTOFF  = datetime.datetime(2026, 7, 9)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler('whatsapp_backfill_log.txt', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

# Notifiable statuses → (template_name, param_builder)
WA_TEMPLATES = {
    "REGISTERED":           ("myg_onsitego_registered_main",      lambda n, mo, sr: [n, mo, sr]),
    "REPAIR COMPLETED":     ("myg_onsitego_repair_completed_main", lambda n, mo, sr: [n, sr]),
    "REPLACEMENT APPROVED": ("myg_onsitego_replacement_main",      lambda n, mo, sr: [n, mo]),
    "REJECTED":             ("osg_clm_reject",                     lambda n, mo, sr: [n]),
}

def clean_mobile(raw):
    m = str(raw or '').strip()
    if '.' in m: m = m.split('.')[0]
    m = m.replace('+', '').replace(' ', '').replace('-', '')
    return m if len(m) >= 10 else ''

conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
conn.autocommit = False
cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

log.info(f"=== WA BACKFILL {'DRY RUN' if DRY_RUN else 'LIVE'} | Cutoff: {CUTOFF.date()} ===")

# Fetch all eligible claims
cur.execute("""
    SELECT claim_id, customer_name, mobile_number, status,
           date, last_notified_status, sr_no, model
    FROM claims
    WHERE date >= %s
    AND UPPER(TRIM(status)) = ANY(%s)
    ORDER BY date ASC
""", (CUTOFF.date().isoformat(), list(WA_TEMPLATES.keys())))

rows = cur.fetchall()
log.info(f"Total claims from {CUTOFF.date()} with notifiable status: {len(rows)}")

sent = 0; skipped_notified = 0; skipped_mobile = 0; failed = 0

for row in rows:
    claim_id    = row['claim_id']
    cust        = (row['customer_name'] or 'Customer').strip()
    mobile_raw  = row['mobile_number']
    status_up   = (row['status'] or '').strip().upper()
    last_notif  = (row['last_notified_status'] or '').strip().upper()
    sr_no       = (row['sr_no'] or claim_id).strip()
    model       = (row['model'] or 'your product').strip()

    # Skip if already notified for this status
    if last_notif == status_up:
        log.info(f"[SKIP_NOTIFIED] {claim_id} | status={status_up} already notified")
        skipped_notified += 1
        continue

    # Validate mobile
    mobile = clean_mobile(mobile_raw)
    if not mobile:
        log.warning(f"[SKIP_MOBILE] {claim_id} | invalid mobile='{mobile_raw}'")
        skipped_mobile += 1
        continue

    template_name, param_fn = WA_TEMPLATES[status_up]
    params = param_fn(cust, model, sr_no)

    log.info(f"[{'DRY' if DRY_RUN else 'SEND'}] {claim_id} | {status_up} | {mobile} | {template_name} | {params}")

    if DRY_RUN:
        sent += 1
        continue

    # === LIVE SEND ===
    try:
        from services.whatsapp_service import send_whatsapp_message
        resp = send_whatsapp_message(mobile=mobile, template_name=template_name, params=params)
        log.info(f"[RESP] {claim_id} | {resp}")

        if not resp.get('blocked') and resp.get('status_code') in [200, 201, 202]:
            # Update last_notified_status and last_notified_at in DB
            cur.execute("""
                UPDATE claims
                SET last_notified_status = %s,
                    last_notified_at     = %s
                WHERE claim_id = %s
            """, (status_up, datetime.datetime.utcnow(), claim_id))
            conn.commit()
            log.info(f"[DB_UPDATED] {claim_id} | last_notified_status={status_up}")
            sent += 1
        else:
            log.warning(f"[SEND_FAILED] {claim_id} | resp={resp}")
            failed += 1

        time.sleep(1)  # Rate limit: 1 msg/sec

    except Exception as e:
        log.error(f"[ERROR] {claim_id} | {e}")
        failed += 1

log.info(f"""
=== BACKFILL COMPLETE ===
  Sent / Queued    : {sent}
  Skipped (already): {skipped_notified}
  Skipped (mobile) : {skipped_mobile}
  Failed           : {failed}
  Mode             : {'DRY RUN - no messages sent' if DRY_RUN else 'LIVE'}
""")

cur.close()
conn.close()
