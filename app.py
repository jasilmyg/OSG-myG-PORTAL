import os
import time
import datetime
import pytz
import pandas as pd
import requests
import smtplib
from functools import wraps
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

# ----------------------
# CONFIG
# ----------------------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
EXCEL_FILE = os.path.join(BASE_DIR, "Onsitego OSID (1).xlsx")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
DB_FILE = os.path.join(BASE_DIR, "claims.db")

# Email Config
TARGET_EMAIL = "mygloyalty3@gmail.com"
CC_EMAILS = ["arjunpm@myg.in"]
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "jasil@myg.in"
SENDER_PASSWORD = "vurw qnwv ynys xkrf"
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbxiAe_F3lcG9kNyvcbYcETC8Rc4ZZ3O-o3CdgPfmbjpQj8_cby9FMP9f33M1LenQ006VA/exec"

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'osg_myg_secret_key_2025'  # Required for session
app.permanent_session_lifetime = datetime.timedelta(hours=24) # 24 hour session expiry

db = SQLAlchemy(app)

# ----------------------
# AUTHENTICATION
# ----------------------
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "password123"

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_logged_in' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session.permanent = True  # Enable permanent session (24h)
            session['user_logged_in'] = True
            session['username'] = username
            flash('Login successful!', 'success')
            
            # Redirect to next page if it exists
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_logged_in', None)
    session.pop('username', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# ----------------------
# DATA MODEL (Wrapper)
# ----------------------
class ClaimWrapper:
    """Wraps dictionary data from Google Sheet to provide object-like access for templates"""
    def __init__(self, data):
        self.data = data
    
    def get(self, key, default=None):
        return self.data.get(key, default)
    
    # Generic access
    def __getattr__(self, name):
        # Map pythonic names to Sheet Headers
        # If specific logic needed, add property
        return self.data.get(name, self.data.get(name.replace('_', ' ').title(), None))

    # Properties matching the old SQLAlchemy model for template compatibility
    @property
    def id(self): return self.data.get("Claim ID") # Use Claim ID as ID
    @property
    def claim_id(self): return self.data.get("Claim ID")
    @property
    def created_at(self): 
        # Parse date string
        d = self.data.get("Date")
        if not d: return datetime.datetime.now()
        s = str(d).strip()
        
        # Try multiple date formats
        formats_to_try = [
            '%Y-%m-%d %H:%M:%S',  # 2025-12-17 10:30:00
            '%Y-%m-%d',           # 2025-12-17
            '%d-%m-%Y',           # 17-12-2025
            '%d/%m/%Y',           # 17/12/2025
            '%m/%d/%Y',           # 12/17/2025
        ]
        
        for fmt in formats_to_try:
            try:
                if fmt == '%Y-%m-%d %H:%M:%S':
                    return datetime.datetime.strptime(s[:19], fmt)
                else:
                    return datetime.datetime.strptime(s[:10], fmt)
            except:
                continue
        
        # If all parsing fails, return current time
        return datetime.datetime.now()

    @property
    def customer_name(self): return self.data.get("Customer Name")
    @property
    def mobile_no(self): return self.data.get("Mobile Number")
    @property
    def address(self): return self.data.get("Address")
    @property
    def invoice_no(self): return self.data.get("Invoice Number")
    @property
    def serial_no(self): return self.data.get("Serial Number")
    @property
    def model(self): return self.data.get("Model")
    @property
    def osid(self): return self.data.get("OSID")
    @property
    def issue(self): return self.data.get("Issue")
    @property
    def branch(self): return self.data.get("Branch")
    
    # Workflow
    @property
    def follow_up_date(self): return self.data.get("Follow Up - Dates")
    @property
    def follow_up_notes(self): return self.data.get("Follow Up - Notes")
    @property
    def claim_settled_date(self): return self.data.get("Claim Settled Date")
    @property
    def remarks(self): return self.data.get("Remarks")
    @property
    def status(self): return self.data.get("Status")
    
    # Booleans (Sheet has "Yes"/"No" or empty)
    def _bool(self, key):
        val = self.data.get(key, "")
        return str(val).lower() == "yes"

    @property
    def repair_feedback_completed(self): return self._bool("Repair Feedback Completed (Yes/No)")

    @property
    def cust_confirmation_pending(self): 
        return self._bool("Replacement: Confirmation Pending") or self._bool("Confirmation Pending From Customer (Yes/No)")
    
    @property
    def approval_mail_received(self): 
        return self._bool("Replacement: OSG Approval") or self._bool("Approval Mail Received From Onsitego (Yes/No)")
    
    @property
    def mail_sent_to_store(self): 
        return self._bool("Replacement: Mail to Store") or self._bool("Mail Sent To Store (Yes/No)")
    
    @property
    def invoice_generated(self): 
        return self._bool("Replacement: Invoice Generated") or self._bool("Invoice Generated (Yes/No)")
    
    @property
    def invoice_sent_osg(self): 
        return self._bool("Replacement: Invoice Sent to OSG") or self._bool("Invoice Sent To Onsitego (Yes/No)")
    
    @property
    def settled_with_accounts(self): 
        return self._bool("Replacement: Settled with Accounts") or self._bool("Settled With Accounts (Yes/No)")
    
    @property
    def complete(self): 
        return self._bool("Complete") or self._bool("Complete (Yes/No)")

    @property
    def assigned_staff(self): return self.data.get("Assigned Staff")
    
    @property
    def tat(self): return self.data.get("Settled Time (TAT)")
    
# ----------------------
# HELPER FUNCTIONS
# ----------------------
CLAIMS_CACHE = {
    'data': [],
    'last_updated': 0
}
CACHE_DURATION = 120  # 2 minutes cache

def get_ist_now():
    return datetime.datetime.now(pytz.timezone('Asia/Kolkata'))

def invalidate_cache():
    global CLAIMS_CACHE
    print("Invalidating Cache...")
    CLAIMS_CACHE['last_updated'] = 0

def fetch_claims_from_sheet(force_refresh=False):
    global CLAIMS_CACHE
    
    current_time = time.time()
    if not force_refresh and (current_time - CLAIMS_CACHE['last_updated'] < CACHE_DURATION) and CLAIMS_CACHE['data']:
        print("Using Cached Data")
        return CLAIMS_CACHE['data']

    try:
        print("Fetching Fresh Data from Google Sheets...")
        if not WEB_APP_URL: return []
        resp = requests.get(WEB_APP_URL, timeout=10)
        print(f"Fetch Status: {resp.status_code}") 
        if resp.status_code == 200:
            try:
                data = resp.json()
            except:
                print(f"JSON Decode Error. Raw: {resp.text[:500]}")
                return []
            
            if isinstance(data, list):
                # Convert list of dicts to list of Wrappers
                claims = [ClaimWrapper(d) for d in data]
                # Sort by Date desc
                sorted_claims = sorted(claims, key=lambda x: x.created_at, reverse=True)
                
                # Update Cache
                CLAIMS_CACHE['data'] = sorted_claims
                CLAIMS_CACHE['last_updated'] = current_time
                
                return sorted_claims
        return []
    except Exception as e:
        print(f"Fetch Error: {e}")
        # Return stale cache if fetch fails
        if CLAIMS_CACHE['data']:
            print("Fetch failed, returning stale cache")
            return CLAIMS_CACHE['data']
        return []

# ... (Reuse load_excel_data, lookup_customer, email logic here) ...
# I will NOT rewrite them in this replacement block to save space, assuming they persist if I don't overwrite effectively.
# Wait, I am overwriting the DB Model and Routes. I need to keep the other helpers.
# The tool 'replace_file_content' replaces a block. I need to be careful.
# I will target lines 32 -> end.

# ----------------------
# ROUTES
# ----------------------
@app.route('/')
@login_required
def dashboard():
    refresh = request.args.get('refresh') == 'true'
    claims = fetch_claims_from_sheet(force_refresh=refresh)
    
    total = len(claims)
    pending = len([c for c in claims if not c.complete])
    completed = len([c for c in claims if c.complete])
    
    return render_template('dashboard.html', claims=claims, total=total, pending=pending, completed=completed)

 

# ...


# ----------------------
# HELPER FUNCTIONS
# ----------------------
def get_ist_now():
    return datetime.datetime.now(pytz.timezone('Asia/Kolkata'))

# Global Cache
CACHED_DF = None
LAST_MOD_TIME = 0
CACHE_FILE = os.path.join(BASE_DIR, "cache.pkl")

def load_excel_data():
    global CACHED_DF, LAST_MOD_TIME
    try:
        if not os.path.exists(EXCEL_FILE):
            return pd.DataFrame()
            
        current_mtime = os.path.getmtime(EXCEL_FILE)
        
        # 1. In-Memory
        if CACHED_DF is not None and current_mtime == LAST_MOD_TIME:
            return CACHED_DF

        # 2. Pickle Cache (Disk)
        if os.path.exists(CACHE_FILE):
            if os.path.getmtime(CACHE_FILE) >= current_mtime:
                try:
                    # Fast load
                    df = pd.read_pickle(CACHE_FILE)
                    CACHED_DF = df
                    LAST_MOD_TIME = current_mtime
                    return df
                except:
                    pass

        # 3. Fresh Load
        print("Loading Excel...")
        df = pd.read_excel(EXCEL_FILE)
        
        # Normalize
        df.columns = (
            df.columns.astype(str)
            .str.strip()
            .str.replace("\u00A0", " ")
            .str.lower()
            .str.replace(r"\s+", " ", regex=True)
        )
        
        # Optimized Mobile Column
        mob_col = None
        candidates = ["mobile no", "mobile", "mobile_no", "mobile no rf", "mob", "phoneno", "phone", "contact"]
        for v in candidates:
            if v in df.columns:
                mob_col = v
                break
        
        if not mob_col:
            for c in df.columns:
                if "mobile" in c or "phone" in c:
                    mob_col = c
                    break

        if mob_col:
            df['target_mobile_str'] = (
                df[mob_col]
                .fillna('')
                .astype(str)
                .str.replace(r'\.0$', '', regex=True)
                .str.strip()
            )
            
        # Save Cache
        df.to_pickle(CACHE_FILE)
        CACHED_DF = df
        LAST_MOD_TIME = current_mtime
        return df

    except Exception as e:
        print(f"Excel Load Error: {e}")
        return pd.DataFrame()

def col_lookup(df, variations):
    for v in variations:
        if v in df.columns:
            return v
    return None

@app.route('/lookup-customer', methods=['POST'])
@login_required
def lookup_customer():
    data = request.json
    mobile = data.get('mobile', '').strip()
    
    if not mobile or len(mobile) != 10:
        return jsonify({"success": False, "message": "Invalid Number"})

    df = load_excel_data()
    if df.empty:
        return jsonify({"success": False, "message": "Data Source Unavailable"})

    # Search
    if 'target_mobile_str' in df.columns:
        matches = df[df['target_mobile_str'] == mobile]
    else:
        # Fallback
        mob_col = col_lookup(df, ["mobile no", "mobile", "mobile_no"])
        if not mob_col:
             return jsonify({"success": False, "message": "Mobile Column Not Found"})
        matches = df[df[mob_col].astype(str).str.strip() == mobile]

    if matches.empty:
        return jsonify({"success": False, "message": "No Customer Found"})
    
    customer_name = matches.iloc[0].get(col_lookup(df, ["customer", "customer name"]), "Unknown")
    
    products = []
    inv_col = col_lookup(df, ["invoice no", "invoice", "invoice_no"])
    mod_col = col_lookup(df, ["model"])
    ser_col = col_lookup(df, ["serial no", "serialno", "serial_no"])
    osid_col = col_lookup(df, ["osid"])
    branch_col = col_lookup(df, ["store name", "store_name", "branch", "branch name"])

    for idx, row in matches.iterrows():
        products.append({
            "idx": idx, 
            "invoice": str(row.get(inv_col, "")),
            "model": str(row.get(mod_col, "")),
            "serial": str(row.get(ser_col, "")),
            "osid": str(row.get(osid_col, "")),
            "branch": str(row.get(branch_col, "Main Branch")), 
            "display": f"{row.get(mod_col, '')} (OSID: {row.get(osid_col, '')})"
        })

    return jsonify({
        "success": True, 
        "customer_name": str(customer_name),
        "products": products
    })
def send_email_notification(claim_data, files=None):
    try:
        msg = MIMEMultipart()
        msg["From"] = SENDER_EMAIL
        msg["To"] = TARGET_EMAIL
        msg["Cc"] = ", ".join(CC_EMAILS)
        msg["Subject"] = f"🛡️ Warranty Claim Submission – OSID: {claim_data.get('osid', 'N/A')} – {claim_data.get('customer_name', 'Unknown')}"
        
        body = f"""
        <html><body>
        <div style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #2E86C1 0%, #5DADE2 100%); color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0;">
                <h2 style="margin: 0;">🛡️ Warranty Claim Submission</h2>
                <p style="margin: 5px 0 0 0;">New claim received from customer</p>
            </div>
            <div style="background: #f8f9fa; padding: 20px; border-radius: 0 0 10px 10px;">
                <p>Dear Team,</p>
                <div style="background: white; padding: 15px; border-radius: 8px; margin: 12px 0; border-left: 4px solid #2E86C1;">
                    <h3 style="color: #2E86C1; margin-top: 0;">👤 Customer Information</h3>
                    <p><strong>Name:</strong> {claim_data.get('customer_name')}<br>
                    <strong>Mobile No:</strong> {claim_data.get('mobile_no')}<br>
                    <strong>Address:</strong> {claim_data.get('address')}</p>
                </div>
                <div style="background: white; padding: 15px; border-radius: 8px; margin: 12px 0; border-left: 4px solid #28A745;">
                    <h3 style="color: #28A745; margin-top: 0;">📦 Product Details & Issue</h3>
                    <p><strong>Model:</strong> {claim_data.get('model')}<br>
                    <strong>Serial:</strong> {claim_data.get('serial_no')}<br>
                    <strong>OSID:</strong> {claim_data.get('osid')}<br>
                    <strong>Invoice:</strong> {claim_data.get('invoice_no')}<br>
                    <strong>Issue:</strong> {claim_data.get('issue')}</p>
                </div>
                <div style="background: #e7f3ff; padding: 12px; border-radius: 8px; margin: 12px 0;">
                    <p><strong>📅 Submitted:</strong> {get_ist_now().strftime('%Y-%m-%d %H:%M:%S IST')}</p>
                </div>
            </div>
        </div>
        </body></html>
        """
        msg.attach(MIMEText(body, "html"))

        if files:
            for f in files:
                try:
                    with open(f, "rb") as fil:
                        part = MIMEApplication(fil.read(), Name=os.path.basename(f))
                        part['Content-Disposition'] = f'attachment; filename="{os.path.basename(f)}"'
                        msg.attach(part)
                except Exception as e:
                    print(f"Failed to attach file: {e}")

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, [TARGET_EMAIL] + CC_EMAILS, msg.as_string())
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False

