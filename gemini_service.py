import logging
from typing import List, Dict, Optional
from google import genai
from google.genai import types
import config

logger = logging.getLogger(__name__)

def get_client() -> Optional[genai.Client]:
    if not config.GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY belgilanmagan!")
        return None
    return genai.Client(api_key=config.GEMINI_API_KEY)

async def detect_gender_and_appeal(name: str, lang: str = "uz") -> Dict[str, str]:
    """Ism orqali jins va mos hurmatli murojaatni aniqlash"""
    client = get_client()
    default_res = {
        "gender": "female",
        "appeal": f"{name} ona" if lang == "uz" else f"Уважаемая {name}"
    }
    if not client:
        return default_res

    prompt = (
        f"Foydalanuvchi ismi: '{name}', tanlangan til: '{lang}'.\n"
        "Ushbu ism egasi katta yoshli (keksa) inson hisoblanadi.\n"
        "Vazifang:\n"
        "1. Uning jinsini aniqla ('male' yoki 'female').\n"
        "2. Unga nisbatan eng hurmatli, muloyim va odobli murojaat shaklini yarat "
        "(hech qanday erish, noo'rin 'jonim' kabi so'zlar bo'lmasin, masalan: o'zbekcha ayolga 'Nigina ona' yoki 'Onajon', "
        "erkakka 'Jasur ota' yoki 'Otaxonto'ram'; ruscha ayolga 'Уважаемая Каролина' yoki 'Дорогая бабушка', "
        "erkakka 'Уважаемый Александр' yoki 'Дорогой дедушка').\n"
        "Javobni aniq JSON formatida ber:\n"
        "{\n"
        '  "gender": "male" yoki "female",\n'
        '  "appeal": "murojaat shakli"\n'
        "}"
    )

    try:
        res = await client.aio.models.generate_content(
            model=config.GEMINI_MODEL,
            contents=prompt
        )
        raw = res.text.strip() if res.text else ""
        if "{" in raw and "}" in raw:
            import json
            j_str = raw[raw.find("{"):raw.rfind("}")+1]
            return json.loads(j_str)
    except Exception as e:
        logger.error(f"Ismni tahlil qilishda xato: {e}")
    return default_res

