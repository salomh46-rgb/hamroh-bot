import os
import time
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
import database
import gemini_service
import tts_service

router = Router()

class ReadingStates(StatesGroup):
    waiting_for_reading_report = State()

def get_reading_kb(lang: str = "uz") -> InlineKeyboardMarkup:
    btn_done = "✅ Bugun 5 sahifa o'qidim!" if lang == "uz" else "✅ Сегодня я прочитал 5 страниц!"
    btn_next = "📖 Yangi vazifa olish" if lang == "uz" else "📖 Новое задание"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=btn_done, callback_data="reading:done")],
        [InlineKeyboardButton(text=btn_next, callback_data="reading:next")]
    ])

@router.message(F.text.in_(["📚 Kitobxonlik", "📚 Чтение книг"]))
async def show_reading_mission(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    user = await database.get_user(user_id)
    lang = user.get("language", "uz") if user else "uz"

    loading_text = "📚 Bugungi qiziqarli o'qish vazifasi tayyorlanmoqda..." if lang == "uz" else "📚 Готовлю интересное задание по чтению..."
    loading = await message.answer(loading_text)

    task_data = await gemini_service.generate_reading_task(lang=lang)
    task_text = task_data.get("task", "Bugun sevimli kitobingdan 5 sahifa o'qiymiz!")
    tip_text = task_data.get("tip", "Kitob o'qigan bola har doim eng bilimdon bo'ladi!")

    # Audio ovoz
    audio_file = f"read_{user_id}_{int(time.time())}.mp3"
    audio_path = await tts_service.text_to_speech_file(
        f"{task_text} {tip_text}",
        audio_file,
        lang=lang,
        gender="female",
        rate="-2%"
    )

    await loading.delete()

    title = "📚 **BUGUNGI KITOBXONLIK VAZIFASI (5 SAHIFA):**" if lang == "uz" else "📚 **ЕЖЕДНЕВНЫЙ ЧИТАТЕЛЬСКИЙ ЧЕЛЛЕНДЖ (5 СТРАНИЦ):**"
    caption = (
        f"{title}\n\n"
        f"📖 **Vazifa:** {task_text}\n\n"
        f"💡 **Donolik siri:** {tip_text}\n\n"
        f"5 sahifani o'qib bo'lgach, pastdagi '✅ O'qidim' tugmasini bos va menga nima haqida o'qiganingni yozib ber! Senga **+10 ball** beriladi! 🌟"
        if lang == "uz" else
        f"{title}\n\n"
        f"📖 **Задание:** {task_text}\n\n"
        f"💡 **Секрет мудрости:** {tip_text}\n\n"
        f"Когда прочитаешь 5 страниц, нажми кнопку '✅ Прочитал' ниже и расскажи в сообщении, о чём была книга! За это ты получишь **+10 баллов**! 🌟"
    )

    if audio_path:
        await message.answer_voice(voice=FSInputFile(audio_path), caption=caption, reply_markup=get_reading_kb(lang))
        if os.path.exists(audio_path):
            try:
                os.remove(audio_path)
            except Exception:
                pass
    else:
        await message.answer(caption, reply_markup=get_reading_kb(lang))

@router.callback_query(F.data == "reading:done")
async def on_reading_done(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    user = await database.get_user(user_id)
    lang = user.get("language", "uz") if user else "uz"

    await state.set_state(ReadingStates.waiting_for_reading_report)
    msg = (
        "🎉 **Ofarin, haqiqiy kitobxonsan!** 🌟\n\n"
        "Bugun qaysi ertak yoki kitobni o'qiding? Qisqacha ovozli yoki matnli xabar qilib aytib ber:"
        if lang == "uz" else
        "🎉 **Молодец, настоящий книголюб!** 🌟\n\n"
        "Какую книгу или сказку ты сегодня читал? Расскажи кратко голосом или текстом:"
    )
    await callback.message.answer(msg)
    await callback.answer()

@router.message(ReadingStates.waiting_for_reading_report)
async def process_reading_report(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user = await database.get_user(user_id)
    lang = user.get("language", "uz") if user else "uz"
    await state.clear()

    new_points = await database.add_user_points(user_id, 10)
    book_desc = message.text or "[Ovozli xabar]"

    feedback = (
        f"🌟 **Barakalla!** Kitob o'qish orqali sen eng aqlli va zukko inson bo'lib voyaga yetasan!\n"
        f"Vazifani bajarganing uchun senga **+10 ball** qo'shildi! 🏆 (Jami: {new_points} ball)"
        if lang == "uz" else
        f"🌟 **Умница!** Читая книги, ты становишься с каждым днём умнее и талантливее!\n"
        f"За чтение тебе начислено **+10 баллов**! 🏆 (Всего: {new_points} баллов)"
    )
    await message.answer(feedback)

@router.callback_query(F.data == "reading:next")
async def on_reading_next(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await show_reading_mission(callback.message, state)
    await callback.answer()
