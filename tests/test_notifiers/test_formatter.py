"""알림 포매터 테스트."""

from __future__ import annotations

import pytest
from airline_sked.differ.events import EventType, RouteEvent
from airline_sked.notifiers.formatter import (
    format_telegram_html,
    format_discord_embed,
    format_plain_text,
    format_batch_summary,
)


class TestFormatter:
    def _make_event(self) -> RouteEvent:
        return RouteEvent(
            event_type=EventType.NEW_ROUTE,
            airline_code="7C",
            origin="ICN",
            destination="KOJ",
            summary="제주항공 인천-가고시마 신규 취항",
        )

    def test_telegram_format(self):
        msg = format_telegram_html(self._make_event())
        assert "<b>NEW_ROUTE</b>" in msg
        assert "7C" in msg
        assert "ICN-KOJ" in msg

    def test_discord_embed(self):
        embed = format_discord_embed(self._make_event())
        assert embed["title"] == "🆕 NEW_ROUTE"
        assert embed["color"] == 0xEF4444  # HIGH priority

    def test_plain_text(self):
        msg = format_plain_text(self._make_event())
        assert "[HIGH]" in msg

    def test_batch_summary(self):
        events = [self._make_event(), self._make_event()]
        summary = format_batch_summary(events)
        assert "총 2건" in summary