# ----------------------
# ROUTES
# ----------------------





@app.route('/submit-claim', methods=['GET', 'POST'])
@login_required
def submit_claim():
    if request.method == 'GET':
        return render_template('submit.html')
    
    # Handle POST
    try:
        data = request.form
        customer_name = data.get('customer_name')
        mobile = data.get('mobile')
        address = data.get('address')
        
        claims_json = data.get('claims_data')
        if not claims_json:
            # Fallback for old requests? Or just Error.
            # If standard flow used old 'selected_product', we could support it, 
            # but we updated frontend so assuming data comes as claims_data.
            # Let's check if 'selected_product' exists just in case of cached frontend.
            if data.get('selected_product'):
                import json
                # Convert old format to list
                prod = json.loads(data.get('selected_product'))
                prod['issue'] = data.get('issue')
                prod['file_key'] = 'files' # Old file key
                claims_json = json.dumps([prod])
            else:
                 return jsonify({"success": False, "message": "No claims data received"})
            
        import json
        claims_list = json.loads(claims_json)
        
        results = []
        
        # Ensure upload folder exists
        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER)
        
        for idx, item in enumerate(claims_list):
            # Files
            file_key = item.get('file_key')
            uploaded_files = request.files.getlist(file_key) if file_key else []
            # Check fallback for old frontend
            if not uploaded_files and file_key == 'files':
                 uploaded_files = request.files.getlist('files')

            saved_paths = []
            
            for f in uploaded_files:
                if f.filename:
                    # Unique filename
                    fn = secure_filename(f"{int(time.time())}_{idx}_{f.filename}")
                    path = os.path.join(UPLOAD_FOLDER, fn)
                    f.save(path)
                    saved_paths.append(path)

            # Claim Object
            # Ensure unique ID slightly if processing fast
            unique_suffix = int(time.time()) + idx
            new_claim = {
                "Claim ID": f"CLM-{unique_suffix}",
                "Date": get_ist_now().strftime('%Y-%m-%d'),
                "Customer Name": customer_name,
                "Mobile Number": mobile,
                "Address": address,
                "Product": item.get('model', ''),
                "Invoice Number": item.get('invoice', ''),
                "Serial Number": item.get('serial', ''),
                "Model": item.get('model', ''),
                "OSID": item.get('osid', ''),
                "Branch": item.get('branch', 'Main Branch'),
                "Issue": item.get('issue', ''),
                "Status": "Submitted"
            }
            
            # Sync
            print(f"Syncing Claim {idx+1}/{len(claims_list)}: {new_claim['Claim ID']}")
            sync_to_google_sheet_dict(new_claim)
            
            # Email
            send_email_notification({
                "customer_name": customer_name,
                "mobile_no": mobile,
                "address": address,
                "model": item.get('model'),
                "serial_no": item.get('serial'),
                "osid": item.get('osid'),
                "invoice_no": item.get('invoice'),
                "issue": item.get('issue')
            }, saved_paths)
            
            results.append(new_claim["Claim ID"])
            
            # Delay to be polite to Google Script API if needed
            time.sleep(0.5)

        invalidate_cache()
        return jsonify({"success": True, "message": f"Successfully submitted {len(results)} claim(s)!"})

    except Exception as e:
        print(f"Submit Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": str(e)})

