import json
import sqlite3
from contextlib import contextmanager
from datetime import date

from config import DATABASE_PATH, PROPOSALS_DIR

MAIN_PRODUCT_SLUGS = ("ai_recruiter", "supply_chain", "video_analytics")

VIDEO_ANALYTICS_INDUSTRIES = [
    ("poultry_farms", "Poultry Farms"),
    ("sports_organizations", "Sports Organizations"),
    ("fitness_gyms", "Fitness & Gyms"),
    ("manufacturing", "Manufacturing"),
    ("smart_cities", "Smart Cities"),
    ("retail_stores", "Retail Stores"),
    ("warehouses_logistics", "Warehouses & Logistics"),
    ("security_surveillance", "Security & Surveillance"),
    ("agriculture", "Agriculture"),
    ("education_training", "Education & Training"),
    ("healthcare_facilities", "Healthcare Facilities"),
    ("construction_sites", "Construction Sites"),
    ("hotels_hospitality", "Hotels & Hospitality"),
    ("airports_transport", "Airports & Transport"),
]



@contextmanager
def get_db():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slug TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                email_subject TEXT NOT NULL,
                email_body TEXT NOT NULL,
                proposal_file TEXT
            );

            CREATE TABLE IF NOT EXISTS industries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                slug TEXT NOT NULL,
                parent_id INTEGER,
                sort_order INTEGER DEFAULT 0,
                FOREIGN KEY (product_id) REFERENCES products(id),
                UNIQUE(product_id, slug)
            );

            CREATE TABLE IF NOT EXISTS countries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                code TEXT UNIQUE NOT NULL
            );

            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                industry_id INTEGER NOT NULL,
                country_id INTEGER NOT NULL,
                email TEXT NOT NULL,
                name TEXT DEFAULT '',
                company TEXT DEFAULT '',
                status TEXT DEFAULT 'pending',
                uploaded_at TEXT DEFAULT (datetime('now')),
                sent_at TEXT,
                FOREIGN KEY (product_id) REFERENCES products(id),
                FOREIGN KEY (industry_id) REFERENCES industries(id),
                FOREIGN KEY (country_id) REFERENCES countries(id)
            );

            CREATE TABLE IF NOT EXISTS email_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contact_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                sent_at TEXT DEFAULT (datetime('now')),
                status TEXT NOT NULL,
                error_message TEXT,
                FOREIGN KEY (contact_id) REFERENCES contacts(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            );

            CREATE INDEX IF NOT EXISTS idx_contacts_product_industry_status
                ON contacts(product_id, industry_id, status);
            CREATE INDEX IF NOT EXISTS idx_email_log_sent_at
                ON email_log(sent_at);

            CREATE TABLE IF NOT EXISTS csv_uploads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                industry_id INTEGER NOT NULL,
                country_id INTEGER NOT NULL,
                original_filename TEXT NOT NULL,
                stored_filename TEXT NOT NULL,
                contact_count INTEGER NOT NULL DEFAULT 0,
                uploaded_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (product_id) REFERENCES products(id),
                FOREIGN KEY (industry_id) REFERENCES industries(id),
                FOREIGN KEY (country_id) REFERENCES countries(id)
            );

            CREATE INDEX IF NOT EXISTS idx_csv_uploads_uploaded_at
                ON csv_uploads(uploaded_at);

            CREATE TABLE IF NOT EXISTS auto_send_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ran_at TEXT DEFAULT (datetime('now')),
                sent INTEGER NOT NULL DEFAULT 0,
                failed INTEGER NOT NULL DEFAULT 0,
                skipped INTEGER NOT NULL DEFAULT 0,
                message TEXT,
                details TEXT
            );
            """
        )
        _seed_countries(conn)
        _seed_video_analytics_industries(conn)
        _sync_product_names(conn)
        _migrate_email_log(conn)
        _migrate_contacts_upload_id(conn)


def _migrate_email_log(conn):
    columns = {row[1] for row in conn.execute("PRAGMA table_info(email_log)").fetchall()}
    if "recipient_email" not in columns:
        conn.execute("ALTER TABLE email_log ADD COLUMN recipient_email TEXT")


def _migrate_contacts_upload_id(conn):
    columns = {row[1] for row in conn.execute("PRAGMA table_info(contacts)").fetchall()}
    if "upload_id" not in columns:
        conn.execute("ALTER TABLE contacts ADD COLUMN upload_id INTEGER")


def _sync_product_names(conn):
    names = {
        "ai_recruiter": "AI Recruiter System",
        "supply_chain": "Supply Chain Forecasting",
        "video_analytics": "Video Analytics Solution",
    }
    for slug, name in names.items():
        conn.execute(
            "UPDATE products SET name = ? WHERE slug = ?",
            (name, slug),
        )


def _seed_countries(conn):
    defaults = [
        ("USA", "usa"),
        ("Pakistan", "pakistan"),
        ("UAE", "uae"),
        ("Sri Lanka", "sri_lanka"),
        ("Saudi Arabia", "saudi_arabia"),
        ("Qatar", "qatar"),
        ("Canada", "canada"),
        ("UK", "uk"),
        ("Australia", "australia"),
        ("India", "india"),
    ]
    for name, code in defaults:
        conn.execute(
            "INSERT OR IGNORE INTO countries (name, code) VALUES (?, ?)",
            (name, code),
        )


def _seed_video_analytics_industries(conn):
    product = conn.execute(
        "SELECT id FROM products WHERE slug = 'video_analytics'"
    ).fetchone()
    if not product:
        return

    product_id = product["id"]
    for order, (slug, name) in enumerate(VIDEO_ANALYTICS_INDUSTRIES, start=1):
        conn.execute(
            """
            INSERT INTO industries (product_id, slug, name, sort_order)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(product_id, slug) DO UPDATE SET
                name = excluded.name,
                sort_order = excluded.sort_order
            """,
            (product_id, slug, name, order),
        )


def get_products():
    placeholders = ",".join("?" for _ in MAIN_PRODUCT_SLUGS)
    with get_db() as conn:
        return conn.execute(
            f"""
            SELECT * FROM products
            WHERE slug IN ({placeholders})
            ORDER BY CASE slug
                WHEN 'ai_recruiter' THEN 1
                WHEN 'supply_chain' THEN 2
                WHEN 'video_analytics' THEN 3
                ELSE 99 END
            """,
            MAIN_PRODUCT_SLUGS,
        ).fetchall()


def get_product(product_id):
    with get_db() as conn:
        return conn.execute(
            "SELECT * FROM products WHERE id = ?", (product_id,)
        ).fetchone()


def get_industries_for_product(product_id):
    product = get_product(product_id)
    if not product:
        return []

    with get_db() as conn:
        if product["slug"] == "video_analytics":
            slugs = [s for s, _ in VIDEO_ANALYTICS_INDUSTRIES]
            placeholders = ",".join("?" for _ in slugs)
            return conn.execute(
                f"""
                SELECT * FROM industries
                WHERE product_id = ? AND slug IN ({placeholders})
                ORDER BY sort_order, name
                """,
                (product_id, *slugs),
            ).fetchall()

        return conn.execute(
            """
            SELECT * FROM industries
            WHERE product_id = ?
            ORDER BY sort_order, name
            """,
            (product_id,),
        ).fetchall()


def get_countries():
    with get_db() as conn:
        return conn.execute("SELECT * FROM countries ORDER BY name").fetchall()


def get_product_tree_json():
    tree = []
    for product in get_products():
        children = get_industries_for_product(product["id"])
        tree.append(
            {
                "id": product["id"],
                "slug": product["slug"],
                "name": product["name"],
                "has_children": len(children) > 0,
                "children": [
                    {"id": c["id"], "slug": c["slug"], "name": c["name"]}
                    for c in children
                ],
            }
        )
    return json.dumps(tree)


def resolve_selection(product_id, industry_id=None, country_id=None):
    product = get_product(int(product_id))
    if not product:
        return None, None, None, "Product not found."

    if product["slug"] not in MAIN_PRODUCT_SLUGS:
        return None, None, None, "Invalid product selection."

    industries = get_industries_for_product(product["id"])
    industry = None
    if industries:
        if not industry_id:
            label = (
                "Please select a Video Analytics industry."
                if product["slug"] == "video_analytics"
                else "Please select a target industry."
            )
            return None, None, None, label
        industry = conn_get_industry(int(industry_id))
        if not industry or industry["product_id"] != product["id"]:
            return None, None, None, "Invalid industry selection."

    if not country_id:
        return None, None, None, "Please select a country."

    country = conn_get_country(int(country_id))
    if not country:
        return None, None, None, "Invalid country selection."

    return product, industry, country, None


def conn_get_industry(industry_id):
    with get_db() as conn:
        return conn.execute(
            "SELECT * FROM industries WHERE id = ?", (industry_id,)
        ).fetchone()


def conn_get_country(country_id):
    with get_db() as conn:
        return conn.execute(
            "SELECT * FROM countries WHERE id = ?", (country_id,)
        ).fetchone()


def get_email_content(product, industry=None, name="John", company="Example Corp"):
    from email_templates import build_email
    from proposals_config import resolve_proposal_filename

    industry_slug = industry["slug"] if industry else None
    industry_name = industry["name"] if industry else ""

    email = build_email(name, company, industry_name, product["slug"], industry_slug)
    proposal_file = resolve_proposal_filename(product["slug"], industry_slug)
    return email["subject"], email["html"], email["plain"], proposal_file


def add_contacts(product_id, industry_id, country_id, rows, upload_id=None):
    with get_db() as conn:
        for row in rows:
            conn.execute(
                """
                INSERT INTO contacts (product_id, industry_id, country_id, email, name, company, upload_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    product_id,
                    industry_id,
                    country_id,
                    row["email"],
                    row.get("name", ""),
                    row.get("company", ""),
                    upload_id,
                ),
            )


