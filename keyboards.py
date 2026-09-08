from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def get_lang_selection_kb() -> InlineKeyboardMarkup:
    """Tilni tanlash inline klaviaturasi"""
    buttons = [
        [
            InlineKeyboardButton(text="🇺🇿 O'zbek tili", callback_data="set_lang:uz"),
            InlineKeyboardButton(text="🇷🇺 Русский язык", callback_data="set_lang:ru")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_role_selection_kb(lang: str = "uz") -> InlineKeyboardMarkup:
    """Keksa yoki Bola rejimini tanlash tugmalari"""
    if lang == "ru":
        buttons = [
            [
                InlineKeyboardButton(text="👵 Старшее поколение (Дедушка / Бабушка)", callback_data="set_role:keksa"),
                InlineKeyboardButton(text="🧒 Дети (Малыш)", callback_data="set_role:bola")
            ]
        ]
    else:
        buttons = [
            [
                InlineKeyboardButton(text="👵 Keksa (Otaxon / Onaxon)", callback_data="set_role:keksa"),
                InlineKeyboardButton(text="🧒 Bola (Kichkintoy)", callback_data="set_role:bola")
            ]
        ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_main_menu_kb(user_type: str = "keksa", lang: str = "uz") -> ReplyKeyboardMarkup:
    """Asosiy menyu tugmalari (O'zbekcha va Ruscha)"""
    if lang == "ru":
        if user_type == "keksa":
            keyboard = [
                [KeyboardButton(text="💊 Напоминания"), KeyboardButton(text="📞 Врач / SOS")],
                [KeyboardButton(text="🧠 Тренировка памяти"), KeyboardButton(text="🎵 Ретро-музыка")],
                [KeyboardButton(text="📻 Полезные видео"), KeyboardButton(text="📿 Мудрые притчи")],
                [KeyboardButton(text="🎙️ Голосовой собеседник"), KeyboardButton(text="⚙️ Режим / Язык")]
            ]
        else:
            keyboard = [
                [KeyboardButton(text="🗺️ Квест-Сказка"), KeyboardButton(text="🎨 Мой рисунок (AI)")],
                [KeyboardButton(text="📚 Чтение книг"), KeyboardButton(text="🎮 Мир животных")],
                [KeyboardButton(text="📖 Слушать сказку"), KeyboardButton(text="🏆 Мои баллы")],
                [KeyboardButton(text="🎙️ Голосовой собеседник"), KeyboardButton(text="⚙️ Режим / Язык")]
            ]
    else:
        if user_type == "keksa":
            keyboard = [
                [KeyboardButton(text="💊 Dori eslatmalari"), KeyboardButton(text="📞 Shifokor / SOS")],
                [KeyboardButton(text="🧠 Xotira mashqlari"), KeyboardButton(text="🎵 Oltin taronalar")],
                [KeyboardButton(text="📻 Foydali videolar"), KeyboardButton(text="📿 Hikmat va Rivoyat")],
                [KeyboardButton(text="🎙️ Ovozli suhbat"), KeyboardButton(text="⚙️ Rejim / Til")]
            ]
        else:
            keyboard = [
                [KeyboardButton(text="🗺️ Kvest-Ertak"), KeyboardButton(text="🎨 Rasm chizish (AI)")],
                [KeyboardButton(text="📚 Kitobxonlik"), KeyboardButton(text="🎮 Hayvonlar olami")],
                [KeyboardButton(text="📖 Ertak eshitish"), KeyboardButton(text="🏆 Ballarim")],
                [KeyboardButton(text="🎙️ Ovozli suhbat"), KeyboardButton(text="⚙️ Rejim / Til")]
            ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True, is_persistent=True)


def get_reminders_kb(lang: str = "uz") -> InlineKeyboardMarkup:
    """Dori eslatmalari amallari"""
    if lang == "ru":
        buttons = [
            [InlineKeyboardButton(text="➕ Добавить напоминание", callback_data="reminder:add")],
            [InlineKeyboardButton(text="📋 Мои напоминания", callback_data="reminder:list")],
            [InlineKeyboardButton(text="📊 Отчёт о приёме лекарств", callback_data="reminder:report")]
        ]
    else:
        buttons = [
            [InlineKeyboardButton(text="➕ Yangi dori eslatmasi qo'shish", callback_data="reminder:add")],
            [InlineKeyboardButton(text="📋 Barcha eslatmalarim", callback_data="reminder:list")],
            [InlineKeyboardButton(text="📊 Salomatlik va dori hisoboti", callback_data="reminder:report")]
        ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
