"""알림 발송 모듈."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Optional

from airline_sked.differ.events import RouteEvent, Priority

logger = logging.getLogger(__name__)


class BaseNotifier(ABC):
    """알림 발송 기본 클래스."""

    @abstractmethod
    async def send(self, event: RouteEvent, chat_id: Optional[str] = None) -> bool:
        """이벤트 알림을 발송."""
        ...

    @abstractmethod
    async def send_batch(self, events: list[RouteEvent], chat_id: Optional[str] = None) -> int:
        """여러 이벤트를 한 번에 발송. 발송 성공 건수 반환."""
        ...


class TelegramNotifier(BaseNotifier):
    """Telegram Bot 알림 발송."""

    def __init__(self, bot_token: str, default_chat_id: str = "") -> None:
        self.bot_token = bot_token
        self.default_chat_id = default_chat_id
        self._bot = None

    async def _get_bot(self):
        if self._bot is None:
            from telegram import Bot
            self._bot = Bot(token=self.bot_token)
        return self._bot

    async def send(self, event: RouteEvent, chat_id: Optional[str] = None) -> bool:
        target = chat_id or self.default_chat_id
        if not target:
            logger.error("Telegram chat_id가 설정되지 않았습니다.")
            return False

        try:
            bot = await self._get_bot()
            message = self._format_message(event)
            await bot.send_message(chat_id=target, text=message, parse_mode="HTML")
            logger.info(f"Telegram 알림 발송: {event.event_type.value} {event.od_pair}")
            return True
        except Exception as e:
            logger.error(f"Telegram 발송 실패: {e}")
            return False

    async def send_batch(self, events: list[RouteEvent], chat_id: Optional[str] = None) -> int:
        if not events:
            return 0

        high = [e for e in events if e.priority == Priority.HIGH]
        medium = [e for e in events if e.priority == Priority.MEDIUM]
        low = [e for e in events if e.priority == Priority.LOW]

        sent = 0
        for group_name, group in [("긴급", high), ("주요", medium), ("일반", low)]:
            if not group:
                continue
            message = self._format_batch_message(group_name, group)
            target = chat_id or self.default_chat_id
            try:
                bot = await self._get_bot()
                await bot.send_message(chat_id=target, text=message, parse_mode="HTML")
                sent += len(group)
            except Exception as e:
                logger.error(f"Telegram 배치 발송 실패 ({group_name}): {e}")

        return sent

    @staticmethod
    def _format_message(event: RouteEvent) -> str:
        return (
            f"{event.emoji} <b>{event.event_type.value}</b>\n"
            f"항공사: <code>{event.airline_code}</code>\n"
            f"노선: <code>{event.od_pair}</code>\n"
            f"───────────\n"
            f"{event.summary}"
        )

    @staticmethod
    def _format_batch_message(group_name: str, events: list[RouteEvent]) -> str:
        header = f"📢 <b>airline-sked 알림 ({group_name} {len(events)}건)</b>\n\n"
        body = "\n\n".join(
            f"{e.emoji} <b>{e.airline_code} {e.od_pair}</b>\n{e.summary}"
            for e in events
        )
        return header + body


class DiscordNotifier(BaseNotifier):
    """Discord Bot 알림 발송 (placeholder)."""

    def __init__(self, bot_token: str, channel_id: str = "") -> None:
        self.bot_token = bot_token
        self.channel_id = channel_id

    async def send(self, event: RouteEvent, chat_id: Optional[str] = None) -> bool:
        logger.warning("Discord notifier 미구현")
        return False

    async def send_batch(self, events: list[RouteEvent], chat_id: Optional[str] = None) -> int:
        logger.warning("Discord notifier 미구현")
        return 0
