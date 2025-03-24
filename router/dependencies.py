from fastapi import Header, HTTPException, status

from config import settings
from logger import setup_logger, log_operation
from db_manager import db_manager
import logging
# Настройка логгера
logger_dependencies = setup_logger("api.dependencies")


async def validate_admin_token(authorization: str = Header(...)):
    """Зависимость для проверки токена администратора"""
    if settings.IGNPRE_API_KEYS:
        log_operation(logger_dependencies, "admin_validate", "Режим без проверки API ключей - пропуск проверки админа")
        return ""

    if not authorization or not authorization.startswith("Bearer "):
        log_operation(logger_dependencies, "error", "Некорректный заголовок Authorization", level=logging.WARNING)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Некорректный или отсутствующий заголовок Authorization"
        )

    token = authorization.split(" ")[1]
    if token != settings.ADMIN_TOKEN:
        log_operation(logger_dependencies, "error", "Недействительный токен администратора", level=logging.WARNING)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недействительный токен администратора"
        )

    log_operation(logger_dependencies, "admin_validate", "Токен администратора успешно проверен")
    return token


async def validate_api_key(authorization: str = Header(...)):
    """Зависимость для проверки API ключа"""
    if settings.IGNPRE_API_KEYS:
        log_operation(logger_dependencies, "api_key_validate", "Режим без проверки API ключей")
        return ""

    if not authorization or not authorization.startswith("Bearer "):
        log_operation(logger_dependencies, "error", "Некорректный заголовок Authorization", level=logging.WARNING)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Некорректный или отсутствующий заголовок Authorization"
        )

    token = authorization.split(" ")[1]
    valid = db_manager.validate_api_key(token)

    if not valid:
        log_operation(logger_dependencies, "error", "Недействительный API ключ", level=logging.WARNING)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный API ключ"
        )

    return token