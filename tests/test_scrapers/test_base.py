"""스크래퍼 기본 테스트."""

from __future__ import annotations

import pytest
from airline_sked.scrapers.base import ScrapedSchedule, ScrapeResult


class TestScrapedSchedule:
    def test_od_pair(self):
        sched = ScrapedSchedule(
            airline_code="KE",
            flight_number="KE701",
            origin="ICN",
            destination="NRT",
            departure_time="09:20",
            arrival_time="11:40",
            days_of_week="1,2,3,4,5,6,7",
        )
        assert sched.od_pair == "ICN-NRT"
        assert sched.route_key == "KE:ICN-NRT"


class TestScrapeResult:
    def test_empty_result(self):
        result = ScrapeResult(airline_code="KE")
        assert result.success is False
        assert result.route_count == 0

    def test_with_schedules(self):
        result = ScrapeResult(
            airline_code="KE",
            schedules=[
                ScrapedSchedule(
                    airline_code="KE", flight_number="KE701",
                    origin="ICN", destination="NRT",
                    departure_time="09:20", arrival_time="11:40",
                    days_of_week="1,2,3,4,5,6,7",
                ),
                ScrapedSchedule(
                    airline_code="KE", flight_number="KE703",
                    origin="ICN", destination="NRT",
                    departure_time="15:20", arrival_time="17:40",
                    days_of_week="1,2,3,4,5,6,7",
                ),
            ],
        )
        assert result.success is True
        assert result.route_count == 1  # same OD pair
