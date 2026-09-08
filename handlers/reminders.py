import re
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import database
import keyboards

router = Router()

import re
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import database
import keyboards

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

class ReminderStates(StatesGroup):
    waiting_for_dori_nomi = State()
    waiting_for_vaqt = State()

def get_cancel_kb(lang: str = "uz") -> InlineKeyboardMarkup:
    text = "❌ Отмена" if lang == "ru" else "❌ Bekor qilish"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=text, callback_data="reminder:cancel")]
    ])

@router.callback_query(F.data == "reminder:cancel")
async def cancel_reminder_flow(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    user = await database.get_user(user_id)
    lang = user.get("language", "uz") if user else "uz"

    await state.clear()
    msg = "❌ Добавление напоминания отменено." if lang == "ru" else "❌ Dori eslatmasi qo'shish bekor qilindi."
    await callback.message.edit_text(msg)
    await callback.answer()

@router.message(F.text.in_(["💊 Dori eslatmalari", "💊 Напоминания"]))
async def show_reminders_menu(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    user = await database.get_user(user_id)
    lang = user.get("language", "uz") if user else "uz"

    reminders = await database.get_user_reminders(user_id)
    if not reminders:
        if lang == "ru":
            msg = "В настоящее время у вас нет активных напоминаний о лекарствах.\n\nЧтобы добавить напоминание, нажмите кнопку ниже:"
        else:
            msg = "Hozirda sizda hech qanday dori eslatmasi belgilanmagan.\n\nYangi eslatma qo'shish uchun quyidagi tugmani bosing:"
    else:
        if lang == "ru":
            msg = "📋 **Ваши напоминания о приёме лекарств:**\n\n"
            for i, r in enumerate(reminders, 1):
                msg += f"{i}. 💊 **{r['dori_nomi']}** — ⏰ Время: `{r['vaqt']}`\n"
            msg += "\nВы можете добавить новое или удалить ненужное напоминание:"
        else:
            msg = "📋 **Sizning dori eslatmalaringiz:**\n\n"
            for i, r in enumerate(reminders, 1):
                msg += f"{i}. 💊 **{r['dori_nomi']}** — ⏰ Soat: `{r['vaqt']}`\n"
            msg += "\nYangi eslatma qo'shish yoki mavjudlarini o'chirish mumkin:"

    await message.answer(msg, reply_markup=keyboards.get_reminders_kb(lang))

@router.callback_query(F.data == "reminder:add")
async def start_add_reminder(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    user = await database.get_user(user_id)
    lang = user.get("language", "uz") if user else "uz"

    await state.set_state(ReminderStates.waiting_for_dori_nomi)
    await state.update_data(lang=lang)

    if lang == "ru":
        msg = (
            "📝 Пожалуйста, напишите название лекарства и дозу:\n"
            "(Например: `Аспирин кардио 1 таблетка` или `Кальций Д3`)"
        )
    else:
        msg = (
            "📝 Iltimos, dori nomini va dozasini yozing:\n"
            "(Masalan: `Aspirin kardio 1 tabletka` yoki `Kalsiy D3`)"
        )

    await callback.message.answer(msg, reply_markup=get_cancel_kb(lang))
    await callback.answer()

@router.message(ReminderStates.waiting_for_dori_nomi)
async def process_dori_nomi(message: types.Message, state: FSMContext):
    if message.text in MENU_BUTTONS or message.text.startswith("/"):
        await state.clear()
        return

    data = await state.get_data()
    lang = data.get("lang", "uz")

    dori_nomi = message.text.strip()
    if len(dori_nomi) < 2:
        msg = "Пожалуйста, введите полное название лекарства:" if lang == "ru" else "Iltimos, dori nomini to'liqroq kiriting:"
        await message.answer(msg, reply_markup=get_cancel_kb(lang))
        return

    await state.update_data(dori_nomi=dori_nomi)
    await state.set_state(ReminderStates.waiting_for_vaqt)

    if lang == "ru":
        msg = (
            f"✅ Лекарство: **{dori_nomi}**\n\n"
            f"Теперь введите время приёма в формате `ЧЧ:ММ`:\n"
            f"(Например: `08:30`, `14:00`, `20:45`)"
        )
    else:
        msg = (
            f"✅ Dori: **{dori_nomi}**\n\n"
            f"Endi har kuni dori ichish vaqtini `SS:DD` formatida kiriting:\n"
            f"(Masalan: `08:30`, `14:00`, `20:45`)"
        )

    await message.answer(msg, reply_markup=get_cancel_kb(lang))

@router.message(ReminderStates.waiting_for_vaqt)
async def process_vaqt(message: types.Message, state: FSMContext):
    if message.text in MENU_BUTTONS or message.text.startswith("/"):
        await state.clear()
        return

    data = await state.get_data()
    lang = data.get("lang", "uz")
    dori_nomi = data.get("dori_nomi", "Dori")

    vaqt_text = message.text.strip()
    match = re.match(r"^([0-1]?[0-9]|2[0-3]):([0-5][0-9])$", vaqt_text)
    if not match:
        if lang == "ru":
            err_msg = (
                "⚠️ Неверный формат времени!\n"
                "Пожалуйста, укажите время в 24-часовом формате, например `08:30` или `21:15`:"
            )
        else:
            err_msg = (
                "⚠️ Vaqt noto'g'ri kiritildi!\n"
                "Iltimos, `08:30` yoki `21:15` kabi 24 soatlik formatda yozing:"
            )
        await message.answer(err_msg, reply_markup=get_cancel_kb(lang))
        return

    soat, daqiqa = match.groups()
    formatlangan_vaqt = f"{int(soat):02d}:{daqiqa}"

    await database.add_reminder(
        user_id=message.from_user.id,
        dori_nomi=dori_nomi,
        vaqt=formatlangan_vaqt
    )
    await state.clear()

    if lang == "ru":
        success_msg = (
            f"🎉 **Напоминание успешно сохранено!**\n\n"
            f"💊 Лекарство: **{dori_nomi}**\n"
            f"⏰ Каждый день в **{formatlangan_vaqt}** я буду заботливо напоминать вам голосом и текстом."
        )
    else:
        success_msg = (
            f"🎉 **Eslatma muvaffaqiyatli saqlandi!**\n\n"
            f"💊 Dori: **{dori_nomi}**\n"
            f"⏰ Har kuni soat: **{formatlangan_vaqt}** da ovozli va matnli eslatib turaman."
        )

    await message.answer(success_msg, reply_markup=keyboards.get_main_menu_kb("keksa", lang))

@router.callback_query(F.data == "reminder:list")
async def list_and_manage_reminders(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = callback.from_user.id
    user = await database.get_user(user_id)
    lang = user.get("language", "uz") if user else "uz"

    reminders = await database.get_user_reminders(user_id)
    if not reminders:
        msg = "У вас нет активных напоминаний." if lang == "ru" else "Sizda faol eslatmalar mavjud emas."
        await callback.message.answer(msg)
        await callback.answer()
        return

    buttons = []
    del_prefix = "🗑️ Удалить:" if lang == "ru" else "🗑️ O'chirish:"
    for r in reminders:
        buttons.append([
            InlineKeyboardButton(
                text=f"{del_prefix} {r['dori_nomi']} ({r['vaqt']})",
                callback_data=f"rem_del:{r['id']}"
            )
        ])
    add_btn_text = "➕ Добавить ещё" if lang == "ru" else "➕ Yangi qo'shish"
    buttons.append([InlineKeyboardButton(text=add_btn_text, callback_data="reminder:add")])
    
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    choose_msg = "Нажмите на напоминание, которое хотите удалить:" if lang == "ru" else "O'chirmoqchi bo'lgan eslatmangiz ustiga bosing:"
    await callback.message.answer(choose_msg, reply_markup=kb)
    await callback.answer()

@router.callback_query(F.data.startswith("rem_del:"))
async def delete_reminder_action(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user = await database.get_user(user_id)
    lang = user.get("language", "uz") if user else "uz"

    rem_id = int(callback.data.split(":")[1])
    success = await database.delete_reminder(rem_id, user_id)
    if success:
        msg = "✅ Напоминание успешно удалено." if lang == "ru" else "✅ Eslatma muvaffaqiyatli o'chirildi."
        await callback.message.edit_text(msg)
    else:
        err = "Ошибка при удалении напоминания." if lang == "ru" else "Eslatmani o'chirishda xatolik yuz berdi."
        await callback.answer(err, show_alert=True)
    await callback.answer()

@router.callback_query(F.data.startswith("med_taken:"))
async def on_med_taken(callback: types.CallbackQuery):
    """Foydalanuvchi [✅ Dorini ichdim] tugmasini bosganda tasdiqlash va ball berish"""
    user_id = callback.from_user.id
    user = await database.get_user(user_id)
    lang = user.get("language", "uz") if user else "uz"
    appeal = user.get("appeal") or user.get("name") or ("qadrdonimiz" if lang == "uz" else "дорогой друг")

    parts = callback.data.split(":")
    log_id = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0

    if log_id:
        await database.mark_reminder_taken(log_id, user_id)

    # Foydalanuvchiga +5 salomatlik balli
    await database.add_user_points(user_id, 5)

    if lang == "ru":
        alert_text = f"Прекрасно, {appeal}! Лекарство принято вовремя. Крепкого здоровья! 🌸"
        badge_text = "✅ Принято вовремя 🌸"
    else:
        alert_text = f"Ofarin, {appeal}! Dorini o'z vaqtida qabul qildingiz. Hamisha sog'-omon bo'ling! 🌸"
        badge_text = "✅ O'z vaqtida ichildi 🌸"

    await callback.answer(alert_text, show_alert=True)
    try:
        await callback.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=badge_text, callback_data="none")]
        ]))
    except Exception:
        pass

