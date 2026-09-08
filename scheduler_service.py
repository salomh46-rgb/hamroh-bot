import logging
from datetime import datetime
from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import database
import gemini_service

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

async def check_and_send_reminders(bot: Bot):
    """Har daqiqada dori eslatmalarini tekshirib yuborish"""
    try:
        now_str = datetime.now().strftime("%H:%M")
        reminders = await database.get_all_active_reminders_by_time(now_str)
        
        for rem in reminders:
            user_id = rem["user_id"]
            dori_nomi = rem["dori_nomi"]
            vaqt = rem["vaqt"]
            lang = rem.get("language") or "uz"
            gender = rem.get("gender") or "female"
            user_name = rem.get("appeal") or rem.get("name") or rem.get("full_name") or ("qadrdonimiz" if lang == "uz" else "дорогой друг")

            msg_text = await gemini_service.generate_reminder_text(user_name, dori_nomi, vaqt, lang=lang)

            try:
                import tts_service
                import os
                import time
                from aiogram.types import FSInputFile

                rem_voice_file = f"rem_{user_id}_{int(time.time())}.mp3"
                audio_path = await tts_service.text_to_speech_file(
                    msg_text, 
                    rem_voice_file, 
                    lang=lang,
                    gender=gender,
                    rate="-5%"
                )

                header = "💊 **НАПОМИНАНИЕ О ЛЕКАРСТВЕ**" if lang == "ru" else "💊 **DORI ESLATMASI**"

                if audio_path:
                    voice_in = FSInputFile(audio_path)
                    await bot.send_voice(
                        chat_id=user_id,
                        voice=voice_in,
                        caption=f"{header}\n\n{msg_text}"
                    )
                    if os.path.exists(audio_path):
                        try:
                            os.remove(audio_path)
                        except Exception:
                            pass
                else:
                    await bot.send_message(
                        chat_id=user_id,
                        text=f"{header}\n\n{msg_text}"
                    )
                logger.info(f"Eslatma yuborildi: user={user_id}, dori={dori_nomi}, lang={lang}")
            except Exception as e:
                logger.error(f"Eslatmani yuborishda xatolik (user_id={user_id}): {e}")

    except Exception as e:
        logger.error(f"Scheduler tekshiruvida xatolik: {e}")

def start_scheduler(bot: Bot):
    """Scheduler ishga tushirish"""
    if not scheduler.running:
        scheduler.add_job(
            check_and_send_reminders,
            trigger=CronTrigger(second=0),
            args=[bot],
            id="reminders_job",
            replace_existing=True
        )
        scheduler.start()
        logger.info("APScheduler dori eslatmalari tekshiruvi ishga tushdi.")
