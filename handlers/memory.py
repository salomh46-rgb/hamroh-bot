import os
import time
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
import database
import gemini_service
import tts_service

router = Router()

class MemoryStates(StatesGroup):
    waiting_for_memory_answer = State()

def get_memory_kb(lang: str = "uz") -> InlineKeyboardMarkup:
    btn_text = "🔄 Boshqa savol olish" if lang == "uz" else "🔄 Другой вопрос"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=btn_text, callback_data="memory:next")]
    ])

@router.message(F.text.in_(["🧠 Xotira mashqlari", "🧠 Тренировка памяти"]))
async def start_memory_exercise(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    user = await database.get_user(user_id)
    lang = user.get("language", "uz") if user else "uz"
    gender = user.get("gender", "female") if user else "female"
    appeal = user.get("appeal", "") if user else ""

    loading_text = "🧠 Xotirani charxlovchi savol tayyorlanmoqda..." if lang == "uz" else "🧠 Подбираю интересное упражнение для памяти..."
    loading = await message.answer(loading_text)

    question = await gemini_service.generate_memory_question(lang=lang, appeal=appeal)

    # Audio ovoz yaratish
    audio_file = f"mem_{user_id}_{int(time.time())}.mp3"
    audio_path = await tts_service.text_to_speech_file(
        question, 
        audio_file, 
        lang=lang, 
        gender=gender, 
        rate="-4%"
    )

    await loading.delete()

    title = "🧠 **XOTIRA VA AQLIY TETIKLIK MASHQI:**" if lang == "uz" else "🧠 **ТРЕНИРОВКА ПАМЯТИ И БОДРОСТИ УМА:**"
    inst = (
        "Iltimos, javobingizni ovozli yoki matnli xabar qilib yuboring. Siz bilan dildan suhbatlashamiz! 😊"
        if lang == "uz" else
        "Пожалуйста, ответьте голосовым или текстовым сообщением. С удовольствием выслушаю вас! 😊"
    )
    caption = f"{title}\n\n💬 *{question}*\n\n{inst}"

    await state.set_state(MemoryStates.waiting_for_memory_answer)
    await state.update_data(lang=lang, gender=gender, appeal=appeal)

    if audio_path:
        await message.answer_voice(voice=FSInputFile(audio_path), caption=caption, reply_markup=get_memory_kb(lang))
        if os.path.exists(audio_path):
            try:
                os.remove(audio_path)
            except Exception:
                pass
    else:
        await message.answer(caption, reply_markup=get_memory_kb(lang))

@router.callback_query(F.data == "memory:next")
async def next_memory_exercise(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await start_memory_exercise(callback.message, state)
    await callback.answer()

@router.message(MemoryStates.waiting_for_memory_answer)
async def process_memory_answer(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    gender = data.get("gender", "female")
    appeal = data.get("appeal", "")
    await state.clear()

    ans_text = message.text or "[Ovozli xabar]"
    prompt = (
        f"Keksa inson ({appeal}) xotira mashqi savoliga shunday javob berdi: '{ans_text}'. "
        f"Unga juda samimiy, mehrli, uning xotirasini va javobini qadrlab, tabassum ulashuvchi qisqa (2-3 jumla) dalda ber. "
        f"Til: {'rus tili' if lang == 'ru' else 'o\'zbek tili'}."
    )
    client = gemini_service.get_client()
    feedback = (
        f"Juda ajoyib javob berdingiz, {appeal}! Xotirangiz hamisha charx va o'tkir bo'lsin. Siz bilan suhbatlashish katta zavq bag'ishlaydi! 🌸"
        if lang == "uz" else
        f"Прекрасный и душевный ответ, {appeal}! Пусть ваша память всегда остаётся ясной, а на душе будет тепло и радостно! 🌸"
    )
    if client:
        try:
            res = await client.aio.models.generate_content(
                model=gemini_service.config.GEMINI_MODEL,
                contents=prompt
            )
            if res.text:
                feedback = res.text.strip()
        except Exception:
            pass

    # Audio feedback
    voice_file = f"mem_fb_{message.from_user.id}_{int(time.time())}.mp3"
    audio_path = await tts_service.text_to_speech_file(
        feedback, 
        voice_file, 
        lang=lang, 
        gender=gender
    )

    if audio_path:
        await message.answer_voice(voice=FSInputFile(audio_path), caption=f"🌸 {feedback}")
        if os.path.exists(audio_path):
            try:
                os.remove(audio_path)
            except Exception:
                pass
    else:
        await message.answer(f"🌸 {feedback}")
