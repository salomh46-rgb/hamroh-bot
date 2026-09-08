from aiogram import Router, types
from aiogram.filters import Command
import config
import database

router = Router()

@router.message(Command("stats"))
async def cmd_stats(message: types.Message):
    """Adminlar uchun statistika"""
    if config.ADMIN_IDS and message.from_user.id not in config.ADMIN_IDS:
        await message.answer("Kechirasiz, bu buyruq faqat bot adminlari uchun.")
        return

    stats = await database.get_system_stats()
    await message.answer(
        f"📊 **Hamroh Bot Statistikasi:**\n\n"
        f"👥 Foydalanuvchilar soni: {stats['users']}\n"
        f"⏰ Faol dori eslatmalari: {stats['reminders']}\n"
        f"⭐ Premium a'zolar: {stats['premium']}"
    )
