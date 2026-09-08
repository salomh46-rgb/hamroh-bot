import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

import config
import database
from scheduler_service import start_scheduler
from handlers import all_routers

# Loglarni sozlash
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("HamrohBot")

async def main():
    if not config.TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN topilmadi! Iltimos, .env faylini to'ldiring.")
        return

    logger.info("Hamroh Bot ishga tushirilmoqda...")

    # Bot va Dispatcher obyektlari
    bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # Routerlarni ulash
    for router in all_routers:
        dp.include_router(router)

    # Ma'lumotlar bazasini ishga tushirish
    db_pool = await database.init_db()
    if not db_pool:
        logger.warning("PostgreSQL ulanishida muammo bo'ldi. Baza sozlamalarini (.env) tekshiring!")

    # Dori eslatmalari schedulerini ishga tushirish
    start_scheduler(bot)

    # Telegram Bot "Меню" komandalarini o'rnatish
    from aiogram.types import BotCommand
    await bot.set_my_commands([
        BotCommand(command="start", description="Botni qayta boshlash / Перезапуск"),
        BotCommand(command="role", description="Rejim / Tilni o'zgartirish / Сменить режим"),
        BotCommand(command="sos", description="Shifokor & Tez yordam / Врач и SOS"),
        BotCommand(command="help", description="Qo'llanma va yordam / Справка")
    ])

    # Eski kutilayotgan yangilanishlarni tashlab yuborish va pollingni boshlash
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Bot Telegram serverlari bilan muvaffaqiyatli bog'landi va xabarlarni qabul qilmoqda!")
    
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        if database.db_pool:
            await database.db_pool.close()
        logger.info("Bot to'xtatildi.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot faoliyati foydalanuvchi tomonidan yakunlandi.")
