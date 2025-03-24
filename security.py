import secrets
import hashlib
from typing import Optional

from .logger import setup_logger, log_operation

# Настройка логгера
logger = setup_logger("core.security")

def generate_api_key(length: int = 32) -> str:
    """Генерация API ключа указанной длины"""
    return secrets.token_hex(length // 2)

def hash_key(api_key: str) -> str:
    """Хеширование API ключа для безопасного хранения"""
    return hashlib.sha256(api_key.encode()).hexdigest()

def verify_key_hash(api_key: str, hashed_key: str) -> bool:
    """Проверка API ключа по его хешу"""
    return hash_key(api_key) == hashed_key

def generate_rate_limit_key(api_key: str, endpoint: str) -> str:
    """Создание ключа для ограничения частоты запросов"""
    return f"{api_key}:{endpoint}"

def mask_api_key(api_key: str) -> str:
    """Маскирование API ключа для логов и вывода (показывает только первые 4 и последние 4 символа)"""
    if len(api_key) <= 8:
        return "****"
    return f"{api_key[:4]}...{api_key[-4:]}"