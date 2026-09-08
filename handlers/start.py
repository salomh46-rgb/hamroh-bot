import os
import time
import logging
from aiogram import Router, F, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import BufferedInputFile, InlineKeyboardMarkup, InlineKeyboardButton
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

from typing import Optional

ALL_MAIN_MENU_TEXTS = [
    # Uzbek
    "💊 Dori eslatmalari", "📞 Shifokor / SOS", "🧠 Xotira mashqlari", "🎵 Oltin taronalar",
    "📻 Foydali videolar", "📿 Hikmat va Rivoyat", "🎙️ Ovozli suhbat", "⚙️ Rejim / Til",
    "🗺️ Kvest-Ertak", "🎨 Rasm chizish (AI)", "📚 Kitobxonlik", "🎮 Hayvonlar olami",
    "📖 Ertak eshitish", "🏆 Ballarim",
    # Russian
    "💊 Напоминания", "📞 Врач / SOS", "🧠 Тренировка памяти", "🎵 Ретро-музыка",
    "📻 Полезные видео", "📿 Мудрые притчи", "🎙️ Голосовой собеседник", "⚙️ Режим / Язык",
    "🗺️ Квест-Сказка", "🎨 Мой рисунок (AI)", "📚 Чтение книг", "🎮 Мир животных",
    "📖 Слушать сказку", "🏆 Мои баллы",
    # Extra commands & buttons
    "ℹ️ Yordam", "ℹ️ Помощь", "yordam", "help", "/help", "/sos", "/start", "/role",
    "📊 Salomatlik hisoboti", "📊 Отчёт о здоровье"
]

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
            skip_btn = "⏭️ Пропустить этот шаг"
            skip_prompt = "👇 Напишите ваше имя или нажмите кнопку ниже:"
        else:
            msg = (
                "👵 **Siz bilan tanishishdan bag'oyat mamnunmiz!**\n\n"
                "Sizga o'zbekona odob va yuksak hurmat bilan murojaat qilishimiz uchun, iltimos, ismingizni yozib yuboring:\n"
                "(Masalan: *Nigina*, *Jasur*, *Sardor*, *Nishonoyxon*...)"
            )
            skip_btn = "⏭️ O'tkazib yuborish"
            skip_prompt = "👇 Ismingizni yozing yoki tugmani bosing:"

        # Darhol yangi til va rejimdagi asosiy menyuni klaviaturaga chiqaramiz!
        await callback.message.answer(
            msg, 
            reply_markup=keyboards.get_main_menu_kb("keksa", lang)
        )
        skip_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=skip_btn, callback_data="skip_name_entry")]
        ])
        await callback.message.answer(skip_prompt, reply_markup=skip_kb)
    else:
        # Bolalar rejimi
        if lang == "ru":
            msg = "🧒 **Привет, юный друг! Добро пожаловать в мир сказок и приключений!** 🎉"
        else:
            msg = "🧒 **Salom, aziz bolajon! Sehrli ertaklar va qiziqarli sarguzashtlar olamiga xush kelibsiz!** 🎉"

        await callback.message.answer(msg, reply_markup=keyboards.get_main_menu_kb("bola", lang))
    await callback.answer()

@router.callback_query(F.data == "skip_name_entry")
async def on_skip_name_entry(callback: types.CallbackQuery, state: FSMContext):
    """Ism kiritishni o'tkazib yuborish va darhol asosiy menyuni tasdiqlash"""
    await state.clear()
    user_id = callback.from_user.id
    user = await database.get_user(user_id)
    lang = user.get("language", "uz") if user else "uz"
    appeal = "Qadrdonimiz" if lang == "uz" else "Уважаемый собеседник"
    await database.set_user_profile(user_id, appeal, "unknown", appeal)
    await callback.message.delete()

    welcome_text = (
        "Xush kelibsiz! Marhamat, quyidagi menyudan foydalanishingiz mumkin:" 
        if lang == "uz" else 
        "Добро пожаловать! Вы можете воспользоваться меню ниже:"
    )
    await callback.message.answer(
        welcome_text, 
        reply_markup=keyboards.get_main_menu_kb("keksa", lang)
    )
    await callback.answer()