@app.route('/claim/<string:id>', methods=['GET']) # Using String ID now
@login_required
def get_claim(id):
    # Fetch all and filter (inefficient but works for small-medium sheets)
    claims = fetch_claims_from_sheet()
    
    # Find claim by Claim ID (id) or numeric ID? User passes int ID earlier, but now strings CLM-...
    # Let's support both if possible or just filter by Claim ID
    
    found = None
    for c in claims:
        # Check against "Claim ID"
        if str(c.claim_id) == str(id):
            found = c
            break
            
    if not found:
        return jsonify({"error": "Not found"}), 404

    # Convert Wrapper to dict for frontend
    # We need to map back to the keys JS expects
    
    # Helper to parse boolean values
    def parse_bool(val):
        if val is None or val == '':
            return False
        return str(val).strip().lower() in ['yes', 'true', '1']
    
    return jsonify({
        "id": found.claim_id,
        "date": found.created_at.strftime('%Y-%m-%d'),
        "customer_name": found.customer_name,
        "status": found.status,
        "follow_up_date": found.follow_up_date or "",
        "follow_up_notes": found.follow_up_notes or "",
        "remarks": found.remarks or "",
        "repair_feedback_completed": found.repair_feedback_completed,
        
        # Replacement workflow fields (Columns O-T)
        "replacement_confirmation": parse_bool(found.data.get("Confirmation Pending From Customer (Yes/No)")),
        "replacement_osg_approval": parse_bool(found.data.get("Approval Mail Received From Onsitego (Yes/No)")),
        "replacement_mail_store": parse_bool(found.data.get("Mail Sent To Store (Yes/No)")),
        "replacement_invoice_gen": parse_bool(found.data.get("Invoice Generated (Yes/No)")),
        "replacement_invoice_sent": parse_bool(found.data.get("Invoice Sent To Onsitego (Yes/No)")),
        "replacement_settled_accounts": parse_bool(found.data.get("Settled With Accounts (Yes/No)")),
        
        # Complete flag
        "complete": parse_bool(found.data.get("Complete (Yes/No)")),
        
        "tat": found.tat,
        "assigned_staff": found.assigned_staff or ""
    })

