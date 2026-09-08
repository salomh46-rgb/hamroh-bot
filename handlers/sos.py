from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import database
import keyboards

router = Router()

class SOSStates(StatesGroup):
    waiting_for_doctor_phone = State()

def get_sos_kb(lang: str = "uz", doctor_phone: str = None) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="🚨 103 (Tez yordam / Скорая помощь)", url="tel:103")]
    ]
    if doctor_phone:
        btn_text = f"📞 Shifokor / Yaqin inson ({doctor_phone})" if lang == "uz" else f"📞 Врач / Близкий ({doctor_phone})"
        buttons.append([InlineKeyboardButton(text=btn_text, url=f"tel:{doctor_phone}")])
    
    add_btn_text = "✏️ Shaxsiy shifokor/farzand raqamini saqlash" if lang == "uz" else "✏️ Сохранить номер врача/близкого"
    buttons.append([InlineKeyboardButton(text=add_btn_text, callback_data="sos:set_phone")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@router.message(F.text.in_(["📞 Shifokor / SOS", "📞 Врач / SOS", "/sos"]))
async def show_sos_menu(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    user = await database.get_user(user_id)
    lang = user.get("language", "uz") if user else "uz"
    doctor_phone = user.get("doctor_phone") if user else None

    if lang == "ru":
        msg = (
            "🆘 **ЭКСТРЕННАЯ ПОМОЩЬ И СВЯЗЬ С ВРАЧОМ:**\n\n"
            "Здоровье и безопасность — самое главное! В случае недомогания вы можете сразу связаться с помощью:\n\n"
            "• **103** — Государственная скорая медицинская помощь.\n"
            f"• **Личный контакт врача/семьи**: `{doctor_phone or 'Не указан'}`\n\n"
            "💡 **Первая помощь при высоком давлении:**\n"
            "1. Сядьте в удобное кресло, расстегните воротник.\n"
            "2. Сделайте медленный глубокий вдох и спокойный выдох.\n"
            "3. Выпейте тёплой воды и примите назначенные врачом препараты.\n\n"
            "Выберите нужное действие ниже:"
        )
    else:
        msg = (
            "🆘 **TEZKOR YORDAM VA SHIFOKOR BILAN BOG'LANISH:**\n\n"
            "Sog'lig'ingiz biz uchun eng muhimi! O'zingizni noxush his qilsangiz, quyidagi tugmalar orqali bir zumda yordam chaqirishingiz mumkin:\n\n"
            "• **103** — Respublika tez tibbiy yordam xizmati.\n"
            f"• **Shaxsiy shifokor yoki farzandingiz raqami**: `{doctor_phone or 'Kiritilmagan'}`\n\n"
            "💡 **Qon bosimi ko'tarilganda tezkor tavsiyalar:**\n"
            "1. O'tirgan holatda tinchlaning, yoqani bo'shating.\n"
            "2. Burun bilan chuqur nafas olib, og'izdan sekin chiqaring.\n"
            "3. Iliq suv iching va shifokor tavsiya qilgan dorini qabul qiling.\n\n"
            "Kerakli amalni tanlang:"
        )

    await message.answer(msg, reply_markup=get_sos_kb(lang, doctor_phone))

@router.callback_query(F.data == "sos:set_phone")
async def ask_doctor_phone(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    user = await database.get_user(user_id)
    lang = user.get("language", "uz") if user else "uz"

    await state.set_state(SOSStates.waiting_for_doctor_phone)
    msg = (
        "Iltimos, shifokoringiz yoki yaqin insoningiz telefon raqamini kiriting:\n(Masalan: `+998901234567`)"
        if lang == "uz" else
        "Пожалуйста, введите номер телефона врача или близкого человека:\n(Например: `+998901234567`)"
    )
    await callback.message.answer(msg)
    await callback.answer()

@router.message(SOSStates.waiting_for_doctor_phone)
async def save_doctor_phone(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user = await database.get_user(user_id)
    lang = user.get("language", "uz") if user else "uz"

    phone = message.text.strip()
    await database.set_user_doctor_phone(user_id, phone)
    await state.clear()

    msg = (
        f"✅ Raqam muvaffaqiyatli saqlandi: **{phone}**\nEndi kerak bo'lganda bir tugma bilan qo'ng'iroq qilishingiz mumkin."
        if lang == "uz" else
        f"✅ Номер успешно сохранён: **{phone}**\nТеперь вы можете связаться в одно касание."
    )
    await message.answer(msg, reply_markup=keyboards.get_main_menu_kb("keksa", lang))