@router.callback_query(F.data.startswith("reminder:report"))
@router.message(F.text.in_(["📊 Salomatlik hisoboti", "📊 Salomatlik va dori hisoboti", "📊 Отчёт о приёме лекарств", "📊 Отчёт о здоровье"]))
async def show_health_report_handler(event: types.Message | types.CallbackQuery):
    """Haftalik yoki oylik salomatlik / dori intizomi hisobotini chiroyli grafik bilan chiqarish"""
    is_callback = isinstance(event, types.CallbackQuery)
    message = event.message if is_callback else event
    user_id = event.from_user.id
    user = await database.get_user(user_id)
    lang = user.get("language", "uz") if user else "uz"
    appeal = user.get("appeal") or user.get("name") or ("qadrdonimiz" if lang == "uz" else "дорогой друг")

    days = 7
    if is_callback and ":" in event.data:
        parts = event.data.split(":")
        if len(parts) >= 3 and parts[2].isdigit():
            days = int(parts[2])

    report = await database.get_health_report(user_id, days=days)
    total = report["total"]
    taken = report["taken"]
    missed = report["missed"]
    rate = report["rate"]
    recent = report["recent_logs"]

    filled = min(10, max(0, int(round(rate / 10))))
    bar = "🟩" * filled + "⬜" * (10 - filled)

    if lang == "ru":
        period_text = f"{days} дней"
        title = f"📊 **ОТЧЁТ О ПРИЁМЕ ЛЕКАРСТВ ({period_text.upper()}):**\n\n"
        greeting = f"👵 Дорогой(ая) **{appeal}**! Вот ваша дисциплина здоровья:\n\n"
        progress = f"📈 **Соблюдение графика:** `{rate}%`\n`[{bar}]`\n\n"
        stats = (
            f"📋 **Статистика за {days} дней:**\n"
            f"• Всего напоминаний: **{total}**\n"
            f"• Принято вовремя: **{taken}** ✅\n"
            f"• Пропущено / не отмечено: **{missed}** ⚠️\n\n"
        )
        if rate >= 80:
            advice = "💡 *Совет доктора:* Замечательный результат! Вы заботитесь о здоровье, продолжайте в том же духе! 🌸\n\n"
        else:
            advice = "💡 *Совет доктора:* Не забывайте вовремя принимать назначенные лекарства. Ваше здоровье — самое дорогое! 🌿\n\n"

        logs_header = "📝 **Последние приёмы:**\n"
        logs_str = ""
        for item in recent[:6]:
            st = "✅ Принято" if item["status"] == "taken" else "⚠️ Ожидание"
            logs_str += f"• 💊 {item['dori_nomi']} ({item.get('scheduled_time', '')}) — {st}\n"
        if not logs_str:
            logs_str = "• Записей о приёме пока нет.\n"

        other_days = 30 if days == 7 else 7
        toggle_btn = f"📅 Показать за {other_days} дней"
    else:
        period_text = f"{days} kunlik"
        title = f"📊 **SALOMATLIK VA DORI HISOBOTI ({period_text.upper()}):**\n\n"
        greeting = f"👵 Hurmatli **{appeal}**! Sizning dori qabul qilish intizomingiz:\n\n"
        progress = f"📈 **Grafik intizomi:** `{rate}%`\n`[{bar}]`\n\n"
        stats = (
            f"📋 **{days} kunlik ko'rsatkichlar:**\n"
            f"• Yuborilgan eslatmalar: **{total} ta**\n"
            f"• O'z vaqtida ichilgan: **{taken} ta** ✅\n"
            f"• E'tibordan chetda qolgan: **{missed} ta** ⚠️\n\n"
        )
        if rate >= 80:
            advice = "💡 *Shifokor tavsiyasi:* Ajoyib natija! O'z salomatligingizga mas'uliyat bilan qarayotganingiz quvonarli! 🌸\n\n"
        else:
            advice = "💡 *Shifokor tavsiyasi:* Shifokor yozib bergan dorilarni o'z vaqtida ichishga harakat qiling. Salomatlik — eng oliy boylik! 🌿\n\n"

        logs_header = "📝 **Oxirgi qaydlar:**\n"
        logs_str = ""
        for item in recent[:6]:
            st = "✅ Ichildi" if item["status"] == "taken" else "⚠️ Kutilmoqda"
            logs_str += f"• 💊 {item['dori_nomi']} ({item.get('scheduled_time', '')}) — {st}\n"
        if not logs_str:
            logs_str = "• Hozircha dori qabul qilish qaydlari yo'q.\n"

        other_days = 30 if days == 7 else 7
        toggle_btn = f"📅 {other_days} kunlik hisobotni ko'rish"

    full_text = f"{title}{greeting}{progress}{stats}{advice}{logs_header}{logs_str}"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=toggle_btn, callback_data=f"reminder:report:{other_days}")],
        [InlineKeyboardButton(text="➕ Yangi eslatma qo'shish" if lang == "uz" else "➕ Добавить напоминание", callback_data="reminder:add")]
    ])

    if is_callback:
        await event.message.edit_text(full_text, reply_markup=kb)
        await event.answer()
    else:
        await message.answer(full_text, reply_markup=kb)