@app.route('/update-claim/<string:id>', methods=['POST'])
@login_required
def update_claim(id):
    # Fetch existing to preserve other fields?
    # Actually, we can just send the PATCH data + ID to Google ID upsert
    data = request.json
    
    # Map JS keys back to Sheet Headers
    payload = {
        "Claim ID": id
    }
    
    if 'status' in data: payload["Status"] = data['status']
    if 'date' in data: payload["Date"] = data['date']
    if 'follow_up_notes' in data: payload["Follow Up - Notes"] = data['follow_up_notes']
    if 'remarks' in data: payload["Remarks"] = data['remarks']
    if 'assigned_staff' in data: payload["Assigned Staff"] = data['assigned_staff']
    
    if 'follow_up_date' in data: payload["Follow Up - Dates"] = data['follow_up_date']
    if 'approval_mail_date' in data: payload["Approval Mail Received Date"] = data['approval_mail_date']
    if 'mail_sent_to_store_date' in data: payload["Mail Sent To Store Date"] = data['mail_sent_to_store_date']
    if 'invoice_generated_date' in data: payload["Invoice Generated Date"] = data['invoice_generated_date']
    if 'invoice_sent_osg_date' in data: payload["Invoice Sent To Onsitego Date"] = data['invoice_sent_osg_date']
    if 'claim_settled_date' in data: payload["Claim Settled Date"] = data['claim_settled_date']

    def fmt_bool(val): return "Yes" if val else "No"
    
    if 'repair_feedback_completed' in data: payload["Repair Feedback Completed (Yes/No)"] = fmt_bool(data['repair_feedback_completed'])
    
    # Replacement workflow fields (Columns O-T) - Updated to new Sheet Headers
    if 'replacement_confirmation' in data: payload["Replacement: Confirmation Pending"] = fmt_bool(data['replacement_confirmation'])
    if 'replacement_osg_approval' in data: payload["Replacement: OSG Approval"] = fmt_bool(data['replacement_osg_approval'])
    if 'replacement_mail_store' in data: payload["Replacement: Mail to Store"] = fmt_bool(data['replacement_mail_store'])
    if 'replacement_invoice_gen' in data: payload["Replacement: Invoice Generated"] = fmt_bool(data['replacement_invoice_gen'])
    if 'replacement_invoice_sent' in data: payload["Replacement: Invoice Sent to OSG"] = fmt_bool(data['replacement_invoice_sent'])
    if 'replacement_settled_accounts' in data: payload["Replacement: Settled with Accounts"] = fmt_bool(data['replacement_settled_accounts'])
    
    # Complete flag
    if 'complete' in data: payload["Complete"] = fmt_bool(data['complete'])

    # CRITICAL: If status is 'Repair Completed', clear all Replacement Workflow data
    if payload.get("Status") == "Repair Completed":
        payload["Replacement: Confirmation Pending"] = ""
        payload["Replacement: OSG Approval"] = ""
        payload["Replacement: Mail to Store"] = ""
        payload["Replacement: Invoice Generated"] = ""
        payload["Replacement: Invoice Sent to OSG"] = ""
        payload["Replacement: Settled with Accounts"] = ""

    # Sync
    try:
        sync_to_google_sheet_dict(payload)
    except Exception as e:
        print(f"Update Sync Error: {e}")
        return jsonify({"success": False})

    return jsonify({"success": True})

