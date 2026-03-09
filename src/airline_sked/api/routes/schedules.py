"""스케줄 API 라우터."""

from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Query
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from airline_sked.database import get_session
from airline_sked.models import Route, Schedule

router = APIRouter()


@router.get("/routes")
async def list_routes(
    airline: Optional[str] = Query(None, description="항공사 코드 필터"),
    origin: Optional[str] = Query(None, description="출발지 필터"),
    destination: Optional[str] = Query(None, description="도착지 필터"),
    status: Optional[str] = Query(None, description="상태 필터 (ACTIVE/SUSPENDED/SEASONAL)"),
):
    """노선 목록 조회."""
    async with get_session() as session:
        stmt = select(Route)
        if airline:
            stmt = stmt.where(Route.airline_code == airline.upper())
        if origin:
            stmt = stmt.where(Route.origin == origin.upper())
        if destination:
            stmt = stmt.where(Route.destination == destination.upper())
        if status:
            stmt = stmt.where(Route.status == status.upper())

        result = await session.exec(stmt)
        return result.all()


@router.get("/routes/{route_id}/schedules")
async def get_route_schedules(route_id: int, limit: int = Query(10, le=100)):
    """특정 노선의 스케줄 이력 조회."""
    async with get_session() as session:
        stmt = (
            select(Schedule)
            .where(Schedule.route_id == route_id)
            .order_by(Schedule.collected_at.desc())
            .limit(limit)
        )
        result = await session.exec(stmt)
        return result.all()
