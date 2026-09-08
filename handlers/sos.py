import logging
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile
import database
import keyboards
import tts_service

logger = logging.getLogger(__name__)
router = Router()

class SOSStates(StatesGroup):
    waiting_for_doctor_phone = State()

def get_sos_main_kb(lang: str = "uz", doctor_phone: str = None) -> InlineKeyboardMarkup:
    """Asosiy SOS boshqaruv tugmalari"""
    if lang == "ru":
        buttons = [
            [InlineKeyboardButton(text="🚨 Инструкция вызова 103", callback_data="sos:info_103")],
            [InlineKeyboardButton(text="🩺 Первая помощь при недомогании", callback_data="sos:first_aid")],
            [InlineKeyboardButton(text="🎙️ Успокаивающий голосовой совет", callback_data="sos:voice_calm")]
        ]
        if doctor_phone:
            buttons.append([InlineKeyboardButton(text=f"✏️ Изменить номер ({doctor_phone})", callback_data="sos:set_phone")])
        else:
            buttons.append([InlineKeyboardButton(text="✏️ Сохранить номер врача/семьи", callback_data="sos:set_phone")])
    else:
        buttons = [
            [InlineKeyboardButton(text="🚨 103 Chaqirish yo'riqnomasi", callback_data="sos:info_103")],
            [InlineKeyboardButton(text="🩺 Birinchi tezkor yordam choralari", callback_data="sos:first_aid")],
            [InlineKeyboardButton(text="🎙️ Sokin ovozli tasalli va yo'riqnoma", callback_data="sos:voice_calm")]
        ]
        if doctor_phone:
            buttons.append([InlineKeyboardButton(text=f"✏️ Shaxsiy raqamni yangilash ({doctor_phone})", callback_data="sos:set_phone")])
        else:
            buttons.append([InlineKeyboardButton(text="✏️ Shaxsiy shifokor/farzand raqamini saqlash", callback_data="sos:set_phone")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_first_aid_kb(lang: str = "uz") -> InlineKeyboardMarkup:
    """Birinchi yordam ko'rsatmalari ro'yxati"""
    if lang == "ru":
        buttons = [
            [InlineKeyboardButton(text="🩸 При высоком давлении (гипертония)", callback_data="sos:aid_pressure")],
            [InlineKeyboardButton(text="❤️ При болях в сердце", callback_data="sos:aid_heart")],
            [InlineKeyboardButton(text="🍬 При слабости / низком сахаре", callback_data="sos:aid_sugar")],
            [InlineKeyboardButton(text="🌀 При головокружении", callback_data="sos:aid_dizzy")],
            [InlineKeyboardButton(text="🔙 Назад в меню SOS", callback_data="sos:main")]
        ]
    else:
        buttons = [
            [InlineKeyboardButton(text="🩸 Qon bosimi ko'tarilganda", callback_data="sos:aid_pressure")],
            [InlineKeyboardButton(text="❤️ Yurak bezovta qilganda", callback_data="sos:aid_heart")],
            [InlineKeyboardButton(text="🍬 Qand tushishi va holsizlikda", callback_data="sos:aid_sugar")],
            [InlineKeyboardButton(text="🌀 Bosh aylanganda", callback_data="sos:aid_dizzy")],
            [InlineKeyboardButton(text="🔙 SOS menyusiga qaytish", callback_data="sos:main")]
        ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@router.message(Command("sos"))
@router.message(F.text.in_(["📞 Shifokor / SOS", "📞 Врач / SOS", "sos", "SOS", "/sos"]))
async def show_sos_menu(message: types.Message, state: FSMContext):
    """SOS va Shifokor bilan tezkor bog'lanish bosh menyusi"""
    await state.clear()
    user_id = message.from_user.id
    user = await database.get_user(user_id)
    lang = user.get("language", "uz") if user else "uz"
    appeal = user.get("appeal") or user.get("name") or ("qadrdonimiz" if lang == "uz" else "дорогой друг")
    doctor_phone = user.get("doctor_phone") if user else None

    if lang == "ru":
        msg = (
            f"🆘 **ЭКСТРЕННАЯ ПОМОЩЬ И СВЯЗЬ С ВРАЧОМ**\n\n"
            f"Уважаемый(ая) **{appeal}**! Ваше здоровье и спокойствие — превыше всего.\n\n"
            f"📞 **Номера для немедленного звонка:**\n"
            f"• 🚨 Скорая помощь: **103** *(нажмите на номер для вызова)*\n"
            f"• 👨‍⚕️ Личный врач / Близкий: **{doctor_phone or 'Не указан'}**\n\n"
            f"ℹ️ *В Telegram вы можете нажать прямо на номер телефона, чтобы совершить звонок.*\n\n"
            f"Выберите необходимое действие ниже:"
        )
    else:
        msg = (
            f"🆘 **TEZKOR YORDAM VA SHIFOKOR BILAN BOG'LANISH**\n\n"
            f"Hurmatli **{appeal}**! Salomatligingiz va xotirjamligingiz biz uchun eng oliy qadriyat.\n\n"
            f"📞 **Tezkor qo'ng'iroq qilish uchun raqamlar:**\n"
            f"• 🚨 Tez tibbiy yordam: **103** *(raqam ustiga bosing)*\n"
            f"• 👨‍⚕️ Shaxsiy shifokor / Farzand: **{doctor_phone or 'Kiritilmagan'}**\n\n"
            f"ℹ️ *Telegramda raqam ustiga bosish orqali to'g'ridan-to'g'ri qo'ng'iroq qilishingiz mumkin.*\n\n"
            f"Quyidagi kerakli bo'limni tanlang:"
        )

    await message.answer(msg, reply_markup=get_sos_main_kb(lang, doctor_phone))

@router.callback_query(F.data == "sos:main")
async def back_to_sos_main(callback: types.CallbackQuery, state: FSMContext):
    """SOS asosiy menyusiga qaytish"""
    await state.clear()
    user_id = callback.from_user.id
    user = await database.get_user(user_id)
    lang = user.get("language", "uz") if user else "uz"
    appeal = user.get("appeal") or user.get("name") or ("qadrdonimiz" if lang == "uz" else "дорогой друг")
    doctor_phone = user.get("doctor_phone") if user else None

    if lang == "ru":
        msg = (
            f"🆘 **ЭКСТРЕННАЯ ПОМОЩЬ И СВЯЗЬ С ВРАЧОМ**\n\n"
            f"Уважаемый(ая) **{appeal}**! Ваше здоровье — самое главное.\n\n"
            f"📞 **Номера для звонка:**\n"
            f"• 🚨 Скорая помощь: **103**\n"
            f"• 👨‍⚕️ Личный врач / Семья: **{doctor_phone or 'Не указан'}**\n\n"
            f"Выберите раздел:"
        )
    else:
        msg = (
            f"🆘 **TEZKOR YORDAM VA SHIFOKOR BILAN BOG'LANISH**\n\n"
            f"Hurmatli **{appeal}**! Salomatligingiz biz uchun eng muhimi.\n\n"
            f"📞 **Qo'ng'iroq uchun raqamlar:**\n"
            f"• 🚨 Tez yordam: **103**\n"
            f"• 👨‍⚕️ Shaxsiy shifokor / Farzand: **{doctor_phone or 'Kiritilmagan'}**\n\n"
            f"Kerakli bo'limni tanlang:"
        )

    await callback.message.edit_text(msg, reply_markup=get_sos_main_kb(lang, doctor_phone))
    await callback.answer()

@router.callback_query(F.data == "sos:info_103")
async def show_103_instructions(callback: types.CallbackQuery):
    """103 Tez yordam chaqirish qoidalari va yo'riqnoma"""
    user_id = callback.from_user.id
    user = await database.get_user(user_id)
    lang = user.get("language", "uz") if user else "uz"

    if lang == "ru":
        text = (
            "🚨 **КАК ПРАВИЛЬНО ВЫЗВАТЬ СКОРУЮ ПОМОЩЬ (103):**\n\n"
            "1. **Наберите 103** и спокойно ответьте на вопросы диспетчера.\n"
            "2. **Чётко назовите адрес:** город, улицу, номер дома, подъезд, этаж и код домофона.\n"
            "3. **Назовите ориентир:** рядом с какой мечетью, школой или магазином находится дом.\n"
            "4. **Опишите состояние:** возраст, что именно болит (давление, сердце, одышка).\n\n"
            "💡 **Что сделать до приезда врачей:**\n"
            "• Откройте входную дверь, чтобы врачи не теряли время.\n"
            "• Приготовьте паспорт и список лекарств, которые вы обычно принимаете.\n"
            "• Сделайте доступ свежего воздуха (откройте форточку).\n\n"
            "📞 Позвонить в скорую: **103**"
        )
        back_btn = "🔙 Назад в меню SOS"
    else:
        text = (
            "🚨 **103 TEZ TIBBIY YORDAMNI TO'G'RI CHAQIRISH YO'RIQNOMASI:**\n\n"
            "1. **103 raqamini tering** va dispetcher savollariga xotirjam javob bering.\n"
            "2. **Aniq manzilni ayting:** Tuman, ko'cha, uy raqami, podyezd va qavat.\n"
            "3. **Mo'ljalni ko'rsating:** Uyingiz qaysi bekat, maktab yoki do'kon yaqinida joylashgan.\n"
            "4. **Holatni tushuntiring:** Bemorning yoshi, asosiy shikoyati (qon bosimi, yurak, hansirash).\n\n"
            "💡 **Shifokorlar kelguncha nima qilish kerak:**\n"
            "• Shifokorlar tezda kirishi uchun xonadon eshigini ochiq qoldiring.\n"
            "• Pasport va doimiy ichadigan dorilaringizni ko'rinadigan joyga qo'ying.\n"
            "• Xonaga toza havo kirishi uchun derazani oching.\n\n"
            "📞 Tez yordam raqami: **103**"
        )
        back_btn = "🔙 SOS menyusiga qaytish"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=back_btn, callback_data="sos:main")]
    ])
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()

