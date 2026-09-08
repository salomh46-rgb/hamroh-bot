import os
import re
import logging
import edge_tts
from typing import Optional

logger = logging.getLogger(__name__)

# O'zbek tili neyron ovozlari
VOICE_UZ_FEMALE = "uz-UZ-MadinaNeural"
VOICE_UZ_MALE = "uz-UZ-SardorNeural"

# Rus tili neyron ovozlari
VOICE_RU_FEMALE = "ru-RU-SvetlanaNeural"
VOICE_RU_MALE = "ru-RU-DmitryNeural"

def get_voice(lang: str = "uz", gender: str = "female") -> str:
    """Til va jinsga qarab mos neyron ovozni tanlash"""
    if lang == "ru":
        return VOICE_RU_MALE if gender == "male" else VOICE_RU_FEMALE
    return VOICE_UZ_MALE if gender == "male" else VOICE_UZ_FEMALE

def clean_text_for_speech(text: str, lang: str = "uz") -> str:
    """Matndan markdown belgilar va maxsus simvollarni tozalash hamda o'zbek tili fonetikasini to'g'rilash"""
    if not text:
        return ""
    
    # 1. HTML teglarni tozalash
    text = re.sub(r"<[^>]+>", "", text)
    
    # 2. O'zbek tili uchun oʻ va gʻ harflarini rasmiy \u02bb modifikatoriga keltirish
    if lang == "uz":
        MOD = "\u02bb"
        # o va g dan keyingi barcha turdagi apostroflarni (', `, ’, ‘, ´, ʼ) \u02bb ga almashtirish va bo'shliqlarni yo'qotish
        text = re.sub(r"([oO])\s*['`\u2019\u2018\u00b4\u02bc\u02bb]\s*", r"\1" + MOD, text)
        text = re.sub(r"([gG])\s*['`\u2019\u2018\u00b4\u02bc\u02bb]\s*", r"\1" + MOD, text)
        # Boshqa so'z ichidagi tutuq belgilarini (masalan, ma'lumot, sun'iy, san'at) ham to'g'rilash
        text = re.sub(r"(?<=[a-zA-Z])\s*['`\u2019\u2018\u00b4\u02bc]\s*(?=[a-zA-Z])", MOD, text)

    # 3. Markdown belgilarni tozalash (lekin \u02bb modifikatori saqlanadi)
    clean = re.sub(r"[\*\_#~`]", "", text)
    
    # 4. Ortiqcha probellarni tozalash
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean

import io

async def text_to_speech_bytes(
    text: str, 
    lang: str = "uz", 
    gender: str = "female", 
    rate: str = "-4%"
) -> Optional[bytes]:
    """
    Matnni xotirada (in-memory io.BytesIO) neyron ovozga aylantirish.
    Diskka yozmaydi, juda tez va PermissionError lardan holi!
    """
    try:
        clean_text = clean_text_for_speech(text, lang=lang)
        if not clean_text:
            return None

        voice = get_voice(lang=lang, gender=gender)
        communicate = edge_tts.Communicate(
            text=clean_text,
            voice=voice,
            rate=rate
        )
        buffer = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                buffer.write(chunk["data"])
        
        val = buffer.getvalue()
        if val and len(val) > 0:
            return val
    except Exception as e:
        logger.error(f"TTS ovoz baytlarini olishda xatolik ({lang}): {e}")
    return None

async def text_to_speech_file(
    text: str, 
    output_path: str, 
    lang: str = "uz", 
    gender: str = "female", 
    rate: str = "-4%"
) -> Optional[str]:
    """
    Matnni diskdagi faylga aylantirish (orqaga moslik uchun saqlangan).
    """
    try:
        audio_bytes = await text_to_speech_bytes(text, lang=lang, gender=gender, rate=rate)
        if audio_bytes:
            with open(output_path, "wb") as f:
                f.write(audio_bytes)
            return output_path
    except Exception as e:
        logger.error(f"TTS fayl yozishda xato: {e}")
    return None


