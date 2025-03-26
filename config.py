import os
from typing import Optional, Dict, Any
from pydantic import BaseModel
from dotenv import load_dotenv

# Загрузка переменных из .env файла
load_dotenv()


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

    # Настройки логирования
    # Эмодзи для различных уровней логирования
    LOG_LEVELS = {
        "DEBUG": 10,
        "INFO": 20,
        "WARNING": 30,
        "ERROR": 40,
        "CRITICAL": 50
    }

    LOG_LEVEL_STR: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_LEVEL: int = LOG_LEVELS.get(LOG_LEVEL_STR, 20)


settings = Settings()