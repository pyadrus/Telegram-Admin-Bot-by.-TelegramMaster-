import re

from aiogram import F
from aiogram import types
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


@dp.message(F.text)
async def any_message(message: types.Message):
    """
    Проверка сообщения на наличие ссылок если ссылка в сообщении есть, то удаляем сообщение и предупреждаем пользователя.
    """
    logger.info(f'Проверяем сообщение {message.text} от {message.from_user.username} {message.from_user.id}')
    user_id = message.from_user.id  # Получаем ID пользователя
    logger.info(f'Текст сообщения: {message.text}')
    if user_id in allowed_user_ids:  # Проверка на наличие пользователя в списке разрешенных
        logger.info(f'Админ {user_id} написал сообщение {message.text}')
    else:
        try:
            for entity in message.entities:  # Проверка на наличие ссылок
                logger.info(f'Тип ссылки: {entity.type}')
                if entity.type in ["url", "text_link", "mention"]:

                    users = await read_database()
                    for user in users:
                        logger.info(f'ID из базы данных: {user[0]}')

                        if entity.type == "url":
                            link = message.text[entity.offset:entity.offset + entity.length]
                            logger.info(f"Ссылка (url) в сообщении 🔗: {link}")  # Здесь вы можете обработать ссылку
                            username_id = await connect_session_to_telegram_account(link)
                            logger.info(f'ID группы {link}: {username_id}')
                            if username_id == user[0]:
                                user_id = message.from_user.id
                                permissions = ChatPermissions(can_send_messages=False)
                                await bot.restrict_chat_member(chat_id=message.chat.id, user_id=user_id,
                                                               permissions=permissions)
                                await message.reply(
                                    f"Пользователь {message.reply_to_message.from_user.mention} был заглушен.")

                                logger.info(f'Сообщение от:({message.from_user.username} {message.from_user.id}). '
                                            f'Текст сообщения {message.text}')
                                await message.delete()  # Удаляем сообщение содержащее ссылку

                        elif entity.type == "text_link":
                            link = entity.url
                            logger.info(
                                f"Ссылка (text_link) в сообщении 🔗: {link}")  # Здесь вы можете обработать ссылку
                            username_id = await connect_session_to_telegram_account(link)
                            logger.info(f'ID группы {link}: {username_id}')
                            if username_id == user[0]:
                                logger.info(f'Сообщение от:({message.from_user.username} {message.from_user.id}). '
                                            f'Текст сообщения {message.text}')
                                await message.delete()  # Удаляем сообщение содержащее ссылку

                        elif entity.type == "mention":
                            link = message.text[entity.offset:entity.offset + entity.length]
                            logger.info(f"Ссылка (mention) в сообщении 🔗: {link}")  # Здесь вы можете обработать ссылку
                            username_id = await connect_session_to_telegram_account(link)
                            logger.info(f'ID группы {link}: {username_id}')
                            if username_id == user[0]:
                                logger.info(f'Сообщение от:({message.from_user.username} {message.from_user.id}). '
                                            f'Текст сообщения {message.text}')
                                await message.delete()  # Удаляем сообщение содержащее ссылку

        except Exception as e:
            logger.info(f'Возникла ошибка {e}, так как в сообщении {message.text} от {message.from_user.username} '
                        f'{message.from_user.id} нет ссылки')


@dp.edited_message(F.text)
async def edit_message(message: types.Message):
    """
    Проверка изменяемых сообщений на наличие ссылок если есть ссылка, то удаляем сообщение и предупреждаем пользователя.
    """
    logger.info(f'Измененное сообщение пользователем: {message.from_user.id}, текст измененного '
                f'сообщения: {message.text}')
    user_id = message.from_user.id  # Получаем ID пользователя
    if user_id in allowed_user_ids:  # Проверка на наличие пользователя в списке разрешенных
        logger.info(f'Админ {user_id} изменил сообщение {message.text}')
    else:
        try:
            for entity in message.entities:  # Проверка на наличие ссылок
                logger.info(f'Тип ссылки: {entity.type}')
                if entity.type in ["url", "text_link", "mention"]:
                    logger.info(f'Сообщение от:({message.from_user.username} {message.from_user.id}). '
                                f'Текст сообщения {message.text}')
                    await message.delete()  # Удаляем сообщение содержащее ссылку
        except Exception as e:
            logger.info(f'Возникла ошибка {e}, так как в сообщении {message.text} от {message.from_user.username} '
                        f'{message.from_user.id} нет ссылки')


def register_greeting_handler():
    """Регистрируем handlers для бота"""
    dp.message.register(command_start_handler)  # Обработчик команды /start, он же пост приветствия 👋
