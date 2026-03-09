"""항공사별 스크래퍼 정의.

14개 항공사 스크래퍼를 설정 기반으로 등록합니다.
각 항공사의 실제 스크래핑 로직은 _scrape_XXX 메서드로 분리하여
사이트 구조가 다른 경우에만 개별 구현합니다.

사용 예시:
    from airline_sked.scrapers import get_scraper
    scraper = get_scraper("KE")
    result = await scraper.scrape_schedules()
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from airline_sked.scrapers.base import BaseScraper, ScrapeResult, ScrapedSchedule
from airline_sked.scrapers import register_scraper

@dataclass
class AirlineConfig:
    """항공사 스크래핑 설정."""

    code: str
    name: str
    country: str
    base_url: str
    schedule_url: str
    scrape_method: str = "api"
    target_airports: list[str] | None = None


AIRLINE_CONFIGS: dict[str, AirlineConfig] = {
    "KE": AirlineConfig(
        code="KE", name="대한항공", country="KR",
        base_url="https://www.koreanair.com",
        schedule_url="https://www.koreanair.com/flights/en-kr/flights-from-korea",
        scrape_method="api",
    ),
    "OZ": AirlineConfig(
        code="OZ", name="아시아나항공", country="KR",
        base_url="https://flyasiana.com",
        schedule_url="https://flyasiana.com/C/US/EN/contents/book-online",
        scrape_method="api",
    ),
    "7C": AirlineConfig(
        code="7C", name="제주항공", country="KR",
        base_url="https://www.jejuair.net",
        schedule_url="https://www.jejuair.net/en/prepare/flight/viewScheduleInfo.do",
        scrape_method="html",
    ),
    "LJ": AirlineConfig(
        code="LJ", name="진에어", country="KR",
        base_url="https://www.jinair.com",
        schedule_url="https://www.jinair.com",
        scrape_method="html",
    ),
    "TW": AirlineConfig(
        code="TW", name="티웨이항공", country="KR",
        base_url="https://www.twayair.com",
        schedule_url="https://www.twayair.com/app/serviceInfo/flightSchedule",
        scrape_method="html",
    ),
    "RS": AirlineConfig(
        code="RS", name="에어서울", country="KR",
        base_url="https://flyairseoul.com/CW/en/main.do",
        schedule_url="https://flyairseoul.com/CW/en/booking_reservation.do",
        scrape_method="html",
    ),
    "BX": AirlineConfig(
        code="BX", name="에어부산", country="KR",
        base_url="https://en.airbusan.com",
        schedule_url="https://en.airbusan.com/content/individual/booking/reserve/booking",
        scrape_method="html",
    ),
    "ZE": AirlineConfig(
        code="ZE", name="이스타항공", country="KR",
        base_url="https://www.eastarjet.com",
        schedule_url="https://www.eastarjet.com/newstar/PGWIG00001",
        scrape_method="html",
    ),
    "NH": AirlineConfig(
        code="NH", name="ANA", country="JP",
        base_url="https://www.ana.co.jp",
        schedule_url="https://www.ana.co.jp/en/jp/book-plan/airinfo/timetable/international/",
        scrape_method="api",
        target_airports=["ICN", "GMP", "PUS", "CJU"],
    ),
    "JL": AirlineConfig(
        code="JL", name="JAL", country="JP",
        base_url="https://www.jal.co.jp",
        schedule_url="https://www.jal.co.jp/jp/en/inter/route/",
        scrape_method="api",
        target_airports=["ICN", "GMP", "PUS"],
    ),
    "MM": AirlineConfig(
        code="MM", name="피치항공", country="JP",
        base_url="https://www.flypeach.com/en",
        schedule_url="https://www.flypeach.com/en/lm/st/routemap",
        scrape_method="html",
        target_airports=["ICN", "GMP", "PUS", "CJU"],
    ),
    "GK": AirlineConfig(
        code="GK", name="젯스타재팬", country="JP",
        base_url="https://www.jetstar.com/jp/en/home",
        schedule_url="https://www.jetstar.com/jp/en/flights",
        scrape_method="html",
        target_airports=["ICN", "PUS"],
    ),
    "IJ": AirlineConfig(
        code="IJ", name="스프링재팬", country="JP",
        base_url="https://jp.ch.com",
        schedule_url="https://jp.ch.com",
        scrape_method="html",
        target_airports=["ICN", "PUS"],
    ),
    "BC": AirlineConfig(
        code="BC", name="스카이마크", country="JP",
        base_url="https://www.skymark.co.jp/en",
        schedule_url="https://www.skymark.co.jp/en/",
        scrape_method="html",
        target_airports=["ICN"],
    ),
}

KR_ORIGINS = ["ICN", "GMP", "PUS", "CJU", "TAE", "CJJ", "MWX"]

JP_DESTINATIONS = [
    "NRT", "HND", "KIX", "FUK", "NGO", "CTS", "OKA",
    "KOJ", "OIT", "KMJ", "TAK", "HIJ", "SDJ", "KMQ",
    "NGS", "FSZ", "IBR", "TOY", "MYJ", "AOJ",
]

class AirlineScraper(BaseScraper):
    """설정 기반 항공사 스크래퍼.

    AirlineConfig를 받아 해당 항공사의 스케줄을 수집합니다.
    스크래핑 방식(api/html/playwright)에 따라 내부적으로 분기합니다.
    """

    def __init__(self, config: AirlineConfig) -> None:
        super().__init__()
        self.config = config
        self.airline_code = config.code
        self.airline_name = config.name
        self.base_url = config.base_url

    async def scrape_schedules(
        self,
        origin: Optional[str] = None,
        destination: Optional[str] = None,
    ) -> ScrapeResult:
        """스케줄 수집 메인 로직.

        각 항공사 사이트 구조 분석 후 아래 메서드를 구현하세요:
        - _scrape_via_api()     : JSON API 응답 파싱
        - _scrape_via_html()    : HTML 페이지 파싱 (selectolax/bs4)
        - _scrape_via_playwright(): JS 렌더링 후 파싱
        """
        result = ScrapeResult(
            airline_code=self.airline_code,
            source=self.config.schedule_url,
        )

        self._log_info(f"스크래핑 시작 (method={self.config.scrape_method})")

        if self.config.country == "KR":
            origins = [origin] if origin else KR_ORIGINS
            destinations = [destination] if destination else JP_DESTINATIONS
        else:
            origins = [origin] if origin else JP_DESTINATIONS
            destinations = [destination] if destination else (
                self.config.target_airports or KR_ORIGINS
            )

        try:
            if self.config.scrape_method == "api":
                await self._scrape_via_api(result, origins, destinations)
            elif self.config.scrape_method == "html":
                await self._scrape_via_html(result, origins, destinations)
            elif self.config.scrape_method == "playwright":
                await self._scrape_via_playwright(result, origins, destinations)
        except Exception as e:
            self._log_error(f"스크래핑 실패: {e}")
            result.errors.append(str(e))

        self._log_info(
            f"스크래핑 완료: {len(result.schedules)} schedules, "
            f"{result.route_count} routes, {len(result.errors)} errors"
        )
        return result

    async def _scrape_via_api(
        self, result: ScrapeResult, origins: list[str], destinations: list[str]
    ) -> None:
        """JSON API 방식 스크래핑.

        TODO: 각 항공사 API 엔드포인트 분석 후 구현.

        구현 예시 (대한항공):
            client = await self.get_client()
            for orig in origins:
                for dest in destinations:
                    resp = await client.post(
                        self.config.schedule_url,
                        json={"origin": orig, "destination": dest},
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        for flight in data.get("flights", []):
                            result.schedules.append(ScrapedSchedule(...))
                    await self._delay()
        """
        self._log_info("API 스크래핑 (미구현 - 템플릿)")

    async def _scrape_via_html(
        self, result: ScrapeResult, origins: list[str], destinations: list[str]
    ) -> None:
        """HTML 파싱 방식 스크래핑.

        TODO: 각 항공사 페이지 구조 분석 후 구현.

        구현 예시:
            from selectolax.parser import HTMLParser
            client = await self.get_client()
            resp = await client.get(self.config.schedule_url)
            tree = HTMLParser(resp.text)
            for row in tree.css(".schedule-row"):
                result.schedules.append(ScrapedSchedule(...))
        """
        self._log_info("HTML 스크래핑 (미구현 - 템플릿)")

    async def _scrape_via_playwright(
        self, result: ScrapeResult, origins: list[str], destinations: list[str]
    ) -> None:
        """Playwright (JS 렌더링) 방식 스크래핑.

        TODO: JS 렌더링이 필요한 사이트용.

        구현 예시:
            from playwright.async_api import async_playwright
            async with async_playwright() as p:
                browser = await p.chromium.launch()
                page = await browser.new_page()
                await page.goto(self.config.schedule_url)
                await browser.close()
        """
        self._log_info("Playwright 스크래핑 (미구현 - 템플릿)")

def _create_and_register_all() -> None:
    """AIRLINE_CONFIGS의 모든 항공사에 대해 스크래퍼 클래스를 동적 생성 및 등록."""
    for code, config in AIRLINE_CONFIGS.items():
        def make_factory(cfg: AirlineConfig):
            class FactoryScraper(AirlineScraper):
                airline_code = cfg.code
                airline_name = cfg.name

                def __init__(self):
                    super().__init__(cfg)

            FactoryScraper.__name__ = f"{cfg.code}Scraper"
            return FactoryScraper

        register_scraper(make_factory(config))


_create_and_register_all()
