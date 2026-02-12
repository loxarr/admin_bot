# Telegram Bot

Бот для проверки статуса пользователей Telegram.

## Установка

1. Активируй виртуальное окружение:
```bash
source telegram_bot_env/bin/activate
```

2. Установи зависимости:
```bash
pip install -r requirements.txt
```

3. Настрой переменные окружения в файле `.env`:
```
API_ID=your_api_id
API_HASH=your_api_hash
BOT_TOKEN=your_bot_token
```

## Использование

### Запуск основного бота
```bash
python bot.py
```

### Проверка конкретного пользователя
```bash
python check_user_example.py
```

Функция `get_user_entity(identifier)` выводит полную информацию о пользователе по username, ID или ссылке на профиль.

## Стек
- Язык: Python 3.12+
- Telegram MTProto: Telethon 1.36.0 (полный клиент API)
- Конфигурация: dotenv (.env файлы)
- Планировщик: schedule (автопроверки)
- Логирование: logging (структурированные логи)
- Парсинг: re (регулярные выражения)
- Асинхронность: asyncio (неблокирующие проверки)

## Структура

- `bot.py` — основной файл бота
- `check_user_example.py` — пример для проверки одного пользователя
- `bot_settings.json` — конфигурация бота
- `bot_session.session` — сессия клиента Telegram
