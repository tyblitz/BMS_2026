import os
import json
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
CONFIG_FILE = DATA_DIR / "db_config.json"


class Settings(BaseSettings):
    PROJECT_NAME: str = "BMS Web Application"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "bms-secret-key-change-in-production-2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 # 24 hours
    
    # Initial Decentralized Database (SQLite local default)
    DATABASE_URL: str = f"sqlite:///{DATA_DIR / 'bms_local.db'}"

    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    @classmethod
    def load_active_database_url(cls) -> str:
        """Loads custom configured DB URL if saved by admin, otherwise falls back to default."""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    if "database_url" in cfg and cfg["database_url"].strip():
                        return cfg["database_url"].strip()
            except Exception:
                pass
        return f"sqlite:///{DATA_DIR / 'bms_local.db'}"

    @classmethod
    def save_active_database_url(cls, db_url: str):
        """Persists custom configured DB URL."""
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump({"database_url": db_url}, f, indent=2)


settings = Settings()
