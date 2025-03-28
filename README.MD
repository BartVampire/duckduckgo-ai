# DuckDuckGo AI OpenAI API 🦆

API сервис, имитирующий OpenAI API, но использующий DuckDuckGo AI для генерации ответов.
## ✨ Особенности

- 🔑 Система управления API ключами
- 📡 Поддержка потоковой и обычной генерации ответов
- 💾 Поддержка SQLite и PostgreSQL
- 🚫 Возможность работы без базы данных
- 🌐 Веб-интерфейс для тестирования API
- 📊 Логирование запросов и операций
- 🐳 Поддержка Docker и Docker Compose

## 📋 Требования

- Python 3.8+
- SQLite или PostgreSQL (опционально)
- Docker и Docker Compose (опционально)

## 🛠 Установка и запуск

### Настройка окружения

1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/yourusername/duckduckgo-ai-openai-api.git
   cd duckduckgo-ai-openai-api
   ```

2. Создайте файл .env на основе примера:
   ```bash
   cp .env.example .env
   ```

3. Отредактируйте .env файл, установив нужные значения.

### Запуск локально

1. Создайте и активируйте виртуальное окружение:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Для Linux/Mac
   # или
   venv\Scripts\activate     # Для Windows
   ```

2. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

3. Запустите API сервер:
   ```bash
   python -m app.main
   ```

4. Для запуска Telegram бота (в отдельном терминале):
   ```bash
   python -m telegram_bot.bot
   ```

### Запуск с Docker

1. Сборка и запуск с Docker Compose:
   ```bash
   docker-compose up -d
   ```

2. Для запуска только API без Telegram бота:
   ```bash
   docker-compose up -d api
   ```

3. Для использования PostgreSQL вместо SQLite, раскомментируйте соответствующие строки в docker-compose.yml и настройте переменные окружения.

## 📝 Использование API

### API Ключи

#### Создание API ключа

```bash
curl -X POST http://localhost:8080/api-keys \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-super-secret-admin-token" \
  -d '{"description": "Тестовый ключ"}'
```

Ответ:
```json
{
  "id": 1,
  "key": "generatedapikey123456",
  "description": "Тестовый ключ",
  "created_at": "2025-03-06T12:00:00"
}
```

#### Получение списка API ключей

```bash
curl -X GET http://localhost:8080/api-keys \
  -H "Authorization: Bearer your-super-secret-admin-token"
```

#### Удаление API ключа

```bash
curl -X DELETE http://localhost:8080/api-keys/generatedapikey123456 \
  -H "Authorization: Bearer your-super-secret-admin-token"
```

### Генерация ответов

#### Обычный запрос

```bash
curl -X POST http://localhost:8080/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer generatedapikey123456" \
  -d '{
    "model": "llama-3.3-70b",
    "messages": [{"role": "user", "content": "Расскажи о России"}]
  }'
```

#### Потоковый запрос

```bash
curl -X POST http://localhost:8080/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer generatedapikey123456" \
  -d '{
    "model": "llama-3.3-70b",
    "messages": [{"role": "user", "content": "Расскажи о России"}],
    "stream": true
  }'
```

## 🤖 Telegram бот

Telegram бот позволяет удобно использовать API через мессенджер Telegram.

### Основные команды

- `/start` - Начало работы с ботом
- `/settings` - Настройки бота
- `/clear` - Очистка истории сообщений
- `/model <название_модели>` - Быстрая смена модели

### Настройка бота

1. Получите токен у [@BotFather](https://t.me/BotFather) в Telegram
2. Добавьте токен в файл .env:
   ```
   TELEGRAM_TOKEN=your-telegram-bot-token
   ```
3. Запустите бота через Docker или локально

## 💾 Работа с базой данных

### SQLite

По умолчанию приложение использует SQLite. База данных будет создана по пути, указанному в переменной окружения `SQLITE_DB_PATH`.

### PostgreSQL

Для использования PostgreSQL:

1. Раскомментируйте соответствующие строки в docker-compose.yml
2. Установите переменную окружения:
   ```
   DATABASE_URL=postgresql://user:password@postgres:5432/ddgai
   ```

### Режим без базы данных

Для тестирования или быстрого запуска можно активировать режим без проверки API ключей:

```
IGNPRE_API_KEYS=True
```

В этом режиме все запросы будут обрабатываться без проверки API ключей.

## 📊 Логирование

Приложение ведет детальные логи операций с русскими сообщениями и эмодзи для удобства чтения.

- В режиме отладки (DEBUG=True) логи также сохраняются в директорию logs/
- Уровень логирования можно настроить через переменную LOG_LEVEL

## 📁 Структура проекта

```
duckduckgo-ai-openai-api/
├── app/                      # Основной API сервис
│   ├── api/                  # API маршруты и зависимости
│   ├── core/                 # Конфигурация, логирование, безопасность
│   ├── database/             # Работа с базой данных
│   ├── static/               # Статические файлы и веб-интерфейс
│   └── utils/                # Вспомогательные функции
├── telegram_bot/             # Телеграм бот
│   ├── handlers/             # Обработчики сообщений
│   └── utils/                # Утилиты для бота
├── docs/                     # Документация
├── logs/                     # Директория для логов
├── .env.example              # Пример конфигурации
├── docker-compose.yml        # Docker Compose конфигурация
├── Dockerfile                # Dockerfile
└── requirements.txt          # Зависимости проекта
```

## 🔒 Безопасность

- Всегда изменяйте значение ADMIN_TOKEN перед использованием в продакшене
- Используйте HTTPS/SSL для защиты коммуникации
- Не оставляйте открытый доступ к API из интернета без должной защиты
- Регулярно обновляйте зависимости проекта

## 🤝 Вклад в проект

Вклады в проект приветствуются! Пожалуйста, открывайте issues для отчетов о багах или предложений функций.