@router.callback_query(F.data == "sos:first_aid")
async def show_first_aid_menu(callback: types.CallbackQuery):
    """Birinchi yordam kategoriyalari"""
    user_id = callback.from_user.id
    user = await database.get_user(user_id)
    lang = user.get("language", "uz") if user else "uz"

    msg = (
        "🩺 **ПЕРВАЯ ПОМОЩЬ ДО ПРИХОДА ВРАЧА:**\n\n"
        "Выберите состояние, чтобы узнать правильный порядок действий:"
        if lang == "ru" else
        "🩺 **SHIFOKOR KELGUNCHA BIRINCHI TEZKOR YORDAM:**\n\n"
        "Bemor holatini tanlang va tavsiyalar bilan tanishing:"
    )
    await callback.message.edit_text(msg, reply_markup=get_first_aid_kb(lang))
    await callback.answer()

@router.callback_query(F.data.startswith("sos:aid_"))
async def show_aid_detail(callback: types.CallbackQuery):
    """Har bir holat bo'yicha aniq tibbiy tavsiyalar"""
    aid_type = callback.data.split("_")[1]
    user_id = callback.from_user.id
    user = await database.get_user(user_id)
    lang = user.get("language", "uz") if user else "uz"

    if aid_type == "pressure":
        if lang == "ru":
            content = (
                "🩸 **ПЕРВАЯ ПОМОЩЬ ПРИ ВЫСОКОМ ДАВЛЕНИИ:**\n\n"
                "1. Сядьте в удобное полусидячее положение, опустите ноги вниз.\n"
                "2. Расстегните воротник рубашки, обеспечьте доступ свежего воздуха.\n"
                "3. Сделайте глубокий медленный вдох носом и плавный выдох через рот (повторите 5-10 раз).\n"
                "4. Опустите ступни ног в тазик с тёплой водой на 10-15 минут (это оттягивает кровь от головы).\n"
                "5. Примите назначенное вашим врачом гипотензивное средство (не принимайте чужие таблетки!).\n"
                "⚠️ Если давление не падает или появилась боль в груди — немедленно звоните **103**!"
            )
        else:
            content = (
                "🩸 **QON BOSIMI KO'TARILGANDA TEZKOR YORDAM:**\n\n"
                "1. Yotmang! Yostiqqa suyanib, yarim o'tirgan holatda qulay joylashing, oyoqlarni pastga tushiring.\n"
                "2. Yoqangizni bo'shating, xonani shamollating.\n"
                "3. Burun bilan chuqur va sokin nafas olib, og'iz orqali sekin chiqaring (5-10 marta).\n"
                "4. Oyoqlaringizni 10-15 daqiqa iliq suvga solib turing (bu qonni oyoqlarga haydab, bosh bosimini tushiradi).\n"
                "5. Shaxsiy shifokoringiz tavsiya etgan bosim tushiruvchi dorini qabul qiling.\n"
                "⚠️ Agar bosim tushmasa yoki ko'krakda og'riq sezilsa, kechiktirmay **103** ga qo'ng'iroq qiling!"
            )
    elif aid_type == "heart":
        if lang == "ru":
            content = (
                "❤️ **ПЕРВАЯ ПОМОЩЬ ПРИ БОЛИ В ОБЛАСТИ СЕРДЦА:**\n\n"
                "1. Немедленно прекратите любые физические нагрузки, присядьте.\n"
                "2. Расстегните стесняющую одежду, откройте окно.\n"
                "3. Постарайтесь сохранять спокойствие, избегайте паники.\n"
                "4. Если врач ранее назначал нитроглицерин — положите одну таблетку под язык.\n"
                "⚠️ **ВАЖНО:** Если давящая или жгучая боль длится более 5 минут и отдаёт в левую руку или челюсть — **СРОЧНО ЗВОНИТЕ 103** (подозрение на инфаркт)!"
            )
        else:
            content = (
                "❤️ **YURAK SOHASIDA OG'RIQ BO'LGANDA TEZKOR YORDAM:**\n\n"
                "1. Har qanday harakatni to'xtating, qulay o'tiring yoki yoting.\n"
                "2. Qisib turgan kiyimlarni yeching, derazani ochib xonani havolating.\n"
                "3. Tinchlanishga harakat qiling, vahimaga tushmang.\n"
                "4. Agar shifokoringiz buyurgan bo'lsa, til ostiga dorini qo'ying.\n"
                "⚠️ **DIQQAT:** Agar ko'krakdagi siquvchi yoki achishtiruvchi og'riq 5 daqiqadan ortiq davom etsa va chap qo'l yoki jag'ga uzatilsa — **DARHOL 103 GA QO'NG'IROQ QILING**!"
            )
    elif aid_type == "sugar":
        if lang == "ru":
            content = (
                "🍬 **ПРИ РЕЗКОЙ СЛАБОСТИ ИЛИ ПАДЕНИИ САХАРА (ГИПОГЛИКЕМИЯ):**\n\n"
                "Симптомы: дрожь в руках, холодный пот, сильная слабость, чувство голода.\n\n"
                "1. Срочно выпейте полстакана тёплой сладкой воды (2-3 кусочка сахара или ложка мёда).\n"
                "2. Либо выпейте сладкого фруктового сока или съешьте конфету.\n"
                "3. Прилягте и отдохните 15 минут.\n"
                "⚠️ Если через 15 минут самочувствие не улучшилось — вызовите врача по номеру **103**!"
            )
        else:
            content = (
                "🍬 **HOLSIDLIK VA QAND MODDASI TUSHIB KETGANDA:**\n\n"
                "Belgilari: Qo'l-oyoq qaltirashi, sovuq ter bosishi, qattiq ochlik va darmonsizlik.\n\n"
                "1. Zudlik bilan yarim stakan iliq shirin choy yoki 2 qoshiq shakarli suv iching.\n"
                "2. Yoki konfet, asal, shirin sharbat iste'mol qiling.\n"
                "3. Yotib, 15 daqiqa xotirjam dam oling.\n"
                "⚠️ Agar 15 daqiqadan so'ng o'zgarish bo'lmasa — darhol **103** ga xabar bering!"
            )
    else: # dizzy
        if lang == "ru":
            content = (
                "🌀 **ПЕРВАЯ ПОМОЩЬ ПРИ ГОЛОВОКРУЖЕНИИ И ПРЕДОБМОРОКЕ:**\n\n"
                "1. Немедленно прилягте на спину, приподняв ноги чуть выше уровня головы (на подушку).\n"
                "2. Поверните голову набок на случай тошноты.\n"
                "3. Сбрызните лицо и шею прохладной водой, поднесите к носу ватку с нашатырным спиртом (если есть).\n"
                "4. Не вставайте резко, пока самочувствие полностью не нормализуется."
            )
        else:
            content = (
                "🌀 **BOSH AYLANISHI VA HUSHDAN KETISH XAVFIDA:**\n\n"
                "1. Zudlik bilan chalqancha yoting, oyoqlarni boshingizdan biroz balandroq qilib yostiq ustiga qo'ying.\n"
                "2. Boshni bir chetga burib qo'ying.\n"
                "3. Yuz va bo'yinga sovuq suv seping, toza havodan nafas oling.\n"
                "4. O'zingizga to'liq kelmaguningizcha keskin o'rningizdan turmang."
            )

    back_btn = "🔙 К списку первой помощи" if lang == "ru" else "🔙 Birinchi yordam bo'limiga qaytish"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=back_btn, callback_data="sos:first_aid")],
        [InlineKeyboardButton(text="🚨 103 Chaqirish tartibi" if lang == "uz" else "🚨 Вызвать 103", callback_data="sos:info_103")]
    ])
    await callback.message.edit_text(content, reply_markup=kb)
    await callback.answer()

