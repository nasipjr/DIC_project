from flask import Flask, request, session, redirect, url_for, g

from models import db
from settings import Config
from utils.logging_config import setup_logging

from routes.dashboard import dashboard_bp
from routes.patients import patients_bp
from routes.appointments import appointments_bp
from routes.treatments import treatments_bp
from routes.payments import payments_bp
from routes.invoices import invoices_bp
from routes.reports import reports_bp
from routes.settings import settings_bp
from routes.auth import auth_bp
from routes.portal import portal_bp
from routes.stock import stock_bp
from routes.archive import archive_bp




import sys
import os

if getattr(sys, 'frozen', False):
    base_dir = sys._MEIPASS
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))

template_dir = os.path.join(base_dir, 'templates')
static_dir = os.path.join(base_dir, 'static')

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
app.config.from_object(Config)

LOG_DIRECTORY = app.config["LOG_DIRECTORY"]
LOG_FILE_NAME = app.config["LOG_FILE_NAME"]

db.init_app(app)


def populate_default_settings():
    from models import SystemSetting
    from utils.settings_helper import DEFAULT_SETTINGS
    try:
        for key, val in DEFAULT_SETTINGS.items():
            setting = SystemSetting.query.filter_by(key=key).first()
            if not setting:
                db.session.add(SystemSetting(key=key, value=val))
        db.session.commit()
    except Exception:
        db.session.rollback()


def check_and_add_discount_column():
    from sqlalchemy import text
    try:
        db.session.execute(text("SELECT discount FROM invoice LIMIT 1"))
    except Exception:
        db.session.rollback()
        try:
            app.logger.info("Adding discount column to invoice table")
            db.session.execute(text("ALTER TABLE invoice ADD COLUMN discount DECIMAL(10, 2) NOT NULL DEFAULT 0.00"))
            db.session.commit()
            app.logger.info("Successfully added discount column")
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Failed to add discount column: {e}")

    try:
        db.session.execute(text("SELECT discount_type FROM invoice LIMIT 1"))
    except Exception:
        db.session.rollback()
        try:
            app.logger.info("Adding discount_type column to invoice table")
            db.session.execute(text("ALTER TABLE invoice ADD COLUMN discount_type VARCHAR(20) NOT NULL DEFAULT 'value'"))
            db.session.commit()
            app.logger.info("Successfully added discount_type column")
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Failed to add discount_type column: {e}")


def check_and_add_tax_rate_column():
    from sqlalchemy import text
    try:
        db.session.execute(text("SELECT tax_rate FROM invoice LIMIT 1"))
    except Exception:
        db.session.rollback()
        try:
            app.logger.info("Adding tax_rate column to invoice table")
            db.session.execute(text("ALTER TABLE invoice ADD COLUMN tax_rate DECIMAL(5, 2) NOT NULL DEFAULT 0.00"))
            db.session.commit()
            app.logger.info("Successfully added tax_rate column")
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Failed to add tax_rate column: {e}")


def check_and_add_patient_id_column():
    from sqlalchemy import text
    try:
        db.session.execute(text("SELECT patient_id FROM user LIMIT 1"))
    except Exception:
        db.session.rollback()
        try:
            app.logger.info("Adding patient_id column to user table")
            db.session.execute(text("ALTER TABLE user ADD COLUMN patient_id INT NULL"))
            db.session.commit()
            app.logger.info("Successfully added patient_id column to user table")
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Failed to add patient_id column: {e}")
        try:
            app.logger.info("Adding foreign key constraint for patient_id on user table")
            db.session.execute(text("ALTER TABLE user ADD CONSTRAINT fk_user_patient FOREIGN KEY (patient_id) REFERENCES patient(id)"))
            db.session.commit()
            app.logger.info("Successfully added foreign key constraint")
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Failed to add foreign key constraint: {e}")


def check_and_add_plain_password_column():
    from sqlalchemy import text
    try:
        db.session.execute(text("SELECT plain_password FROM user LIMIT 1"))
    except Exception:
        db.session.rollback()
        try:
            app.logger.info("Adding plain_password column to user table")
            db.session.execute(text("ALTER TABLE user ADD COLUMN plain_password VARCHAR(255) NULL"))
            db.session.commit()
            app.logger.info("Successfully added plain_password column to user table")
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Failed to add plain_password column: {e}")


def check_and_add_file_category_column():
    from sqlalchemy import text
    try:
        db.session.execute(text("SELECT category FROM patient_file LIMIT 1"))
    except Exception:
        db.session.rollback()
        try:
            app.logger.info("Adding category column to patient_file table")
            db.session.execute(text("ALTER TABLE patient_file ADD COLUMN category VARCHAR(100) NOT NULL DEFAULT 'General'"))
            db.session.commit()
            app.logger.info("Successfully added category column to patient_file table")
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Failed to add category column: {e}")


def ensure_default_admin():
    from models import User
    try:
        admin = User.query.filter_by(role="admin").first()
        if not admin:
            app.logger.info("Seeding default admin account...")
            default_admin = User(
                username="admin",
                role="admin",
                first_name="Admin",
                last_name="User"
            )
            default_admin.set_password("admin123")
            db.session.add(default_admin)
            db.session.commit()
            app.logger.info("Successfully seeded default admin account!")
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Failed to seed default admin: {e}")


