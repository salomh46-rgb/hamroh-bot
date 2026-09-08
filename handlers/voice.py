import os
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

    temp_audio = f"voice_{user_id}_{int(time.time())}.ogg"
    try:
        # Telegramdan ovozli faylni yuklab olish
        file_info = await bot.get_file(message.voice.file_id)
        await bot.download_file(file_info.file_path, destination=temp_audio)

        await status_msg.edit_text(loading_text_2)

        # 1. Avval Gemini Multimodal Audio orqali sinab ko'ramiz (eng ishonchli va yuqori aniqlikda)
        history = await database.get_recent_chat_history(user_id, limit=6)
        ai_res = await gemini_service.process_voice_audio(
            temp_audio, 
            user_type=user_type, 
            history=history,
            lang=lang,
            appeal=appeal
        )

        text = ai_res.get("transcribe", "")
        response_text = ai_res.get("response", "")

        # 2. Agar Gemini transkripsiya bermasa, Whisper STT ga murojaat qilamiz
        if not text:
            text = await whisper_service.audio_to_text(temp_audio)
            if text:
                response_text = await gemini_service.chat_response(
                    text, 
                    user_type=user_type, 
                    history=history,
                    lang=lang,
                    appeal=appeal
                )

        if not response_text or (not text and "xatolik" in response_text.lower()):
            await status_msg.edit_text(error_listen_text)
            return

        # Suhbat tarixini saqlash
        user_msg = text if text else ("[Ovozli xabar]" if lang == "uz" else "[Голосовое сообщение]")
        await database.save_chat_message(user_id, "user", user_msg)
        await database.save_chat_message(user_id, "model", response_text)

        await status_msg.delete()

        # Ovozli javob (TTS) generatsiya qilish
        voice_resp_file = f"resp_{user_id}_{int(time.time())}.mp3"
        import tts_service
        audio_created = await tts_service.text_to_speech_file(
            response_text, 
            voice_resp_file,
            lang=lang,
            gender=gender
        )

        if audio_created:
            voice_input = types.FSInputFile(voice_resp_file)
            caption_text = f"🗣️ *\"{text}\"*\n\n🤖 {response_text}" if text else f"🤖 {response_text}"
            # Telegram caption limiti 1024 belgi
            if len(caption_text) > 1000:
                await message.answer_voice(voice=voice_input)
                await message.answer(caption_text)
            else:
                await message.answer_voice(voice=voice_input, caption=caption_text)

            if os.path.exists(voice_resp_file):
                try:
                    os.remove(voice_resp_file)
                except Exception:
                    pass
        else:
            if text:
                await message.answer(f"🗣️ *\"{text}\"*\n\n🤖 {response_text}")
            else:
                await message.answer(f"🤖 {response_text}")


    except Exception as e:
        logger.error(f"Ovozli xabarni qayta ishlashda xato: {e}")
        await status_msg.edit_text(f"Ovozni qabul qilishda nosozlik yuz berdi: {e}")
    finally:
        if os.path.exists(temp_audio):
            try:
                os.remove(temp_audio)
            except Exception:
                pass

