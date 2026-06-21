import os
import sys
import re
from sqlalchemy import create_engine, text

# Add parent directory to path to import app and models
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db

uri = app.config.get("SQLALCHEMY_DATABASE_URI")
match = re.match(r"^(mysql\+pymysql://[^/]+)/([^?]+)", uri)
if match:
    base_uri, db_name = match.groups()
    print(f"Connecting to MySQL server at {base_uri}...")
    temp_engine = create_engine(base_uri)
    with temp_engine.connect() as conn:
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
        print(f"Dropping database {db_name} if exists...")
        conn.execute(text(f"DROP DATABASE IF EXISTS {db_name}"))
        print(f"Creating database {db_name}...")
        conn.execute(text(f"CREATE DATABASE {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
    temp_engine.dispose()

with app.app_context():
    print("Creating all tables in the clean database...")
    db.create_all()
    from app import populate_default_settings, ensure_default_admin
    populate_default_settings()
    ensure_default_admin()
    print("Database has been completely recreated and seeded successfully!")
