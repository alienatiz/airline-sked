"""공항공사 운항정보 수집기.

인천공항공사, 한국공항공사 등의 공개 데이터에서
운항 스케줄 정보를 수집합니다.
"""

from __future__ import annotations

import logging
from typing import Optional
from airline_sked.scrapers.base import BaseScraper, ScrapeResult

logger = logging.getLogger(__name__)


class AirportKRScraper(BaseScraper):
    """공항공사 데이터 수집기 (보조 소스)."""

    airline_code = ""  # 특정 항공사가 아님
    airline_name = "공항공사"
    base_url = "https://www.airport.co.kr"

    async def scrape_schedules(
        self,
        origin: Optional[str] = None,
        destination: Optional[str] = None,
    ) -> ScrapeResult:
        """TODO: 공항공사 운항정보 수집 구현.

        가능한 데이터 소스:
        - 인천공항 운항정보 API (flights.airport.kr)
        - 한국공항공사 운항정보 (airport.co.kr)
        - 국토교통부 항공통계 (stat.molit.go.kr)
        """
        logger.info("공항공사 데이터 수집 (미구현)")
        return ScrapeResult(airline_code="AIRPORT_KR", source="airport.co.kr")
