import csv
import io
import logging
from datetime import datetime
from functools import wraps

from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.utils import secure_filename

from config import (
    ADMIN_PASSWORD,
    AUTO_SEND_ENABLED,
    AUTO_SEND_INTERVAL_MINUTES,
    AUTO_SEND_PER_RUN,
    DAILY_EMAIL_LIMIT,
    SECRET_KEY,
    UPLOADS_DIR,
)
from database import (
    add_contacts,
    conn_get_country,
    conn_get_industry,
    create_csv_upload,
    display_name,
    get_auto_send_status,
    get_contacts_by_upload,
    get_contacts_for_selection,
    get_countries,
    get_dashboard_stats,
    get_email_content,
    get_product,
    get_product_tree_json,
    get_products,
    get_upload_detail,
    get_upload_history_by_day,
    init_db,
    resolve_product_industry,
    resolve_selection,
)
from email_service import send_batch, send_direct_email, send_single_contact
from news_service import get_dashboard_intelligence
from proposals_config import resolve_proposal_path
from scheduler import start_auto_sender

app = Flask(__name__)
app.secret_key = SECRET_KEY

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated


def parse_csv_contacts(file_stream):
    """Parse CSV and normalize email, name, company columns."""
    text = file_stream.read().decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))

    if not reader.fieldnames:
        raise ValueError("CSV file is empty or has no headers.")

    headers = {h.strip().lower(): h for h in reader.fieldnames if h}

    def find_col(*candidates):
        for c in candidates:
            if c in headers:
                return headers[c]
        return None

    email_col = find_col("email", "e-mail", "email address", "mail")
    name_col = find_col("name", "full name", "contact name", "person")
    company_col = find_col("company", "organization", "org", "business")

    if not email_col:
        raise ValueError("CSV must have an 'email' column.")

    rows = []
    seen = set()
    for i, row in enumerate(reader, start=2):
        email = (row.get(email_col) or "").strip().lower()
        if not email or "@" not in email:
            continue
        if email in seen:
            continue
        seen.add(email)
        rows.append(
            {
                "email": email,
                "name": (row.get(name_col) or "").strip() if name_col else "",
                "company": (row.get(company_col) or "").strip() if company_col else "",
            }
        )

    if not rows:
        raise ValueError("No valid email addresses found in CSV.")

    return rows


