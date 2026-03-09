"""알림 구독 API 라우터."""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Optional
from sqlmodel import select

from airline_sked.database import get_session
from airline_sked.models import Subscription

router = APIRouter()


class SubscriptionCreate(BaseModel):
    platform: str
    chat_id: str
    filter_airlines: Optional[str] = None
    filter_origins: Optional[str] = None
    filter_destinations: Optional[str] = None
    filter_events: Optional[str] = None
    min_priority: str = "LOW"


@router.get("/")
async def list_subscriptions(platform: Optional[str] = Query(None)):
    """구독 목록 조회."""
    async with get_session() as session:
        stmt = select(Subscription).where(Subscription.is_active == 1)
        if platform:
            stmt = stmt.where(Subscription.platform == platform)
        result = await session.exec(stmt)
        return result.all()


@router.post("/")
async def create_subscription(sub: SubscriptionCreate):
    """새 구독 등록."""
    async with get_session() as session:
        subscription = Subscription(**sub.model_dump())
        session.add(subscription)
        await session.flush()
        return subscription


@router.delete("/{sub_id}")
async def deactivate_subscription(sub_id: int):
    """구독 비활성화."""
    async with get_session() as session:
        sub = await session.get(Subscription, sub_id)
        if not sub:
            return {"error": "not found"}
        sub.is_active = 0
        return {"status": "deactivated", "id": sub_id}
