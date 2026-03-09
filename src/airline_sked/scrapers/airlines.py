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

import re
from datetime import date, datetime, timedelta
from dataclasses import dataclass
from typing import Any
from typing import Optional

from airline_sked.config import settings
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
        schedule_url="https://flyasiana.com/I/US/EN/RetrieveFlightSchedule.do",
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

KE_ROUTE_PATTERN = re.compile(
    r"([A-Za-z][A-Za-z .,'/-]+?)\s+\(([A-Z]{3})\)\s*to\s*([A-Za-z][A-Za-z .,'/-]+?)\s+\(([A-Z]{3})\)"
)

OZ_CITY_BY_AIRPORT = {
    "ICN": "SEL",
    "GMP": "SEL",
    "PUS": "PUS",
    "CJU": "CJU",
    "TAE": "TAE",
    "CJJ": "CJJ",
    "MWX": "MWX",
    "NRT": "TYO",
    "HND": "TYO",
    "KIX": "OSA",
    "FUK": "FUK",
    "NGO": "NGO",
    "CTS": "SPK",
    "OKA": "OKA",
    "KOJ": "KOJ",
    "OIT": "OIT",
    "KMJ": "KMJ",
    "TAK": "TAK",
    "HIJ": "HIJ",
    "SDJ": "SDJ",
    "KMQ": "KMQ",
    "NGS": "NGS",
    "FSZ": "FSZ",
    "IBR": "IBR",
    "TOY": "TOY",
    "MYJ": "MYJ",
    "AOJ": "AOJ",
}


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
            if self.airline_code == "KE":
                await self._scrape_ke_live(result, origins, destinations)
            elif self.airline_code == "OZ":
                await self._scrape_oz_live(result, origins, destinations)
            elif self.config.scrape_method == "api":
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

    async def _scrape_ke_live(
        self, result: ScrapeResult, origins: list[str], destinations: list[str]
    ) -> None:
        """Korean Air route crawl via the public route/deals page."""
        routes = await self._load_ke_routes()
        allowed_origins = set(origins)
        allowed_destinations = set(destinations)
        seen: set[tuple[str, str]] = set()

        for origin, destination in routes:
            if origin not in allowed_origins or destination not in allowed_destinations:
                continue
            if (origin, destination) in seen:
                continue
            seen.add((origin, destination))
            result.schedules.append(
                ScrapedSchedule(
                    airline_code=self.airline_code,
                    flight_number=f"{self.airline_code}-{origin}-{destination}",
                    origin=origin,
                    destination=destination,
                    departure_time="00:00",
                    arrival_time="00:00",
                    days_of_week="1",
                    aircraft_type=None,
                    frequency_weekly=None,
                )
            )

        if not result.schedules:
            result.errors.append("No Korean Air KR->JP routes were extracted from the live page.")

    async def _scrape_oz_live(
        self, result: ScrapeResult, origins: list[str], destinations: list[str]
    ) -> None:
        """Asiana weekly schedule crawl via the official schedule page."""
        start_date = date.today() + timedelta(days=14)
        direct_segments: list[dict[str, Any]] = []

        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=settings.scrape_browser_headless)
            context = await browser.new_context(user_agent=settings.scrape_browser_user_agent)
            page = await context.new_page()
            await page.goto(
                self.config.schedule_url,
                wait_until="domcontentloaded",
                timeout=settings.scrape_browser_timeout_ms,
            )
            await page.wait_for_timeout(2500)

            for origin in origins:
                for destination in destinations:
                    if origin not in KR_ORIGINS or destination not in JP_DESTINATIONS:
                        continue

                    for offset in range(7):
                        target_date = start_date + timedelta(days=offset)
                        payload = _build_oz_search_payload(origin, destination, target_date)
                        response = await page.evaluate(
                            """
                            async ({ payload }) => {
                              const res = await fetch('RetrieveFlightScheduleSearch.do', {
                                method: 'POST',
                                headers: {
                                  'X-Requested-With': 'XMLHttpRequest',
                                  'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                                },
                                body: new URLSearchParams(payload).toString(),
                                credentials: 'include',
                              });
                              const text = await res.text();
                              try {
                                return { ok: res.ok, status: res.status, data: JSON.parse(text) };
                              } catch (error) {
                                return { ok: res.ok, status: res.status, text };
                              }
                            }
                            """,
                            {"payload": payload},
                        )

                        if not response.get("ok") or "data" not in response:
                            message = (
                                f"OZ schedule query failed for {origin}-{destination} "
                                f"on {target_date:%Y-%m-%d}: status={response.get('status')}"
                            )
                            if response.get("text"):
                                message += f" body={response['text'][:120]}"
                            result.errors.append(message)
                            await self._delay()
                            continue

                        direct_segments.extend(
                            _extract_oz_direct_segments(response["data"], origin, destination)
                        )
                        await self._delay()

            await context.close()
            await browser.close()

        result.schedules.extend(_build_oz_weekly_schedules(self.airline_code, direct_segments))
        if not result.schedules and not result.errors:
            result.errors.append("No Asiana schedules were returned from the live schedule page.")

    async def _load_ke_routes(self) -> list[tuple[str, str]]:
        """Load Korean Air route cards using a browser context."""
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=settings.scrape_browser_headless)
            context = await browser.new_context(user_agent=settings.scrape_browser_user_agent)
            page = await context.new_page()
            await page.goto(
                self.config.schedule_url,
                wait_until="domcontentloaded",
                timeout=settings.scrape_browser_timeout_ms,
            )
            await page.wait_for_timeout(3000)
            body_text = await page.locator("body").inner_text()
            await context.close()
            await browser.close()
        return _extract_ke_routes_from_text(body_text)


