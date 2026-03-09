"""Helpers to execute scraper runs end-to-end."""

from __future__ import annotations

from dataclasses import dataclass, field

from airline_sked.database import get_session
from airline_sked.differ import DiffEngine
from airline_sked.differ.events import RouteEvent
from airline_sked.scrapers import get_all_scrapers, get_scraper
from airline_sked.scrapers.base import BaseScraper, ScrapeResult


@dataclass
class ScrapeRunSummary:
    """Summary of one scraper execution."""

    airline_code: str
    success: bool
    route_count: int = 0
    schedule_count: int = 0
    change_count: int = 0
    saved_schedule_count: int = 0
    errors: list[str] = field(default_factory=list)


async def run_scraper(
    scraper: BaseScraper,
    origin: str | None = None,
    destination: str | None = None,
) -> tuple[ScrapeResult, list[RouteEvent], ScrapeRunSummary]:
    """Run a scraper, persist snapshots, and compute diffs."""
    async with scraper:
        result = await scraper.scrape_schedules(origin=origin, destination=destination)

    if not result.success:
        return result, [], ScrapeRunSummary(
            airline_code=scraper.airline_code,
            success=False,
            errors=result.errors,
        )

    async with get_session() as session:
        engine = DiffEngine(session)
        events = await engine.process_scrape_result(result)
        route_map = await engine.update_routes(result)
        _attach_route_ids(events, route_map)
        saved_schedules = await engine.save_schedules(result, route_map)
        if events:
            await engine.save_events(events)

    summary = ScrapeRunSummary(
        airline_code=scraper.airline_code,
        success=True,
        route_count=result.route_count,
        schedule_count=len(result.schedules),
        change_count=len(events),
        saved_schedule_count=len(saved_schedules),
        errors=result.errors,
    )
    return result, events, summary


async def run_scraper_by_code(
    airline_code: str,
    origin: str | None = None,
    destination: str | None = None,
) -> tuple[ScrapeResult, list[RouteEvent], ScrapeRunSummary]:
    """Resolve and run one scraper by airline code."""
    scraper = get_scraper(airline_code.upper())
    if scraper is None:
        raise ValueError(f"Unknown airline scraper: {airline_code}")
    return await run_scraper(scraper, origin=origin, destination=destination)


async def run_all_scrapers() -> list[ScrapeRunSummary]:
    """Run all registered scrapers."""
    summaries: list[ScrapeRunSummary] = []
    for scraper in get_all_scrapers():
        _, _, summary = await run_scraper(scraper)
        summaries.append(summary)
    return summaries


def _attach_route_ids(events: list[RouteEvent], route_map: dict[str, object]) -> None:
    """Backfill route IDs after route upsert so change events can be persisted."""
    for event in events:
        if event.route_id is not None:
            continue
        route = route_map.get(f"{event.airline_code}:{event.origin}-{event.destination}")
        route_id = getattr(route, "id", None)
        if route_id is not None:
            event.route_id = route_id
