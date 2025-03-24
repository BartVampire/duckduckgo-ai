import uvicorn
import logging
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from config import settings
from logger import setup_logger, log_operation
from router import router as all_router

# Настройка логгера
logger = setup_logger("main")
# Создание приложения FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    description="API для работы с DuckDuckGo AI в формате совместимом с OpenAI",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.openapi_components = {
    "securitySchemes": {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Введите токен администратора или API ключ с префиксом 'Bearer '"
        }
    }
}

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров
app.include_router(all_router)

# Настройка статических файлов и шаблонов
app_directory = Path(__file__).parent
static_directory = app_directory

# Обработчик ошибок
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    log_operation(logger, "error", f"Необработанная ошибка: {str(exc)}", level=logging.ERROR)
    return JSONResponse(
        status_code=500,
        content={"detail": f"Внутренняя ошибка сервера: {str(exc)}"}
    )

# Главная страница
@app.get("/", response_class=HTMLResponse)
async def serve_html():
    """Отдача HTML страницы"""
    try:
        html_path = static_directory / "website.html"
        with open(html_path, "r", encoding="utf-8") as file:
            html_content = file.read()
        return HTMLResponse(content=html_content)
    except Exception as e:
        log_operation(logger, "error", f"Ошибка при загрузке HTML: {str(e)}", level=logger.ERROR)
        return HTMLResponse(content="<h1>Ошибка при загрузке веб-интерфейса</h1>")

# Маршрут для проверки состояния сервера
@app.get("/health", tags=["Health"])
async def health_check():
    """Маршрут для проверки состояния сервера"""
    return {
        "status": "ok",
        "db_mode": settings.DB_MODE,
        "ignore_api_keys": settings.IGNPRE_API_KEYS
    }

# Запуск приложения
if __name__ == "__main__":
    log_operation(logger, "server_start", f"Запуск сервера на порту 8080, режим БД: {settings.DB_MODE}")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080,
        reload=settings.DEBUG
    )