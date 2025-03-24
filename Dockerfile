FROM python:3.12-slim

WORKDIR /app

# Установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Создание директорий для базы данных и логов
RUN mkdir -p /data/db /app/logs

# Копирование исходного кода
COPY . .

# Переменные окружения
ENV PYTHONPATH=/app
ENV SQLITE_DB_PATH=/data/db/api_keys.db

# Открытие порта
EXPOSE 8080

# Запуск приложения
CMD ["python", "main.py"]