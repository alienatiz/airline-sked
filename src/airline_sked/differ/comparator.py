"""스케줄 비교 유틸리티.

두 스케줄 스냅샷을 비교하는 상세 로직.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class ScheduleComparison:
    """두 스케줄 간 비교 결과."""

    field: str
    old_value: Optional[str]
    new_value: Optional[str]
    is_changed: bool

    @property
    def description(self) -> str:
        if not self.is_changed:
            return f"{self.field}: 변경 없음"
        return f"{self.field}: {self.old_value} → {self.new_value}"


def compare_days_of_week(old: str, new: str) -> tuple[bool, str]:
    """운항요일 비교.

    Args:
        old: "1,3,5" 형태의 기존 운항요일
        new: "1,2,3,4,5" 형태의 신규 운항요일

    Returns:
        (변경 여부, 설명 문자열)
    """
    old_set = set(old.split(",")) if old else set()
    new_set = set(new.split(",")) if new else set()

    if old_set == new_set:
        return False, "변경 없음"

    added = new_set - old_set
    removed = old_set - new_set

    DAY_NAMES = {"1": "월", "2": "화", "3": "수", "4": "목", "5": "금", "6": "토", "7": "일"}

    parts = []
    if added:
        parts.append(f"추가: {','.join(DAY_NAMES.get(d, d) for d in sorted(added))}")
    if removed:
        parts.append(f"제거: {','.join(DAY_NAMES.get(d, d) for d in sorted(removed))}")

    return True, " / ".join(parts)


def calculate_weekly_frequency(days_of_week: str) -> int:
    """운항요일 문자열에서 주간 빈도 계산."""
    if not days_of_week:
        return 0
    return len([d for d in days_of_week.split(",") if d.strip()])
