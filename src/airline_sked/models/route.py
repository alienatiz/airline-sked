"""노선 및 스케줄 모델."""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class Route(SQLModel, table=True):
    __tablename__ = "routes"

    id: Optional[int] = Field(default=None, primary_key=True)
    airline_code: str = Field(foreign_key="airlines.iata_code", index=True)
    origin: str = Field(foreign_key="airports.iata_code")
    destination: str = Field(foreign_key="airports.iata_code")
    status: str = Field(default="ACTIVE", description="ACTIVE, SUSPENDED, SEASONAL")
    first_seen: Optional[date] = None
    last_seen: Optional[date] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        table_args = {"sqlite_autoincrement": True}

    @property
    def od_pair(self) -> str:
        return f"{self.origin}-{self.destination}"

    @property
    def route_key(self) -> str:
        return f"{self.airline_code}:{self.origin}-{self.destination}"


class Schedule(SQLModel, table=True):
    __tablename__ = "schedules"

    id: Optional[int] = Field(default=None, primary_key=True)
    route_id: int = Field(foreign_key="routes.id", index=True)
    season: Optional[str] = None
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    days_of_week: Optional[str] = None
    departure_time: Optional[str] = None
    arrival_time: Optional[str] = None
    flight_number: Optional[str] = None
    aircraft_type: Optional[str] = None
    frequency_weekly: Optional[int] = None
    collected_at: datetime = Field(default_factory=datetime.utcnow)
    source: Optional[str] = None
