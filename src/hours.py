"""현행 엑셀 근무시간 값(`8H`)을 DB 숫자로 변환."""

from __future__ import annotations

import re


def parse_work_hours(value: object) -> float:
    if value is None:
        return 0.0
    if isinstance(value, bool):
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().upper().replace(" ", "")
    if not text:
        return 0.0
    text = text.replace("시간", "").replace("H", "")
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if not match:
        return 0.0
    return float(match.group(0))


def is_overtime_hours(value: object) -> bool:
    """취합 대상인지. 0·빈값·0H는 특근 미실시로 본다."""
    return parse_work_hours(value) > 0