@router.callback_query(F.data == "sos:voice_calm")
async def send_calming_voice(callback: types.CallbackQuery):
    """Hayajonlangan insonni tinchlantiruvchi samimiy neyron ovozli xabar"""
    user_id = callback.from_user.id
    user = await database.get_user(user_id)
    lang = user.get("language", "uz") if user else "uz"
    gender = user.get("gender", "female") if user else "female"
    appeal = user.get("appeal") or user.get("name") or ("qadrdonimiz" if lang == "uz" else "дорогой друг")

    if lang == "ru":
        calm_text = (
            f"Здравствуйте, {appeal}. Пожалуйста, не волнуйтесь и не переживайте. "
            "Сделайте медленный, глубокий вдох и спокойный выдох. "
            "Ваше здоровье — самое дорогое для ваших детей и внуков. "
            "Присядьте поудобнее, выпейте несколько глотков тёплой воды. "
            "Если вам нездоровится, обязательно наберите 103 или свяжитесь с близкими. "
            "Мы рядом с вами, всё обязательно будет хорошо!"
        )
        caption = f"🎙️ **Голосовое напутствие и поддержка для {appeal}:**\n\n{calm_text}"
    else:
        calm_text = (
            f"Assalomu alaykum, {appeal}. Iltimos, aslo xavotir olmang va hayajonlanmang. "
            "Sekin va chuqur nafas oling. Sizning sihat-salomatligingiz farzandlaringiz va barchamiz uchun eng katta boylik. "
            "Qulay o'tirib, iliq suvdan bir necha qultum iching. "
            "Agar o'zingizni noxush his qilayotgan bo'lsangiz, albatta 103 raqamiga qo'ng'iroq qiling yoki yaqinlaringizga xabar bering. "
            "Hammasi yaxshi bo'ladi, biz hamisha siz bilanmiz!"
        )
        caption = f"🎙️ **{appeal} uchun taskin va samimiy yo'l-yo'riq:**\n\n{calm_text}"

    await callback.answer("Ovozli yo'riqnoma tayyorlanmoqda..." if lang == "uz" else "Подготавливаю голосовое сообщение...")
    try:
        audio_bytes = await tts_service.text_to_speech_bytes(calm_text, lang=lang, gender=gender, rate="-4%")
        if audio_bytes:
            voice_in = BufferedInputFile(audio_bytes, filename="calm_sos.mp3")
            await callback.message.answer_voice(voice=voice_in, caption=caption)
        else:
            await callback.message.answer(caption)
    except Exception as e:
        logger.error(f"SOS ovozida xatolik: {e}")
        await callback.message.answer(caption)

