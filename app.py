from flask import Flask, request, session, redirect, url_for, g
from models import db
from settings import Config
from utils.logging_config import setup_logging
import sys
import os

from routes.dashboard import dashboard_bp
from routes.invoices import invoices_bp
from routes.auth import auth_bp
from routes.stock import stock_bp
from routes.settings import settings_bp
from routes.clients import clients_bp
from routes.payments import payments_bp

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


def seed_clients_from_invoices():
    from models import Invoice, Client
    try:
        unique_names = db.session.query(Invoice.client_name).distinct().all()
        for name_tuple in unique_names:
            name = name_tuple[0]
            if name:
                existing = Client.query.filter_by(name=name).first()
                if not existing:
                    inv = Invoice.query.filter_by(client_name=name).first()
                    new_client = Client(
                        name=name,
                        phone=inv.client_phone if inv else None,
                        address=inv.client_address if inv else None
                    )
                    db.session.add(new_client)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Failed to seed clients from invoices: {e}")


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


def check_and_add_columns():
    from sqlalchemy import inspect, text
    try:
        inspector = inspect(db.engine)
        if 'inventory_item' in inspector.get_table_names():
            columns = [c['name'] for c in inspector.get_columns('inventory_item')]
            if 'company' not in columns:
                app.logger.info("Adding 'company' column to 'inventory_item' table...")
                with db.engine.begin() as conn:
                    conn.execute(text("ALTER TABLE inventory_item ADD COLUMN company VARCHAR(255) NULL"))
                app.logger.info("Successfully added 'company' column to 'inventory_item' table!")
    except Exception as e:
        app.logger.error(f"Failed to inspect or alter database tables: {e}")


with app.app_context():
    create_database_if_not_exists()
    db.create_all()
    check_and_add_columns()
    populate_default_settings()
    ensure_default_admin()
    seed_clients_from_invoices()

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
    if request.endpoint in ("auth.login", "static") or not request.endpoint:
        return
    if "user_id" not in session:
        return redirect(url_for("auth.login"))


@app.context_processor
def inject_settings():
    from utils.settings_helper import get_setting, get_currency_symbol
    from utils.translations import TRANSLATIONS
    
    current_lang = request.cookies.get('lang', 'ar')
    if current_lang not in ('ar', 'en'):
        current_lang = 'ar'
        
    current_theme = request.cookies.get('theme', 'light')
    if current_theme not in ('light', 'dark'):
        current_theme = 'light'

    def translate_helper(key):
        item = TRANSLATIONS.get(key)
        if not item:
            return key
        return item.get(current_lang, item.get('ar', key))

    clinic_desc = get_setting("clinic_description")
    if not clinic_desc:
        clinic_desc = translate_helper("footer_default_description")

    operating_hours_weekdays = get_setting("operating_hours_weekdays")
    if not operating_hours_weekdays:
        operating_hours_weekdays = translate_helper("footer_default_weekdays")

    operating_hours_weekend = get_setting("operating_hours_weekend")
    if not operating_hours_weekend:
        operating_hours_weekend = translate_helper("footer_default_weekend")

    return {
        "clinic_name": get_setting("clinic_name", "المركز التقني للري بالتنقيط"),
        "currency_symbol": get_currency_symbol(),
        "clinic_phone": get_setting("clinic_phone", "+963 958 948 727"),
        "clinic_email": get_setting("clinic_email", "irrigation.tech.center@gmail.com"),
        "clinic_address": get_setting("clinic_address", "Damascus, Syria"),
        "clinic_description": clinic_desc,
        "social_facebook": get_setting("social_facebook", "https://facebook.com"),
        "social_instagram": get_setting("social_instagram", "https://instagram.com"),
        "social_linkedin": get_setting("social_linkedin", "https://linkedin.com"),
        "social_whatsapp": get_setting("social_whatsapp", "https://wa.me/963958948727"),
        "operating_hours_weekdays": operating_hours_weekdays,
        "operating_hours_weekend": operating_hours_weekend,
        "current_user": g.current_user if "current_user" in dir(g) else None,
        "current_lang": current_lang,
        "current_theme": current_theme,
        "_": translate_helper
    }


app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(invoices_bp)
app.register_blueprint(stock_bp)
app.register_blueprint(settings_bp)
app.register_blueprint(clients_bp)
app.register_blueprint(payments_bp)


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
        # Start database backup scheduler thread
        try:
            from utils.backup_helper import schedule_daily_backups
            schedule_daily_backups(app)
            app.logger.info("Database backup scheduler thread started successfully")
        except Exception as e:
            app.logger.error(f"Failed to start database backup scheduler: {e}")

    app.logger.info("Flask app is running")
    app.run(debug=True)