async def chat_response(
    message: str, 
    user_type: str = "keksa", 
    history: Optional[List[Dict[str, str]]] = None,
    lang: str = "uz",
    appeal: str = ""
) -> str:
    """Keksa yoki bola rejimida suhbatlashish (o'zbek yoki rus tilida)"""
    client = get_client()
    if not client:
        return "Gemini API kaliti kiritilmagan. Iltimos, .env faylida GEMINI_API_KEY ni sozlang."

    murojaat = appeal if appeal else ("Otaxonto'ram / Onajonim" if lang == "uz" else "Уважаемый собеседник")

    if lang == "ru":
        if user_type == "keksa":
            system_instruction = (
                f"Ты — 'Hamroh Bot' (Спутник), заботливый, вежливый и душевный виртуальный собеседник для пожилых людей (дедушек и бабушек).\n"
                f"Обращайся к пользователю с уважением: '{murojaat}' (на 'Вы').\n"
                "Правила общения:\n"
                "1. Отвечай исключительно на грамотном, красивом, теплом русском языке.\n"
                "2. Никаких неуместных фамильярностей (не используй 'милочка', 'душенька' и т.д.). Общайся с глубоким уважением, как с родным мудрым человеком.\n"
                "3. Интересуйся здоровьем и настроением, поддерживай беседу о жизни, добрых воспоминаниях, уюте, природе.\n"
                "4. НЕ давай прямых медицинских диагнозов. При жалобах на здоровье мягко советуй обратиться к врачу.\n"
                "5. Ответы должны быть четкими, душевными, без длинных утомительных текстов."
            )
        else:
            system_instruction = (
                "Ты — 'Hamroh Bot', веселый, умный и добрый друг для детей.\n"
                "Общайся на русском языке, дружелюбно, на 'ты', с юмором и поощрением ('Молодец!', 'Здорово!').\n"
                "Учи хорошим поступкам, дружбе, науке и добру простыми словами."
            )
    else:
        if user_type == "keksa":
            system_instruction = (
                f"Sen 'Hamroh Bot' — nuroniy, keksa otaxon va onaxonlarimiz uchun mehribon, hurmatli va g'amxo'r virtual hamroh AI san.\n"
                f"Foydalanuvchiga har doim hurmat bilan murojaat qil: '{murojaat}' (har doim 'Siz').\n"
                "Qoidalar:\n"
                "1. Har doim o'zbek tilida juda muloyim, milliy odob-axloq qoidalariga mos gapir. "
                "Hech qanday erish, noo'rin so'zlarni (masalan 'jonim', 'asalim' kabi) ISHLATMA!\n"
                "2. Ularning hol-ahvolini so'rab, yaxshi kayfiyat ulash, dildan suhbatlash.\n"
                "3. Agar sog'liq yoki dori haqida so'rashsa, aniq tibbiy tashxis qo'yma, shifokor bilan maslahatlashishni uqtir.\n"
                "4. Javoblaring ravon, lo'nda va ko'zni charchatmaydigan bo'lsin."
            )
        else:
            system_instruction = (
                "Sen 'Hamroh Bot' — bolajonlar uchun quvnoq, bilimdon, qiziqarli do'st va ustoz AI san.\n"
                "Qoidalar:\n"
                "1. Har doim o'zbek tilida juda do'stona, samimiy ('sen', 'do'stginam', 'zo'rsan', 'ofarin!') ohangda gapir.\n"
                "2. Bolalarning qiziqishlarini qo'llab-quvvatla, ularga yaxshi odoblarni, ilm o'rganishni o'rgat.\n"
                "3. Murakkab so'zlarni ishlatma, sodda va yorqin misollar bilan tushuntir.\n"
                "4. Bolaga savollar berib, uning fikrlashini rag'batlantir."
            )


    try:
        # Suhbat kontekstini yig'ish
        contents = []
        if history:
            for item in history:
                role = "user" if item["role"] == "user" else "model"
                contents.append(types.Content(role=role, parts=[types.Part.from_text(text=item["content"])]))
        contents.append(types.Content(role="user", parts=[types.Part.from_text(text=message)]))

        gen_config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.7
        )

        response = await client.aio.models.generate_content(
            model=config.GEMINI_MODEL,
            contents=contents,
            config=gen_config
        )
        return response.text.strip() if response.text else "Kechirasiz, javob matni bo'sh bo'ldi."
    except Exception as e:
        logger.error(f"Gemini suhbat xatosi: {e}")
        return f"Kechirasiz, javob tayyorlashda xatolik yuz berdi: {e}"

async def generate_ertak(mavzu: str, yosh: int = 7, lang: str = "uz") -> str:
    """Bolalar uchun sehrli va tarbiyaviy ertak yozish (O'zbek / Rus)"""
    client = get_client()
    if not client:
        return "Gemini API kaliti kiritilmagan."

    if lang == "ru":
        prompt = f"""
Ты — замечательный добрый сказочник.
Напиши для ребенка {yosh} лет интересную, поучительную и волшебную сказку на тему "{mavzu}".
Сказка должна учить добру, дружбе, честности, взаимовыручке.
Язык — живой, образный, понятный и увлекательный для детей.
Начни в классическом сказочном стиле (например: "В некотором царстве, в некотором государстве...").
Объем: 3-4 небольших абзаца.
"""
    else:
        prompt = f"""
Sen o'zbek xalq ertaklari uslubida ijod qiluvchi mohir ertakchi san.
{yosh} yoshli bola uchun "{mavzu}" mavzusida qiziqarli, ibratli va sehrli ertak yozib ber.
Ertakda do'stlik, to'g'riso'zlik, ota-onani hurmat qilish yoki tabiatni asrash kabi ezgu fazilatlar ulug'lansin.
Tili ravon, sodda va bolabop bo'lsin.
Boshlanishi ertak an'anasiga mos bo'lsin (masalan: "Bor ekanda, yo'q ekan, qadim o'tgan zamonda...").
Hajmi: 3-4 ta ixcham xatboshi.
"""
    try:
        response = await client.aio.models.generate_content(
            model=config.GEMINI_MODEL,
            contents=prompt
        )
        return response.text.strip() if response.text else "Ertak hosil qilib bo'lmadi."
    except Exception as e:
        logger.error(f"Ertak generatsiyasi xatosi: {e}")
        return f"Ertak to'qishda xatolik yuz berdi: {e}"

