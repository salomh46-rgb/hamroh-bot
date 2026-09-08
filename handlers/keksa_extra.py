import os
import time
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
import database
import gemini_service
import tts_service

router = Router()

# Otaxon-onaxonlar uchun qiziqarli va foydali saralangan YouTube videolari (O'zbekcha)
YOUTUBE_VIDEOS_UZ = [
    {
        "title": "🌿 Shifobaxsh giyohlar va qon bosimini tushirish usullari",
        "url": "https://www.youtube.com/results?search_query=shifobaxsh+giyohlar+tabobat"
    },
    {
        "title": "🎵 O'zbek mumtoz maqomlari va xalq qo'shiqlari",
        "url": "https://www.youtube.com/results?search_query=ozbek+mumtoz+maqom+qoshiqlari"
    },
    {
        "title": "🕌 O'zbekiston tabarruk ziyoratgohlari (Samarqand, Buxoro)",
        "url": "https://www.youtube.com/results?search_query=ozbekiston+ziyoratgohlari+samarqand+buxoro"
    },
    {
        "title": "🧘 Keksalar uchun ertalabki yengil badantarbiya",
        "url": "https://www.youtube.com/results?search_query=keksalar+uchun+ertalabki+mashqlar"
    }
]

# Rusiyzabon keksalar uchun YouTube videolari (Ruscha)
YOUTUBE_VIDEOS_RU = [
    {
        "title": "🌿 Травяные чаи и советы для здоровья и долголетия",
        "url": "https://www.youtube.com/results?search_query=народная+медицина+для+пожилых+долголетие"
    },
    {
        "title": "🎵 Душевные песни прошлых лет и ретро-романсы",
        "url": "https://www.youtube.com/results?search_query=душевные+ретро+песни+ссср+романсы"
    },
    {
        "title": "🏛️ Экскурсии по красивым историческим местам и храмам",
        "url": "https://www.youtube.com/results?search_query=золотое+кольцо+экскурсии+святые+места"
    },
    {
        "title": "🧘 Оздоровительная гимнастика для суставов 60+",
        "url": "https://www.youtube.com/results?search_query=гимнастика+для+пожилых+лфк+60"
    }
]

def get_video_kb(lang: str = "uz") -> InlineKeyboardMarkup:
    videos = YOUTUBE_VIDEOS_RU if lang == "ru" else YOUTUBE_VIDEOS_UZ
    buttons = []
    for item in videos:
        buttons.append([InlineKeyboardButton(text=item["title"], url=item["url"])])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@router.message(F.text.in_(["📻 Foydali videolar", "📻 Полезные видео"]))
async def show_useful_videos(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    user = await database.get_user(user_id)
    lang = user.get("language", "uz") if user else "uz"

    if lang == "ru":
        msg = (
            "📺 **Отобранные душевные и полезные видеоролики:**\n\n"
            "Выберите тему, чтобы открыть подборку на YouTube:\n\n"
            "• 🌿 **Здоровье и долголетие**\n"
            "• 🎵 **Любимые ретро-песни и романсы**\n"
            "• 🏛️ **Путешествия и святые места**\n"
            "• 🧘 **Мягкая оздоровительная гимнастика**\n\n"
            "Нажмите на нужный раздел:"
        )
    else:
        msg = (
            "📺 **Otaxon va onaxonlarimiz uchun saralangan foydali videoroliklar:**\n\n"
            "Quyidagi mavzulardan birini tanlab, to'g'ridan-to'g'ri YouTube orqali tomosha qilishingiz mumkin:\n\n"
            "• 🌿 **Tabobat va salomatlik sirlari**\n"
            "• 🎵 **Mumtoz maqom va xalq navolari**\n"
            "• 🕌 **Tabarruk ziyoratgohlar sayohati**\n"
            "• 🧘 **Yengil ertalabki mashqlar**\n\n"
            "Kerakli bo'lim ustiga bosing:"
        )
    await message.answer(msg, reply_markup=get_video_kb(lang))

@router.message(F.text.in_(["📿 Hikmat va Rivoyat", "📿 Мудрые притчи"]))
async def send_wisdom_story(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    user = await database.get_user(user_id)
    lang = user.get("language", "uz") if user else "uz"
    gender = user.get("gender", "female") if user else "female"

    wait_text = "📿 Dono hikmat va ruhiy orom baxsh etuvchi rivoyat tayyorlanmoqda..." if lang == "uz" else "📿 Подбираю мудрую и душевную притчу для вас..."
    loading = await message.answer(wait_text)

    if lang == "ru":
        prompt = (
            "Напиши короткую (3-4 предложения), очень мудрую, добрую и вдохновляющую притчу для пожилого человека. "
            "О ценности душевного покоя, доброты, семьи или благодарности за каждый прожитый день. "
            "Язык — красивый, тёплый, уважительный русский литературный язык."
        )
        default_story = "У мудреца спросили: «Какое самое драгоценное богатство в мире?» Мудрец с улыбкой ответил: «Это мир в душе и здоровье. Когда они есть — каждый день становится благословением»."
    else:
        prompt = (
            "Nuroniy keksa otaxon va onaxonlarimiz uchun o'zbek xalq og'zaki ijodi yoki Sharq donishmandlaridan "
            "bitta qisqa (3-4 jumla), qalbga iliqlik, mehr va xotirjamlik beruvchi ibratli rivoyat yoz. "
            "Tili juda muloyim, hurmatli va ravon o'zbek tilida bo'lsin."
        )
        default_story = "Dono qariyadan so'rashibdi: 'Dunyoda eng katta boylik nima?' Donishmand tabassum qilib javob beribdi: 'Qalb xotirjamligi va sog'likdir. Ular bo'lsa, har bir kun bayramdir'."

    client = gemini_service.get_client()
    story_text = default_story

    if client:
        try:
            res = await client.aio.models.generate_content(
                model=gemini_service.config.GEMINI_MODEL,
                contents=prompt
            )
            if res.text:
                story_text = res.text.strip()
        except Exception:
            pass

    # Audio ovoz yaratish
    audio_file = f"wisdom_{user_id}_{int(time.time())}.mp3"
    audio_path = await tts_service.text_to_speech_file(
        story_text, 
        audio_file, 
        lang=lang, 
        gender=gender, 
        rate="-4%"
    )

    await loading.delete()

    title = "📿 **МУДРАЯ ПРИТЧА ДЛЯ ДУШИ:**" if lang == "ru" else "📿 **QALB OROMI — HIKMAT:**"
    caption_text = f"{title}\n\n{story_text}"

    if audio_path:
        voice_in = FSInputFile(audio_path)
        await message.answer_voice(voice=voice_in, caption=caption_text)
        if os.path.exists(audio_path):
            try:
                os.remove(audio_path)
            except Exception:
                pass
    else:
        await message.answer(caption_text)