@router.callback_query(F.data == "sos:set_phone")
async def ask_doctor_phone(callback: types.CallbackQuery, state: FSMContext):
    """Shaxsiy shifokor yoki farzand raqamini kiritishni so'rash"""
    user_id = callback.from_user.id
    user = await database.get_user(user_id)
    lang = user.get("language", "uz") if user else "uz"

    await state.set_state(SOSStates.waiting_for_doctor_phone)
    msg = (
        "📝 Iltimos, shaxsiy shifokoringiz yoki favqulodda vaziyatda bog'laniladigan yaqiningiz telefon raqamini yozing:\n"
        "(Masalan: `+998901234567` yoki `901234567`)"
        if lang == "uz" else
        "📝 Пожалуйста, введите номер телефона вашего личного врача или близкого человека:\n"
        "(Например: `+998901234567`)"
    )
    await callback.message.answer(msg)
    await callback.answer()

@router.message(SOSStates.waiting_for_doctor_phone)
async def save_doctor_phone(message: types.Message, state: FSMContext):
    """Kiritilgan telefon raqamini tekshirish va saqlash"""
    user_id = message.from_user.id
    user = await database.get_user(user_id)
    lang = user.get("language", "uz") if user else "uz"

    phone = message.text.strip()
    await database.set_user_doctor_phone(user_id, phone)
    await state.clear()

    msg = (
        f"✅ Telefon raqami muvaffaqiyatli saqlandi: **{phone}**\n\n"
        f"Endi kerak bo'lganda /sos bo'limi orqali tezkor qo'ng'iroq qilishingiz mumkin."
        if lang == "uz" else
        f"✅ Номер телефона успешно сохранён: **{phone}**\n\n"
        f"Теперь вы сможете быстро связаться с ним через раздел /sos."
    )
    await message.answer(msg, reply_markup=keyboards.get_main_menu_kb("keksa", lang))

