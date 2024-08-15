import re
import sqlite3
from aiogram import F
from aiogram import types
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import ChatMemberUpdatedFilter, IS_NOT_MEMBER, IS_MEMBER
from aiogram.filters import CommandStart
from aiogram.types import ChatMemberUpdated, ChatPermissions
from aiogram.types import Message
from loguru import logger  # https://github.com/Delgan/loguru

from models.models import connect_session_to_telegram_account, read_database
from system.dispatcher import bot, dp, allowed_user_ids

phone_number_pattern = re.compile(r'(\+?\d{1,3}[-\s]?\d{3,4}[-\s]?\d{2,4}[-\s]?\d{2,4})')


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    user_id = message.from_user.id
    user_name = message.from_user.username
    user_first_name = message.from_user.first_name
    user_last_name = message.from_user.last_name
    user_date = message.date.strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"{user_id} {user_name} {user_first_name} {user_last_name} {user_date}")

    # Если пользователя нет в базе данных, предлагаем пройти регистрацию
    sign_up_text = (
        "⚠️ Бот для администрирования групп ⚠️\n\n"
    )

    # Отправляем сообщение с предложением зарегистрироваться и клавиатурой
    await bot.send_message(message.from_user.id, sign_up_text,
                           disable_web_page_preview=True)


@dp.chat_member(ChatMemberUpdatedFilter(IS_NOT_MEMBER >> IS_MEMBER))
async def on_user_join(event: ChatMemberUpdated):
    """
    Пользователь вступил в группу
    IS_NOT_MEMBER >> IS_MEMBER - новый участник
    IS_MEMBER >> IS_NOT_MEMBER - покинул группу участник группы
    """
    logger.info(f'Пользователь: Имя - {event.new_chat_member.user.first_name} {event.new_chat_member.user.last_name} '
                f'username - {event.new_chat_member.user.username} id - {event.new_chat_member.user.id} '
                f'вступил в группу.')


@dp.message(F.new_chat_members)
async def new_chat_member(message: types.Message):
    """
    Пользователь вступил в группу
    ContentType = new_chat_members (https://docs.aiogram.dev/en/v3.1.1/api/enums/content_type.html)
    """
    await message.delete()  # Удаляем системное сообщение о новом участнике группы


@dp.message(F.left_chat_member)
async def left_chat_member(message: types.Message):
    """
    Пользователь покинул группу
    ContentType = left_chat_member (https://docs.aiogram.dev/en/v3.1.1/api/enums/content_type.html)
    """
    await message.delete()  # Удаляем системное сообщение о покидании группы


async def write_to_database(link):
    try:
        # Подключение к базе данных (создаст файл базы данных, если он не существует)
        conn = sqlite3.connect('setting/database.db')
        cursor = conn.cursor()

        # Создание таблицы, если она не существует
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                link TEXT NOT NULL UNIQUE,
                added_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Проверка на наличие дубликата
        cursor.execute('SELECT COUNT(1) FROM links WHERE link = ?', (link,))
        if cursor.fetchone()[0] > 0:
            logger.info(f"Ссылка '{link}' уже существует в базе данных. Запись не требуется.")
            return

        # Вставка новой записи в таблицу
        cursor.execute('INSERT INTO links (link) VALUES (?)', (link,))

        # Сохранение изменений
        conn.commit()

        logger.info(f"Ссылка '{link}' успешно добавлена в базу данных.")

    except sqlite3.Error as error:
        logger.error(f"Ошибка при работе с базой данных: {error}")

    finally:
        # Закрытие соединения с базой данных
        conn.close()


