import os
import time
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
import gemini_service
import database
import tts_service

router = Router()

def get_quiz_kb(lang: str = "uz") -> InlineKeyboardMarkup:
    """Topishmoq javobini ko'rish va yangi savol olish tugmalari"""
    if lang == "ru":
        buttons = [
            [InlineKeyboardButton(text="💡 Посмотреть ответ", callback_data="quiz:show_ans")],
            [InlineKeyboardButton(text="🔄 Новая загадка", callback_data="quiz:next")]
        ]
    else:
        buttons = [
            [InlineKeyboardButton(text="💡 Javobni ko'rish", callback_data="quiz:show_ans")],
            [InlineKeyboardButton(text="🔄 Yangi qiziqarli topshiriq", callback_data="quiz:next")]
        ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Vaqtinchalik so'nggi to'g'ri javobni xotirada saqlash
last_quiz_answers = {}

@router.message(F.text.in_(["🎮 Qiziqarli topishmoq", "🎮 Загадки"]))
async def send_quiz(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    user = await database.get_user(user_id)
    lang = user.get("language", "uz") if user else "uz"

    loading_text = "🤔 Подбираю интересную загадку для тебя..." if lang == "ru" else "🤔 Yangi qiziqarli topshiriq va topishmoq tayyorlanmoqda..."
    loading = await message.answer(loading_text)

    if lang == "ru":
        prompt = (
            "Придумай 1 интересную, весёлую логическую загадку для детей на русском языке. "
            "Формат строго такой:\n"
            "ВОПРОС: <текст загадки>\n"
            "ОТВЕТ: <правильный ответ и добрый комментарий>"
        )
        quiz_text = "На дереве висело пять яблок, два упали. Сколько яблок осталось на дереве?"
        ans_text = "Осталось три яблока! 🍎"
    else:
        prompt = (
            "Bolajonlar uchun o'zbek tilida 1 ta juda qiziqarli mantiqiy topishmoq yoki topshiriq tuz. "
            "Topishmoq o'ylantiruvchi, quvnoq bo'lsin. "
            "Format quyidagicha bo'lsin:\n"
            "SAVOL: <topishmoq matni>\n"
            "JAVOB: <to'g'ri javob va qisqa izoh>"
        )
        quiz_text = "Daraxtda beshta olma bor edi, ikkitasi tushib ketdi. Nechtasi qoldi?"
        ans_text = "Uchta olma qoldi! 🍎"

    client = gemini_service.get_client()
    if client:
        try:
            res = await client.aio.models.generate_content(
                model=gemini_service.config.GEMINI_MODEL,
                contents=prompt
            )
            raw = res.text.strip() if res.text else ""
            if "ВОПРОС:" in raw and "ОТВЕТ:" in raw:
                parts = raw.split("ОТВЕТ:")
                quiz_text = parts[0].replace("ВОПРОС:", "").strip()
                ans_text = parts[1].strip()
            elif "SAVOL:" in raw and "JAVOB:" in raw:
                parts = raw.split("JAVOB:")
                quiz_text = parts[0].replace("SAVOL:", "").strip()
                ans_text = parts[1].strip()
            else:
                quiz_text = raw
        except Exception:
            pass

    last_quiz_answers[user_id] = ans_text
    new_points = await database.add_user_points(user_id, 5)

    # Audio ovoz hosil qilish
    audio_file = f"quiz_{user_id}_{int(time.time())}.mp3"
    audio_path = await tts_service.text_to_speech_file(quiz_text, audio_file, lang=lang, gender="female", rate="-2%")

    await loading.delete()

    if lang == "ru":
        full_caption = (
            f"🧠 **ИНТЕЛЛЕКТУАЛЬНАЯ ЗАГАДКА:**\n\n"
            f"{quiz_text}\n\n"
            f"⭐ За решение загадки тебе начислено +5 баллов! (Всего: {new_points} баллов)"
        )
    else:
        full_caption = (
            f"🧠 **KICHKINTOYLAR UCHUN TOPSHIRIQ:**\n\n"
            f"{quiz_text}\n\n"
            f"⭐ Topshiriqni o'ylaganing uchun +5 ball! (Jami: {new_points} ball)"
        )

    if audio_path:
        voice_in = FSInputFile(audio_path)
        await message.answer_voice(voice=voice_in, caption=full_caption, reply_markup=get_quiz_kb(lang))
        if os.path.exists(audio_path):
            try:
                os.remove(audio_path)
            except Exception:
                pass
    else:
        await message.answer(full_caption, reply_markup=get_quiz_kb(lang))

@router.callback_query(F.data == "quiz:show_ans")
async def show_quiz_answer(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user = await database.get_user(user_id)
    lang = user.get("language", "uz") if user else "uz"

    default_ans = "Молодец! Отличный ответ!" if lang == "ru" else "Topishmoq javobi topildi! Barakalla!"
    ans = last_quiz_answers.get(user_id, default_ans)
    title = "🎯 **Правильный ответ:**" if lang == "ru" else "🎯 **To'g'ri javob:**"
    await callback.message.reply(f"{title}\n\n{ans}")
    await callback.answer()

@router.callback_query(F.data == "quiz:next")
async def next_quiz(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await send_quiz(callback.message, state)
    await callback.answer()

@router.message(F.text.in_(["🏆 Ballarim", "🏆 Мои баллы"]))
async def show_points(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    user = await database.get_user(user_id)
    lang = user.get("language", "uz") if user else "uz"

    points = await database.get_user_points(user_id)

    if lang == "ru":
        daraja = "Юный знаток 🌟"
        if points >= 100:
            daraja = "Повелитель сказок 👑"
        elif points >= 50:
            daraja = "Мастер загадок 🧙"

        await message.answer(
            f"🏆 **Твои достижения и баллы:**\n\n"
            f"💰 Всего очков: **{points} баллов**\n"
            f"🎖️ Твоё звание: **{daraja}**\n\n"
            f"Слушай больше сказок, разгадывай загадки и проходи квесты, чтобы подняться ещё выше!"
        )
    else:
        daraja = "Yosh bilimdon 🌟"
        if points >= 100:
            daraja = "Ertaklar sultoni 👑"
        elif points >= 50:
            daraja = "Zukko topqir 🧙"

        await message.answer(
            f"🏆 **Sening to'plagan ballaring va yutuqlaring:**\n\n"
            f"💰 Jami ballar: **{points} ball**\n"
            f"🎖️ Hozirgi darajang: **{daraja}**\n\n"
            f"Ko'proq ertaklar eshit, topishmoqlarni top va yangi rekordlar o'rnat!"
        )