async def generate_reminder_text(user_name: str, dori_nomi: str, vaqt: str, lang: str = "uz") -> str:
    """Dori ichish vaqtini eslatuvchi iliq va g'amxo'r xabar"""
    client = get_client()
    if not client:
        if lang == "ru":
            return f"Уважаемый(ая) {user_name or 'дорогой друг'}! На часах {vaqt}. Пожалуйста, не забудьте принять лекарство: '{dori_nomi}'. Крепкого здоровья! 💊"
        return f"Hurmatli {user_name or 'qadrdonimiz'}! Soat {vaqt} bo'ldi. '{dori_nomi}' dorisini qabul qilishni unutmang. Salomat bo'ling! 💊"

    if lang == "ru":
        prompt = f"""
Имя: {user_name or 'Уважаемый друг'}
Лекарство: {dori_nomi}
Время: {vaqt}

Напиши очень теплое, заботливое и короткое (2-3 предложения) напоминание на русском языке о приёме лекарства с пожеланием доброго здоровья и бодрости.
"""
    else:
        prompt = f"""
Foydalanuvchi ismi: {user_name or 'Hurmatli qadrdonimiz'}
Dori nomi: {dori_nomi}
Belgilangan vaqt: {vaqt}

Ushbu inson uchun mehrli, e'tiborli va dori ichishni eslatuvchi juda qisqa (2-3 jumla) tabassum ulashuvchi o'zbekcha xabar yoz.
Masalan: salomatlik tilab, bir qultum suv bilan dori ichish vaqti kelganini eslat.
"""
    try:
        response = await client.aio.models.generate_content(
            model=config.GEMINI_MODEL,
            contents=prompt
        )
        if response.text:
            return response.text.strip()
    except Exception as e:
        logger.error(f"Eslatma generatsiyasi xatosi: {e}")

    if lang == "ru":
        return f"Уважаемый(ая) {user_name}! Настало время принять лекарство '{dori_nomi}' ({vaqt}). Берегите себя! 💊"
    return f"Hurmatli {user_name or 'qadrdonimiz'}! Soat {vaqt} bo'ldi. '{dori_nomi}' dorisini o'z vaqtida qabul qilishni unutmang. Salomat bo'ling! 💊"

async def generate_quiz_question(yosh: int = 8) -> str:
    """Bolalar uchun qiziqarli savol/topishmoq generatsiyasi"""
    client = get_client()
    if not client:
        return "Quyosh nima uchun kunduzi charaqlaydi? Bilasanmi, do'stim?"

    prompt = f"""
{yosh} yoshli bola uchun o'zbek tilida bitta qiziqarli mantiqiy savol yoki topishmoq tuz.
Javob variantlari (A, B, C) bo'lsin va oxirida to'g'ri javob ko'rsatilsin (yashirin formatda).
"""
    try:
        response = await client.aio.models.generate_content(
            model=config.GEMINI_MODEL,
            contents=prompt
        )
        return response.text.strip() if response.text else "Bir uyda o'n aka-uka yashaydi, hammasining ismi bitta. U nima? (Topishmoq)"
    except Exception as e:
        return "Quyosh nima uchun kunduzi charaqlaydi? Bilasanmi, do'stim?"

