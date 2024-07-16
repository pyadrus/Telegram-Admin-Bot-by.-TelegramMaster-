import asyncio
import logging
import sys

from loguru import logger

from handlers.handlers import register_greeting_handler
from system.dispatcher import dp, bot

logger.add("logs/log.log", retention="1 days", enqueue=True)  # Логирование бота


async def main() -> None:
    """Запуск бота https://t.me/Newwwbotik_bot"""
    await dp.start_polling(bot)
    register_greeting_handler()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