@router.message(ProfileState.waiting_for_name)
async def process_elderly_name(message: types.Message, state: FSMContext):
    """Keksa inson ismini qabul qilib, jinsi va hurmatli murojaatni aniqlash"""
    name = (message.text or "").strip()
    user_id = message.from_user.id
    user = await database.get_user(user_id)
    lang = user.get("language", "uz") if user else "uz"

    # Agar foydalanuvchi ism yozish o'rniga menyu tugmasini yoki biror buyruqni bossa:
    if name.startswith("/") or name in ALL_MAIN_MENU_TEXTS:
        await state.clear()
        if name.startswith("/help") or name in ["ℹ️ Yordam", "ℹ️ Помощь", "yordam", "help"]:
            await cmd_help(message, state)
            return
        if name.startswith("/role") or name in ["⚙️ Rejim / Til", "⚙️ Режим / Язык", "⚙️ Rejim / Tilni o'zgartirish"]:
            await cmd_change_role_or_lang(message, state)
            return
        if name.startswith("/sos") or name in ["📞 Shifokor / SOS", "📞 Врач / SOS", "sos", "SOS"]:
            from handlers.sos import show_sos_menu
            await show_sos_menu(message, state)
            return
        if name in ["💊 Dori eslatmalari", "💊 Напоминания"]:
            from handlers.reminders import show_reminders_menu
            await show_reminders_menu(message, state)
            return
        if name in ["🧠 Xotira mashqlari", "🧠 Тренировка памяти"]:
            from handlers.memory import start_memory_exercise
            await start_memory_exercise(message, state)
            return
        if name in ["🎵 Oltin taronalar", "🎵 Ретро-музыка"]:
            from handlers.music import show_music_menu
            await show_music_menu(message, state)
            return
        if name in ["📻 Foydali videolar", "📻 Полезные видео"]:
            from handlers.keksa_extra import show_useful_videos
            await show_useful_videos(message, state)
            return
        if name in ["📿 Hikmat va Rivoyat", "📿 Мудрые притчи"]:
            from handlers.keksa_extra import send_wisdom_story
            await send_wisdom_story(message, state)
            return
        if name in ["🎙️ Ovozli suhbat", "🎙️ Голосовой собеседник"]:
            from handlers.chat import prompt_voice
            await prompt_voice(message)
            return

        user_type = user.get("user_type", "keksa") if user else "keksa"
        await message.answer(
            "Bosh menyu:" if lang == "uz" else "Главное меню:",
            reply_markup=keyboards.get_main_menu_kb(user_type, lang)
        )
        return

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
    try:
        audio_bytes = await tts_service.text_to_speech_bytes(
            text=audio_text,
            lang=lang,
            gender=gender
        )
        if audio_bytes:
            voice_input = BufferedInputFile(audio_bytes, filename="welcome.mp3")
            await message.answer_voice(
                voice=voice_input,
                caption="🎙️ *Ovozli salomlashuv*" if lang == "uz" else "🎙️ *Голосовое приветствие*"
            )
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

