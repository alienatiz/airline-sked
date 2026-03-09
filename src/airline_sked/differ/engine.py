"""변경 감지 엔진."""

from __future__ import annotations

import json
import logging
from datetime import date, datetime
from typing import Optional

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from airline_sked.models import Change, Route, Schedule
from airline_sked.scrapers.base import ScrapeResult, ScrapedSchedule
from airline_sked.differ.events import EventType, RouteEvent

logger = logging.getLogger(__name__)


class DiffEngine:
    """스케줄 변경 감지 엔진.

    새로 수집된 스케줄과 DB에 저장된 기존 스케줄을 비교하여
    변경 이벤트를 생성합니다.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def process_scrape_result(self, result: ScrapeResult) -> list[RouteEvent]:
        """스크래핑 결과를 기존 DB와 비교하여 변경 이벤트를 반환."""
        if not result.success:
            logger.warning(f"[{result.airline_code}] 스크래핑 결과가 비어있습니다.")
            return []

        events: list[RouteEvent] = []
        scraped_routes: dict[str, list[ScrapedSchedule]] = {}
        for sched in result.schedules:
            scraped_routes.setdefault(sched.route_key, []).append(sched)

        stmt = select(Route).where(
            Route.airline_code == result.airline_code,
            Route.status == "ACTIVE",
        )
        db_routes = (await self.session.exec(stmt)).all()
        db_route_keys = {r.route_key for r in db_routes}

        for route_key, schedules in scraped_routes.items():
            if route_key not in db_route_keys:
                sample = schedules[0]
                events.append(RouteEvent(
                    event_type=EventType.NEW_ROUTE,
                    airline_code=result.airline_code,
                    origin=sample.origin,
                    destination=sample.destination,
                    summary=(
                        f"{result.airline_code} {sample.od_pair} 신규 취항 감지! "
                        f"편명: {sample.flight_number}, "
                        f"운항요일: {sample.days_of_week}"
                    ),
                    detail={
                        "flight_number": sample.flight_number,
                        "departure_time": sample.departure_time,
                        "arrival_time": sample.arrival_time,
                        "days_of_week": sample.days_of_week,
                        "aircraft_type": sample.aircraft_type,
                    },
                ))

        scraped_route_keys = set(scraped_routes.keys())
        for db_route in db_routes:
            if db_route.route_key not in scraped_route_keys:
                events.append(RouteEvent(
                    event_type=EventType.ROUTE_SUSPENDED,
                    airline_code=result.airline_code,
                    origin=db_route.origin,
                    destination=db_route.destination,
                    summary=f"{result.airline_code} {db_route.od_pair} 단항/운휴 감지!",
                    route_id=db_route.id,
                ))

        for db_route in db_routes:
            if db_route.route_key in scraped_route_keys:
                route_events = await self._compare_schedules(
                    db_route, scraped_routes[db_route.route_key]
                )
                events.extend(route_events)

        return events

    async def _compare_schedules(
        self, route: Route, new_schedules: list[ScrapedSchedule]
    ) -> list[RouteEvent]:
        """기존 노선의 스케줄 상세 비교."""
        events: list[RouteEvent] = []

        stmt = (
            select(Schedule)
            .where(Schedule.route_id == route.id)
            .order_by(Schedule.collected_at.desc())
            .limit(10)
        )
        old_schedules = (await self.session.exec(stmt)).all()

        if not old_schedules:
            return events

        old_freq = old_schedules[0].frequency_weekly
        new_freq = new_schedules[0].frequency_weekly
        if old_freq and new_freq and old_freq != new_freq:
            events.append(RouteEvent(
                event_type=EventType.FREQ_CHANGE,
                airline_code=route.airline_code,
                origin=route.origin,
                destination=route.destination,
                summary=f"운항 빈도 변경: 주{old_freq}회 → 주{new_freq}회",
                detail={"old_frequency": old_freq, "new_frequency": new_freq},
                route_id=route.id,
            ))

        old_dep = old_schedules[0].departure_time
        new_dep = new_schedules[0].departure_time
        if old_dep and new_dep and old_dep != new_dep:
            events.append(RouteEvent(
                event_type=EventType.TIME_CHANGE,
                airline_code=route.airline_code,
                origin=route.origin,
                destination=route.destination,
                summary=f"출발시간 변경: {old_dep} → {new_dep}",
                detail={"old_departure": old_dep, "new_departure": new_dep},
                route_id=route.id,
            ))

        old_ac = old_schedules[0].aircraft_type
        new_ac = new_schedules[0].aircraft_type
        if old_ac and new_ac and old_ac != new_ac:
            events.append(RouteEvent(
                event_type=EventType.AIRCRAFT_CHANGE,
                airline_code=route.airline_code,
                origin=route.origin,
                destination=route.destination,
                summary=f"기재 변경: {old_ac} → {new_ac}",
                detail={"old_aircraft": old_ac, "new_aircraft": new_ac},
                route_id=route.id,
            ))

        return events

    async def save_events(self, events: list[RouteEvent]) -> list[Change]:
        """감지된 이벤트를 DB에 저장."""
        changes = []
        for event in events:
            change = Change(
                route_id=event.route_id,
                event_type=event.event_type.value,
                priority=event.priority.value,
                summary=event.summary,
                detail_json=json.dumps(event.detail, ensure_ascii=False) if event.detail else None,
                detected_at=datetime.utcnow(),
            )
            self.session.add(change)
            changes.append(change)

        await self.session.flush()
        return changes

    async def update_routes(self, result: ScrapeResult) -> dict[str, Route]:
        """스크래핑 결과를 기반으로 routes 테이블 업데이트."""
        today = date.today()
        route_map: dict[str, Route] = {}

        for sched in result.schedules:
            stmt = select(Route).where(
                Route.airline_code == sched.airline_code,
                Route.origin == sched.origin,
                Route.destination == sched.destination,
            )
            route = (await self.session.exec(stmt)).first()

            if route is None:
                route = Route(
                    airline_code=sched.airline_code,
                    origin=sched.origin,
                    destination=sched.destination,
                    status="ACTIVE",
                    first_seen=today,
                    last_seen=today,
                )
                self.session.add(route)
            else:
                route.last_seen = today
                route.status = "ACTIVE"
                route.updated_at = datetime.utcnow()

            route_map[sched.route_key] = route

        await self.session.flush()
        return route_map

    async def save_schedules(
        self, result: ScrapeResult, route_map: Optional[dict[str, Route]] = None
    ) -> list[Schedule]:
        """스크래핑 결과를 schedules 테이블에 스냅샷으로 저장."""
        schedules: list[Schedule] = []
        resolved_routes = route_map or {}

        for scraped in result.schedules:
            route = resolved_routes.get(scraped.route_key)
            if route is None:
                stmt = select(Route).where(
                    Route.airline_code == scraped.airline_code,
                    Route.origin == scraped.origin,
                    Route.destination == scraped.destination,
                )
                route = (await self.session.exec(stmt)).first()

            if route is None or route.id is None:
                logger.warning("Route not found for scraped schedule %s", scraped.route_key)
                continue

            schedule = Schedule(
                route_id=route.id,
                season=self._infer_season(scraped.effective_from or date.today()),
                effective_from=scraped.effective_from,
                effective_to=scraped.effective_to,
                days_of_week=scraped.days_of_week,
                departure_time=scraped.departure_time,
                arrival_time=scraped.arrival_time,
                flight_number=scraped.flight_number,
                aircraft_type=scraped.aircraft_type,
                frequency_weekly=scraped.frequency_weekly,
                source=result.source,
            )
            self.session.add(schedule)
            schedules.append(schedule)

        await self.session.flush()
        return schedules

    @staticmethod
    def _infer_season(target_date: date) -> str:
        """날짜를 기준으로 단순 IATA summer/winter 표기로 변환."""
        suffix = "S" if 3 <= target_date.month <= 10 else "W"
        return f"{target_date.year}{suffix}"
