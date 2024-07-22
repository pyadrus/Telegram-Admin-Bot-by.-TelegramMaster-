import sqlite3

from aiogram import types
from aiogram.filters import Command
from loguru import logger

from system.dispatcher import dp  # Подключение к боту и диспетчеру пользователя

# Инициализация базы данных SQLite
conn = sqlite3.connect('setting/database.db')
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS groups (id INTEGER PRIMARY KEY)')


def checking_for_presence_in_the_user_database(user_id):
    # Инициализация базы данных SQLite
    conn = sqlite3.connect('setting/database.db')
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS groups (id INTEGER PRIMARY KEY)')
    # Проверка наличия ID в базе данных
    cursor.execute('SELECT id FROM groups WHERE id = ?', (user_id,))
    result = cursor.fetchone()
    return result


@dp.message(Command('id'))
async def process_id_command(message: types.Message):
    """Обработчик команды /id"""
    try:
        user_id = int(message.text.split()[1])
        result = checking_for_presence_in_the_user_database(user_id)  # Запись ID в базу данных
        if result is None:
            cursor.execute('INSERT INTO groups (id) VALUES (?)', (user_id,))
            conn.commit()
            await message.reply(f"ID {user_id} успешно записан в базу данных.")
        else:
            await message.reply(f"ID {user_id} уже существует в базе данных.")
    except (IndexError, ValueError):
        await message.reply("Используйте команду /id followed by ваш ID.")
    except Exception as error:
        logger.exception(error)


def greeting_handler():
    dp.message.register(process_id_command)
