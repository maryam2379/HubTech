import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
VENV_SITE_PACKAGES = BASE_DIR / "hubtech_env" / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages"

if VENV_SITE_PACKAGES.exists() and str(VENV_SITE_PACKAGES) not in sys.path:
    sys.path.insert(0, str(VENV_SITE_PACKAGES))

import os
from flask import Flask
from flask_migrate import Migrate
from config import Config
from db import db
from routes import main_bp
from models import *

app = Flask(__name__)
app.config.from_object(Config)

# Créer le dossier d'upload
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialiser SQLAlchemy et Migrate
db.init_app(app)
migrate = Migrate(app, db)

with app.app_context():
    db.create_all()

app.register_blueprint(main_bp)

if __name__ == '__main__':
    app.run(debug=True)