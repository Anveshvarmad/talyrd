import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path("/app")
STORAGE_DIR = BASE_DIR / "storage"
UPLOAD_DIR = STORAGE_DIR / "uploads"
OUTPUT_DIR = STORAGE_DIR / "outputs"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_URL = os.getenv("DATABASE_URL")

APP_NAME = "Talyrd"
APP_VERSION = "0.1.0"