async def process_voice_audio(
    audio_path: str, 
    user_type: str = "keksa", 
    history: Optional[List[Dict[str, str]]] = None,
    lang: str = "uz",
    appeal: str = ""
) -> Dict[str, str]:
    """Ovozli xabarni to'g'ridan-to'g'ri Gemini Multimodal orqali tushunish va javob berish (O'zbek / Rus)"""
    client = get_client()
    if not client:
        return {"transcribe": "", "response": "Gemini API kaliti kiritilmagan."}

    try:
        with open(audio_path, "rb") as f:
            audio_bytes = f.read()

        mime_type = "audio/ogg"
        if audio_path.endswith(".wav"):
            mime_type = "audio/wav"
        elif audio_path.endswith(".mp3"):
            mime_type = "audio/mp3"

        audio_part = types.Part.from_bytes(data=audio_bytes, mime_type=mime_type)

        murojaat = appeal if appeal else ("Hurmatli do'stim" if lang == "uz" else "Уважаемый собеседник")

        if lang == "ru":
            if user_type == "keksa":
                role_prompt = (
                    f"Ты — 'Hamroh Bot', заботливый, душевный и вежливый виртуальный собеседник для пожилых людей (бабушек и дедушек).\n"
                    f"Обращайся уважительно: '{murojaat}' (всегда на 'Вы').\n"
                    "Правила: никаких фамильярностей и пошлостей (не используй 'милый', 'дорогуша' без повода). Проявляй искреннее уважение к возрасту, желай здоровья, поддерживай интересные душевные беседы о жизни, книгах, культуре, природе."
                )
            else:
                role_prompt = (
                    "Ты — 'Hamroh Bot', веселый, добрый и умный друг для детей.\n"
                    "Общайся на русском языке, дружелюбно, на 'ты', поддерживай любознательность."
                )
            lang_desc = "русском языке"
        else:
            if user_type == "keksa":
                role_prompt = (
                    f"Sen nuroniy, keksa otaxon va onaxonlarimiz uchun mehribon, hurmatli virtual hamroh AI san.\n"
                    f"Hurmat bilan murojaat qil: '{murojaat}' (har doim 'Siz').\n"
                    "Qoidalar: O'zbek milliy odob-axloqiga mos gapir. Hech qanday erish, noo'rin ('jonim', 'asalim') so'zlarni ishlatma!"
                )
            else:
                role_prompt = (
                    "Sen bolajonlar uchun quvnoq, samimiy do'st va bilimdon ustoz AI san.\n"
                    "Do'stona ('sen', 'ofarin!') ohangda gapir."
                )
            lang_desc = "o'zbek tilida"

        prompt = (
            f"Vazifang:\n"
            f"1. Ushbu audio yozuvni tinglab ({lang_desc}), foydalanuvchi nima deganini aniq matnga o'gir (TRANSCRIBE).\n"
            f"2. {role_prompt}\n\n"
            f"Javobingni aniq quyidagi formatda ber:\n"
            f"TRANSCRIBE: <audio ichidagi matn>\n"
            f"RESPONSE: <foydalanuvchiga javobing>"
        )

        response = await client.aio.models.generate_content(
            model=config.GEMINI_MODEL,
            contents=[audio_part, prompt]
        )

        res_text = response.text.strip() if response.text else ""
        transcribe = ""
        bot_response = res_text

        if "TRANSCRIBE:" in res_text and "RESPONSE:" in res_text:
            parts = res_text.split("RESPONSE:")
            transcribe = parts[0].replace("TRANSCRIBE:", "").strip()
            bot_response = parts[1].strip()
        elif "TRANSCRIBE:" in res_text:
            transcribe = res_text.replace("TRANSCRIBE:", "").strip()

        return {"transcribe": transcribe, "response": bot_response}

    except Exception as e:
        logger.error(f"Gemini ovozli xabar tahlilida xatolik: {e}")
        return {"transcribe": "", "response": f"Ovozni qayta ishlashda xatolik yuz berdi: {e}"}

