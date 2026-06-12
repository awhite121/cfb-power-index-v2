from pathlib import Path
from dotenv import load_dotenv
import os

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
TEMPLATE_DIR = DATA_DIR / "templates"
LOG_DIR = PROJECT_ROOT / "logs"

load_dotenv(PROJECT_ROOT / ".env")
CFBD_API_KEY = os.getenv("CFBD_API_KEY", "").strip()

for folder in [RAW_DIR, PROCESSED_DIR, TEMPLATE_DIR, LOG_DIR]:
    folder.mkdir(parents=True, exist_ok=True)
