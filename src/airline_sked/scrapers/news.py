"""항공 뉴스/커뮤니티 크롤러.

Aviation Wire, Traicy, 마일모아 등에서
한-일 노선 관련 뉴스를 수집합니다.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import httpx

from airline_sked.config import settings

logger = logging.getLogger(__name__)


@dataclass
class NewsItem:
    """수집된 뉴스 항목."""

    title: str
    url: str
    source: str
    summary: Optional[str] = None
    related_airline: Optional[str] = None
    related_route: Optional[str] = None
    published_at: Optional[datetime] = None


class NewsCrawler:
    """항공 뉴스 크롤러."""

    SOURCES = {
        "aviationwire": "https://www.aviationwire.jp",
        "traicy": "https://www.traicy.com",
        "milemoa": "https://www.milemoa.com",
    }

    KEYWORDS_KO = ["신규취항", "취항", "단항", "운휴", "증편", "감편", "노선", "인천", "김포", "부산"]
    KEYWORDS_JP = ["新規就航", "就航", "運休", "増便", "減便", "路線", "仁川", "金浦", "釜山"]

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

    async def crawl_all(self) -> list[NewsItem]:
        """모든 소스에서 뉴스 수집."""
        items: list[NewsItem] = []

        for source_name in self.SOURCES:
            try:
                source_items = await self._crawl_source(source_name)
                items.extend(source_items)
            except Exception as e:
                logger.error(f"뉴스 크롤링 실패 [{source_name}]: {e}")

        return items

    async def _crawl_source(self, source: str) -> list[NewsItem]:
        """TODO: 개별 소스 크롤링 구현."""
        logger.info(f"뉴스 크롤링 [{source}] (미구현)")
        return []
