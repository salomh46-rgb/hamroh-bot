import os
import time
import json
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile
import gemini_service
import database
import tts_service

router = Router()

# Har bir foydalanuvchining kvest holatini vaqtinchalik saqlash
user_quests = {}

@router.message(F.text.in_(["🗺️ Kvest-Ertak", "🗺️ Квест-Сказка"]))
async def start_quest(message: types.Message, state: FSMContext):
    """Interaktiv kvest-ertakni boshlash"""
    await state.clear()
    user_id = message.from_user.id
    user = await database.get_user(user_id)
    lang = user.get("language", "uz") if user else "uz"

    loading_text = "🧙‍♂️ Волшебный квест начинается, подожди секундочку..." if lang == "ru" else "🧙‍♂️ Sehrli kvest-sarguzasht boshlanmoqda, kutib turing..."
    loading = await message.answer(loading_text)

    user_quests[user_id] = {
        "step": 1,
        "history": "Волшебное приключение началось." if lang == "ru" else "Sehrli o'rmonda sarguzasht boshlandi.",
        "lang": lang
    }

    if lang == "ru":
        prompt = (
            "Создай 1-Ю ЧАСТЬ интерактивной сказки-квеста для детей на русском языке. "
            "Герой — смелый ребёнок, попавший в волшебную страну. "
            "Текст короткий (2-3 предложения), захватывающий и заканчивается интригой. "
            "В конце дай 2 интересных варианта выбора пути. "
            "Ответ строго в формате JSON:\n"
            "{\n"
            '  "story": "Краткий текст начала сказки...",\n'
            '  "opt1": "Вариант 1 (кратко)",\n'
            '  "opt2": "Вариант 2 (кратко)"\n'
            "}"
        )
        story = "Ты стоишь перед сияющей волшебной дверью. Когда она открывается, перед тобой открываются две дороги: хрустальный мост над облаками и тропинка к поющему водопаду. Куда ты пойдёшь?"
        opt1 = "🌉 Пойти по хрустальному мосту"
        opt2 = "🌊 Пойти к поющему водопаду"
    else:
        prompt = (
            "Bolajonlar uchun o'zbek tilida qiziqarli interaktiv sarguzasht ertakning 1-QISMINI tuz. "
            "Qahramon: Jasur bolakay yoki qizaloq. U sehrli olamga tushib qoldi. "
            "Matn qisqa (2-3 jumla), qiziqarli va intriga bilan tugasin. "
            "Oxirida bolaga 2 ta tanlov berilishi kerak. "
            "Javob formati aniq quyidagicha JSON bo'lsin:\n"
            "{\n"
            '  "story": "Sehrli ertakning qisqa matni...",\n'
            '  "opt1": "1-tanlov qisqa nomi",\n'
            '  "opt2": "2-tanlov qisqa nomi"\n'
            "}"
        )
        story = "Sen sehrli yaltiroq eshik oldida turibsan. Eshik ochilganda ichkaridan mayin kuy va yaltiroq yulduzchalar ko'rindi. Oldingda ikkita yo'l bor: biri billur ko'prik, ikkinchisi sehrli sharsharaga eltadi. Qaysi biridan yurasan?"
        opt1 = "🌉 Billur ko'prikdan yurish"
        opt2 = "🌊 Sharsharaga borish"

    client = gemini_service.get_client()
    if client:
        try:
            res = await client.aio.models.generate_content(
                model=gemini_service.config.GEMINI_MODEL,
                contents=prompt
            )
            raw = res.text.strip() if res.text else ""
            if "{" in raw and "}" in raw:
                j_str = raw[raw.find("{"):raw.rfind("}")+1]
                data = json.loads(j_str)
                story = data.get("story", story)
                opt1 = data.get("opt1", opt1)
                opt2 = data.get("opt2", opt2)
        except Exception:
            pass

    user_quests[user_id]["history"] = story

    # Audio ovoz (in-memory BytesIO)
    audio_bytes = await tts_service.text_to_speech_bytes(story, lang=lang, gender="female", rate="-2%")

    await loading.delete()

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=opt1, callback_data="quest:opt1")],
        [InlineKeyboardButton(text=opt2, callback_data="quest:opt2")]
    ])

    title = "🗺️ **ВОЛШЕБНЫЙ КВЕСТ (ШАГ 1):**" if lang == "ru" else "🗺️ **SEHRLI KVEST (1-QADAM):**"
    full_caption = f"{title}\n\n{story}"

    if audio_bytes:
        voice_in = BufferedInputFile(audio_bytes, filename="quest.mp3")
        await message.answer_voice(voice=voice_in, caption=full_caption, reply_markup=kb)
    else:
        await message.answer(full_caption, reply_markup=kb)