async def analyze_child_drawing(image_path: str, lang: str = "uz") -> str:
    """Bolalar chizgan rasmini Gemini Vision (AI) orqali mehr bilan tahlil qilish va maqtash"""
    client = get_client()
    if not client:
        return "Ofarin, juda chiroyli rasm chizibsan!" if lang == "uz" else "Молодец! Очень красивый рисунок!"

    try:
        with open(image_path, "rb") as f:
            image_bytes = f.read()

        mime = "image/jpeg"
        if image_path.lower().endswith(".png"):
            mime = "image/png"

        image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime)

        if lang == "ru":
            prompt = (
                "Ты — добрый, любящий и внимательный детский наставник. "
                "Посмотри на этот рисунок, который нарисовал ребёнок. "
                "1. С восхищением опиши, что именно изображено на рисунке (цвета, персонажи, детали, настроение). "
                "2. Похвали старания и фантазию ребёнка, поддержи его интерес к творчеству. "
                "3. Скажи доброе тёплое напутствие. "
                "Тон: радостный, вдохновляющий, простой и понятный для ребёнка (на 'ты'). Объем: 3-4 предложения."
            )
        else:
            prompt = (
                "Sen bolajonlarni juda sevadigan mehribon va quvnoq AI ustozi san. "
                "Bola chizgan ushbu rasmni diqqat bilan ko'rib chiq. "
                "1. Unda nimalar tasvirlanganini (ranglar, tabiat, qahramonlar, chiroyli detallar) qiziqish va hayrat bilan ta'riflab ber. "
                "2. Bolani mehnati va tasavvuri uchun juda chiroyli maqtovlar bilan qo'llab-quvvatla. "
                "3. Yana yangi rasmlar chizishga ruhlantir. "
                "Ohang: quvnoq, samimiy va mehrli (bolaga 'sen' deb gapir). Hajmi: 3-4 jumla."
            )

        response = await client.aio.models.generate_content(
            model=config.GEMINI_MODEL,
            contents=[image_part, prompt]
        )
        return response.text.strip() if response.text else ("Ajoyib rasm chizibsan, do'stim!" if lang == "uz" else "Замечательный рисунок!")
    except Exception as e:
        logger.error(f"Rasm tahlilida xatolik: {e}")
        return "Rasm juda chiroyli va yorqin chiqibdi! Barakalla!" if lang == "uz" else "Очень красивый и яркий рисунок! Молодец!"

async def generate_memory_question(lang: str = "uz", appeal: str = "") -> str:
    """Keksalar uchun xotirani mustahkamlovchi va ruhiy tetiklik beruvchi savol"""
    client = get_client()
    default_q_uz = "Bugun nonushtaga nima tanovul qildingiz? Kuningiz qanday boshlandi?"
    default_q_ru = "Что вы сегодня кушали на завтрак? С чего началось ваше утро?"
    if not client:
        return default_q_ru if lang == "ru" else default_q_uz

    murojaat = appeal if appeal else ("Hurmatli ota/ona" if lang == "uz" else "Уважаемый(ая)")
    try:
        if lang == "ru":
            prompt = (
                f"Обращение к пожилому человеку: '{murojaat}'. "
                "Придумай 1 добрый, теплый вопрос для тренировки памяти и приятной беседы. "
                "Темы: детские воспоминания, любимые семейные праздники, что было на обед, какая книга или фильм запомнились, "
                "какой был первый город, куда поехали. "
                "Вопрос должен вызывать улыбку, побуждать вспомнить приятное и ответить. Только сам вопрос (1-2 предложения)."
            )
        else:
            prompt = (
                f"Keksa nuroniy insonga murojaat: '{murojaat}'. "
                "Xotirani charxlovchi, aqliy faollikni oshiruvchi va dildan suhbatlashishga undovchi 1 ta juda samimiy savol tuz. "
                "Mavzular: yoshlikdagi unutilmas do'stlar, bugungi yoki kechagi shirin lahzalar, qaysi faslni xush ko'rishlari, sevimli taomlari. "
                "Faqat savolning o'zini yoz (1-2 jumla)."
            )

        res = await client.aio.models.generate_content(
            model=config.GEMINI_MODEL,
            contents=prompt
        )
        return res.text.strip() if res.text else (default_q_ru if lang == "ru" else default_q_uz)
    except Exception as e:
        logger.error(f"Xotira savoli generatsiyasida xato: {e}")
        return default_q_ru if lang == "ru" else default_q_uz

