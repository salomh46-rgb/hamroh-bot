import os
import time
import logging
from aiogram import Router, F, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import FSInputFile
import database
import keyboards
import gemini_service
import tts_service

logger = logging.getLogger(__name__)
router = Router()

class ProfileState(StatesGroup):
    waiting_for_name = State()

@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    """Botni boshlash — avvalo til so'raladi"""
    await state.clear()
    user_id = message.from_user.id
    user = await database.get_user(user_id)

    if not user:
        await database.upsert_user(
            user_id=user_id,
            username=message.from_user.username,
            full_name=message.from_user.full_name,
            user_type="keksa"
        )

    # Foydalanuvchidan til tanlashni so'rash
    await message.answer(
        "👋 **Assalomu alaykum! Xush kelibsiz! / Здравствуйте! Добро пожаловать!**\n\n"
        "Muloqot qilish uchun qulay tilni tanlang:\n"
        "Пожалуйста, выберите язык для общения:",
        reply_markup=keyboards.get_lang_selection_kb()
    )

@router.callback_query(F.data.startswith("set_lang:"))
async def on_lang_selected(callback: types.CallbackQuery, state: FSMContext):
    """Til tanlanganda rejim tanlashga o'tish"""
    await state.clear()
    lang = callback.data.split(":")[1]
    user_id = callback.from_user.id
    await database.set_user_language(user_id, lang)

    await callback.message.delete()

    if lang == "ru":
        text = (
            "🌟 **Добро пожаловать в 'Hamroh Bot'!**\n\n"
            "Я ваш добрый и заботливый виртуальный помощник.\n\n"
            "Пожалуйста, выберите подходящий для вас режим:"
        )
    else:
        text = (
            "🌟 **'Hamroh Bot'ga xush kelibsiz!**\n\n"
            "Men sizning eng yaqin va g'amxo'r virtual yordamchingizman.\n\n"
            "Iltimos, o'zingizga mos rejimni tanlang:"
        )

    await callback.message.answer(text, reply_markup=keyboards.get_role_selection_kb(lang))
    await callback.answer()

@router.callback_query(F.data.startswith("set_role:"))
async def on_role_selected(callback: types.CallbackQuery, state: FSMContext):
    """Rejim tanlanganda ishlaydi"""
    await state.clear()
    role = callback.data.split(":")[1]
    user_id = callback.from_user.id
    user = await database.get_user(user_id)
    lang = user.get("language", "uz") if user else "uz"

    await database.set_user_type(user_id, role)
    await callback.message.delete()

    if role == "keksa":
        # Keksa rejimida ismini so'raymiz
        await state.set_state(ProfileState.waiting_for_name)
        await state.update_data(lang=lang)

        if lang == "ru":
            msg = (
                "👵 **Очень приятно познакомиться!**\n\n"
                "Чтобы наше общение было тёплым и уважительным, подскажите, пожалуйста, ваше имя?\n"
                "(Например: *Каролина*, *Александр*, *Нина Ивановна*...)"
            )
        else:
            msg = (
                "👵 **Siz bilan tanishishdan bag'oyat mamnunmiz!**\n\n"
                "Sizga o'zbekona odob va yuksak hurmat bilan murojaat qilishimiz uchun, iltimos, ismingizni yozib yuboring:\n"
                "(Masalan: *Nigina*, *Jasur*, *Sardor*, *Nishonoyxon*...)"
            )
        await callback.message.answer(msg)
    else:
        # Bolalar rejimi
        if lang == "ru":
            msg = "🧒 **Привет, юный друг! Добро пожаловать в мир сказок и приключений!** 🎉"
        else:
            msg = "🧒 **Salom, aziz bolajon! Sehrli ertaklar va qiziqarli sarguzashtlar olamiga xush kelibsiz!** 🎉"

        await callback.message.answer(msg, reply_markup=keyboards.get_main_menu_kb("bola", lang))
    await callback.answer()

