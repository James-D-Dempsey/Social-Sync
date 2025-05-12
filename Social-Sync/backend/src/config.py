# config.py
from dotenv import load_dotenv
from pathlib import Path
import os

BASE_DIR    = Path(__file__).parent.parent.resolve()
DOTENV_PATH = BASE_DIR / ".env"

loaded = load_dotenv(dotenv_path=DOTENV_PATH, verbose=True)
print(f"→ load_dotenv({DOTENV_PATH!r}) returned {loaded!r}")

SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
SPOTIPY_REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")

MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")