async def generate_reading_task(lang: str = "uz") -> Dict[str, str]:
    """Bolalar uchun kunlik kitobxonlik tavsiyasi va rag'bati"""
    client = get_client()
    default_res = {
        "task": "Bugun birgalikda sevimli ertak yoki kitobingdan 5 sahifa o'qiymiz! Qaysi kitobni tanlading?",
        "tip": "Har bir sahifani dona-dona, intonatsiya bilan o'qish nutqingni yanada chiroyli qiladi!"
    }
    if not client:
        return default_res

    try:
        if lang == "ru":
            prompt = (
                "Ты наставник по чтению для детей. Составь весёлый план на сегодня: прочитать 5 страниц интересной книги. "
                "Ответ строго в JSON:\n"
                "{\n"
                '  "task": "Задание на чтение...",\n'
                '  "tip": "Добрый совет о том, как полезно читать книги"\n'
                "}"
            )
        else:
            prompt = (
                "Bolalar uchun kitobxonlik ustozi sifatida kunlik 5 sahifa kitob o'qish vazifasini tuz. "
                "Javob JSON formatida bo'lsin:\n"
                "{\n"
                '  "task": "Vazifa matni...",\n'
                '  "tip": "Kitob o\'qishning foydasi haqida qisqa hikmat"\n'
                "}"
            )

        res = await client.aio.models.generate_content(
            model=config.GEMINI_MODEL,
            contents=prompt
        )
        raw = res.text.strip() if res.text else ""
        if "{" in raw and "}" in raw:
            import json
            j_str = raw[raw.find("{"):raw.rfind("}")+1]
            return json.loads(j_str)
    except Exception:
        pass
    return default_res

async def generate_animal_quiz(lang: str = "uz") -> Dict[str, str]:
    """Hayvonlar olami va ularning ovozlari haqida qiziqarli bolalar viktorinasi"""
    client = get_client()
    default_res = {
        "question": "Qaysi jonivor erta tongda 'Qu-qu-re-qu!' deb barchani uyqudan uyg'otadi?",
        "options": ["Xo'rozvoy", "Kuchukcha", "Mushukcha", "Bo'taloq"],
        "answer": "Xo'rozvoy",
        "fact": "Xo'rozlar quyosh chiqishini sezib, o'z oilasini uyg'otish uchun qichqiradilar! 🐓"
    }
    if not client:
        return default_res

    try:
        if lang == "ru":
            prompt = (
                "Придумай 1 интересную детскую викторину про животных и звуки, которые они издают (например: дельфин, сова, слон, собака, кот). "
                "Формат строго JSON:\n"
                "{\n"
                '  "question": "Текст вопроса...",\n'
                '  "options": ["Вариант1", "Вариант2", "Вариант3", "Вариант4"],\n'
                '  "answer": "Правильный вариант",\n'
                '  "fact": "Удивительный короткий факт об этом животном"\n'
                "}"
            )
        else:
            prompt = (
                "Bolalar uchun hayvonlar va ularning ovozlari/odatlariga oid 1 ta qiziqarli savol tuz. "
                "Format aniq JSON:\n"
                "{\n"
                '  "question": "Savol matni...",\n'
                '  "options": ["Variant1", "Variant2", "Variant3", "Variant4"],\n'
                '  "answer": "To\'g\'ri javob",\n'
                '  "fact": "Hayvon haqida hayratlanarli qisqa fakt"\n'
                "}"
            )

        res = await client.aio.models.generate_content(
            model=config.GEMINI_MODEL,
            contents=prompt
        )
        raw = res.text.strip() if res.text else ""
        if "{" in raw and "}" in raw:
            import json
            j_str = raw[raw.find("{"):raw.rfind("}")+1]
            return json.loads(j_str)
    except Exception:
        pass
    return default_res



