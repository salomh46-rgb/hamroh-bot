import os
import io
import time
import logging
from aiogram import Router, F, types
from aiogram import Bot
import database
import whisper_service
import gemini_service

logger = logging.getLogger(__name__)
router = Router()

@router.message(F.voice)
async def handle_voice_message(message: types.Message, bot: Bot):
    """Ovozli xabarni qabul qilish, tushunish va javob qaytarish"""
    user_id = message.from_user.id
    user = await database.get_user(user_id)
    user_type = user.get("user_type", "keksa") if user else "keksa"
    lang = user.get("language", "uz") if user else "uz"
    gender = user.get("gender", "female") if user else "female"
    appeal = user.get("appeal", "") if user else ""

    loading_text_1 = "🎙️ Ovoz tinglanmoqda..." if lang == "uz" else "🎙️ Слушаю голос..."
    loading_text_2 = "🧠 Ovoz tahlil qilinmoqda..." if lang == "uz" else "🧠 Анализирую сообщение..."
    error_listen_text = (
        "Kechirasiz, ovozni to'liq ajrata olmadim. Iltimos, yana bir bor gapirib ko'ring."
        if lang == "uz" else
        "Извините, не удалось четко расслышать. Пожалуйста, повторите еще раз."
    )

    status_msg = await message.answer(loading_text_1)

    temp_audio_io = io.BytesIO()
    try:
        # Telegramdan ovozli faylni to'g'ridan-to'g'ri xotiraga (RAM) yuklab olish
        await bot.download(message.voice, destination=temp_audio_io)
        audio_bytes = temp_audio_io.getvalue()

        await status_msg.edit_text(loading_text_2)

        # 1. Gemini Multimodal Audio orqali xotiradagi baytlarni tahlil qilish
        history = await database.get_recent_chat_history(user_id, limit=6)
        ai_res = await gemini_service.process_voice_audio(
            audio_bytes, 
            user_type=user_type, 
            history=history,
            lang=lang,
            appeal=appeal
        )

        text = ai_res.get("transcribe", "")
        response_text = ai_res.get("response", "")

        # 2. Agar Gemini transkripsiya bermasa, matnli chat fallback
        if not text and not response_text:
            await status_msg.edit_text(error_listen_text)
            return

        if not response_text or (not text and "xatolik" in response_text.lower()):
            await status_msg.edit_text(error_listen_text)
            return

        # Suhbat tarixini saqlash
        user_msg = text if text else ("[Ovozli xabar]" if lang == "uz" else "[Голосовое сообщение]")
        await database.save_chat_message(user_id, "user", user_msg)
        await database.save_chat_message(user_id, "model", response_text)

        await status_msg.delete()

        # Ovozli javobni xotirada (in-memory) hosil qilish
        import tts_service
        audio_resp_bytes = await tts_service.text_to_speech_bytes(
            response_text, 
            lang=lang,
            gender=gender
        )

        caption_text = f"🗣️ *\"{text}\"*\n\n🤖 {response_text}" if text else f"🤖 {response_text}"

        if audio_resp_bytes:
            voice_input = types.BufferedInputFile(audio_resp_bytes, filename="voice_resp.mp3")
            if len(caption_text) > 1000:
                await message.answer_voice(voice=voice_input)
                await message.answer(caption_text)
            else:
                await message.answer_voice(voice=voice_input, caption=caption_text)
        else:
            await message.answer(caption_text)

    except Exception as e:
        logger.error(f"Ovozli xabarni qayta ishlashda xato: {e}")
        await status_msg.edit_text(f"Ovozni qabul qilishda nosozlik yuz berdi: {e}")


