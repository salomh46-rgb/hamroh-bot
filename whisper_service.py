import os
import sys
import logging
import asyncio
import subprocess
import aiohttp
from typing import Optional
import config

logger = logging.getLogger(__name__)

# FFmpeg yo'lini tekshirish va qo'shish
FFMPEG_PATHS = [
    r"C:\Users\salom\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.1-full_build\bin",
]
for p in FFMPEG_PATHS:
    if os.path.exists(p) and p not in os.environ.get("PATH", ""):
        os.environ["PATH"] = p + os.pathsep + os.environ.get("PATH", "")

_local_pipeline = None

def get_local_pipeline():
    global _local_pipeline
    if _local_pipeline is None:
        try:
            import torch
            from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline

            model_id = config.WHISPER_MODEL
            logger.info(f"Mahalliy Whisper model yuklanmoqda: {model_id}")
            
            device = "cuda:0" if torch.cuda.is_available() else "cpu"
            torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

            processor = AutoProcessor.from_pretrained(model_id, token=config.HF_TOKEN or None)
            model = AutoModelForSpeechSeq2Seq.from_pretrained(
                model_id,
                torch_dtype=torch_dtype,
                low_cpu_mem_usage=True,
                token=config.HF_TOKEN or None
            )
            model.to(device)

            _local_pipeline = pipeline(
                "automatic-speech-recognition",
                model=model,
                tokenizer=processor.tokenizer,
                feature_extractor=processor.feature_extractor,
                torch_dtype=torch_dtype,
                device=device,
                chunk_length_s=30,
            )
            logger.info("Mahalliy Whisper pipeline muvaffaqiyatli tayyorlandi.")
        except Exception as e:
            logger.error(f"Mahalliy Whisper pipeline yaratishda xato: {e}")
            _local_pipeline = None
    return _local_pipeline

async def query_hf_api(audio_path: str) -> Optional[str]:
    """Hugging Face Inference API orqali ovozni matnga aylantirish"""
    if not config.HF_TOKEN:
        logger.warning("HF_TOKEN ko'rsatilmagan, Hugging Face API chaqirilmadi.")
        return None

    api_url = f"https://api-inference.huggingface.co/models/{config.WHISPER_MODEL}"
    headers = {"Authorization": f"Bearer {config.HF_TOKEN}"}

    try:
        with open(audio_path, "rb") as f:
            data = f.read()

        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, headers=headers, data=data, timeout=60) as resp:
                if resp.status == 200:
                    res_json = await resp.json()
                    if isinstance(res_json, dict) and "text" in res_json:
                        return res_json["text"].strip()
                else:
                    err_body = await resp.text()
                    logger.error(f"HF API xatosi ({resp.status}): {err_body}")
    except Exception as e:
        logger.error(f"HF API so'rov xatosi: {e}")
    return None

def convert_audio_to_wav(input_path: str, output_path: str) -> bool:
    """Telegram ogg/opus faylini 16kHz wav formatiga aylantirish"""
    try:
        res = subprocess.run(
            ["ffmpeg", "-y", "-i", input_path, "-ar", "16000", "-ac", "1", output_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        if res.returncode == 0 and os.path.exists(output_path):
            return True
    except Exception:
        pass

    try:
        from pydub import AudioSegment
        sound = AudioSegment.from_file(input_path)
        sound = sound.set_frame_rate(16000).set_channels(1)
        sound.export(output_path, format="wav")
        return True
    except Exception as e:
        logger.error(f"Audio konvertatsiyasida xato: {e}")
        return False

async def audio_to_text(audio_path: str) -> str:
    """Ovozli fayldan o'zbekcha matnni olish"""
    wav_path = audio_path + ".wav"
    converted = convert_audio_to_wav(audio_path, wav_path)
    target_file = wav_path if converted else audio_path

    text_result = ""

    # 1. Hugging Face Inference API orqali
    if config.USE_HF_INFERENCE_API and config.HF_TOKEN:
        text_result = await query_hf_api(target_file)
        if text_result:
            if os.path.exists(wav_path):
                try:
                    os.remove(wav_path)
                except Exception:
                    pass
            return text_result

    # 2. Mahalliy Whisper orqali
    loop = asyncio.get_event_loop()
    pipe = await loop.run_in_executor(None, get_local_pipeline)

    if pipe:
        try:
            res = await loop.run_in_executor(
                None,
                lambda: pipe(target_file, generate_kwargs={"language": "uz", "task": "transcribe"})
            )
            text_result = res.get("text", "").strip()
        except Exception as e:
            logger.error(f"Mahalliy Whisper xatosi: {e}")

    if os.path.exists(wav_path):
        try:
            os.remove(wav_path)
        except Exception:
            pass

    return text_result
