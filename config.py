import logging
import os
from typing import Optional, Dict, Any
from pydantic import BaseModel
from dotenv import load_dotenv

# Загрузка переменных из .env файла
load_dotenv()

# Настройки логирования
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL
}

class Settings(BaseModel):
    """Настройки приложения"""

    # Базовые настройки приложения
    APP_NAME: str = "duckduckgo-ai-openai-api"
    API_PREFIX: str = ""
    DEBUG: bool = os.getenv("DEBUG", "False") == "True"

    # Настройки безопасности
    IGNPRE_API_KEYS: bool = os.getenv("IGNPRE_API_KEYS", "False") == "True"
    ADMIN_TOKEN: str = os.getenv("ADMIN_TOKEN", "your-super-secret-admin-token")

    # Настройки базы данных
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")
    DB_MODE: str = "PostgreSQL" if DATABASE_URL else "SQLite"
    SQLITE_DB_PATH: str = os.getenv("SQLITE_DB_PATH", "api_keys.db")

    # Настройки моделей
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "llama-3.3-70b")
    AVAILABLE_MODELS: Dict[str, str] = {
        "o3-mini": "o3-mini",
        "gpt-4o-mini": "gpt-4o-mini",
        "llama-3.3-70b": "llama-3.3-70b",
        "claude-3-haiku": "claude-3-haiku",
        "mixtral-8x7b": "mixtral-8x7b"
    }

    # Настройки CORS
    CORS_ORIGINS: list = ["*"]
    CORS_HEADERS: list = ["*"]


    LOG_LEVEL_STR: str = os.getenv("LOG_LEVEL", "INFO").upper()
    LOG_LEVEL: int = LOG_LEVELS.get(LOG_LEVEL_STR, logging.INFO)


settings = Settings()