from telethon import TelegramClient
from loguru import logger


async def connect_session_to_telegram_account():
    api_id = 12345
    api_hash = '0123456789abcdef0123456789abcdef'
    session_name = 'session_name'

    client = TelegramClient(f'setting/account/{session_name}', api_id, api_hash)
    await client.connect()
    logger.info(f'Подключено к аккаунту Telegram с именем сеанса {session_name}')
    await client.disconnect()

if __name__ == '__main__':
    connect_session_to_telegram_account()
