"""데이터베이스 연결 및 세션 관리."""

from __future__ import annotations

from sqlmodel import SQLModel, create_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlalchemy.orm import sessionmaker
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from airline_sked.config import settings


engine: AsyncEngine = create_async_engine(
    settings.database_url,
    echo=False,
    future=True,
)

async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db() -> None:
    """DB 테이블 생성 (개발용, 프로덕션에서는 alembic 사용)."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """비동기 DB 세션 컨텍스트 매니저."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
