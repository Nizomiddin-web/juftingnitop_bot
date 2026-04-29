import time
from collections import defaultdict, deque
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from bot.config import is_admin


class RateLimitMiddleware(BaseMiddleware):
    """Limits flood per user — N events per W seconds."""

    def __init__(self, max_events: int = 30, window_sec: int = 60, alert_after: int = 31):
        self.max_events = max_events
        self.window_sec = window_sec
        self.alert_after = alert_after
        self._buckets: Dict[int, deque] = defaultdict(deque)
        self._alerted: Dict[int, float] = {}

    def _allow(self, user_id: int) -> bool:
        now = time.monotonic()
        bucket = self._buckets[user_id]
        cutoff = now - self.window_sec
        while bucket and bucket[0] < cutoff:
            bucket.popleft()
        if len(bucket) >= self.max_events:
            return False
        bucket.append(now)
        return True

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        if user and not is_admin(user.id) and not self._allow(user.id):
            now = time.monotonic()
            last = self._alerted.get(user.id, 0)
            if now - last > 30 and isinstance(event, (Message, CallbackQuery)):
                self._alerted[user.id] = now
                try:
                    if isinstance(event, Message):
                        await event.answer(
                            "⏱ Juda tez harakat qilyapsiz. Bir necha soniya kuting."
                        )
                    else:
                        await event.answer(
                            "⏱ Juda tez harakat qilyapsiz.",
                            show_alert=True,
                        )
                except Exception:
                    pass
            return None
        return await handler(event, data)