def create_database_if_not_exists():
    from sqlalchemy import create_engine, text
    import re
    uri = app.config.get("SQLALCHEMY_DATABASE_URI")
    if not uri:
        return
    match = re.match(r"^(mysql\+pymysql://[^/]+)/([^?]+)", uri)
    if match:
        base_uri, db_name = match.groups()
        try:
            temp_engine = create_engine(base_uri)
            with temp_engine.connect() as conn:
                conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
            temp_engine.dispose()
        except Exception as e:
            print(f"Database auto-creation status/warning: {e}")


with app.app_context():
    create_database_if_not_exists()
    db.create_all()
    populate_default_settings()
    check_and_add_discount_column()
    check_and_add_tax_rate_column()
    check_and_add_patient_id_column()
    check_and_add_plain_password_column()
    check_and_add_file_category_column()
    ensure_default_admin()

setup_logging(app, LOG_DIRECTORY, LOG_FILE_NAME)
app.logger.info("Application started successfully")


@app.template_filter("format_price")
def format_price(value):
    if value is None:
        return "0"
    try:
        val = float(value)
        # Format with whole number and thousands separator
        formatted = "{:,.0f}".format(val)
        # Replace commas with dots
        return formatted.replace(",", ".")
    except (ValueError, TypeError):
        return str(value)


@app.before_request
def load_logged_in_user():
    from models import User
    user_id = session.get("user_id")
    if user_id is None:
        g.current_user = None
    else:
        g.current_user = User.query.get(user_id)


@app.before_request
def check_login():
    # Exclude login, static resources, and patient portal
    if request.endpoint in ("auth.login", "static") or not request.endpoint or request.endpoint.startswith("portal."):
        return
    if "user_id" not in session:
        return redirect(url_for("auth.login"))


@app.context_processor
def inject_settings():
    from utils.settings_helper import get_setting, get_currency_symbol
    from datetime import datetime

    # Get dynamic operating hours formatting
    start_str = get_setting("working_hours_start", "08:00")
    end_str = get_setting("working_hours_end", "18:00")
    
    def to_12h(t_str):
        try:
            return datetime.strptime(t_str, "%H:%M").strftime("%I:%M %p").lstrip("0")
        except Exception:
            return t_str
            
    hours_formatted = f"{to_12h(start_str)} - {to_12h(end_str)}"
    
    wd_str = get_setting("working_days", "0,1,2,3,4,6")
    active_days = set()
    for x in wd_str.split(","):
        if x.strip().isdigit():
            active_days.add(int(x))
            
    DAY_NAMES = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    SHORT_DAY_NAMES = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    
    active_names = [SHORT_DAY_NAMES[d] for d in range(7) if d in active_days]
    closed_names = [DAY_NAMES[d] for d in range(7) if d not in active_days]
    
    active_set = set(active_days)
    if active_set == {0, 1, 2, 3, 4, 6}:
        days_str = "Sat - Thu"
    elif active_set == {0, 1, 2, 3, 4}:
        days_str = "Sun - Thu"
    elif active_set == {1, 2, 3, 4, 5}:
        days_str = "Mon - Fri"
    elif active_set == {1, 2, 3, 4, 5, 6}:
        days_str = "Mon - Sat"
    elif active_set == {0, 1, 2, 3, 4, 5, 6}:
        days_str = "Every day"
    else:
        days_str = ", ".join(active_names)
        
    if not closed_names:
        closed_str = "None"
    else:
        closed_str = ", ".join(closed_names)

    from models import Appointment
    try:
        pending_count = Appointment.query.filter_by(status="Pending").count()
    except Exception:
        pending_count = 0

    return {
        "clinic_name": get_setting("clinic_name", "Clinic"),
        "currency_symbol": get_currency_symbol(),
        "clinic_phone": get_setting("clinic_phone", "+963 958 948 727"),
        "clinic_email": get_setting("clinic_email", "kh.nasipdragon@gmail.com"),
        "clinic_address": get_setting("clinic_address", "Damascus, Syria"),
        "clinic_vat_number": get_setting("clinic_vat_number", ""),
        "current_user": g.current_user if "current_user" in dir(g) else None,
        "operating_hours": hours_formatted,
        "operating_days": days_str,
        "operating_closed": closed_str,
        "working_days": wd_str,
        "working_hours_start": start_str,
        "working_hours_end": end_str,
        "pending_count": pending_count
    }


app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(patients_bp)
app.register_blueprint(appointments_bp)
app.register_blueprint(treatments_bp)
app.register_blueprint(payments_bp)
app.register_blueprint(invoices_bp)
app.register_blueprint(reports_bp)
app.register_blueprint(settings_bp)
app.register_blueprint(portal_bp)
app.register_blueprint(stock_bp)
app.register_blueprint(archive_bp)





@app.errorhandler(404)
def not_found_error(error):
    app.logger.warning(f"404 Not Found | path={request.path}")
    return "page not found", 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    app.logger.exception("500 Internal Server Error")
    return "internal server error", 500


if __name__ == "__main__":
    with app.app_context():
        try:
            db.create_all()
            app.logger.info("Database tables created successfully or already exist")
        except Exception:
            app.logger.exception("Failed to create database tables")

        # Start database backup scheduler thread
        try:
            from utils.backup_helper import schedule_daily_backups
            schedule_daily_backups(app)
            app.logger.info("Database backup scheduler thread started successfully")
        except Exception as e:
            app.logger.error(f"Failed to start database backup scheduler: {e}")

        try:
            from utils.notification_helper import schedule_appointment_reminders
            schedule_appointment_reminders(app)
            app.logger.info("Appointment reminders scheduler thread started successfully")
        except Exception as e:
            app.logger.error(f"Failed to start appointment reminders scheduler: {e}")

    app.logger.info("Flask app is running")
    app.run(debug=True)