def _extract_ke_routes_from_text(text: str) -> list[tuple[str, str]]:
    """Extract KR->JP routes from the Korean Air deals page text."""
    matches = KE_ROUTE_PATTERN.findall(" ".join(text.replace("\xa0", " ").split()))
    routes: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for _, origin, _, destination in matches:
        route = (origin, destination)
        if origin not in KR_ORIGINS or destination not in JP_DESTINATIONS:
            continue
        if route in seen:
            continue
        seen.add(route)
        routes.append(route)
    return routes


def _build_oz_search_payload(origin: str, destination: str, target_date: date) -> dict[str, str]:
    """Build the payload used by Asiana's schedule AJAX call."""
    return {
        "departureArea": "",
        "departureAirport": origin,
        "departureCity": OZ_CITY_BY_AIRPORT.get(origin, origin),
        "departureMultiCity": "false",
        "arrivalArea": "",
        "arrivalAirport": destination,
        "arrivalMultiCity": "false",
        "departureDate": target_date.strftime("%Y%m%d"),
        "arrivalDate": "",
        "tripType": "OW",
    }


def _extract_oz_direct_segments(
    payload: dict[str, Any], expected_origin: str, expected_destination: str
) -> list[dict[str, Any]]:
    """Extract direct Asiana-operated segments from the schedule response."""
    time_table = payload.get("timeTable") or {}
    flight_rows = time_table.get("departureTimeTableAvailDataList") or []
    matches: list[dict[str, Any]] = []

    for row in flight_rows:
        paths = row.get("flightInfoDataList") or []
        if not paths or not isinstance(paths[0], list):
            continue
        segments = paths[0]
        if len(segments) != 1:
            continue
        segment = segments[0]
        if (segment.get("carrierCode") or "").upper() != "OZ":
            continue
        if segment.get("departureAirport") != expected_origin:
            continue
        if segment.get("arrivalAirport") != expected_destination:
            continue
        matches.append(segment)

    return matches


def _build_oz_weekly_schedules(
    airline_code: str, segments: list[dict[str, Any]]
) -> list[ScrapedSchedule]:
    """Collapse multiple day-specific Asiana results into weekly schedules."""
    grouped: dict[tuple[str, str, str, str, str, str | None], set[date]] = {}

    for segment in segments:
        departure_date = _parse_compact_date(segment.get("departureDate"))
        if departure_date is None:
            continue

        key = (
            segment.get("departureAirport", ""),
            segment.get("arrivalAirport", ""),
            _compact_to_hhmm(segment.get("departureDate")),
            _compact_to_hhmm(segment.get("arrivalDate")),
            f"{segment.get('carrierCode', airline_code)}{segment.get('flightNo', '')}",
            segment.get("aircraftType") or None,
        )
        grouped.setdefault(key, set()).add(departure_date)

    schedules: list[ScrapedSchedule] = []
    for key, dates in grouped.items():
        if not dates:
            continue
        origin, destination, departure_time, arrival_time, flight_number, aircraft_type = key
        ordered_dates = sorted(dates)
        days = sorted({d.isoweekday() for d in ordered_dates})
        schedules.append(
            ScrapedSchedule(
                airline_code=airline_code,
                flight_number=flight_number,
                origin=origin,
                destination=destination,
                departure_time=departure_time,
                arrival_time=arrival_time,
                days_of_week=",".join(str(day) for day in days),
                effective_from=ordered_dates[0],
                effective_to=ordered_dates[-1],
                aircraft_type=aircraft_type,
                frequency_weekly=len(days),
            )
        )

    schedules.sort(key=lambda s: (s.origin, s.destination, s.flight_number, s.departure_time))
    return schedules


def _parse_compact_date(value: Any) -> date | None:
    """Parse YYYYMMDD or YYYYMMDDHHMM values."""
    if not value:
        return None
    text = str(value)
    if len(text) < 8 or not text[:8].isdigit():
        return None
    return datetime.strptime(text[:8], "%Y%m%d").date()


def _compact_to_hhmm(value: Any) -> str:
    """Convert YYYYMMDDHHMM timestamps to HH:MM."""
    if not value:
        return "00:00"
    text = str(value)
    if len(text) >= 12 and text[8:12].isdigit():
        return f"{text[8:10]}:{text[10:12]}"
    return "00:00"

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
