"""Scraper runner tests."""

from __future__ import annotations

from datetime import date

from airline_sked.differ import DiffEngine
from airline_sked.differ.events import EventType, RouteEvent
from airline_sked.scrapers.runner import _attach_route_ids


class _RouteStub:
    def __init__(self, route_id: int) -> None:
        self.id = route_id


def test_attach_route_ids_backfills_missing_ids():
    event = RouteEvent(
        event_type=EventType.NEW_ROUTE,
        airline_code="KE",
        origin="ICN",
        destination="NRT",
        summary="New route",
    )

    _attach_route_ids([event], {"KE:ICN-NRT": _RouteStub(12)})

    assert event.route_id == 12


def test_attach_route_ids_keeps_existing_ids():
    event = RouteEvent(
        event_type=EventType.FREQ_CHANGE,
        airline_code="KE",
        origin="ICN",
        destination="NRT",
        summary="Frequency changed",
        route_id=7,
    )

    _attach_route_ids([event], {"KE:ICN-NRT": _RouteStub(12)})

    assert event.route_id == 7


def test_infer_season_uses_expected_suffixes():
    assert DiffEngine._infer_season(date(2026, 3, 1)) == "2026S"
    assert DiffEngine._infer_season(date(2026, 11, 1)) == "2026W"
