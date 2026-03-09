"""DiffEngine 테스트."""

from __future__ import annotations

import pytest
from airline_sked.differ.events import EventType, Priority, RouteEvent


class TestRouteEvent:
    """RouteEvent 기본 동작 테스트."""

    def test_new_route_event(self):
        event = RouteEvent(
            event_type=EventType.NEW_ROUTE,
            airline_code="7C",
            origin="ICN",
            destination="KOJ",
            summary="제주항공 인천-가고시마 신규 취항",
        )
        assert event.priority == Priority.HIGH
        assert event.od_pair == "ICN-KOJ"
        assert event.emoji == "🆕"

    def test_freq_change_event(self):
        event = RouteEvent(
            event_type=EventType.FREQ_CHANGE,
            airline_code="KE",
            origin="ICN",
            destination="NRT",
            summary="주14회 → 주21회",
            detail={"old_frequency": 14, "new_frequency": 21},
        )
        assert event.priority == Priority.MEDIUM
        assert "ICN-NRT" in event.format_message()

    def test_suspended_event(self):
        event = RouteEvent(
            event_type=EventType.ROUTE_SUSPENDED,
            airline_code="RS",
            origin="ICN",
            destination="TAK",
            summary="에어서울 인천-다카마쓰 운휴",
        )
        assert event.priority == Priority.HIGH
        assert event.emoji == "🚫"


class TestComparator:
    """비교 유틸리티 테스트."""

    def test_compare_days_of_week(self):
        from airline_sked.differ.comparator import compare_days_of_week

        changed, desc = compare_days_of_week("1,3,5", "1,2,3,4,5")
        assert changed is True
        assert "추가" in desc

    def test_compare_days_no_change(self):
        from airline_sked.differ.comparator import compare_days_of_week

        changed, desc = compare_days_of_week("1,3,5", "1,3,5")
        assert changed is False

    def test_weekly_frequency(self):
        from airline_sked.differ.comparator import calculate_weekly_frequency

        assert calculate_weekly_frequency("1,2,3,4,5,6,7") == 7
        assert calculate_weekly_frequency("1,3,5") == 3
        assert calculate_weekly_frequency("") == 0
