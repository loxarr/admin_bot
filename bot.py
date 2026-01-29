import asyncio
import logging
import re
import os
import json
from datetime import datetime
import pytz
from dotenv import load_dotenv

from telethon import TelegramClient, events, Button
from telethon.tl.types import UserStatusOffline, UserStatusLastWeek, UserStatusLastMonth
from telethon.errors import FloodWaitError, UsernameNotOccupiedError

load_dotenv()

# --- КОНФИГУРАЦИЯ ---
API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_IDS = [652210871] 
SOURCE_CHANNEL = 'for_testing_my_bot123' 
DATA_FILE = 'bot_settings.json'

MSK = pytz.timezone('Europe/Moscow')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

client = TelegramClient('bot_session', API_ID, API_HASH)

DEFAULT_CONFIG = {
    'check_mode': 'interval',
    'interval_hours': 1,
    'fixed_times': ["10:00", "18:00"],
    'check_bots': True,
    'check_users': True,
    'links_data': {}
}

config = DEFAULT_CONFIG.copy()

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---

def save_data():
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=4)

def load_data():
    global config
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                config.update(json.load(f))
        except Exception as e:
            logger.error(f"Ошибка загрузки: {e}")

def get_menu_text():
    mode_str = "⏲ Интервал" if config['check_mode'] == 'interval' else "📍 Точное время"
    val_str = f"{config['interval_hours']} ч." if config['check_mode'] == 'interval' else ", ".join(config['fixed_times'])
    
    return (
        f"🖥 **Главное меню управления**\n\n"
        f"⚙️ **Режим:** `{mode_str}`\n"
        f"⏰ **Настройка:** `{val_str}`\n\n"
        f"🤖 **Боты:** {'✅ ВКЛ' if config['check_bots'] else '❌ ВЫКЛ'}\n"
        f"👤 **Юзеры:** {'✅ ВКЛ' if config['check_users'] else '❌ ВЫКЛ'}\n\n"
        f"📡 **База:** `{len(config['links_data'])} категорий`"
    )

def get_menu_buttons():
    return [
        [Button.inline("🚀 Запустить проверку сейчас", b"run_check")],
        [
            Button.inline(f"🤖 Боты: {'✅' if config['check_bots'] else '❌'}", b"toggle_bots"),
            Button.inline(f"👤 Юзеры: {'✅' if config['check_users'] else '❌'}", b"toggle_users")
        ],
        [Button.inline("📅 Сменить режим (Время/Интервал)", b"change_mode")],
        [Button.inline("🔄 Обновить статус меню", b"refresh")]
    ]

# --- ЛОГИКА ПРОВЕРКИ ---

async def get_detailed_status(username):
    try:
        entity = await client.get_entity(username)
        is_bot = getattr(entity, 'bot', False) or username.lower().endswith('bot')
        
        if is_bot and not config['check_bots']: return None, "skip"
        if not is_bot and not config['check_users']: return None, "skip"

        if hasattr(entity, 'status'):
            status = entity.status
            deleted = entity.deleted
            if isinstance(status, UserStatusOffline) and status.was_online:
                days = (datetime.now(pytz.utc) - status.was_online).days
                if days > 30: return "заморожен (30+ дней)", "dead"
            elif isinstance(status, (UserStatusLastWeek, UserStatusLastMonth)):
                return "не активен (давно)", "inactive"
            elif deleted:
                return "удален ❌", "dead"
        return "живой ✅", "alive"
    except UsernameNotOccupiedError:
        return "удален ❌", "dead"
    except Exception:
        return "ошибка доступа ⚠️", "error"


async def fetch_entity_by_username(identifier, *, as_dict: bool = False):
    """Возвращает объект entity по username/id или словарь с ключевыми полями."""
    try:
        entity = await client.get_entity(identifier)
        return entity
        # if not as_dict:
        #     return entity
        # return {
        #     'id': getattr(entity, 'id', None),
        #     'username': getattr(entity, 'username', None),
        #     'first_name': getattr(entity, 'first_name', None),
        #     'last_name': getattr(entity, 'last_name', None),
        #     'phone': getattr(entity, 'phone', None),
        #     'bot': getattr(entity, 'bot', False),
        #     'status': repr(getattr(entity, 'status', None)),
        # }
    except UsernameNotOccupiedError:
        return {'error': 'Username not occupied'}
    except Exception as e:
        return {'error': str(e)}