def get_help_kb(user_type: str = "keksa", lang: str = "uz") -> InlineKeyboardMarkup:
    """Yordam bo'limi uchun interaktiv inline tugmalar"""
    if lang == "ru":
        if user_type == "keksa":
            buttons = [
                [InlineKeyboardButton(text="💊 Как работают напоминания о лекарствах?", callback_data="help:reminders")],
                [InlineKeyboardButton(text="🎙️ Как общаться голосом через микрофон?", callback_data="help:voice")],
                [InlineKeyboardButton(text="📞 Скорая помощь 103 и Врач (/sos)", callback_data="help:sos")],
                [InlineKeyboardButton(text="⚙️ Сменить режим или язык (/role)", callback_data="help:role")]
            ]
        else:
            buttons = [
                [InlineKeyboardButton(text="🗺️ Как играть в Квест-Сказки?", callback_data="help:kvest")],
                [InlineKeyboardButton(text="🎨 Как отправить рисунок на оценку?", callback_data="help:draw")],
                [InlineKeyboardButton(text="🏆 Как копить баллы и побеждать?", callback_data="help:points")],
                [InlineKeyboardButton(text="⚙️ Сменить режим или язык (/role)", callback_data="help:role")]
            ]
    else:
        if user_type == "keksa":
            buttons = [
                [InlineKeyboardButton(text="💊 Dori eslatmalari qanday ishlaydi?", callback_data="help:reminders")],
                [InlineKeyboardButton(text="🎙️ Ovozli suhbatdan foydalanish siri", callback_data="help:voice")],
                [InlineKeyboardButton(text="📞 103 Tez yordam va Shifokor (/sos)", callback_data="help:sos")],
                [InlineKeyboardButton(text="⚙️ Rejim yoki tilni o'zgartirish (/role)", callback_data="help:role")]
            ]
        else:
            buttons = [
                [InlineKeyboardButton(text="🗺️ Kvest-Ertaklar qanday o'ynaladi?", callback_data="help:kvest")],
                [InlineKeyboardButton(text="🎨 Chizgan rasmni qanday tekshirtirish mumkin?", callback_data="help:draw")],
                [InlineKeyboardButton(text="🏆 Ballar yig'ish va yutuqlar siri", callback_data="help:points")],
                [InlineKeyboardButton(text="⚙️ Rejim yoki tilni o'zgartirish (/role)", callback_data="help:role")]
            ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@router.message(F.text.in_(["ℹ️ Yordam", "ℹ️ Помощь", "yordam", "help", "/help"]))
@router.message(Command("help"))
async def cmd_help(message: types.Message, state: Optional[FSMContext] = None):
    """Foydalanuvchi roliga moslashgan interaktiv yordam markazi"""
    if state:
        await state.clear()
    user_id = message.from_user.id
    user = await database.get_user(user_id)
    lang = user.get("language", "uz") if user else "uz"
    user_type = user.get("user_type", "keksa") if user else "keksa"
    appeal = user.get("appeal") or user.get("name") or ("qadrdonimiz" if lang == "uz" else "дорогой друг")

    if lang == "ru":
        if user_type == "keksa":
            text = (
                f"💡 **РУКОВОДСТВО ПО ИСПОЛЬЗОВАНИЮ 'HAMROH BOT'**\n\n"
                f"Здравствуйте, уважаемый(ая) **{appeal}**! Наш бот создан, чтобы окружить вас заботой, теплом и вниманием:\n\n"
                f"• 💊 **Напоминания о лекарствах**: Бот вовремя напомнит о приёме таблеток голосом и текстом, а также ведёт график дисциплины.\n"
                f"• 📞 **Врач и SOS (/sos)**: Быстрый вызов 103, номер близких и медицинские подсказки при давлении.\n"
                f"• 🎙️ **Голосовой собеседник**: Просто удерживайте микрофон в Telegram — бот поговорит с вами на любые темы!\n"
                f"• 🧠 **Тренировка памяти**: Ежедневные упражнения для ясности ума и бодрости.\n"
                f"• 🎵 **Ретро-музыка и притчи**: Золотые шлягеры 70-90-х годов и мудрые истории.\n\n"
                f"Нажмите на интересующую кнопку ниже, чтобы узнать подробнее:"
            )
        else:
            text = (
                f"💡 **ГИД ПО ПРИКЛЮЧЕНИЯМ ДЛЯ ЮНЫХ ГЕРОЕВ!** 🚀\n\n"
                f"Привет, юный друг! В 'Hamroh Bot' тебя ждут увлекательные игры и задания:\n\n"
                f"• 🗺️ **Квест-Сказка**: Ты сам выбираешь путь героя и побеждаешь драконов (+25 баллов)!\n"
                f"• 🎨 **Волшебная кисть (AI)**: Рисуй на бумаге, фотографируй и получай оценку искусственного интеллекта (+15 баллов)!\n"
                f"• 📚 **Читательский клуб**: Читай по 5 страниц в день и становись самым умным (+10 баллов)!\n"
                f"• 🎮 **Мир животных**: Угадывай голоса зверей и получай золотые монеты (+10 баллов)!\n\n"
                f"Выбирай кнопку ниже, чтобы узнать все секреты:"
            )
    else:
        if user_type == "keksa":
            text = (
                f"💡 **'HAMROH BOT' FOYDALANISH BO'YICHA TO'LIQ QO'LLANMA**\n\n"
                f"Assalomu alaykum, muhtaram **{appeal}**! Botimiz sizga mehrli hamroh bo'lish va salomatligingizni asrash uchun xizmat qiladi:\n\n"
                f"• 💊 **Dori eslatmalari**: Belgilangan vaqtda bot Madina/Sardor ovozida dorini eslatadi va [✅ Dorini ichdim] tugmasi bilan nazorat qiladi.\n"
                f"• 📞 **Shifokor va SOS (/sos)**: 103 Tez tibbiy yordam, farzand raqami va qon bosimi ko'tarilganda birinchi yordam choralari.\n"
                f"• 🎙️ **Ovozli suhbat**: Klaviaturada yozib o'tirmasdan, mikrofonda ovoz yuborsangiz, bot siz bilan dildan suhbatlashadi.\n"
                f"• 🧠 **Xotira mashqlari**: Zehnni charxlovchi savollar va aqliy tetiklik mashg'ulotlari.\n"
                f"• 🎵 **Oltin taronalar va Hikmatlar**: 70-80-90-yillar retro musiqalari, tabobat videolari va dono rivoyatlar.\n\n"
                f"Batafsil ma'lumot olish uchun quyidagi mavzulardan birini tanlang:"
            )
        else:
            text = (
                f"💡 **KICHKINTOYLAR UCHUN SEHRLI QO'LLANMA!** 🚀\n\n"
                f"Salom, jajji qahramon! 'Hamroh Bot' bilan sen har kuni bilim olasan va o'ynaysan:\n\n"
                f"• 🗺️ **Kvest-Ertak**: Ertakdagi yo'lni o'zing tanlaysan va g'olib bo'lib +25 ball yutasan!\n"
                f"• 🎨 **Sehrli mo'yqalam (AI)**: O'z rasmingni chizib, rasmga olib tashla, sun'iy intellekt uni maqtaydi (+15 ball)!\n"
                f"• 📚 **Kitobxonlik**: Har kuni 5 sahifa o'qib, dono bilimdonga aylan (+10 ball)!\n"
                f"• 🎮 **Hayvonlar olami**: Jonivorlar ovozini topib, chaqqonligingni ko'rsat (+10 ball)!\n\n"
                f"O'zingga qiziq bo'lim ustiga bosib, barcha sirlarni bilib ol:"
            )

    await message.answer(text, reply_markup=get_help_kb(user_type, lang))

@router.callback_query(F.data == "help:main")
async def back_to_help_main(callback: types.CallbackQuery):
    """Asosiy yordam menyusiga qaytish"""
    user_id = callback.from_user.id
    user = await database.get_user(user_id)
    lang = user.get("language", "uz") if user else "uz"
    user_type = user.get("user_type", "keksa") if user else "keksa"
    appeal = user.get("appeal") or user.get("name") or ("qadrdonimiz" if lang == "uz" else "дорогой друг")

    if lang == "ru":
        text = f"💡 **Справочный центр 'Hamroh Bot' для {appeal}**\n\nВыберите тему, которая вас интересует:"
    else:
        text = f"💡 **{appeal} uchun 'Hamroh Bot' ma'lumotlar markazi**\n\nQuyidagi mavzulardan birini tanlang:"

    await callback.message.edit_text(text, reply_markup=get_help_kb(user_type, lang))
    await callback.answer()

@router.callback_query(F.data.startswith("help:"))
async def handle_help_subtopics(callback: types.CallbackQuery):
    """Yordam bo'limining batafsil tushuntirishlari"""
    topic = callback.data.split(":")[1]
    user_id = callback.from_user.id
    user = await database.get_user(user_id)
    lang = user.get("language", "uz") if user else "uz"

    back_btn = "🔙 Назад к списку вопросов" if lang == "ru" else "🔙 Savollar ro'yxatiga qaytish"

    if topic == "role":
        await callback.message.delete()
        await callback.message.answer(
            "Tilni tanlang / Выберите язык:",
            reply_markup=keyboards.get_lang_selection_kb()
        )
        await callback.answer()
        return

    if topic == "reminders":
        if lang == "ru":
            info = (
                "💊 **КАК РАБОТАЮТ НАПОМИНАНИЯ О ЛЕКАРСТВАХ?**\n\n"
                "1. В главном меню нажмите **'💊 Напоминания'** и выберите **'+ Добавить напоминание'**.\n"
                "2. Напишите название лекарства (например: `Аспирин 1 таблетка`).\n"
                "3. Введите время в формате ЧЧ:ММ (например: `08:30` или `21:00`).\n"
                "4. В назначенное время бот пришлёт голосовое и текстовое уведомление.\n"
                "5. Нажмите кнопку **[✅ Принял(а) лекарство]** — бот запишет это в ваш еженедельный отчёт о здоровье!"
            )
        else:
            info = (
                "💊 **DORI ESLATMALARI QANDAY ISHLAYDI?**\n\n"
                "1. Asosiy menyudan **'💊 Dori eslatmalari'** tugmasini bosib, **'+ Yangi dori eslatmasi qo'shish'**ni tanlang.\n"
                "2. Dori nomi va dozasini yozing (masalan: `Aspirin kardio 1 tabletka`).\n"
                "3. Ichish vaqtini kiriting (masalan: `08:30` yoki `20:00`).\n"
                "4. Belgilangan vaqtda bot sizga muloyim ovoz va matn bilan eslatma yuboradi.\n"
                "5. Dorini ichgach, xabar ostidagi **[✅ Dorini ichdim]** tugmasini bosing — bot buni qayd qilib, haftalik hisobotingizga qo'shib boradi!"
            )
    elif topic == "voice":
        if lang == "ru":
            info = (
                "🎙️ **КАК ОБЩАТЬСЯ ГОЛОСОМ ЧЕРЕЗ МИКРОФОН?**\n\n"
                "1. Вам не нужно набирать текст на маленькой клавиатуре телефона!\n"
                "2. Внизу экрана справа найдите значок микрофона 🎙️ в Telegram.\n"
                "3. Нажмите на него и удерживайте пальцем во время разговора.\n"
                "4. Расскажите боту, как ваши дела, какое у вас настроение или задайте любой вопрос.\n"
                "5. Отпустите палец — бот внимательно выслушает вас и ответит приятным живым голосом!"
            )
        else:
            info = (
                "🎙️ **OVOZLI SUHBATDAN FOYDALANISH SIRI:**\n\n"
                "1. Telefonda mayda harflarni terib qiynalishingiz shart emas!\n"
                "2. Telegram oynasining pastki o'ng burchagidagi mikrofon 🎙️ belgisini bosing va barmog'ingizni qo'yib yubormasdan gapiring.\n"
                "3. Hol-ahvolingizni ayting, kayfiyatingizni bo'lishing yoki xohlagan savolingizni bering.\n"
                "4. Gapirib bo'lgach barmog'ingizni qo'yib yuboring — bot darhol sizni tinglab, samimiy va chiroyli ovozda javob qaytaradi!"
            )
    elif topic == "sos":
        if lang == "ru":
            info = (
                "📞 **СКОРАЯ ПОМОЩЬ 103 И СВЯЗЬ С ВРАЧОМ (/sos):**\n\n"
                "1. В любой момент отправьте команду `/sos` или нажмите кнопку **'📞 Врач / SOS'**.\n"
                "2. Нажмите прямо на номер **103**, чтобы мгновенно вызвать государственную скорую помощь.\n"
                "3. Вы можете один раз сохранить номер вашего семейного врача или детей, и он всегда будет под рукой.\n"
                "4. В разделе первой помощи собраны чёткие инструкции: что делать при высоком давлении, боли в сердце или головокружении."
            )
        else:
            info = (
                "📞 **103 TEZ YORDAM VA SHIFOKOR BILAN ALOQA (/sos):**\n\n"
                "1. Istalgan vaqtda `/sos` buyrug'ini yuboring yoki menyudagi **'📞 Shifokor / SOS'** tugmasini bosing.\n"
                "2. Davlat tez tibbiy yordamiga qo'ng'iroq qilish uchun to'g'ridan-to'g'ri **103** raqami ustiga bosing.\n"
                "3. 'Shaxsiy raqamni saqlash' tugmasi orqali shifokoringiz yoki farzandingiz telefonini kiritib qo'ysangiz, bir zumda qo'ng'iroq qila olasiz.\n"
                "4. 'Birinchi yordam' bo'limida qon bosimi ko'tarilganda yoki yurak bezovta qilganda nima qilish kerakligi batafsil o'rgatiladi."
            )
    elif topic == "kvest":
        if lang == "ru":
            info = (
                "🗺️ **ИНТЕРАКТИВНЫЕ КВЕСТ-СКАЗКИ:**\n\n"
                "1. Нажми **'🗺️ Квест-Сказка'** в меню.\n"
                "2. Искусственный интеллект сочинит для тебя уникальную сказку с озвучкой.\n"
                "3. В конце каждого шага ты сам выбираешь, куда пойти герою (в пещеру или через мост).\n"
                "4. Пройди квест до конца и получи **+25 золотых монет** в свою копилку!"
            )
        else:
            info = (
                "🗺️ **INTERAKTIV KVEST-ERTAKLAR:**\n\n"
                "1. Menyudan **'🗺️ Kvest-Ertak'** tugmasini tanla.\n"
                "2. Sun'iy intellekt sen uchun yangi qahramonlik ertagini to'qiydi va ovozda aytib beradi.\n"
                "3. Har bir qadamda qaysi yo'ldan borishni o'zing hal qilasan (masalan: g'orga kirish yoki daryodan o'tish).\n"
                "4. Qiyinchiliklarni yengib g'olib bo'lsang, senga **+25 oltin tanga** sovg'a qilinadi!"
            )
    elif topic == "draw":
        if lang == "ru":
            info = (
                "🎨 **СЕКРЕТНЫЙ АРТ-КЛУБ (AI РИСУНОК):**\n\n"
                "1. Возьми альбом, фломастеры или карандаши и нарисуй свой лучший рисунок.\n"
                "2. Сфотографируй его на телефон и просто отправь фото в этот чат Telegram.\n"
                "3. Умное компьютерное зрение рассмотрит твой шедевр, похвалит тебя голосом и начислит **+15 баллов**!"
            )
        else:
            info = (
                "🎨 **SEHRLI MO'YQALAM (AI RASM TAHLILI):**\n\n"
                "1. Oq qog'ozga sevimli rasmingni chiz (mushukcha, qasr, mashina yoki uycha).\n"
                "2. Uni telefoningda rasmga tushir va shu bot chatiga yubor.\n"
                "3. Aqlli sun'iy intellekt rasmingni diqqat bilan tomosha qiladi, chiroyli ovozda maqtaydi va senga **+15 ball** beradi!"
            )
    elif topic == "points":
        if lang == "ru":
            info = (
                "🏆 **БАЛЛЫ, НАГРАДЫ И РЕЙТИНГ:**\n\n"
                "• 🗺️ Квест-сказка: **+25 баллов**\n"
                "• 🎨 Рисование (AI): **+15 баллов**\n"
                "• 📚 Чтение 5 страниц: **+10 баллов**\n"
                "• 🎮 Викторина о животных: **+10 баллов**\n"
                "• 💊 Вовремя принятое лекарство: **+5 баллов**\n\n"
                "Нажимай кнопку **'🏆 Мои баллы'**, чтобы следить за своим чемпионским уровнем!"
            )
        else:
            info = (
                "🏆 **BALLAR VA MUKOFOTLAR QOIDASI:**\n\n"
                "• 🗺️ Kvest-ertakni yakunlash: **+25 ball**\n"
                "• 🎨 Rasm chizib yuborish: **+15 ball**\n"
                "• 📚 5 sahifa kitob o'qish: **+10 ball**\n"
                "• 🎮 Hayvonlar topishmog'i: **+10 ball**\n"
                "• 💊 Dorini o'z vaqtida ichish: **+5 ball**\n\n"
                "O'z darajangni bilish uchun menyudagi **'🏆 Ballarim'** tugmasini bosib tur!"
            )
    else:
        info = "Qo'shimcha savollaringiz bo'lsa, xabaringizni yozishingiz yoki ovozli xabar yuborishingiz mumkin!"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=back_btn, callback_data="help:main")]
    ])
    await callback.message.edit_text(info, reply_markup=kb)
    await callback.answer()


