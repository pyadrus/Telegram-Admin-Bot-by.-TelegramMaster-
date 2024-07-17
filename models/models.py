from telethon import TelegramClient
from loguru import logger


async def connect_session_to_telegram_account(username_messages):
    api_id = 12345
    api_hash = '0123456789abcdef0123456789abcdef'
    session_name = 'session_name'

    client = TelegramClient(f'setting/account/{session_name}', api_id, api_hash)
    await client.connect()
    logger.info(f'Подключено к аккаунту Telegram с именем сеанса {session_name}')
    username = await client.get_entity(f'{username_messages}')
    logger.info(f"ID группы {username_messages}: {username.id}")
    await client.disconnect()
