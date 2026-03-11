"""스크래퍼 베이스 클래스."""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

import httpx

from airline_sked.config import settings

logger = logging.getLogger(__name__)


@dataclass
class ScrapedSchedule:
    """스크래핑된 단일 스케줄 항목."""

    airline_code: str
    flight_number: str
    origin: str
    destination: str
    departure_time: str          # HH:MM
    arrival_time: str            # HH:MM
    days_of_week: str            # "1,2,3,4,5,6,7" 형태
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    aircraft_type: Optional[str] = None
    frequency_weekly: Optional[int] = None
    has_schedule_details: bool = True

    @property
    def od_pair(self) -> str:
        return f"{self.origin}-{self.destination}"

    @property
    def route_key(self) -> str:
        return f"{self.airline_code}:{self.origin}-{self.destination}"


@dataclass
class ScrapeResult:
    """스크래핑 결과."""

    airline_code: str
    schedules: list[ScrapedSchedule] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    scraped_at: Optional[str] = None
    source: str = ""

    @property
    def success(self) -> bool:
        return len(self.schedules) > 0

    @property
    def route_count(self) -> int:
        return len({s.route_key for s in self.schedules})


class BaseScraper(ABC):
    """항공사 스크래퍼 기본 클래스.

    각 항공사별 스크래퍼는 이 클래스를 상속하여 구현합니다.
    """

    airline_code: str = ""
    airline_name: str = ""
    base_url: str = ""

    def __init__(self) -> None:
        self._client: Optional[httpx.AsyncClient] = None

    async def get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                headers={"User-Agent": settings.scrape_user_agent},
                timeout=30.0,
                follow_redirects=True,
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def __aenter__(self) -> BaseScraper:
        return self

    async def __aexit__(self, *args) -> None:
        await self.close()

    @abstractmethod
    async def scrape_schedules(
        self,
        origin: Optional[str] = None,
        destination: Optional[str] = None,
    ) -> ScrapeResult:
        """해당 항공사의 한-일 노선 스케줄을 수집.

        Args:
            origin: 특정 출발지로 필터 (None이면 전체)
            destination: 특정 도착지로 필터 (None이면 전체)

        Returns:
            ScrapeResult: 수집된 스케줄 목록
        """
        ...

    async def _delay(self) -> None:
        """요청 간 딜레이 (rate limiting)."""
        await asyncio.sleep(settings.scrape_request_delay_sec)

    def _log_info(self, msg: str) -> None:
        logger.info(f"[{self.airline_code}] {msg}")

    def _log_error(self, msg: str) -> None:
        logger.error(f"[{self.airline_code}] {msg}")
