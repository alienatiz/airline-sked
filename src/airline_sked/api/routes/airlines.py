"""항공사 API 라우터."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from airline_sked.database import get_session
from airline_sked.models import Airline

router = APIRouter()


@router.get("/")
async def list_airlines():
    """등록된 항공사 목록 조회."""
    async with get_session() as session:
        result = await session.exec(select(Airline))
        return result.all()


@router.get("/{iata_code}")
async def get_airline(iata_code: str):
    """항공사 상세 조회."""
    async with get_session() as session:
        airline = await session.get(Airline, iata_code.upper())
        if not airline:
            return {"error": "not found"}
        return airline
