import asyncio
import logging
import sys
import os
import time
from loguru import logger

from handlers.admin_handlers import greeting_handler
from handlers.handlers import register_greeting_handler
from system.dispatcher import dp, bot

logger.add("logs/log.log", retention="1 days", enqueue=True)  # Логирование бота

file_path = 'setting/account/session_name.session-journal'
try:
    time.sleep(1)
    os.remove(file_path)
    time.sleep(3)
    logger.info(f"Файл {file_path} успешно удален.")
except FileNotFoundError:
    logger.info(f"Файл {file_path} не найден.")


async def main() -> None:
    """Запуск бота https://t.me/Newwwbotik_bot"""
    await dp.start_polling(bot, skip_updates=True)
    register_greeting_handler()
    greeting_handler()  # Запись id группы админом


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
