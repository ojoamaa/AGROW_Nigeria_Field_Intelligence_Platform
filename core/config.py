import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env before reading APP_DATA_DIR. Existing process variables still win.
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

# Local releases use one stable data directory outside replaceable source folders.
# Render/PostgreSQL deployments keep the source directory for transient media unless
# APP_DATA_DIR is explicitly configured to a mounted persistent disk.
if os.getenv("APP_DATA_DIR", "").strip():
    APP_DATA_DIR = Path(os.getenv("APP_DATA_DIR")).expanduser().resolve()
elif DATABASE_URL:
    APP_DATA_DIR = BASE_DIR
else:
    APP_DATA_DIR = (Path.home() / "AGROW_DATA").resolve()

DATA_DIR = APP_DATA_DIR / "data"
UPLOAD_DIR = APP_DATA_DIR / "uploads"
AGENT_PHOTO_DIR = UPLOAD_DIR / "agents"
FARMER_PHOTO_DIR = UPLOAD_DIR / "farmers"
QR_DIR = UPLOAD_DIR / "qrcodes"
OFFLINE_FILE = DATA_DIR / "offline_queue.json"

for directory in (APP_DATA_DIR, DATA_DIR, UPLOAD_DIR, AGENT_PHOTO_DIR, FARMER_PHOTO_DIR, QR_DIR):
    directory.mkdir(parents=True, exist_ok=True)