@router.message(ProfileState.waiting_for_name)
async def process_elderly_name(message: types.Message, state: FSMContext):
    """Keksa inson ismini qabul qilib, jinsi va hurmatli murojaatni aniqlash"""
    name = message.text.strip()
    user_id = message.from_user.id
    user = await database.get_user(user_id)
    lang = user.get("language", "uz") if user else "uz"

    wait_msg = await message.answer(
        "⏳ Tahlil qilinmoqda..." if lang == "uz" else "⏳ Минуточку, настраиваю обращение..."
    )

    # Gemini orqali jinsi va hurmat shaklini aniqlaymiz
    detected = await gemini_service.detect_gender_and_appeal(name, lang)
    gender = detected.get("gender", "female")
    appeal = detected.get("appeal", f"{name} ona" if lang == "uz" else f"Уважаемая {name}")

    # Bazaga yozish
    await database.set_user_profile(user_id, name, gender, appeal)
    await database.set_user_type(user_id, "keksa")
    await state.clear()
    await wait_msg.delete()

    if lang == "ru":
        welcome_text = (
            f"Очень приятно познакомиться, **{appeal}**! 🌸\n\n"
            f"Я ваш заботливый виртуальный собеседник и помощник. "
            f"С радостью напомню вам о приёме лекарств, включу душевные ретро-песни и мудрые притчи, "
            f"и всегда поддержу приятный разговор по душам.\n\n"
            f"Чем я могу вам помочь прямо сейчас?"
        )
        audio_text = f"Здравствуйте, {appeal}! Очень приятно познакомиться. Я ваш заботливый собеседник. Желаю вам крепкого здоровья и отличного настроения!"
    else:
        welcome_text = (
            f"Tanishganimizdan bag'oyat mamnunman, **{appeal}**! 🌸\n\n"
            f"Men sizning eng yaqin va g'amxo'r hamrohingiz bo'laman. "
            f"Dori vaqtlaringizni o'z vaqtida eslatib turaman, ko'ngilga orom beruvchi hikmatlar aytib beraman "
            f"va siz bilan xohlagan mavzuda samimiy dildan suhbatlashaman.\n\n"
            f"Sizga hozir qanday yordam bera olaman?"
        )
        audio_text = f"Assalomu alaykum, {appeal}! Tanishganimizdan judayam xursandman. Men sizning g'amxo'r hamrohingizman. Doimo sog'-salomat bo'ling!"

    # Matnli xabar va asosiy menyu
    await message.answer(
        welcome_text,
        reply_markup=keyboards.get_main_menu_kb("keksa", lang)
    )

    # Ovozli salom yuborish (Madina/Svetlana yoki Sardor/Dmitry ovozida)
    voice_file = f"welcome_{user_id}_{int(time.time())}.mp3"
    try:
        created = await tts_service.text_to_speech_file(
            text=audio_text,
            output_path=voice_file,
            lang=lang,
            gender=gender
        )
        if created:
            voice_input = FSInputFile(voice_file)
            await message.answer_voice(
                voice=voice_input,
                caption="🎙️ *Ovozli salomlashuv*" if lang == "uz" else "🎙️ *Голосовое приветствие*"
            )
            if os.path.exists(voice_file):
                os.remove(voice_file)
    except Exception as e:
        logger.error(f"Xush kelibsiz ovozini yuborishda xato: {e}")

from aiogram.filters import CommandStart, Command

@router.message(F.text.in_(["⚙️ Rejim / Til", "⚙️ Режим / Язык", "⚙️ Rejim / Tilni o'zgartirish", "⚙️ Rejimni o'zgartirish", "⚙️ Сменить режим / язык"]))
@router.message(Command("role"))
async def cmd_change_role_or_lang(message: types.Message, state: FSMContext):
    """Rejim va tilni qayta tanlash"""
    await state.clear()
    await message.answer(
        "Tilni tanlang / Выберите язык:",
        reply_markup=keyboards.get_lang_selection_kb()
    )

@router.message(F.text.in_(["ℹ️ Yordam", "ℹ️ Помощь"]))
@router.message(Command("help"))
async def cmd_help(message: types.Message):
    """Yordam bo'limi"""
    user_id = message.from_user.id
    user = await database.get_user(user_id)
    lang = user.get("language", "uz") if user else "uz"

    if lang == "ru":
        await message.answer(
            "💡 **Справка по использованию 'Hamroh Bot':**\n\n"
            "• 💊 **Напоминания**: Введите название лекарства и время (например: 08:30), и бот вовремя напомнит вам.\n"
            "• 🎙️ **Голосовой собеседник**: Зажмите и удерживайте значок микрофона в Telegram — бот поймет ваш голос и ответит душевным голосом!\n"
            "• 📻 **Полезные видео**: Отобранные полезные видео с YouTube о здоровье, ретро-музыке и гимнастике.\n"
            "• 📿 **Мудрые притчи**: Красивые и вдохновляющие истории с профессиональным озвучиванием.\n"
            "• 🗺️ **Квест-Сказка / Загадки**: Интерактивные развивающие игры и баллы для детей.\n\n"
            "Всегда рады вам помочь!"
        )
    else:
        await message.answer(
            "💡 **Hamroh Bot bo'yicha qo'llanma:**\n\n"
            "• 💊 **Dori eslatmalari**: O'zingiz qabul qiladigan dorilar va vaqtini kiriting (masalan: 08:30), bot sizga aytilgan vaqtda eslatadi.\n"
            "• 🎙️ **Ovozli suhbat**: Telegramdagi mikrofon tugmasini bosib gapirsangiz, bot ovozingizni tinglab, chiroyli ovozda javob qaytaradi.\n"
            "• 📻 **Foydali videolar**: Keksalar uchun tabobat, maqom va yengil mashqlar videolari.\n"
            "• 📿 **Hikmat va Rivoyat**: Qalbga orom beruvchi dono rivoyatlar va audio hikmatlar.\n"
            "• 🗺️ **Kvest-Ertak / Topishmoqlar**: Bolalar uchun interaktiv tarbiyaviy o'yinlar va ballar.\n\n"
            "Savollaringiz bo'lsa, bemalol so'rashingiz mumkin!"
        )