@dp.message(F.text)
async def any_message(message: types.Message):
    """
    Проверка сообщения на наличие ссылок: если ссылка в сообщении есть, то удаляем сообщение и предупреждаем пользователя.
    """
    logger.info(f'Проверяем сообщение {message.text} от {message.from_user.username} {message.from_user.id}')
    logger.info(f'Текст сообщения: {message.text}')
    try:
        if message.entities:  # Проверяем, есть ли сущности в сообщении
            for entity in message.entities:  # Проверка на наличие ссылок
                logger.info(f'Тип ссылки: {entity.type}')
                if entity.type in ["url", "text_link", "mention"]:
                    link = message.text[
                           entity.offset:entity.offset + entity.length] if entity.type != "text_link" else entity.url
                    logger.info(f"Ссылка ({entity.type}) в сообщении 🔗: {link}")

                    # Проверка на наличие ссылки в базе данных
                    conn = sqlite3.connect('setting/database.db')
                    cursor = conn.cursor()
                    cursor.execute('SELECT COUNT(1) FROM links WHERE link = ?', (link,))
                    link_exists = cursor.fetchone()[0] > 0
                    conn.close()

                    if link_exists:
                        logger.info(f"Ссылка '{link}' найдена в базе данных. Проверка по ID не требуется.")
                        continue  # Переход к следующей ссылке, если она найдена в базе данных

                    logger.info(f"Ссылка '{link}' не найдена в базе данных. Продолжаем проверку по ID.")
                    client, username_id = await connect_session_to_telegram_account(link)

                    if message.from_user.id not in allowed_user_ids:
                        logger.info(f'ID группы {link}: {username_id}')
                        users = await read_database()
                        user_found = False
                        for user in users:
                            logger.info(f'ID из базы данных: {user[0]}')
                            if username_id == user[0]:
                                user_found = True
                                user_id = message.from_user.id
                                permissions = ChatPermissions(can_send_messages=False)
                                try:
                                    await bot.restrict_chat_member(chat_id=message.chat.id, user_id=user_id,
                                                                   permissions=permissions)
                                    logger.info(f'Сообщение от:({message.from_user.username} '
                                                f'{message.from_user.id}). Текст сообщения {message.text}')

                                    await message.delete()  # Удаляем сообщение содержащее ссылку
                                    await client.disconnect()
                                except TelegramBadRequest:
                                    await client.disconnect()
                        if not user_found:
                            logger.info(
                                f'ID группы {link}: {username_id} не найдено в базе данных. Записываем ссылку в базу данных.')
                            await write_to_database(link)  # Запись ссылки в базу данных
                    logger.info(f'Сообщение от админа:({message.from_user.username} '
                                f'{message.from_user.id}). Текст сообщения {message.text}')
                    await client.disconnect()
    except Exception as error:
        logger.info(f'Ошибка: {error}')  # Обработка ошибки


@dp.edited_message(F.text)
async def edit_message(message: types.Message):
    """
    Проверка изменяемых сообщений на наличие ссылок если есть ссылка, то удаляем сообщение и предупреждаем пользователя.
    """
    logger.info(f'Проверяем сообщение {message.text} от {message.from_user.username} {message.from_user.id}')
    logger.info(f'Текст сообщения: {message.text}')
    try:
        if message.entities:  # Проверяем, есть ли сущности в сообщении
            for entity in message.entities:  # Проверка на наличие ссылок
                logger.info(f'Тип ссылки: {entity.type}')
                if entity.type in ["url", "text_link", "mention"]:
                    link = message.text[
                           entity.offset:entity.offset + entity.length] if entity.type != "text_link" else entity.url
                    logger.info(f"Ссылка ({entity.type}) в сообщении 🔗: {link}")

                    client, username_id = await connect_session_to_telegram_account(link)
                    logger.info(f'ID группы {link}: {username_id}')
                    users = await read_database()
                    for user in users:
                        logger.info(f'ID из базы данных: {user[0]}')
                        if username_id == user[0]:
                            user_id = message.from_user.id
                            permissions = ChatPermissions(can_send_messages=False)
                            await bot.restrict_chat_member(chat_id=message.chat.id, user_id=user_id,
                                                           permissions=permissions)
                            logger.info(f'Сообщение от:({message.from_user.username} '
                                        f'{message.from_user.id}). Текст сообщения {message.text}')
                            await message.delete()  # Удаляем сообщение содержащее ссылку
                            await client.disconnect()
    except Exception as error:
        logger.info(f'Ошибка: {error}')  # Обработка ошибки


def register_greeting_handler():
    """Регистрируем handlers для бота"""
    dp.message.register(command_start_handler)  # Обработчик команды /start, он же пост приветствия 👋
