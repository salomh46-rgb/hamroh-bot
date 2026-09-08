import os
import time
from aiogram import Router, F, types, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile
import database
import gemini_service
import tts_service

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
    """Bolaning chizgan rasmini qabul qilish va Gemini Vision orqali tahlil qilish"""
    await state.clear()
    user_id = message.from_user.id
    user = await database.get_user(user_id)
    lang = user.get("language", "uz") if user else "uz"

    wait_text = "🎨 Rasmingni hayrat bilan tomosha qilyapman, bir daqiqa..." if lang == "uz" else "🎨 Внимательно рассматриваю твой рисунок, минуточку..."
    loading = await message.answer(wait_text)

    # Eng katta o'lchamdagi rasmni yuklab olish
    photo = message.photo[-1]
    temp_img = f"drawing_{user_id}_{int(time.time())}.jpg"

    try:
        file_info = await bot.get_file(photo.file_id)
        await bot.download_file(file_info.file_path, destination=temp_img)

        # Gemini Vision orqali tahlil
        analysis_text = await gemini_service.analyze_child_drawing(temp_img, lang=lang)

        # Ball qo'shish (+15 ball)
        new_points = await database.add_user_points(user_id, 15)

        # Ovozli maqtov (TTS)
        voice_file = f"draw_voice_{user_id}_{int(time.time())}.mp3"
        audio_path = await tts_service.text_to_speech_file(
            analysis_text,
            voice_file,
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

        if audio_path:
            await message.answer_voice(
                voice=FSInputFile(audio_path),
                caption=caption
            )
            if os.path.exists(audio_path):
                try:
                    os.remove(audio_path)
                except Exception:
                    pass
        else:
            await message.answer(caption)

    except Exception as e:
        await loading.edit_text(f"Rasmni tahlil qilishda nosozlik yuz berdi: {e}")
    finally:
        if os.path.exists(temp_img):
            try:
                os.remove(temp_img)
            except Exception:
                pass