def create_csv_upload(
    product_id, industry_id, country_id, original_filename, stored_filename, contact_count
):
    with get_db() as conn:
        cur = conn.execute(
            """
            INSERT INTO csv_uploads (
                product_id, industry_id, country_id,
                original_filename, stored_filename, contact_count
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                product_id,
                industry_id,
                country_id,
                original_filename,
                stored_filename,
                contact_count,
            ),
        )
        return cur.lastrowid


def get_upload_detail(upload_id):
    with get_db() as conn:
        return conn.execute(
            """
            SELECT u.*,
                   p.name AS product_name, p.slug AS product_slug,
                   i.name AS industry_name, i.slug AS industry_slug,
                   c.name AS country_name
            FROM csv_uploads u
            JOIN products p ON p.id = u.product_id
            JOIN industries i ON i.id = u.industry_id
            JOIN countries c ON c.id = u.country_id
            WHERE u.id = ?
            """,
            (upload_id,),
        ).fetchone()


def get_contacts_by_upload(upload_id):
    with get_db() as conn:
        return conn.execute(
            """
            SELECT c.*, co.name AS country_name
            FROM contacts c
            LEFT JOIN countries co ON co.id = c.country_id
            WHERE c.upload_id = ?
            ORDER BY c.name, c.email
            """,
            (upload_id,),
        ).fetchall()


def get_upload_history_by_day():
    with get_db() as conn:
        uploads = conn.execute(
            """
            SELECT u.*,
                   p.name AS product_name,
                   i.name AS industry_name,
                   c.name AS country_name,
                   date(u.uploaded_at) AS upload_date
            FROM csv_uploads u
            JOIN products p ON p.id = u.product_id
            JOIN industries i ON i.id = u.industry_id
            JOIN countries c ON c.id = u.country_id
            ORDER BY u.uploaded_at DESC
            """
        ).fetchall()

    grouped = {}
    for row in uploads:
        day = row["upload_date"]
        if day not in grouped:
            grouped[day] = {
                "date": day,
                "file_count": 0,
                "contact_count": 0,
                "uploads": [],
            }
        grouped[day]["file_count"] += 1
        grouped[day]["contact_count"] += row["contact_count"]
        grouped[day]["uploads"].append(row)

    return sorted(grouped.values(), key=lambda g: g["date"], reverse=True)


def get_pending_contacts(product_id, industry_id, limit):
    with get_db() as conn:
        return conn.execute(
            """
            SELECT c.*, co.name AS country_name
            FROM contacts c
            LEFT JOIN countries co ON co.id = c.country_id
            WHERE c.product_id = ? AND c.industry_id = ? AND c.status = 'pending'
            ORDER BY c.uploaded_at ASC
            LIMIT ?
            """,
            (product_id, industry_id, limit),
        ).fetchall()


def get_contact(contact_id):
    with get_db() as conn:
        return conn.execute(
            """
            SELECT c.*, co.name AS country_name
            FROM contacts c
            LEFT JOIN countries co ON co.id = c.country_id
            WHERE c.id = ?
            """,
            (contact_id,),
        ).fetchone()


def get_contacts_for_selection(product_id, industry_id, country_id=None, status="pending"):
    query = """
        SELECT c.*, co.name AS country_name
        FROM contacts c
        LEFT JOIN countries co ON co.id = c.country_id
        WHERE c.product_id = ? AND c.industry_id = ?
    """
    params = [product_id, industry_id]

    if country_id:
        query += " AND c.country_id = ?"
        params.append(country_id)

    if status:
        query += " AND c.status = ?"
        params.append(status)

    query += " ORDER BY c.uploaded_at ASC"

    with get_db() as conn:
        return conn.execute(query, params).fetchall()


def mark_contact_sent(contact_id):
    with get_db() as conn:
        conn.execute(
            """
            UPDATE contacts SET status = 'sent', sent_at = datetime('now')
            WHERE id = ?
            """,
            (contact_id,),
        )


def mark_contact_failed(contact_id):
    with get_db() as conn:
        conn.execute(
            "UPDATE contacts SET status = 'failed' WHERE id = ?",
            (contact_id,),
        )


def log_email(contact_id, product_id, status, error_message=None):
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO email_log (contact_id, product_id, status, error_message)
            VALUES (?, ?, ?, ?)
            """,
            (contact_id, product_id, status, error_message),
        )


