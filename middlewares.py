import time
import logging
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject

logger = logging.getLogger(__name__)

class AntiFloodMiddleware(BaseMiddleware):
    """
    Bolalar yoki foydalanuvchilar tugmalarni bir necha marta ketma-ket bosib yuborishidan (spam/flood)
    himoya qiluvchi aqlli middleware.
    """
    def __init__(self, limit_seconds: float = 2.0):
        self.limit_seconds = limit_seconds
        self.last_action: Dict[int, float] = {}
        self.warned_users: Dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user_id = None
        if isinstance(event, Message) and event.from_user:
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery) and event.from_user:
            user_id = event.from_user.id

        if not user_id:
            return await handler(event, data)

        now = time.time()
        last_time = self.last_action.get(user_id, 0)
        diff = now - last_time

        # Agar belgilangan vaqtdan (2 sekund) tezroq bosilgan bo'lsa
        if diff < self.limit_seconds:
            # Agar 3 soniya ichida ogohlantirilmagan bo'lsa, bitta yumshoq ogohlantirish beramiz
            last_warn = self.warned_users.get(user_id, 0)
            if now - last_warn > 3.0:
                self.warned_users[user_id] = now
                if isinstance(event, Message):
                    await event.answer("⏳ **Biroz kuting, do'stim!** Hozirgi topshiriq tayyorlanmoqda... 😊")
                elif isinstance(event, CallbackQuery):
                    await event.answer("⏳ Iltimos, biroz kuting...", show_alert=False)
            
            # Xabarni qayta ishlamaymiz (bloklaymiz)
            logger.info(f"AntiFlood: user_id={user_id} tez-tez bosganligi sababli so'rov bekor qilindi.")
            return

        self.last_action[user_id] = now
        return await handler(event, data)
