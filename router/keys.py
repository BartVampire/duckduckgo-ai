import secrets
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field

from config import settings
from logger import setup_logger, log_operation
from db_manager import db_manager
from .dependencies import validate_admin_token

# Настройка логгера
logger = setup_logger("api.keys")

router = APIRouter(
    prefix="/api-keys",
    tags=["API Keys"],
    dependencies=[Depends(validate_admin_token)]
)


class ApiKeyCreate(BaseModel):
    """
    Модель для создания API ключа.

    Attributes:
        description (Optional[str]): Описание ключа для удобства идентификации (опционально)

    Example:
        {
            "description": "Ключ для Telegram бота"
        }
    """
    description: Optional[str] = Field(None, description="Описание ключа (опционально)")


class ApiKeyResponse(BaseModel):
    """
    Модель ответа с API ключом.

    Attributes:
        id (Optional[int]): Идентификатор ключа в базе данных
        key (str): Значение API ключа
        description (Optional[str]): Описание ключа
        created_at (Optional[str]): Дата и время создания ключа
        last_used_at (Optional[str]): Дата и время последнего использования
        usage_count (Optional[int]): Счетчик использований ключа

    Example:
        {
            "id": 1,
            "key": "abcdef1234567890",
            "description": "Ключ для Telegram бота",
            "created_at": "2023-01-01T12:00:00",
            "last_used_at": "2023-01-02T15:30:00",
            "usage_count": 42
        }
    """
    id: Optional[int] = Field(None, description="Идентификатор ключа в базе данных")
    key: str = Field(..., description="Значение API ключа")
    description: Optional[str] = Field(None, description="Описание ключа")
    created_at: Optional[str] = Field(None, description="Дата и время создания ключа")
    last_used_at: Optional[str] = Field(None, description="Дата и время последнего использования")
    usage_count: Optional[int] = Field(0, description="Счетчик использований ключа")


class ApiKeysListResponse(BaseModel):
    """
    Модель списка API ключей.

    Attributes:
        api_keys (List[ApiKeyResponse]): Список API ключей

    Example:
        {
            "api_keys": [
                {
                    "id": 1,
                    "key": "abcdef1234567890",
                    "description": "Ключ для Telegram бота",
                    "created_at": "2023-01-01T12:00:00",
                    "last_used_at": "2023-01-02T15:30:00",
                    "usage_count": 42
                },
                {
                    "id": 2,
                    "key": "0987654321fedcba",
                    "description": "Ключ для веб-приложения",
                    "created_at": "2023-01-03T10:15:00",
                    "last_used_at": null,
                    "usage_count": 0
                }
            ]
        }
    """
    api_keys: List[ApiKeyResponse] = Field(..., description="Список API ключей")


class MessageResponse(BaseModel):
    """
    Модель для сообщений об успешных операциях.

    Attributes:
        detail (str): Детальное описание результата операции

    Example:
        {
            "detail": "API ключ удален"
        }
    """
    detail: str = Field(..., description="Детальное описание результата операции")


# Маршруты
@router.get(
    "/",
    response_model=ApiKeysListResponse,
    summary="Получение списка всех API ключей",
    description="Возвращает список всех API ключей, зарегистрированных в системе."
)
async def list_api_keys() -> ApiKeysListResponse:
    """
    Получение списка всех API ключей.

    Возвращает список всех API ключей, зарегистрированных в системе,
    включая их идентификаторы, описания, даты создания и использования,
    а также счетчики использования.

    Returns:
        ApiKeysListResponse: Объект, содержащий список API ключей

    Raises:
        HTTPException: В случае ошибок при получении данных из базы

    Note:
        Требуется токен администратора для доступа к этому эндпоинту.

    Example:
        ```
        curl -X GET "http://localhost:8989/api-keys/" \
            -H "Authorization: Bearer ваш_админ_токен"
        ```
    """
    log_operation(logger, "request_received", "Запрос на получение списка API ключей")

    try:
        if settings.IGNPRE_API_KEYS:
            return ApiKeysListResponse(api_keys=[])

        api_keys = db_manager.get_all_api_keys()
        log_operation(logger, "request_processed", f"Возвращено {len(api_keys)} API ключей")
        return ApiKeysListResponse(api_keys=api_keys)
    except Exception as e:
        log_operation(logger, "error", f"Ошибка при получении списка API ключей: {str(e)}", level=logger.ERROR)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Внутренняя ошибка сервера: {str(e)}"
        )


@router.post(
    "/",
    response_model=ApiKeyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создание нового API ключа",
    description="Создает новый API ключ с опциональным описанием."
)
async def create_api_key(api_key_create: ApiKeyCreate) -> ApiKeyResponse:
    """
    Создание нового API ключа.

    Генерирует новый API ключ и сохраняет его в базе данных
    с опциональным описанием.

    Args:
        api_key_create (ApiKeyCreate): Параметры для создания ключа

    Returns:
        ApiKeyResponse: Информация о созданном API ключе

    Raises:
        HTTPException: В случае ошибок при создании ключа в базе данных

    Note:
        Требуется токен администратора для доступа к этому эндпоинту.

    Example:
        ```
        curl -X POST "http://localhost:8080/api-keys/" \
            -H "Content-Type: application/json" \
            -H "Authorization: Bearer ваш_админ_токен" \
            -d '{
                "description": "Ключ для Telegram бота"
            }'
        ```
    """
    log_operation(logger, "request_received", "Запрос на создание API ключа")

    try:
        # Генерация нового API ключа
        new_key = secrets.token_hex(16)

        if settings.IGNPRE_API_KEYS:
            return ApiKeyResponse(key=new_key, description=api_key_create.description)

        # Создание API ключа в базе данных
        key_data = db_manager.create_api_key(new_key, api_key_create.description)
        log_operation(logger, "request_processed", f"API ключ создан: {new_key[:4]}...")

        return ApiKeyResponse(**key_data)
    except Exception as e:
        log_operation(logger, "error", f"Ошибка при создании API ключа: {str(e)}", level=logger.ERROR)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Внутренняя ошибка сервера: {str(e)}"
        )


@router.delete(
    "/{key}",
    response_model=MessageResponse,
    summary="Удаление API ключа",
    description="Удаляет указанный API ключ из системы."
)
async def delete_api_key(key: str) -> MessageResponse:
    """
    Удаление API ключа.

    Удаляет указанный API ключ из базы данных системы.

    Args:
        key (str): API ключ для удаления

    Returns:
        MessageResponse: Сообщение об успешном удалении

    Raises:
        HTTPException: В случае если ключ не найден или при ошибках в базе данных

    Note:
        Требуется токен администратора для доступа к этому эндпоинту.

    Example:
        ```
        curl -X DELETE "http://localhost:8080/api-keys/abcdef1234567890" \
            -H "Authorization: Bearer ваш_админ_токен"
        ```
    """
    log_operation(logger, "request_received", f"Запрос на удаление API ключа {key[:4]}...")

    try:
        if settings.IGNPRE_API_KEYS:
            return MessageResponse(detail="API ключ удален")

        deleted = db_manager.delete_api_key(key)

        if not deleted:
            log_operation(logger, "error", f"API ключ не найден: {key[:4]}...", level=logger.WARNING)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API ключ не найден"
            )

        log_operation(logger, "request_processed", f"API ключ удален: {key[:4]}...")
        return MessageResponse(detail="API ключ удален")
    except HTTPException:
        raise
    except Exception as e:
        log_operation(logger, "error", f"Ошибка при удалении API ключа: {str(e)}", level=logger.ERROR)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Внутренняя ошибка сервера: {str(e)}"
        )