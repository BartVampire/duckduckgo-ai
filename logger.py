import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Union

from config import settings

# Эмодзи для различных уровней логирования
EMOJI_LEVELS: Dict[int, str] = {
    logging.DEBUG: "🔍",
    logging.INFO: "ℹ️",
    logging.WARNING: "⚠️",
    logging.ERROR: "❌",
    logging.CRITICAL: "🔥"
}

# Словарь с русскими наименованиями операций
OPERATION_NAMES: Dict[str, str] = {
    "database_init": "📊 Инициализация базы данных",
    "database_connect": "🔌 Подключение к базе данных",
    "api_key_create": "🔑 Создание API ключа",
    "api_key_delete": "🗑️ Удаление API ключа",
    "api_key_validate": "✅ Проверка API ключа",
    "chat_completion": "💬 Запрос чата",
    "admin_validate": "👮 Проверка администратора",
    "server_start": "🚀 Запуск сервера",
    "request_received": "📩 Получен запрос",
    "request_processed": "📤 Обработан запрос",
    "error": "❌ Ошибка"
}


class CustomFormatter(logging.Formatter):
    """Форматтер логов с эмодзи и временными метками"""

    def format(self, record):
        emoji = EMOJI_LEVELS.get(record.levelno, "")
        record.emoji = emoji

        # Добавляем временную метку
        record.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Возвращаем отформатированное сообщение
        return super().format(record)


def setup_logger(name: str, log_level: Union[str, int] = "INFO") -> logging.Logger:
    # Если log_level уже число, используем его напрямую, иначе получаем числовое значение из logging
    if isinstance(log_level, int):
        level = log_level
    else:
        level = getattr(logging, log_level, settings.LOG_LEVEL)

    # Создаем логгер
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Если обработчики уже существуют, не добавляем новые
    if logger.handlers:
        return logger

    # Создаем обработчик для вывода в консоль
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    # Настраиваем форматирование
    log_format = "%(emoji)s [%(timestamp)s] %(levelname)s [%(name)s] - %(message)s"
    formatter = CustomFormatter(log_format)
    console_handler.setFormatter(formatter)

    # Добавляем обработчик к логгеру
    logger.addHandler(console_handler)

    # Если включен режим отладки, добавляем файловый обработчик
    if settings.DEBUG:
        # Создаем директорию для логов, если она не существует
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        # Создаем обработчик для записи в файл
        file_handler = logging.FileHandler(f"logs/{name}.log", encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)

        # Добавляем обработчик к логгеру
        logger.addHandler(file_handler)

    return logger

def log_operation(logger: logging.Logger, operation: str, details: str = "", level: int = logging.INFO) -> None:
    """Логирование операций с русскими названиями и эмодзи"""
    operation_name = OPERATION_NAMES.get(operation, operation)
    message = f"{operation_name}: {details}" if details else operation_name
    logger.log(level, message)