def sync_to_google_sheet_dict(payload):
    """
    Sends dict payload to Google Sheet.
    Keys must match headers exactly or normalized logic in GAS.
    """
    if not WEB_APP_URL:
        return
        
    # Auto-add timestamp
    payload["Last Updated Timestamp"] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
        response = requests.post(WEB_APP_URL, json=payload, timeout=10)
        print(f"Sync Status: {response.status_code}, Response: {response.text}")
    except Exception as e:
        print(f"Google Sheet Sync Failed: {e}")
        raise e

# ----------------------
# DEBUG ENDPOINT
# ----------------------
@app.route('/debug/sheet-columns')
def debug_sheet_columns():
    """Debug endpoint to see actual column names and sample data"""
    try:
        claims = fetch_claims_from_sheet()
        if len(claims) > 0:
            first_claim = claims[0]
            return jsonify({
                'success': True,
                'sample_claim_id': first_claim.claim_id,
                'all_columns': list(first_claim.data.keys()),
                'replacement_columns': {
                    'Replacement: Confirmation Pending': first_claim.data.get('Replacement: Confirmation Pending'),
                    'Replacement: OSG Approval': first_claim.data.get('Replacement: OSG Approval'),
                    'Replacement: Mail to Store': first_claim.data.get('Replacement: Mail to Store'),
                    'Replacement: Invoice Generated': first_claim.data.get('Replacement: Invoice Generated'),
                    'Replacement: Invoice Sent to OSG': first_claim.data.get('Replacement: Invoice Sent to OSG'),
                    'Replacement: Settled with Accounts': first_claim.data.get('Replacement: Settled with Accounts'),
                    'Complete': first_claim.data.get('Complete')
                }
            })
        return jsonify({'success': False, 'message': 'No claims found'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# ----------------------
# ANALYTICS ROUTES
# ----------------------
@app.route('/analytics')
@login_required
def analytics_dashboard():
    return render_template('analytics.html')

@app.route('/api/analytics-data')
@login_required
def get_analytics_data():
    """
    Fetch and transform claims data for analytics dashboard
    Returns structured JSON with all necessary fields
    """
    try:
        claims = fetch_claims_from_sheet()
        
        # Transform claims for analytics
        analytics_claims = []
        for claim in claims:
            # Calculate TAT if settled
            tat = None
            if claim.claim_settled_date and (claim.data.get("Date") or claim.data.get("Submitted Date")):
                try:
                    s_date = claim.data.get("Date") or claim.data.get("Submitted Date")
                    submitted = datetime.datetime.strptime(str(s_date).split()[0], '%Y-%m-%d')
                    settled = datetime.datetime.strptime(str(claim.claim_settled_date).split()[0], '%Y-%m-%d')
                    tat = (settled - submitted).days
                except:
                    tat = None
            
            # Get replacement workflow fields
            def parse_bool(val):
                if val is None or val == '':
                    return False
                return str(val).strip().lower() in ['yes', 'true', '1']
            
            
            # Format mobile number to ensure it's a clean string
            mobile_raw = claim.mobile_no or ''
            if mobile_raw:
                # Convert to string and remove decimal points (e.g., "8589852744.0" -> "8589852744")
                mobile_str = str(mobile_raw).strip()
                if '.' in mobile_str:
                    mobile_str = mobile_str.split('.')[0]
                mobile_formatted = mobile_str
            else:
                mobile_formatted = ''
            
            analytics_claims.append({
                'claim_id': claim.claim_id or '',
                'submitted_date': str(claim.data.get("Date") or claim.data.get("Submitted Date", '')).split()[0] if (claim.data.get("Date") or claim.data.get("Submitted Date")) else '',
                'customer_name': claim.customer_name or '',
                'mobile_number': mobile_formatted,
                'address': claim.address or '',
                'branch': claim.data.get("Branch") or claim.data.get("Branch Name") or 'Main Branch',
                'product': claim.data.get("Product", claim.model) or '',
                'model': claim.model or '',
                'invoice_number': claim.invoice_no or '',
                'serial_number': claim.serial_no or '',
                'osid': claim.osid or '',
                'issue': claim.issue or '',
                'status': claim.status or 'Unknown',
                'remarks': claim.remarks or '',
                'claim_settled_date': claim.claim_settled_date or '',
                'tat': tat,
                
                # Replacement workflow fields (Columns O-T)
                'replacement_confirmation': parse_bool(claim.data.get("Confirmation Pending From Customer (Yes/No)")),
                'replacement_osg_approval': parse_bool(claim.data.get("Approval Mail Received From Onsitego (Yes/No)")),
                'replacement_mail_store': parse_bool(claim.data.get("Mail Sent To Store (Yes/No)")),
                'replacement_invoice_gen': parse_bool(claim.data.get("Invoice Generated (Yes/No)")),
                'replacement_invoice_sent': parse_bool(claim.data.get("Invoice Sent To Onsitego (Yes/No)")),
                'replacement_settled_accounts': parse_bool(claim.data.get("Settled With Accounts (Yes/No)")),
                
                # Complete flag
                'complete': parse_bool(claim.data.get("Complete (Yes/No)"))
            })
        
        return jsonify({
            'success': True,
            'claims': analytics_claims,
            'total': len(analytics_claims)
        })
        
    except Exception as e:
        print(f"Analytics data error: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'claims': []
        })


if __name__ == '__main__':
    app.run(debug=True, port=5000)
