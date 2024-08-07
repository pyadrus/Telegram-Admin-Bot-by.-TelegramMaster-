import re
import sqlite3

from loguru import logger
from telethon import TelegramClient


async def remove_digits_from_url(url):
    # Регулярное выражение для замены цифр в конце ссылки
    cleaned_url = re.sub(r'/\d+$', '', url)
    return cleaned_url


async def connect_session_to_telegram_account(username_messages):
    try:
        api_id = 12345
        api_hash = '0123456789abcdef0123456789abcdef'
        session_name = 'session_name'

        client = TelegramClient(f'setting/account/{session_name}', api_id, api_hash)
        await client.connect()
        logger.info(f'Подключено к аккаунту Telegram с именем сеанса {session_name}')
        try:
            username = await client.get_entity(f'{username_messages}')
            logger.info(f"ID группы {username_messages}: {username.id}")
        except ValueError:
            cleaned_url = await remove_digits_from_url(username_messages)
            try:
                username = await client.get_entity(cleaned_url)
                logger.info(f"ID группы {cleaned_url}: {username.id}")
            except ValueError:
                logger.error(f'Невозможно получить ID группы для {cleaned_url}')
                username = None
        except sqlite3.OperationalError:
            logger.error(f'Не удалось подключиться к аккаунту Telegram с именем сеанса {session_name}')
        username_id = username.id if username else None
        return client, username_id
    except Exception as e:
        logger.error(f'Ошибка при подключении к аккаунту Telegram: {e}')


async def read_database():
    """Чтение с базы данных"""
    connection = sqlite3.connect('setting/database.db')  # Подключение к базе данных
    cursor = connection.cursor()  # Подключение к таблице
    cursor.execute('SELECT * FROM groups')  # Выполнение запроса
    users = cursor.fetchall()  # Выполнение запроса
    cursor.close()  # Закрытие подключения
    connection.close()  # Закрытие подключения
    return users


if __name__ == '__main__':
    read_database()
