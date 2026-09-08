import os
import time
import logging
from aiogram import Router, F, types
from aiogram.types import BufferedInputFile
import database
import gemini_service
import tts_service

logger = logging.getLogger(__name__)
router = Router()

@router.message(F.text.in_(["🎙️ Ovozli suhbat", "🎙️ Голосовой собеседник"]))
async def prompt_voice(message: types.Message):
    user_id = message.from_user.id
    user = await database.get_user(user_id)
    lang = user.get("language", "uz") if user else "uz"

    if lang == "ru":
        await message.answer(
            "🎙️ **Как пользоваться голосовым собеседником:**\n\n"
            "Нажмите и удерживайте значок микрофона 🎙️ внизу экрана Telegram и наговорите ваше сообщение.\n\n"
            "Я внимательно выслушаю вас и отвечу душевным голосовым сообщением!"
        )
    else:
        await message.answer(
            "🎙️ **Ovozli suhbatdan foydalanish:**\n\n"
            "Telegramdagi mikrofon 🎙️ tugmachasini bosib ushlab turing va ovozingizni yozib yuboring.\n\n"
            "Men sizning ovozingizni tinglab, tushunaman va chiroyli ovozda javob qaytaraman!"
        )

@router.message(F.text & ~F.text.startswith("/"))
async def chat_message(message: types.Message):
    """Foydalanuvchi matn yozganda sun'iy intellekt orqali muloyim javob berish"""
    user_id = message.from_user.id
    user = await database.get_user(user_id)
    
    user_type = user.get("user_type", "keksa") if user else "keksa"
    lang = user.get("language", "uz") if user else "uz"
    gender = user.get("gender", "female") if user else "female"
    appeal = user.get("appeal") if user else None

    # Chat tarixini olish
    history = await database.get_recent_chat_history(user_id, limit=6)

    # Gemini orqali javob generatsiya qilish
    response = await gemini_service.chat_with_persona(
        user_id=user_id,
        user_message=message.text,
        user_type=user_type,
        history=history,
        lang=lang,
        appeal=appeal
    )
    
    # Tarixni saqlash
    await database.save_chat_message(user_id, "user", message.text)
    await database.save_chat_message(user_id, "model", response)

    # Matnli javob yuborish
    await message.answer(response)

    # Agar keksa rejimida bo'lsa, ko'zi ojiz yoki o'qish qiyin bo'lganlar uchun ovozli xabar ham qo'shib beramiz
    if user_type == "keksa" and len(response) <= 400:
        try:
            audio_bytes = await tts_service.text_to_speech_bytes(
                text=response,
                lang=lang,
                gender=gender
            )
            if audio_bytes:
                await message.answer_voice(
                    voice=BufferedInputFile(audio_bytes, filename="voice.mp3"),
                    caption="🎙️ *Ovozli talqin*" if lang == "uz" else "🎙️ *Аудиоверсия ответа*"
                )
        except Exception as e:
            logger.error(f"Chat audio hosil qilishda xato: {e}")
