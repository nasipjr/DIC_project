import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

#gives us Path object for settings.py then gives us the parent directory of settings.py which is the root of our project. This allows us to construct paths to other files in a way that works regardless of where the code is run from.
import sys

if getattr(sys, 'frozen', False):
    # Path of the folder where the .exe file resides
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).resolve().parent


def build_database_uri():
    database_url = os.getenv("DATABASE_URL")

    if database_url:
        return database_url

    db_user = os.getenv("DB_USER", "root")
    db_password = os.getenv("DB_PASSWORD", "1234")
    db_host = os.getenv("DB_HOST", "127.0.0.1")
    db_port = os.getenv("DB_PORT", "3308")
    db_name = os.getenv("DB_NAME", "dental_clinic")

    return (
        f"mysql+pymysql://{db_user}:{db_password}"
        f"@{db_host}:{db_port}/{db_name}"
    )


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")

    SQLALCHEMY_DATABASE_URI = build_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    LOG_DIRECTORY = os.getenv("LOG_DIRECTORY", str(BASE_DIR / "logs"))
    LOG_FILE_NAME = os.getenv("LOG_FILE_NAME", "clinic.log")