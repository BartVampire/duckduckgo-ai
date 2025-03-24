import json
import logging
import time
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from starlette.responses import StreamingResponse
from duckduckgo_search import DDGS

from config import settings
from logger import setup_logger, log_operation
from .dependencies import validate_api_key

# Настройка логгера
logger = setup_logger("api.chat")

router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)


# Модели данных
class ChatMessage(BaseModel):
    """
      Модель сообщения в чате.

      Attributes:
          role (str): Роль отправителя сообщения ('user', 'assistant' и т.д.)
          content (str): Содержание сообщения

      Example:
          {
              "role": "user",
              "content": "Привет, как ты?"
          }
      """
    role: str = Field(..., description="Роль отправителя сообщения ('user', 'assistant')")
    content: str = Field(..., description="Текстовое содержание сообщения")


class ChatCompletionRequest(BaseModel):
    """
    Модель запроса на генерацию ответа.

    Attributes:
        model (Optional[str]): Название модели для генерации
                              (по умолчанию из settings.DEFAULT_MODEL)
        messages (List[ChatMessage]): Список сообщений в чате
        stream (Optional[bool]): Использовать ли потоковый режим генерации (по умолчанию False)
        max_tokens (Optional[int]): Максимальное количество токенов в ответе
        temperature (Optional[float]): Температура генерации (степень рандомизации)

    Example:
        {
            "model": "llama-3.3-70b",
            "messages": [
                {"role": "user", "content": "Расскажи про Москву"}
            ],
            "stream": false
        }
    """
    model: Optional[str] = Field(
        default=settings.DEFAULT_MODEL,
        description=f"Модель для генерации. Доступные модели: {', '.join(settings.AVAILABLE_MODELS.keys())}"
    )
    messages: List[ChatMessage] = Field(..., description="История сообщений чата")
    stream: Optional[bool] = Field(False, description="Использовать потоковый режим генерации")
    max_tokens: Optional[int] = Field(None, description="Максимальное количество токенов в ответе")
    temperature: Optional[float] = Field(None, description="Температура генерации (от 0.0 до 1.0)")


class ChatCompletionResponse(BaseModel):
    """
    Модель ответа на запрос генерации.

    Attributes:
        id (str): Уникальный идентификатор ответа
        object (str): Тип объекта (всегда "chat.completion")
        created (int): Unix-время создания ответа
        model (str): Название использованной модели
        choices (List[Dict[str, Any]]): Список сгенерированных ответов

    Example:
        {
            "id": "cmpl-1234567890",
            "object": "chat.completion",
            "created": 1632156000,
            "model": "llama-3.3-70b",
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "Москва - столица России..."
                    },
                    "finish_reason": "stop",
                    "index": 0
                }
            ]
        }
    """
    id: str = Field(..., description="Уникальный идентификатор ответа")
    object: str = Field("chat.completion", description="Тип объекта")
    created: int = Field(..., description="Unix-время создания ответа")
    model: str = Field(..., description="Название использованной модели")
    choices: List[Dict[str, Any]] = Field(..., description="Список сгенерированных ответов")


