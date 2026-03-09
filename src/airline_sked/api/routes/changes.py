"""변경 이벤트 API 라우터."""

from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Query
from sqlmodel import select

from airline_sked.database import get_session
from airline_sked.models import Change

router = APIRouter()


@router.get("/")
async def list_changes(
    event_type: Optional[str] = Query(None, description="이벤트 유형 필터"),
    priority: Optional[str] = Query(None, description="우선도 필터 (HIGH/MEDIUM/LOW)"),
    limit: int = Query(50, le=200),
):
    """변경 이벤트 목록 조회 (최신순)."""
    async with get_session() as session:
        stmt = select(Change).order_by(Change.detected_at.desc()).limit(limit)
        if event_type:
            stmt = stmt.where(Change.event_type == event_type.upper())
        if priority:
            stmt = stmt.where(Change.priority == priority.upper())

        result = await session.exec(stmt)
        return result.all()


@router.get("/stats")
async def change_stats():
    """변경 이벤트 통계."""
    async with get_session() as session:
        all_changes = (await session.exec(select(Change))).all()

        by_type: dict[str, int] = {}
        by_priority: dict[str, int] = {}
        for c in all_changes:
            by_type[c.event_type] = by_type.get(c.event_type, 0) + 1
            by_priority[c.priority] = by_priority.get(c.priority, 0) + 1

        return {
            "total": len(all_changes),
            "by_event_type": by_type,
            "by_priority": by_priority,
        }
