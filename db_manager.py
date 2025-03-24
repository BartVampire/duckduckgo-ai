import sqlite3
import logging
from contextlib import contextmanager
from typing import Dict, List, Any, Generator, Optional, Union, Tuple

import psycopg2
from psycopg2.extras import RealDictCursor

from config import settings
from logger import setup_logger, log_operation

# Настройка логгера
logger = setup_logger("database")


class DatabaseManager:
    """Менеджер для работы с базой данных SQLite/PostgreSQL"""

    def __init__(self):
        """Инициализация менеджера базы данных"""
        log_operation(logger, "database_init", f"Режим базы данных: {settings.DB_MODE}")
        self.initialize_db()

    @contextmanager
    def get_connection(self) -> Generator:
        """Получение соединения с базой данных"""
        connection = None
        try:
            if settings.IGNPRE_API_KEYS:
                # Если активирован режим игнорирования API ключей
                log_operation(logger, "database_connect", "Режим без базы данных")
                # Создаем фиктивное соединение для совместимости
                yield None
                return

            if settings.DATABASE_URL:
                # PostgreSQL соединение
                log_operation(logger, "database_connect", "PostgreSQL")
                connection = psycopg2.connect(settings.DATABASE_URL, sslmode='require')
                connection.cursor_factory = RealDictCursor
            else:
                # SQLite соединение
                log_operation(logger, "database_connect", "SQLite")
                connection = sqlite3.connect(settings.SQLITE_DB_PATH)
                # Настраиваем SQLite для возврата словарей
                connection.row_factory = sqlite3.Row

            yield connection

            if connection:
                connection.commit()
        except Exception as e:
            if connection:
                connection.rollback()
            log_operation(logger, "error", f"Ошибка базы данных: {str(e)}", level=logging.ERROR)
            raise
        finally:
            if connection:
                connection.close()

    def initialize_db(self) -> None:
        """Инициализация базы данных при первом запуске"""
        if settings.IGNPRE_API_KEYS:
            log_operation(logger, "database_init", "Режим без базы данных активирован")
            return

        with self.get_connection() as conn:
            if not conn:
                return

            cursor = conn.cursor()

            try:
                if settings.DATABASE_URL:
                    # PostgreSQL: таблица openai_api_keys
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS openai_api_keys (
                            id SERIAL PRIMARY KEY,
                            key TEXT UNIQUE NOT NULL,
                            description TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            last_used_at TIMESTAMP,
                            usage_count INTEGER DEFAULT 0
                        )
                    """)
                else:
                    # SQLite: таблица openai_api_keys
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS openai_api_keys (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            key TEXT UNIQUE NOT NULL,
                            description TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            last_used_at TIMESTAMP,
                            usage_count INTEGER DEFAULT 0
                        )
                    """)

                log_operation(logger, "database_init", "База данных успешно инициализирована")
            except Exception as e:
                log_operation(logger, "error", f"Ошибка инициализации базы данных: {str(e)}", level=logging.ERROR)
                raise

    def create_api_key(self, key: str, description: Optional[str] = None) -> Dict[str, Any]:
        """Создание нового API ключа"""
        if settings.IGNPRE_API_KEYS:
            return {"key": key, "description": description}

        with self.get_connection() as conn:
            cursor = conn.cursor()

            try:
                if settings.DATABASE_URL:
                    cursor.execute(
                        "INSERT INTO openai_api_keys (key, description) VALUES (%s, %s) RETURNING id, key, description, created_at",
                        (key, description)
                    )
                    result = cursor.fetchone()
                    key_data = dict(result)
                else:
                    cursor.execute(
                        "INSERT INTO openai_api_keys (key, description) VALUES (?, ?)",
                        (key, description)
                    )
                    key_id = cursor.lastrowid
                    cursor.execute("SELECT id, key, description, created_at FROM openai_api_keys WHERE id = ?",
                                   (key_id,))
                    result = cursor.fetchone()
                    key_data = dict(result)

                log_operation(logger, "api_key_create", f"API ключ создан: {key[:4]}...")
                return key_data

            except Exception as e:
                log_operation(logger, "error", f"Ошибка создания API ключа: {str(e)}", level=logging.ERROR)
                raise

    def delete_api_key(self, key: str) -> bool:
        """Удаление API ключа"""
        if settings.IGNPRE_API_KEYS:
            return True

        with self.get_connection() as conn:
            cursor = conn.cursor()

            try:
                if settings.DATABASE_URL:
                    cursor.execute("DELETE FROM openai_api_keys WHERE key = %s", (key,))
                else:
                    cursor.execute("DELETE FROM openai_api_keys WHERE key = ?", (key,))

                deleted = cursor.rowcount > 0
                if deleted:
                    log_operation(logger, "api_key_delete", f"API ключ удален: {key[:4]}...")
                else:
                    log_operation(logger, "api_key_delete", f"API ключ не найден: {key[:4]}...")

                return deleted

            except Exception as e:
                log_operation(logger, "error", f"Ошибка удаления API ключа: {str(e)}", level=logging.ERROR)
                raise

    def validate_api_key(self, key: str) -> bool:
        """Проверка валидности API ключа и обновление счетчика использования"""
        if settings.IGNPRE_API_KEYS:
            return True

        with self.get_connection() as conn:
            cursor = conn.cursor()

            try:
                if settings.DATABASE_URL:
                    # Проверяем существование ключа и обновляем счетчик и время последнего использования
                    cursor.execute("""
                        UPDATE openai_api_keys 
                        SET usage_count = usage_count + 1, last_used_at = NOW() 
                        WHERE key = %s 
                        RETURNING id
                    """, (key,))
                    result = cursor.fetchone()
                else:
                    # В SQLite обновляем и получаем значение в два запроса
                    cursor.execute("SELECT id FROM openai_api_keys WHERE key = ?", (key,))
                    result = cursor.fetchone()

                    if result:
                        cursor.execute("""
                            UPDATE openai_api_keys 
                            SET usage_count = usage_count + 1, last_used_at = CURRENT_TIMESTAMP 
                            WHERE key = ?
                        """, (key,))

                valid = result is not None
                log_status = "успешно" if valid else "неудачно"
                log_operation(logger, "api_key_validate", f"Проверка API ключа {key[:4]}... - {log_status}")

                return valid

            except Exception as e:
                log_operation(logger, "error", f"Ошибка валидации API ключа: {str(e)}", level=logging.ERROR)
                raise

    def get_all_api_keys(self) -> List[Dict[str, Any]]:
        """Получение всех API ключей"""
        if settings.IGNPRE_API_KEYS:
            return []

        with self.get_connection() as conn:
            cursor = conn.cursor()

            try:
                if settings.DATABASE_URL:
                    cursor.execute("""
                        SELECT id, key, description, created_at, last_used_at, usage_count 
                        FROM openai_api_keys
                        ORDER BY created_at DESC
                    """)
                else:
                    cursor.execute("""
                        SELECT id, key, description, created_at, last_used_at, usage_count 
                        FROM openai_api_keys
                        ORDER BY created_at DESC
                    """)

                # Преобразуем объекты Row в словари
                if settings.DATABASE_URL:
                    result = cursor.fetchall()
                else:
                    result = [dict(row) for row in cursor.fetchall()]

                log_operation(logger, "database_connect", f"Получено {len(result)} API ключей")
                return result

            except Exception as e:
                log_operation(logger, "error", f"Ошибка получения списка API ключей: {str(e)}", level=logging.ERROR)
                raise


# Создаем единственный экземпляр менеджера базы данных
db_manager = DatabaseManager()