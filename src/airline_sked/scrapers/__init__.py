"""스크래퍼 패키지.

각 항공사별 스크래퍼를 등록하고 조회하는 레지스트리.
"""

from __future__ import annotations

from typing import Type
from airline_sked.scrapers.base import BaseScraper

_REGISTRY: dict[str, Type[BaseScraper]] = {}


def register_scraper(cls: Type[BaseScraper]) -> Type[BaseScraper]:
    """스크래퍼 클래스를 레지스트리에 등록하는 데코레이터."""
    if cls.airline_code:
        _REGISTRY[cls.airline_code] = cls
    return cls


def get_scraper(airline_code: str) -> BaseScraper | None:
    """항공사 코드로 스크래퍼 인스턴스를 반환."""
    cls = _REGISTRY.get(airline_code)
    return cls() if cls else None


def get_all_scrapers() -> list[BaseScraper]:
    """등록된 모든 스크래퍼 인스턴스를 반환."""
    return [cls() for cls in _REGISTRY.values()]


def list_registered() -> list[str]:
    """등록된 항공사 코드 목록을 반환."""
    return list(_REGISTRY.keys())


import airline_sked.scrapers.airlines
