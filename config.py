import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_SQLITE_URI = f"sqlite:///{BASE_DIR / 'hubtech.db'}"


def get_database_uri():
    use_local_sqlite = os.getenv('USE_LOCAL_SQLITE', 'true').lower() in {'1', 'true', 'yes', 'on'}

    if use_local_sqlite:
        return DEFAULT_SQLITE_URI

    database_url = os.getenv('DATABASE_URL')
    if database_url:
        return database_url

    return DEFAULT_SQLITE_URI


class Config:
    # Base de données
    SQLALCHEMY_DATABASE_URI = get_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Connection pooling - CRITICAL for Neon/cloud PostgreSQL
    # Prevents "SSL connection has been closed unexpectedly"
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,        # Vérifie la connexion avant chaque requête
        'pool_recycle': 300,          # Recycle les connexions après 5 min
        'pool_size': 5,               # Nombre de connexions permanentes
        'max_overflow': 10,           # Connexions supplémentaires si besoin
        'connect_args': {
            'connect_timeout': 10,
            'keepalives': 1,
            'keepalives_idle': 30,
            'keepalives_interval': 10,
            'keepalives_count': 5,
        }
    }

    # Sécurité
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')

    # Upload
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'static/images')
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))

    # Email
    MAIL_SERVER = os.getenv('MAIL_SERVER')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER')

    # OAuth
    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
    GITHUB_CLIENT_ID = os.getenv('GITHUB_CLIENT_ID')
    GITHUB_CLIENT_SECRET = os.getenv('GITHUB_CLIENT_SECRET')