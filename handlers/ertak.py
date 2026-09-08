from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
import os
import time
import gemini_service
import database
import tts_service

router = Router()

MENU_BUTTONS = [
    "💊 Dori eslatmalari", "💊 Напоминания",
    "📖 Ertak eshitish", "📖 Слушать сказку",
    "🗺️ Kvest-Ertak", "🗺️ Квест-Сказка",
    "🎮 Qiziqarli topishmoq", "🎮 Загадки",
    "🏆 Ballarim", "🏆 Мои баллы",
    "🎙️ Ovozli suhbat", "🎙️ Голосовой собеседник",
    "📻 Foydali videolar", "📻 Полезные видео",
    "📿 Hikmat va Rivoyat", "📿 Мудрые притчи",
    "⚙️ Rejim / Tilni o'zgartirish", "⚙️ Rejimni o'zgartirish", "⚙️ Сменить режим / язык",
    "ℹ️ Yordam", "ℹ️ Помощь"
]

class ErtakStates(StatesGroup):
    waiting_for_mavzu = State()

def get_cancel_ertak_kb(lang: str = "uz") -> InlineKeyboardMarkup:
    text = "❌ Отмена" if lang == "ru" else "❌ Bekor qilish"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=text, callback_data="ertak:cancel")]
    ])

@router.callback_query(F.data == "ertak:cancel")
async def cancel_ertak(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    user = await database.get_user(user_id)
    lang = user.get("language", "uz") if user else "uz"

    await state.clear()
    msg = "❌ Заказ сказки отменён." if lang == "ru" else "❌ Ertak so'rash bekor qilindi."
    await callback.message.edit_text(msg)
    await callback.answer()

@router.message(F.text.in_(["📖 Ertak eshitish", "📖 Слушать сказку"]))
async def start_ertak_request(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    user = await database.get_user(user_id)
    lang = user.get("language", "uz") if user else "uz"

    await state.set_state(ErtakStates.waiting_for_mavzu)
    await state.update_data(lang=lang)

    if lang == "ru":
        msg = (
            "✨ **Какую сказку ты хочешь послушать, дружок?**\n\n"
            "Напиши тему сказки или любимых героев:\n"
            "(Например: *'Волшебный дракон'*, *'Лесные зверята'*, *'Храбрый мальчик'*)\n\n"
            "Я сочиню для тебя сказку и озвучу её красивым голосом! 🎙️"
        )
    else:
        msg = (
            "✨ **Qanday ertak eshitishni xohlaysan, do'stim?**\n\n"
            "Menga ertak mavzusini yoki qahramonlarini yoz:\n"
            "(Masalan: *'Sehrli uchar gilam'*, *'O'rmondagi do'stlar'*, *'Jasur bolakay'*)\n\n"
            "Men senga uni chiroyli ovozda o'qib ham beraman! 🎙️"
        )

    await message.answer(msg, reply_markup=get_cancel_ertak_kb(lang))

@router.message(ErtakStates.waiting_for_mavzu)
async def process_ertak_mavzu(message: types.Message, state: FSMContext):
    if message.text in MENU_BUTTONS or message.text.startswith("/"):
        await state.clear()
        return

    data = await state.get_data()
    lang = data.get("lang", "uz")

    mavzu = message.text.strip()
    await state.clear()

    loading_text = "📖 Сочиняю волшебную сказку и записываю голос..." if lang == "ru" else "📖 Sehrli ertak to'qilmoqda va ovoz yozilmoqda, bir zum kutgin..."
    loading_msg = await message.answer(loading_text)

    ertak_matni = await gemini_service.generate_ertak(mavzu, yosh=7, lang=lang)
    new_points = await database.add_user_points(message.from_user.id, 10)
    
    # Audio ertak generatsiya qilish
    ertak_audio_file = f"ertak_{message.from_user.id}_{int(time.time())}.mp3"
    audio_path = await tts_service.text_to_speech_file(
        ertak_matni, 
        ertak_audio_file, 
        lang=lang, 
        gender="female", 
        rate="-3%"
    )

    await loading_msg.delete()

    if lang == "ru":
        caption_text = (
            f"🌟 **{mavzu.upper()}**\n\n"
            f"🎉 Молодец! За прослушивание новой сказки тебе начислено +10 баллов!\n"
            f"🏆 Твои баллы: **{new_points} баллов**"
        )
        text_prefix = "📖 **Текст сказки:**"
    else:
        caption_text = (
            f"🌟 **{mavzu.upper()}**\n\n"
            f"🎉 Ofarin! Yangi ertak eshitganing uchun senga +10 ball berildi!\n"
            f"🏆 Sening jami ballaring: **{new_points} ball**"
        )
        text_prefix = "📖 **Ertak matni:**"

    if audio_path:
        voice_in = FSInputFile(audio_path)
        await message.answer_voice(voice=voice_in, caption=caption_text)
        await message.answer(f"{text_prefix}\n\n{ertak_matni}")
        if os.path.exists(audio_path):
            try:
                os.remove(audio_path)
            except Exception:
                pass
    else:
        await message.answer(f"{caption_text}\n\n{ertak_matni}")