# Маршрут для генерации ответов
@router.post(
    "/completions",
    response_model=ChatCompletionResponse,
    summary="Генерация ответа на запрос пользователя",
    description="Отправляет запрос пользователя к DuckDuckGo AI и возвращает сгенерированный ответ. "
                "Поддерживает стандартный и потоковый режимы генерации."
)
async def chat_completions(
        request: ChatCompletionRequest,
        api_key: str = Depends(validate_api_key)
) -> ChatCompletionResponse | StreamingResponse:
    """
    Эндпоинт для генерации ответов в чате.

    Принимает запрос с сообщениями пользователя и генерирует ответ от AI модели.
    Поддерживает как стандартный режим генерации, так и потоковый (stream).

    Args:
        request (ChatCompletionRequest): Параметры запроса на генерацию
        api_key (str): API ключ, проверенный через зависимость validate_api_key

    Returns:
        Union[ChatCompletionResponse, StreamingResponse]:
            - В обычном режиме возвращает объект ChatCompletionResponse с полным ответом
            - В потоковом режиме возвращает StreamingResponse с событиями генерации

    Raises:
        HTTPException: В случае ошибок генерации или неверных параметров запроса

    Examples:
        Стандартный запрос:
        ```
        curl -X POST "http://localhost:8080/chat/completions" \
            -H "Content-Type: application/json" \
            -H "Authorization: Bearer ваш_api_ключ" \
            -d '{
                "model": "llama-3.3-70b",
                "messages": [
                    {"role": "user", "content": "Расскажи про Москву"}
                ]
            }'
        ```

        Потоковый запрос:
        ```
        curl -X POST "http://localhost:8080/chat/completions" \
            -H "Content-Type: application/json" \
            -H "Authorization: Bearer ваш_api_ключ" \
            -d '{
                "model": "llama-3.3-70b",
                "messages": [
                    {"role": "user", "content": "Расскажи про Москву"}
                ],
                "stream": true
            }'
        ```
    """

    # Получаем последнее сообщение пользователя
    prompt = request.messages[-1].content if request.messages else ""
    # Получаем модель или используем значение по умолчанию
    model = request.model if request.model and request.model in settings.AVAILABLE_MODELS else settings.DEFAULT_MODEL

    log_operation(logger, "chat_completion", f"Запрос с моделью {model}, stream={request.stream}")

    try:
        # Если запрос на потоковую генерацию
        if request.stream:
            log_operation(logger, "chat_completion", "Использование потоковой генерации")

            # Генератор для потока токенов
            def ddgs_streamer():
                start_time = time.time()
                token_count = 0

                # Начало SSE формата
                yield "data: [BEGIN]\n\n"

                try:
                    for token in DDGS().chat_yield(prompt, model=model):
                        token_count += 1
                        chunk = {
                            "id": f"cmpl-{int(time.time() * 1000)}",
                            "object": "chat.completion.chunk",
                            "created": int(time.time()),
                            "model": model,
                            "choices": [{"delta": {"content": token}}]
                        }
                        yield f"data: {json.dumps(chunk)}\n\n"
                except Exception as e:
                    error_chunk = {
                        "error": True,
                        "message": str(e)
                    }
                    yield f"data: {json.dumps(error_chunk)}\n\n"
                    log_operation(logger, "error", f"Ошибка потоковой генерации: {str(e)}", level=logging.ERROR)

                # Завершение SSE
                yield "data: [DONE]\n\n"

                duration = time.time() - start_time
                log_operation(
                    logger,
                    "request_processed",
                    f"Поток завершен. Токенов: {token_count}, время: {duration:.2f}с"
                )

            return StreamingResponse(ddgs_streamer(), media_type="application/x-ndjson")

        # Для непотоковой генерации
        else:
            log_operation(logger, "chat_completion", "Использование стандартной генерации")
            start_time = time.time()

            try:
                # Получаем ответ от DuckDuckGo AI
                result = DDGS().chat(prompt, model=model)

                # Формируем ответ
                response = {
                    "id": f"cmpl-{int(time.time() * 1000)}",
                    "object": "chat.completion",
                    "created": int(time.time()),
                    "model": model,
                    "choices": [{
                        "message": {"role": "assistant", "content": result},
                        "finish_reason": "stop",
                        "index": 0
                    }]
                }

                duration = time.time() - start_time
                log_operation(
                    logger,
                    "request_processed",
                    f"Генерация завершена. Длина ответа: {len(result)}, время: {duration:.2f}с"
                )

                return response

            except Exception as e:
                log_operation(logger, "error", f"Ошибка генерации: {str(e)}", level=logging.ERROR)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Ошибка генерации ответа: {str(e)}"
                )

    except Exception as e:
        log_operation(logger, "error", f"Необработанная ошибка: {str(e)}", level=logging.ERROR)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Внутренняя ошибка сервера: {str(e)}"
        )