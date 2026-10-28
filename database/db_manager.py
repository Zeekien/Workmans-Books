import os
import sqlite3

# Support both WORKMANS_BOOKS_DB_FILE and legacy MIKE_APP_DB_FILE
DB_FILE = os.environ.get("WORKMANS_BOOKS_DB_FILE", os.environ.get("MIKE_APP_DB_FILE", "main.db"))

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT,
            phone TEXT,
            email TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER,
            title TEXT NOT NULL,
            status TEXT,
            job_date TEXT,
            details TEXT,
            hours_estimate REAL,
            cost_estimate REAL,
            final_hours REAL,
            final_cost REAL,
            addons TEXT,
            FOREIGN KEY (client_id) REFERENCES clients (id)
        )
    """)

    # Check for missing columns and add them if they don't exist (Migration)
    cursor.execute("PRAGMA table_info(jobs)")
    existing_columns = [col[1] for col in cursor.fetchall()]

    new_columns = [
        ("hours_estimate", "REAL"),
        ("cost_estimate", "REAL"),
        ("final_hours", "REAL"),
        ("final_cost", "REAL"),
        ("addons", "TEXT")
    ]

    for col_name, col_type in new_columns:
        if col_name not in existing_columns:
            cursor.execute(f"ALTER TABLE jobs ADD COLUMN {col_name} {col_type}")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL,
            client_id INTEGER NOT NULL,
            job_title TEXT NOT NULL,
            hours REAL,
            cost REAL,
            created_date TEXT,
            job_date TEXT,
            FOREIGN KEY (job_id) REFERENCES jobs (id),
            FOREIGN KEY (client_id) REFERENCES clients (id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quickbooks_config (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            environment TEXT DEFAULT 'SANDBOX',
            client_id TEXT,
            client_secret TEXT,
            redirect_uri TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quickbooks_tokens (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            realm_id TEXT,
            access_token TEXT,
            refresh_token TEXT,
            expires_at REAL
        )
    """)
    
    conn.commit()
    conn.close()

def fetch_all_clients(search_query=""):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    if search_query:
        q = f"%{search_query}%"
        cursor.execute("""
            SELECT id, name, address, phone, email 
            FROM clients 
            WHERE name LIKE ? OR address LIKE ? OR phone LIKE ? OR email LIKE ?
        """, (q, q, q, q))
    else:
        cursor.execute("SELECT id, name, address, phone, email FROM clients")
    rows = cursor.fetchall()
    conn.close()
    return rows

def fetch_jobs_for_date(date_str):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT j.id, j.title, j.status, j.details, j.client_id,
               c.name, c.phone, c.address
        FROM jobs j
        LEFT JOIN clients c ON j.client_id = c.id
        WHERE j.job_date = ?
    """, (date_str,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def fetch_unscheduled_jobs():
    """Fetch all unscheduled jobs (no date assigned)"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT j.id, j.title, j.status, j.details, 
               c.name, c.phone, c.address
        FROM jobs j
        LEFT JOIN clients c ON j.client_id = c.id
        WHERE j.job_date IS NULL OR j.job_date = '' OR j.job_date = 'None'
        ORDER BY j.id DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows

