"""변경 이벤트 타입 정의."""

from __future__ import annotations

from enum import Enum
from dataclasses import dataclass
from typing import Any, Optional


class EventType(str, Enum):
    NEW_ROUTE = "NEW_ROUTE"
    ROUTE_SUSPENDED = "ROUTE_SUSPENDED"
    ROUTE_RESUMED = "ROUTE_RESUMED"
    FREQ_CHANGE = "FREQ_CHANGE"
    TIME_CHANGE = "TIME_CHANGE"
    AIRCRAFT_CHANGE = "AIRCRAFT_CHANGE"
    SEASONAL_START = "SEASONAL_START"
    SEASONAL_END = "SEASONAL_END"


class Priority(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


EVENT_PRIORITY: dict[EventType, Priority] = {
    EventType.NEW_ROUTE: Priority.HIGH,
    EventType.ROUTE_SUSPENDED: Priority.HIGH,
    EventType.ROUTE_RESUMED: Priority.MEDIUM,
    EventType.FREQ_CHANGE: Priority.MEDIUM,
    EventType.TIME_CHANGE: Priority.LOW,
    EventType.AIRCRAFT_CHANGE: Priority.LOW,
    EventType.SEASONAL_START: Priority.MEDIUM,
    EventType.SEASONAL_END: Priority.LOW,
}

EVENT_EMOJI: dict[EventType, str] = {
    EventType.NEW_ROUTE: "🆕",
    EventType.ROUTE_SUSPENDED: "🚫",
    EventType.ROUTE_RESUMED: "✅",
    EventType.FREQ_CHANGE: "🔄",
    EventType.TIME_CHANGE: "⏰",
    EventType.AIRCRAFT_CHANGE: "✈️",
    EventType.SEASONAL_START: "🌸",
    EventType.SEASONAL_END: "🍂",
}


@dataclass
class RouteEvent:
    """감지된 변경 이벤트."""

    event_type: EventType
    airline_code: str
    origin: str
    destination: str
    summary: str
    detail: Optional[dict[str, Any]] = None
    route_id: Optional[int] = None

    @property
    def priority(self) -> Priority:
        return EVENT_PRIORITY[self.event_type]

    @property
    def emoji(self) -> str:
        return EVENT_EMOJI[self.event_type]

    @property
    def od_pair(self) -> str:
        return f"{self.origin}-{self.destination}"

    def format_message(self) -> str:
        """알림 메시지 포매팅."""
        return (
            f"{self.emoji} [{self.priority.value}] {self.event_type.value}\n"
            f"항공사: {self.airline_code}\n"
            f"노선: {self.od_pair}\n"
            f"{self.summary}"
        )
