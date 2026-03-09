"""변경 이벤트 및 구독 모델."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class Change(SQLModel, table=True):
    __tablename__ = "changes"

    id: Optional[int] = Field(default=None, primary_key=True)
    route_id: Optional[int] = Field(default=None, foreign_key="routes.id")
    event_type: str = Field(index=True, description="NEW_ROUTE, ROUTE_SUSPENDED, etc.")
    priority: str = Field(description="HIGH, MEDIUM, LOW")
    summary: str
    detail_json: Optional[str] = None
    detected_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    notified_at: Optional[datetime] = None
    source: Optional[str] = None


class News(SQLModel, table=True):
    __tablename__ = "news"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    url: Optional[str] = Field(default=None, unique=True)
    source: Optional[str] = None
    summary: Optional[str] = None
    related_airline: Optional[str] = None
    related_route: Optional[str] = None
    published_at: Optional[datetime] = None
    collected_at: datetime = Field(default_factory=datetime.utcnow)


class Subscription(SQLModel, table=True):
    __tablename__ = "subscriptions"

    id: Optional[int] = Field(default=None, primary_key=True)
    platform: str = Field(description="telegram, discord")
    chat_id: str
    filter_airlines: Optional[str] = None
    filter_origins: Optional[str] = None
    filter_destinations: Optional[str] = None
    filter_events: Optional[str] = None
    min_priority: str = Field(default="LOW")
    is_active: int = Field(default=1)
    created_at: datetime = Field(default_factory=datetime.utcnow)