def fetch_past_scheduled_jobs():
    """Fetch all jobs with dates in the past and status='Scheduled'"""
    from datetime import datetime
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    today = datetime.now().strftime("%Y-%m-%d")
    
    cursor.execute("""
        SELECT j.id, j.title, j.status, j.job_date, j.details, 
               c.name, c.phone, c.address
        FROM jobs j
        LEFT JOIN clients c ON j.client_id = c.id
        WHERE j.job_date < ? AND j.status = 'Scheduled'
        ORDER BY j.job_date ASC
    """, (today,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def create_invoice(job_id, client_id, job_title, hours, cost, job_date):
    """Create a new invoice from a completed job"""
    from datetime import datetime
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    created_date = datetime.now().strftime("%Y-%m-%d")
    
    cursor.execute("""
        INSERT INTO invoices (job_id, client_id, job_title, hours, cost, created_date, job_date)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (job_id, client_id, job_title, hours, cost, created_date, job_date))
    
    cursor.execute("UPDATE jobs SET status = 'Completed' WHERE id = ?", (job_id,))
    
    conn.commit()
    invoice_id = cursor.lastrowid
    conn.close()
    
    return invoice_id

def fetch_all_invoices(sort_by="recent", client_id=None, job_type=None, date_from=None, date_to=None):
    """Fetch invoices with optional filtering and sorting"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    query = """
        SELECT i.id, i.job_id, i.client_id, i.job_title, i.hours, i.cost, 
               i.created_date, i.job_date, c.name
        FROM invoices i
        LEFT JOIN clients c ON i.client_id = c.id
        WHERE 1=1
    """
    params = []
    
    if client_id:
        query += " AND i.client_id = ?"
        params.append(client_id)
    
    if job_type:
        query += " AND i.job_title LIKE ?"
        params.append(f"%{job_type}%")
    
    if date_from:
        query += " AND i.job_date >= ?"
        params.append(date_from)
    
    if date_to:
        query += " AND i.job_date <= ?"
        params.append(date_to)
    
    if sort_by == "oldest":
        query += " ORDER BY i.created_date ASC"
    else:
        query += " ORDER BY i.created_date DESC"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_invoice_details(invoice_id):
    """Get details of a specific invoice"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT i.id, i.job_id, i.client_id, i.job_title, i.hours, i.cost, 
               i.created_date, i.job_date, c.name, c.phone, c.address, c.email
        FROM invoices i
        LEFT JOIN clients c ON i.client_id = c.id
        WHERE i.id = ?
    """, (invoice_id,))
    row = cursor.fetchone()
    conn.close()
    return row

def get_unique_job_types():
    """Get list of unique job types from invoices"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT job_title FROM invoices ORDER BY job_title")
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows] if rows else []

# --- QuickBooks Helpers ---

def get_quickbooks_config():
    """Fetch stored QuickBooks API credentials and environment mode."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT environment, client_id, client_secret, redirect_uri FROM quickbooks_config WHERE id = 1")
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "environment": row[0] or "SANDBOX",
            "client_id": row[1] or "",
            "client_secret": row[2] or "",
            "redirect_uri": row[3] or ""
        }
    return {"environment": "SANDBOX", "client_id": "", "client_secret": "", "redirect_uri": ""}

def save_quickbooks_config(environment, client_id, client_secret, redirect_uri):
    """Save or update QuickBooks API credentials and environment mode."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO quickbooks_config (id, environment, client_id, client_secret, redirect_uri)
        VALUES (1, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            environment=excluded.environment,
            client_id=excluded.client_id,
            client_secret=excluded.client_secret,
            redirect_uri=excluded.redirect_uri
    """, (environment, client_id, client_secret, redirect_uri))
    conn.commit()
    conn.close()

def get_quickbooks_tokens():
    """Fetch stored active QuickBooks OAuth tokens."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT realm_id, access_token, refresh_token, expires_at FROM quickbooks_tokens WHERE id = 1")
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "realm_id": row[0] or "",
            "access_token": row[1] or "",
            "refresh_token": row[2] or "",
            "expires_at": row[3] or 0.0
        }
    return None

def save_quickbooks_tokens(realm_id, access_token, refresh_token, expires_at):
    """Save or update active QuickBooks OAuth tokens."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO quickbooks_tokens (id, realm_id, access_token, refresh_token, expires_at)
        VALUES (1, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            realm_id=excluded.realm_id,
            access_token=excluded.access_token,
            refresh_token=excluded.refresh_token,
            expires_at=excluded.expires_at
    """, (realm_id, access_token, refresh_token, expires_at))
    conn.commit()
    conn.close()

def delete_quickbooks_tokens():
    """Delete stored QuickBooks OAuth tokens upon disconnect."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM quickbooks_tokens WHERE id = 1")
    conn.commit()
    conn.close()