async def run_full_check():
    if not config['links_data']: return
    report = []
    for cat, data in config['links_data'].items():
        cat_report = [f"📂 **{cat}**"]
        for link in set(data['links']):
            status_text, status_type = await get_detailed_status(link)
            if status_type != "skip":
                cat_report.append(f"• @{link}: {status_text}")
            await asyncio.sleep(1.5)
        if len(cat_report) > 1:
            report.append("\n".join(cat_report))

    final_msg = "📊 **Отчет по проверке**\n\n" + ("\n\n".join(report) if report else "Ничего не проверено.")
    for admin_id in ADMIN_IDS:
        await client.send_message(admin_id, final_msg)

# --- ОБРАБОТЧИКИ КНОПОК ---

@client.on(events.CallbackQuery)
async def callback_handler(event):
    if event.sender_id not in ADMIN_IDS: return
    
    data = event.data
    if data == b"refresh":
        await event.edit(get_menu_text(), buttons=get_menu_buttons())
    
    elif data == b"toggle_bots":
        config['check_bots'] = not config['check_bots']
        save_data()
        await event.edit(get_menu_text(), buttons=get_menu_buttons())
        await event.answer("Настройка ботов изменена")

    elif data == b"toggle_users":
        config['check_users'] = not config['check_users']
        save_data()
        await event.edit(get_menu_text(), buttons=get_menu_buttons())
        await event.answer("Настройка юзеров изменена")

    elif data == b"run_check":
        await event.answer("🚀 Проверка запущена в фоновом режиме!", alert=True)
        asyncio.create_task(run_full_check())

    elif data == b"change_mode":
        await event.respond(
            "📝 **Как изменить режим?**\n\n"
            "Используйте команды:\n"
            "• `/set_mode interval 2` (каждые 2 часа)\n"
            "• `/set_mode fixed 10:00,18:00` (точное время)",
            buttons=[Button.inline("⬅️ Назад", b"refresh")]
        )

# --- ОБРАБОТЧИКИ КОМАНД ---

@client.on(events.NewMessage(pattern='/start|/settings'))
async def start_handler(event):
    if event.sender_id not in ADMIN_IDS: return
    await event.respond(get_menu_text(), buttons=get_menu_buttons())

@client.on(events.NewMessage(pattern=r'/set_mode (\w+) (.+)'))
async def set_mode_handler(event):
    if event.sender_id not in ADMIN_IDS: return
    mode, value = event.pattern_match.group(1), event.pattern_match.group(2)
    if mode == 'interval':
        config['check_mode'], config['interval_hours'] = 'interval', int(value)
    elif mode == 'fixed':
        config['check_mode'], config['fixed_times'] = 'fixed', [t.strip() for t in value.split(',')]
    save_data()
    await event.respond("✅ Режим обновлен! Нажмите 'Обновить' в меню.", buttons=[Button.inline("⬅️ В меню", b"refresh")])

@client.on(events.NewMessage(chats=SOURCE_CHANNEL))
async def sync_channel(event):
    new_links = {}
    lines = event.text.strip().split('\n')
    current_cat = None
    print(lines)
    for line in lines:
        m = re.match(r'^\d+[\)\.]\s*(.+)', line)
        if m: 
            current_cat = m.group(1).strip()
            new_links[current_cat] = {'links': []}
        elif current_cat:
            f = re.findall(r'(?:@|(?:https?://)?t\.me/)([a-zA-Z0-9_]{3,32})', line)
            new_links[current_cat]['links'].extend(list(set(f)))
    if new_links:
        config['links_data'] = new_links
        save_data()

# --- СТАРТ ---

async def scheduler():
    while True:
        await asyncio.sleep(60)
        now = datetime.now(MSK)
        if config['check_mode'] == 'interval':
            if now.minute == 0 and now.hour % config['interval_hours'] == 0:
                await run_full_check()
        elif config['check_mode'] == 'fixed':
            if now.strftime("%H:%M") in config['fixed_times']:
                await run_full_check()
                await asyncio.sleep(61)

async def main():
    load_data()
    await client.start(bot_token=BOT_TOKEN)
    asyncio.create_task(scheduler())
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())

