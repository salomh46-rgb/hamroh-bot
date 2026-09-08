import io
import logging
from aiogram import Router, F, types, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile
import database
import gemini_service
import tts_service

logger = logging.getLogger(__name__)
router = Router()

@router.message(F.text.in_(["🎨 Rasm chizish (AI)", "🎨 Мой рисунок (AI)"]))
async def prompt_drawing(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    user = await database.get_user(user_id)
    lang = user.get("language", "uz") if user else "uz"

    if lang == "ru":
        msg = (
            "🎨 **СЕКРЕТНЫЙ АРТ-КЛУБ ДЛЯ ЮНЫХ ХУДОЖНИКОВ!** 🖌️\n\n"
            "Нарисуй свой любимый рисунок на бумаге (животное, сказочный замок, машинку или семью) "
            "и **сфотографируй его сюда** (отправь фото в этот чат)!\n\n"
            "Наш умный искусственный интеллект внимательно рассмотрит твой шедевр, расскажет о нём и подарит тебе **+15 баллов**! 🌟"
        )
    else:
        msg = (
            "🎨 **YOSH MUSAVVIRLARNING SEHRLI MO'YQALAMI!** 🖌️\n\n"
            "Qog'ozga o'zing yoqtirgan rasmni chiz (jonivorlar, sehrli qasr, mashina, quyoshcha yoki oilangni) "
            "va uni **suratga olib menga yubor** (rasm qilib jo'nat)!\n\n"
            "Men sening rasmingni diqqat bilan tomosha qilib, baholayman, maqtayman va senga **+15 ball** sovg'a qilaman! 🌟"
        )

    await message.answer(msg)

@router.message(F.photo)
async def handle_child_drawing(message: types.Message, bot: Bot, state: FSMContext):
    """Bolaning chizgan rasmini qabul qilish va Gemini Vision orqali xotirada tahlil qilish"""
    await state.clear()
    user_id = message.from_user.id
    user = await database.get_user(user_id)
    lang = user.get("language", "uz") if user else "uz"

    wait_text = "🎨 Rasmingni hayrat bilan tomosha qilyapman, bir daqiqa..." if lang == "uz" else "🎨 Внимательно рассматриваю твой рисунок, минуточку..."
    loading = await message.answer(wait_text)

    try:
        # Eng katta o'lchamdagi rasmni xotiraga (BytesIO) yuklab olish
        photo = message.photo[-1]
        photo_stream = io.BytesIO()
        await bot.download(photo, destination=photo_stream)
        photo_bytes = photo_stream.getvalue()

        # Gemini Vision orqali tahlil
        analysis_text = await gemini_service.analyze_child_drawing(photo_bytes, lang=lang)

        # Ball qo'shish (+15 ball)
        new_points = await database.add_user_points(user_id, 15)

        # Ovozli maqtov (TTS in-memory)
        audio_bytes = await tts_service.text_to_speech_bytes(
            analysis_text,
            lang=lang,
            gender="female",
            rate="-2%"
        )

        await loading.delete()

        title = "🎨 **SEHRLI MO'YQALAM TAHLILI:**" if lang == "uz" else "🎨 **ОЦЕНКА НАШЕГО ЮНОГО МАСТЕРА:**"
        caption = (
            f"{title}\n\n"
            f"{analysis_text}\n\n"
            f"⭐ **Ofarin! Chizgan ijoding uchun senga +15 ball berildi!**\n"
            f"🏆 Jami ballaring: **{new_points} ball**"
            if lang == "uz" else
            f"{title}\n\n"
            f"{analysis_text}\n\n"
            f"⭐ **Молодец! За прекрасный рисунок тебе начислено +15 баллов!**\n"
            f"🏆 Всего баллов: **{new_points} баллов**"
        )

        if audio_bytes:
            await message.answer_voice(
                voice=BufferedInputFile(audio_bytes, filename="draw.mp3"),
                caption=caption
            )
        else:
            await message.answer(caption)

    except Exception as e:
        logger.error(f"Rasmni tahlil qilishda nosozlik: {e}")
        err_msg = "Rasmni tahlil qilishda nosozlik yuz berdi." if lang == "uz" else "Произошла ошибка при анализе рисунка."
        await loading.edit_text(f"{err_msg}: {e}")