def log_direct_email(product_id, recipient_email, status, error_message=None):
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO email_log (contact_id, product_id, status, error_message, recipient_email)
            VALUES (0, ?, ?, ?, ?)
            """,
            (product_id, status, error_message, recipient_email),
        )


def resolve_product_industry(product_id, industry_id):
    product = get_product(int(product_id))
    if not product:
        return None, None, "Product not found."

    industries = get_industries_for_product(product["id"])
    if not industries:
        return product, None, None

    if not industry_id:
        label = (
            "Please select a Video Analytics industry."
            if product["slug"] == "video_analytics"
            else "Please select a target industry."
        )
        return None, None, label

    industry = conn_get_industry(int(industry_id))
    if not industry or industry["product_id"] != product["id"]:
        return None, None, "Invalid industry selection."

    return product, industry, None


def emails_sent_today():
    today = date.today().isoformat()
    with get_db() as conn:
        row = conn.execute(
            """
            SELECT COUNT(*) AS cnt FROM email_log
            WHERE status = 'sent' AND date(sent_at) = ?
            """,
            (today,),
        ).fetchone()
        return row["cnt"]


def get_pending_contacts_queue(limit):
    with get_db() as conn:
        return conn.execute(
            """
            SELECT c.*, co.name AS country_name
            FROM contacts c
            LEFT JOIN countries co ON co.id = c.country_id
            WHERE c.status = 'pending'
            ORDER BY c.uploaded_at ASC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()


