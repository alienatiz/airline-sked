"""항공사 및 공항 마스터 모델."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class Airline(SQLModel, table=True):
    __tablename__ = "airlines"

    iata_code: str = Field(primary_key=True, max_length=3, description="IATA 2-letter code")
    icao_code: Optional[str] = Field(default=None, max_length=4)
    name_ko: str
    name_en: str
    name_ja: Optional[str] = None
    country: str = Field(max_length=2, description="KR or JP")
    carrier_type: str = Field(max_length=3, description="FSC or LCC")
    website_url: Optional[str] = None
    schedule_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Airport(SQLModel, table=True):
    __tablename__ = "airports"

    iata_code: str = Field(primary_key=True, max_length=3)
    icao_code: Optional[str] = Field(default=None, max_length=4)
    name_ko: str
    name_en: str
    name_ja: Optional[str] = None
    city_ko: Optional[str] = None
    city_en: Optional[str] = None
    country: str = Field(max_length=2)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
