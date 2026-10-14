import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILE = BASE_DIR / "config.json"

with CONFIG_FILE.open("r", encoding="utf-8") as f:
    CONFIG = json.load(f)

BOT_TOKEN = CONFIG.get("BOT_TOKEN", "").strip()
LOCAL_API_URL = CONFIG.get("LOCAL_API_URL", "").strip().rstrip("/")
MAX_HEIGHT = int(CONFIG.get("MAX_HEIGHT", 720))

# Channel tujuan. Kosong = video dikirim balik ke chat user.
_raw_channel = str(CONFIG.get("CHANNEL_ID", "")).strip()
CHANNEL_ID = int(_raw_channel) if _raw_channel.lstrip("-").isdigit() else _raw_channel

# Privasi
ALLOWED_USER_IDS = {int(x) for x in CONFIG.get("ALLOWED_USER_IDS", [])}
ONLY_OWNER_CAN_DELETE = bool(CONFIG.get("ONLY_OWNER_CAN_DELETE", True))
PROTECT_CONTENT = bool(CONFIG.get("PROTECT_CONTENT", False))

DOWNLOAD_DIR = BASE_DIR / "downloads"
DOWNLOAD_DIR.mkdir(exist_ok=True)

MAX_FILE_MB = 2000 if LOCAL_API_URL else 50