def count_pending_contacts():
    with get_db() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS cnt FROM contacts WHERE status = 'pending'"
        ).fetchone()
        return row["cnt"]


def log_auto_send_run(sent, failed, skipped=0, message="", details=""):
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO auto_send_runs (sent, failed, skipped, message, details)
            VALUES (?, ?, ?, ?, ?)
            """,
            (sent, failed, skipped, message, details),
        )


def get_auto_send_status():
    with get_db() as conn:
        last_run = conn.execute(
            """
            SELECT * FROM auto_send_runs
            ORDER BY ran_at DESC
            LIMIT 1
            """
        ).fetchone()

    return {
        "pending": count_pending_contacts(),
        "last_run": last_run,
    }


def get_dashboard_stats():
    video_slugs = ",".join(f"'{s}'" for s, _ in VIDEO_ANALYTICS_INDUSTRIES)
    with get_db() as conn:
        rows = conn.execute(
            f"""
            SELECT p.id AS product_id, p.name AS product_name, p.slug AS product_slug,
                   i.id AS industry_id, i.name AS industry_name, i.slug AS industry_slug,
                   COUNT(CASE WHEN c.status = 'pending' THEN 1 END) AS pending,
                   COUNT(CASE WHEN c.status = 'sent' THEN 1 END) AS sent,
                   COUNT(CASE WHEN c.status = 'failed' THEN 1 END) AS failed
            FROM products p
            INNER JOIN industries i ON i.product_id = p.id
            LEFT JOIN contacts c ON c.product_id = p.id AND c.industry_id = i.id
            WHERE p.slug IN ('ai_recruiter', 'supply_chain', 'video_analytics')
              AND (
                p.slug != 'video_analytics'
                OR i.slug IN ({video_slugs})
              )
            GROUP BY p.id, i.id
            ORDER BY p.id, i.sort_order, i.name
            """
        ).fetchall()

        sent_today = emails_sent_today()
        return rows, sent_today


def display_name(product, industry=None, country=None):
    parts = [product["name"]]
    if industry:
        parts.append(industry["name"])
    if country:
        parts.append(country["name"])
    return " > ".join(parts)


def proposal_path(proposal_file):
    if not proposal_file:
        return None
    path = PROPOSALS_DIR / proposal_file
    return path if path.exists() else None
