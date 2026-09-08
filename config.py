import os
from typing import List
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")

# Admin ID lar ro'yxati
admin_ids_raw = os.getenv("ADMIN_IDS", "")
ADMIN_IDS: List[int] = [int(x.strip()) for x in admin_ids_raw.split(",") if x.strip().isdigit()]

# Gemini AI sozlamalari
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

# Hugging Face & Whisper sozlamalari
HF_TOKEN: str = os.getenv("HF_TOKEN", "")
WHISPER_MODEL: str = os.getenv("WHISPER_MODEL", "maqsudxo1ja/uz-whisper-small-stt")
USE_HF_INFERENCE_API: bool = os.getenv("USE_HF_INFERENCE_API", "false").lower() in ("1", "true", "yes")

# Database sozlamalari
DB_HOST: str = os.getenv("DB_HOST", "localhost")
DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
DB_USER: str = os.getenv("DB_USER", "postgres")
DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
DB_NAME: str = os.getenv("DB_NAME", "hamroh_bot")

DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")


