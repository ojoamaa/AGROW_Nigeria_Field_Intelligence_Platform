import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
APP_DATA_DIR = Path(os.getenv("APP_DATA_DIR", BASE_DIR))

DATA_DIR = APP_DATA_DIR / "data"
UPLOAD_DIR = APP_DATA_DIR / "uploads"
AGENT_PHOTO_DIR = UPLOAD_DIR / "agents"
FARMER_PHOTO_DIR = UPLOAD_DIR / "farmers"

OFFLINE_FILE = DATA_DIR / "offline_queue.json"

UPLOAD_DIR = BASE_DIR / "uploads"
AGENT_PHOTO_DIR = UPLOAD_DIR / "agents"
FARMER_PHOTO_DIR = UPLOAD_DIR / "farmers"
QR_DIR = UPLOAD_DIR / "qrcodes"
DATA_DIR.mkdir(parents=True, exist_ok=True)