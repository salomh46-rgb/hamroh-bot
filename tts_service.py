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

def clean_text_for_speech(text: str) -> str:
    """Matndan markdown belgilar va maxsus simvollarni tozalash"""
    clean = re.sub(r"[\*\_`#~]", "", text)
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean

async def text_to_speech_file(
    text: str, 
    output_path: str, 
    lang: str = "uz", 
    gender: str = "female", 
    rate: str = "-4%"
) -> Optional[str]:
    """
    Matnni o'zbek yoki rus tilidagi tabiiy neyron ovozga aylantirish.
    """
    try:
        clean_text = clean_text_for_speech(text)
        if not clean_text:
            return None

        voice = get_voice(lang=lang, gender=gender)

        communicate = edge_tts.Communicate(
            text=clean_text,
            voice=voice,
            rate=rate
        )
        await communicate.save(output_path)
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            return output_path
    except Exception as e:
        logger.error(f"TTS ovoz hosil qilishda xatolik ({lang}/{voice}): {e}")
    return None

