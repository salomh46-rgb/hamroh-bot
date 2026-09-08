from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import database

router = Router()

MUSIC_LIST_UZ = [
    {
        "title": "📻 90-yillar o'zbek oltin qo'shiqlari to'plami",
        "url": "https://www.youtube.com/results?search_query=90-yillar+ozbek+retro+qoshiqlari"
    },
    {
        "title": "🎵 Sherali Jo'rayev — Mumtoz va qalbga yaqin taronalar",
        "url": "https://www.youtube.com/results?search_query=sherali+jorayev+oltin+meros"
    },
    {
        "title": "✨ Botir Zokirov — Betakror xalq qo'shiqlari",
        "url": "https://www.youtube.com/results?search_query=botir+zokirov+eng+yaxshi+qoshiqlari"
    },
    {
        "title": "🌸 Nasiba Abdullayeva va Yulduz Usmonova retro xitlari",
        "url": "https://www.youtube.com/results?search_query=nasiba+abdullayeva+yulduz+usmonova+retro"
    },
    {
        "title": "🎻 O'zbek milliy dutor va tanbur kuylari",
        "url": "https://www.youtube.com/results?search_query=ozbek+milliy+dutor+kuylari"
    }
]

MUSIC_LIST_RU = [
    {
        "title": "📻 Золотые хиты 70-80-90-х годов",
        "url": "https://www.youtube.com/results?search_query=золотые+хиты+ссср+70+80+90"
    },
    {
        "title": "🎵 Анна Герман — Самые душевные песни",
        "url": "https://www.youtube.com/results?search_query=анна+герман+лучшие+песни"
    },
    {
        "title": "✨ Муслим Магомаев — Бессмертная классика",
        "url": "https://www.youtube.com/results?search_query=муслим+магомаев+лучшие+песни"
    },
    {
        "title": "🌸 Любимые старые романсы и вальсы",
        "url": "https://www.youtube.com/results?search_query=старинные+русские+романсы"
    },
    {
        "title": "🎻 Спокойная инструментальная ретро-музыка",
        "url": "https://www.youtube.com/results?search_query=инструментальная+ностальгическая+музыка"
    }
]

def get_music_kb(lang: str = "uz") -> InlineKeyboardMarkup:
    items = MUSIC_LIST_RU if lang == "ru" else MUSIC_LIST_UZ
    buttons = []
    for m in items:
        buttons.append([InlineKeyboardButton(text=m["title"], url=m["url"])])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@router.message(F.text.in_(["🎵 Oltin taronalar", "🎵 Ретро-музыка"]))
async def show_music_menu(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    user = await database.get_user(user_id)
    lang = user.get("language", "uz") if user else "uz"

    if lang == "ru":
        msg = (
            "🎵 **ЛЮБИМЫЕ РЕТРО-ПЕСНИ И МЕЛОДИИ ДУШИ:**\n\n"
            "Музыка греет сердце и дарит тёплые воспоминания! "
            "Специально для вас мы собрали прекрасные золотые композиции прошлых лет:\n\n"
            "• Песни 70-80-90-х годов\n"
            "• Любимые романсы и душевные вальсы\n"
            "• Классика эстрады\n\n"
            "Нажмите на интересующий сборник, чтобы включить музыку:"
        )
    else:
        msg = (
            "🎵 **QALBGA YAQIN OLTIN TARONALAR VA 90-YILLAR XITLARI:**\n\n"
            "Yaxshi kuy va qo'shiq qalbga orom bag'ishlaydi, yoshlikning go'zal xotiralarini yodga soladi. "
            "Siz uchun eng sara mumtoz va retro qo'shiqlar to'plamini tayyorladik:\n\n"
            "• 90-yillar o'zbek retro qo'shiqlari\n"
            "• Sevimli san'atkorlar ijrosi\n"
            "• Dutor va tanbur navolari\n\n"
            "Eshitishni istagan taronangiz ustiga bosing:"
        )

    await message.answer(msg, reply_markup=get_music_kb(lang))