@router.callback_query(F.data.startswith("quest:opt"))
async def continue_quest(callback: types.CallbackQuery):
    """Bolaning tanlovi bo'yicha ertakni davom ettirish"""
    user_id = callback.from_user.id
    q_data = user_quests.get(user_id, {"step": 1, "history": "", "lang": "uz"})
    step = q_data.get("step", 1) + 1
    lang = q_data.get("lang", "uz")

    choice = "1-yo'l" if callback.data == "quest:opt1" else "2-yo'l"
    await callback.message.edit_reply_markup(reply_markup=None)

    wait_text = f"🧭 Шаг {step}: Идём по выбранному пути..." if lang == "ru" else f"🧭 {step}-qadam: Tanlagan yo'ling sari intilmoqdasan..."
    loading = await callback.message.answer(wait_text)

    if step >= 3:
        # Yakuniy qism — G'alaba va Mukofot!
        if lang == "ru":
            prompt = (
                f"Предыдущие события: {q_data.get('history')}. Ребёнок выбрал {choice}. "
                "Заверши сказку радостной победой, нахождением сокровищ или спасением друзей (2-3 предложения). "
                "Поздравь юного героя за смелость!"
            )
            final_story = "Ты смело преодолел путь и нашёл сундук с кристаллами мудрости! Жители волшебного королевства наградили тебя почётным титулом 'Самый храбрый герой'!"
        else:
            prompt = (
                f"Oldingi voqea: {q_data.get('history')}. Bola {choice}ni tanladi. "
                "Endi ertakni bolaning quvonchli g'alabasi, sehrli xazina yoki do'stlar topishi bilan yakunla (3 jumla). "
                "Bolani jasorati uchun tabrikla!"
            )
            final_story = "Sen billur ko'prikdan o'tib, orzular qasrini topding! Qasr ahli sening jasoratingga qoyil qolib, 'Eng dono qahramon' tojini kiydirishdi!"

        client = gemini_service.get_client()
        if client:
            try:
                res = await client.aio.models.generate_content(
                    model=gemini_service.config.GEMINI_MODEL,
                    contents=prompt
                )
                if res.text:
                    final_story = res.text.strip()
            except Exception:
                pass

        new_points = await database.add_user_points(user_id, 25) # Katta mukofot!

        audio_bytes = await tts_service.text_to_speech_bytes(final_story, lang=lang, gender="female", rate="-2%")

        await loading.delete()

        if lang == "ru":
            win_caption = (
                f"🏆 **ПОЗДРАВЛЯЕМ! ТЫ ПОБЕДИЛ!**\n\n"
                f"{final_story}\n\n"
                f"🎉 За успешное прохождение квеста тебе начислено **+25 ЗОЛОТЫХ МОНЕТ**!\n"
                f"⭐ Всего баллов: **{new_points} баллов**!"
            )
            restart_btn = "🔄 Начать новый квест"
        else:
            win_caption = (
                f"🏆 **TABRIKLAYMIZ! SEN G'OLIB BO'LDING!**\n\n"
                f"{final_story}\n\n"
                f"🎉 Sarguzashtni muvaffaqiyatli yakunlaganing uchun senga **+25 OLTIN TANGA** berildi!\n"
                f"⭐ Jami ballaring: **{new_points} ball**!"
            )
            restart_btn = "🔄 Yangi boshqa kvest boshlash"

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=restart_btn, callback_data="quest:restart")]
        ])

        if audio_bytes:
            voice_in = BufferedInputFile(audio_bytes, filename="quest_end.mp3")
            await callback.message.answer_voice(voice=voice_in, caption=win_caption, reply_markup=kb)
        else:
            await callback.message.answer(win_caption, reply_markup=kb)

        user_quests.pop(user_id, None)
        await callback.answer()
        return

    # 2-QADAM
    if lang == "ru":
        prompt = (
            f"Предыдущие события: {q_data.get('history')}. Ребёнок выбрал {choice}. "
            "Напиши 2-Ю ЧАСТЬ интерактивной сказки для детей на русском языке (2-3 предложения). "
            "В конце снова предложи 2 новых варианта выбора. "
            "Ответ строго в JSON:\n"
            "{\n"
            '  "story": "Текст продолжения...",\n'
            '  "opt1": "Вариант А",\n'
            '  "opt2": "Вариант Б"\n'
            "}"
        )
        mid_story = "Ты сделал шаг вперёд и встретил говорящего пушистого лисёнка! Он держит в лапках старинный ключ и карту. Что ты у него спросишь?"
        opt1 = "🔑 Спросить про волшебный ключ"
        opt2 = "🗺️ Попросить показать карту"
    else:
        prompt = (
            f"Oldingi voqea: {q_data.get('history')}. Bola {choice}ni tanladi. "
            "Ertakning 2-QISMINI tuz (2-3 jumla). Qiziqarli voqea yuz bersin. "
            "Oxirida yana 2 ta tanlov ber. "
            "Javob JSON bo'lsin:\n"
            "{\n"
            '  "story": "Ertak davomi...",\n'
            '  "opt1": "Tanlov 1",\n'
            '  "opt2": "Tanlov 2"\n'
            "}"
        )
        mid_story = "Yo'lda davom etib, kichik so'zlovchi olmaxonni uchratding! Uning qo'lida sehrli qulf va jumboqli xat bor. Nima qilasan?"
        opt1 = "🔑 Qulfni ochishga urinish"
        opt2 = "📜 Xatni o'qib ko'rish"

    client = gemini_service.get_client()
    if client:
        try:
            res = await client.aio.models.generate_content(
                model=gemini_service.config.GEMINI_MODEL,
                contents=prompt
            )
            raw = res.text.strip() if res.text else ""
            if "{" in raw and "}" in raw:
                j_str = raw[raw.find("{"):raw.rfind("}")+1]
                data = json.loads(j_str)
                mid_story = data.get("story", mid_story)
                opt1 = data.get("opt1", opt1)
                opt2 = data.get("opt2", opt2)
        except Exception:
            pass

    user_quests[user_id]["step"] = step
    user_quests[user_id]["history"] += f" -> {mid_story}"

    audio_bytes = await tts_service.text_to_speech_bytes(mid_story, lang=lang, gender="female", rate="-2%")

    await loading.delete()

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=opt1, callback_data="quest:opt1")],
        [InlineKeyboardButton(text=opt2, callback_data="quest:opt2")]
    ])

    title = f"🗺️ **ВОЛШЕБНЫЙ КВЕСТ (ШАГ {step}):**" if lang == "ru" else f"🗺️ **SEHRLI KVEST ({step}-QADAM):**"
    full_caption = f"{title}\n\n{mid_story}"

    if audio_bytes:
        voice_in = BufferedInputFile(audio_bytes, filename="quest_step2.mp3")
        await callback.message.answer_voice(voice=voice_in, caption=full_caption, reply_markup=kb)
    else:
        await callback.message.answer(full_caption, reply_markup=kb)

    await callback.answer()

@router.callback_query(F.data == "quest:restart")
async def restart_quest(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await start_quest(callback.message, state)
    await callback.answer()
