"""특근 조사 기본 기간·마감시각. 관리자가 생성 화면에서 수정할 수 있다."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta


def default_overtime_weekend(today: date | None = None) -> tuple[date, date]:
    """이번 주 토~일을 기본 조사 기간으로 쓴다. 일요일이면 이미 시작된 주말(토~일)을 반환한다."""
    today = today or date.today()
    weekday = today.weekday()
    if weekday == 6:
        saturday = today - timedelta(days=1)
    else:
        saturday = today + timedelta(days=(5 - weekday) % 7)
    return saturday, saturday + timedelta(days=1)


def default_deadline(saturday: date) -> datetime:
    """해당 주 목요일 11시. 실무 마감(목요일 오전 11시)을 기본값으로 둔다."""
    thursday = saturday - timedelta(days=2)
    return datetime.combine(thursday, time(11, 0))


def default_survey_title(period_start: date) -> str:
    return f"용인공장 {period_start.month}/{period_start.day} 특근인원"


def parse_deadline(value: str) -> datetime:
    return datetime.fromisoformat(value)


def is_past_deadline(deadline_at: str, now: datetime | None = None) -> bool:
    now = now or datetime.now()
    deadline = parse_deadline(deadline_at)
    if deadline.tzinfo is not None and now.tzinfo is None:
        now = now.replace(tzinfo=deadline.tzinfo)
    elif deadline.tzinfo is None and now.tzinfo is not None:
        deadline = deadline.replace(tzinfo=now.tzinfo)
    return now > deadline
