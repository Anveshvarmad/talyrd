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
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

APP_NAME = "Talyrd"
APP_VERSION = "0.3.0"

MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "5"))
ALLOWED_EXTENSIONS = {"pdf", "docx", "txt", "tex"}
LATEX_TIMEOUT_SECONDS = 30