@app.before_request
def setup():
    init_db()


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("dashboard"))
        flash("Invalid password.", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/", methods=["GET", "POST"])
@login_required
def dashboard():
    stats_rows, sent_today = get_dashboard_stats()
    intelligence = get_dashboard_intelligence(stats_rows)
    auto_status = get_auto_send_status()
    return render_template(
        "dashboard.html",
        stats_rows=stats_rows,
        sent_today=sent_today,
        daily_limit=DAILY_EMAIL_LIMIT,
        remaining_today=max(0, DAILY_EMAIL_LIMIT - sent_today),
        news_items=intelligence["news"],
        pitch_suggestions=intelligence["suggestions"],
        industry_intel=intelligence["intel"],
        news_updated=intelligence["updated"],
        auto_send_enabled=AUTO_SEND_ENABLED,
        auto_send_interval=AUTO_SEND_INTERVAL_MINUTES,
        auto_send_per_run=AUTO_SEND_PER_RUN,
        auto_status=auto_status,
    )


@app.route("/upload", methods=["GET", "POST"])
@login_required
def upload_csv():
    products = get_products()
    countries = get_countries()
    product_tree_json = get_product_tree_json()
    upload_history = get_upload_history_by_day()

    if request.method == "POST":
        product_id = request.form.get("product_id")
        industry_id = request.form.get("industry_id")
        country_id = request.form.get("country_id")
        file = request.files.get("csv_file")

        product, industry, country, error = resolve_selection(
            product_id, industry_id, country_id
        )
        if error:
            flash(error, "error")
            return render_template(
                "upload.html",
                products=products,
                countries=countries,
                product_tree_json=product_tree_json,
                upload_history=upload_history,
            )

        if not file or not file.filename:
            flash("Please choose a CSV file.", "error")
            return render_template(
                "upload.html",
                products=products,
                countries=countries,
                product_tree_json=product_tree_json,
                upload_history=upload_history,
            )

        if not file.filename.lower().endswith(".csv"):
            flash("Only CSV files are allowed.", "error")
            return render_template(
                "upload.html",
                products=products,
                countries=countries,
                product_tree_json=product_tree_json,
                upload_history=upload_history,
            )

        try:
            rows = parse_csv_contacts(file.stream)

            filename = secure_filename(file.filename)
            industry_slug = industry["slug"] if industry else "general"
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            stored_filename = f"{timestamp}_{product['slug']}_{industry_slug}_{filename}"
            save_path = UPLOADS_DIR / stored_filename
            file.stream.seek(0)
            save_path.write_bytes(file.stream.read())

            upload_id = create_csv_upload(
                product["id"],
                industry["id"],
                country["id"],
                filename,
                stored_filename,
                len(rows),
            )
            add_contacts(
                product["id"],
                industry["id"],
                country["id"],
                rows,
                upload_id=upload_id,
            )

            flash(
                f"Uploaded {len(rows)} contacts to {display_name(product, industry, country)}.",
                "success",
            )
            return redirect(url_for("upload_detail", upload_id=upload_id))
        except (ValueError, csv.Error) as exc:
            flash(str(exc), "error")

    return render_template(
        "upload.html",
        products=products,
        countries=countries,
        product_tree_json=product_tree_json,
        upload_history=upload_history,
    )


@app.route("/uploads/<int:upload_id>")
@login_required
def upload_detail(upload_id):
    upload = get_upload_detail(upload_id)
    if not upload:
        flash("Upload not found.", "error")
        return redirect(url_for("upload_csv"))

    contacts = get_contacts_by_upload(upload_id)
    return render_template(
        "upload_detail.html",
        upload=upload,
        contacts=contacts,
    )


@app.route("/send", methods=["GET", "POST"])
@login_required
def send_emails():
    products = get_products()
    countries = get_countries()
    product_tree_json = get_product_tree_json()
    _, sent_today = get_dashboard_stats()

    mode = request.values.get("mode", "individual")
    if mode not in ("individual", "batch"):
        mode = "individual"

    selected_product_id = request.values.get("product_id", "")
    selected_industry_id = request.values.get("industry_id", "")
    selected_country_id = request.values.get("country_id", "")

    selected_product = None
    selected_industry = None
    selected_country = None
    contacts = []
    preview = None
    preview_subject = None
    preview_body = None
    has_proposal = False
    proposal_file = None

    if request.method == "POST" and request.form.get("action") == "send_one":
        contact_id = request.form.get("contact_id")
        result = send_single_contact(int(contact_id))
        if result.get("error"):
            flash(result["error"], "error")
        else:
            flash(result["message"], "success")
        return redirect(
            url_for(
                "send_emails",
                mode="individual",
                product_id=selected_product_id,
                industry_id=selected_industry_id,
                country_id=selected_country_id,
            )
        )

    if request.method == "POST" and mode == "batch":
        action = request.form.get("action")
        product, industry, country, error = resolve_selection(
            request.form.get("product_id"),
            request.form.get("industry_id"),
            request.form.get("country_id"),
        )

        if error:
            flash(error, "error")
        else:
            selected_product = product
            selected_industry = industry
            selected_country = country
            subject, _, preview, proposal_file = get_email_content(product, industry)
            preview_subject = subject

            if action == "preview":
                has_proposal = resolve_proposal_path(product["slug"], industry["slug"]) is not None
            elif action == "send":
                result = send_batch(product["id"], industry["id"])
                if result.get("error"):
                    flash(result["error"], "error")
                else:
                    msg = f"Sent {result['sent']} email(s) for {display_name(product, industry, country)}."
                    if result["failed"]:
                        msg += f" {result['failed']} failed."
                    msg += f" {result['remaining_today']} remaining today."
                    flash(msg, "success" if result["sent"] else "error")
                return redirect(url_for("send_emails", mode="batch"))

    if selected_product_id and selected_industry_id:
        selected_product = get_product(int(selected_product_id))
        selected_industry = conn_get_industry(int(selected_industry_id))
        if selected_country_id:
            selected_country = conn_get_country(int(selected_country_id))

        if selected_product and selected_industry:
            country_id = int(selected_country_id) if selected_country_id else None

            pending_contacts = get_contacts_for_selection(
                selected_product["id"],
                selected_industry["id"],
                country_id,
                status="pending",
            )

            sample = pending_contacts[0] if pending_contacts else None
            if sample:
                preview_subject, _, preview_body, proposal_file = get_email_content(
                    selected_product,
                    selected_industry,
                    name=sample["name"] or "",
                    company=sample["company"] or "",
                )
            else:
                preview_subject, _, preview_body, proposal_file = get_email_content(
                    selected_product, selected_industry
                )
            has_proposal = resolve_proposal_path(
                selected_product["slug"], selected_industry["slug"]
            ) is not None

            if mode == "individual":
                contacts = pending_contacts

    return render_template(
        "send.html",
        mode=mode,
        products=products,
        countries=countries,
        product_tree_json=product_tree_json,
        contacts=contacts,
        selected_product=selected_product,
        selected_industry=selected_industry,
        selected_country=selected_country,
        preview=preview or preview_body,
        preview_subject=preview_subject,
        preview_body=preview_body,
        proposal_file=proposal_file,
        has_proposal=has_proposal,
        selected_product_id=selected_product_id,
        selected_industry_id=selected_industry_id,
        selected_country_id=selected_country_id,
        sent_today=sent_today,
        daily_limit=DAILY_EMAIL_LIMIT,
        remaining_today=max(0, DAILY_EMAIL_LIMIT - sent_today),
    )


@app.route("/compose", methods=["GET", "POST"])
@login_required
def compose_email():
    products = get_products()
    product_tree_json = get_product_tree_json()
    _, sent_today = get_dashboard_stats()

    form = {
        "product_id": request.values.get("product_id", ""),
        "industry_id": request.values.get("industry_id", ""),
        "email": request.values.get("email", ""),
        "name": request.values.get("name", ""),
        "company": request.values.get("company", ""),
    }

    selected_product = None
    selected_industry = None
    preview_subject = None
    preview_body = None
    proposal_file = None
    has_proposal = False

    if request.method == "POST":
        action = request.form.get("action")
        product, industry, error = resolve_product_industry(
            form["product_id"], form["industry_id"]
        )

        if error:
            flash(error, "error")
        elif action == "preview":
            selected_product = product
            selected_industry = industry
            preview_subject, _, preview_body, proposal_file = get_email_content(
                product,
                industry,
                form["name"] or "John",
                form["company"] or "Example Corp",
            )
            has_proposal = resolve_proposal_path(product["slug"], industry["slug"]) is not None
        elif action == "send":
            result = send_direct_email(
                form["email"],
                form["name"],
                form["company"],
                product["id"],
                industry["id"],
            )
            if result.get("error"):
                flash(result["error"], "error")
            else:
                flash(result["message"], "success")
                return redirect(url_for("compose_email"))
    elif form["product_id"] and form["industry_id"]:
        product, industry, error = resolve_product_industry(
            form["product_id"], form["industry_id"]
        )
        if not error and product and industry:
            selected_product = product
            selected_industry = industry
            preview_subject, _, preview_body, proposal_file = get_email_content(
                product,
                industry,
                form["name"] or "John",
                form["company"] or "Example Corp",
            )
            has_proposal = resolve_proposal_path(product["slug"], industry["slug"]) is not None

    return render_template(
        "compose.html",
        products=products,
        product_tree_json=product_tree_json,
        form=form,
        selected_product=selected_product,
        selected_industry=selected_industry,
        preview_subject=preview_subject,
        preview_body=preview_body,
        proposal_file=proposal_file,
        has_proposal=has_proposal,
        sent_today=sent_today,
        daily_limit=DAILY_EMAIL_LIMIT,
        remaining_today=max(0, DAILY_EMAIL_LIMIT - sent_today),
    )


if __name__ == "__main__":
    start_auto_sender(app)
    app.run(debug=True, port=5000)
