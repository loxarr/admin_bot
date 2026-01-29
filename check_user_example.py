import asyncio
from bot import client, load_data

async def get_user_entity(identifier):
    """Возвращает entity пользователя по username/id/URL."""
    try:
        entity = await client.get_entity(identifier)
        print(entity)
        return entity
    except Exception as e:
        print(f"Ошибка: {e}")
        return None

async def main():
    load_data()
    await client.start()

    entity = await get_user_entity('https://t.me/TheGetAnyID_bot')

    await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
