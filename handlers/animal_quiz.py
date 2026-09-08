import os
import time
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
import database
import gemini_service
import tts_service

router = Router()

# Vaqtinchalik to'g'ri javoblar
quiz_answers = {}

def get_animal_kb(options: list, answer: str, lang: str = "uz") -> InlineKeyboardMarkup:
    buttons = []
    for opt in options:
        is_correct = "1" if opt == answer else "0"
        buttons.append([InlineKeyboardButton(text=f"🐾 {opt}", callback_data=f"anim:{is_correct}:{opt}")])
    next_btn = "🔄 Boshqa hayvon haqida topishmoq" if lang == "uz" else "🔄 Другая загадка о животных"
    buttons.append([InlineKeyboardButton(text=next_btn, callback_data="anim:next")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@router.message(F.text.in_(["🎮 Hayvonlar olami", "🎮 Мир животных"]))
async def start_animal_quiz(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    user = await database.get_user(user_id)
    lang = user.get("language", "uz") if user else "uz"

    loading_text = "🦁 Qiziqarli jonivorlar topishmog'i tayyorlanmoqda..." if lang == "uz" else "🦁 Готовлю весёлую викторину о животных..."
    loading = await message.answer(loading_text)

    q_data = await gemini_service.generate_animal_quiz(lang=lang)
    question = q_data.get("question", "Qaysi hayvon 'Miyov-miyov' deb ovoz chiqaradi?")
    options = q_data.get("options", ["Mushuk", "Kuchuk", "Qo'y", "Ot"])
    answer = q_data.get("answer", "Mushuk")
    fact = q_data.get("fact", "Mushuklar inson bilan do'stlashishni yaxshi ko'radi!")

    quiz_answers[user_id] = {"answer": answer, "fact": fact, "lang": lang}

    # Audio savol
    audio_file = f"anim_{user_id}_{int(time.time())}.mp3"
    audio_path = await tts_service.text_to_speech_file(
        question,
        audio_file,
        lang=lang,
        gender="female",
        rate="-2%"
    )

    await loading.delete()

    title = "🐾 **HAYVONLAR OLAMI VA OVOZLARI:**" if lang == "uz" else "🐾 **МИР ЖИВОТНЫХ И ИХ ГОЛОСА:**"
    caption = f"{title}\n\n❓ {question}\n\nQuyidagi variantlardan to'g'risini tanla:" if lang == "uz" else f"{title}\n\n❓ {question}\n\nВыбери правильный вариант:"

    kb = get_animal_kb(options, answer, lang)
    if audio_path:
        await message.answer_voice(voice=FSInputFile(audio_path), caption=caption, reply_markup=kb)
        if os.path.exists(audio_path):
            try:
                os.remove(audio_path)
            except Exception:
                pass
    else:
        await message.answer(caption, reply_markup=kb)

@router.callback_query(F.data.startswith("anim:"))
async def handle_animal_answer(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    parts = callback.data.split(":")
    
    if parts[1] == "next":
        await callback.message.delete()
        await start_animal_quiz(callback.message, state)
        await callback.answer()
        return

    is_correct = parts[1] == "1"
    selected = parts[2]
    stored = quiz_answers.get(user_id, {})
    lang = stored.get("lang", "uz")
    fact = stored.get("fact", "")

    if is_correct:
        new_points = await database.add_user_points(user_id, 10)
        msg = (
            f"🎉 **TOPDING! BARAKALLA!** 🌟\n\n"
            f"To'g'ri javob: **{selected}**!\n"
            f"💡 *Qiziqarli fakt:* {fact}\n\n"
            f"To'g'ri topganing uchun **+10 ball** berildi! 🏆 (Jami: {new_points} ball)"
            if lang == "uz" else
            f"🎉 **ПРАВИЛЬНО! УРА!** 🌟\n\n"
            f"Правильный ответ: **{selected}**!\n"
            f"💡 *Интересный факт:* {fact}\n\n"
            f"Тебе начислено **+10 баллов**! 🏆 (Всего: {new_points} баллов)"
        )
    else:
        right_ans = stored.get("answer", "")
        msg = (
            f"Ozroq adashding, do'stim! Aslida to'g'ri javob: **{right_ans}** edi. 😊\n"
            f"💡 *Bilib ol:* {fact}\n\nHyechqisi yo'q, yangisini sinab ko'r!"
            if lang == "uz" else
            f"Чуть-чуть не угадал! Правильный ответ: **{right_ans}**. 😊\n"
            f"💡 *Знай:* {fact}\n\nНичего страшного, попробуй ещё!"
        )

    next_btn = "🔄 Yangi hayvon topishmog'i" if lang == "uz" else "🔄 Новая загадка о животных"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=next_btn, callback_data="anim:next")]
    ])
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.reply(msg, reply_markup=kb)
    await callback.answer()
