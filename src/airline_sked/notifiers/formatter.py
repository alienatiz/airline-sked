"""알림 메시지 포매팅 유틸리티."""

from __future__ import annotations

from airline_sked.differ.events import RouteEvent, Priority


def format_telegram_html(event: RouteEvent) -> str:
    """Telegram HTML 형식 메시지."""
    return (
        f"{event.emoji} <b>{event.event_type.value}</b>\n"
        f"항공사: <code>{event.airline_code}</code>\n"
        f"노선: <code>{event.od_pair}</code>\n"
        f"우선도: {event.priority.value}\n"
        f"───────────\n"
        f"{event.summary}"
    )


def format_discord_embed(event: RouteEvent) -> dict:
    """Discord embed 형식 데이터."""
    PRIORITY_COLORS = {
        Priority.HIGH: 0xEF4444,
        Priority.MEDIUM: 0xF59E0B,
        Priority.LOW: 0x06B6D4,
    }

    return {
        "title": f"{event.emoji} {event.event_type.value}",
        "description": event.summary,
        "color": PRIORITY_COLORS.get(event.priority, 0x6B7280),
        "fields": [
            {"name": "항공사", "value": event.airline_code, "inline": True},
            {"name": "노선", "value": event.od_pair, "inline": True},
            {"name": "우선도", "value": event.priority.value, "inline": True},
        ],
    }


def format_plain_text(event: RouteEvent) -> str:
    """평문 메시지."""
    return (
        f"[{event.priority.value}] {event.emoji} {event.event_type.value}\n"
        f"항공사: {event.airline_code} | 노선: {event.od_pair}\n"
        f"{event.summary}"
    )


def format_batch_summary(events: list[RouteEvent]) -> str:
    """여러 이벤트의 요약 메시지."""
    high = sum(1 for e in events if e.priority == Priority.HIGH)
    medium = sum(1 for e in events if e.priority == Priority.MEDIUM)
    low = sum(1 for e in events if e.priority == Priority.LOW)

    return (
        f"📢 airline-sked 알림: 총 {len(events)}건 감지\n"
        f"🔴 긴급 {high}건 | 🟡 주요 {medium}건 | 🔵 일반 {low}건"
    )
