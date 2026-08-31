"""네이버 달력식 빨간날. 일요일 + 국경일·공휴일·대체공휴일·선거일 (2026–2031)."""

from __future__ import annotations

from datetime import date, timedelta

# 설날(음력 1/1), 추석(음력 8/15), 부처님오신날(음력 4/8)
_LUNAR = {
    2026: ((2, 17), (9, 25), (5, 24)),
    2027: ((2, 7), (9, 15), (5, 13)),
    2028: ((1, 27), (10, 3), (5, 2)),
    2029: ((2, 13), (9, 22), (5, 20)),
    2030: ((2, 3), (9, 12), (5, 9)),
    2031: ((1, 23), (10, 1), (5, 28)),
}
_ELECTIONS = {
    2026: ((6, 3),),
    2027: ((3, 3),),
    2028: ((4, 12),),
}
_SOLAR = (
    (1, 1),
    (3, 1),
    (5, 1),
    (5, 5),
    (6, 6),
    (7, 17),
    (8, 15),
    (10, 3),
    (10, 9),
    (12, 25),
)
# 토·일과 겹치면 대체공휴일 (신정·현충일 제외)
_SAT_SUN_SUB = {(3, 1), (5, 1), (5, 5), (7, 17), (8, 15), (10, 3), (10, 9), (12, 25)}


def _closed(day: date, holidays: set[date]) -> bool:
    return day.weekday() == 6 or day in holidays


def _next_open(day: date, holidays: set[date]) -> date:
    cursor = day + timedelta(days=1)
    while _closed(cursor, holidays):
        cursor += timedelta(days=1)
    if cursor.weekday() == 5:
        cursor += timedelta(days=1)
        while _closed(cursor, holidays):
            cursor += timedelta(days=1)
    return cursor


def red_days_for_year(year: int) -> set[date]:
    holidays: set[date] = set()
    for month, day in _SOLAR:
        holidays.add(date(year, month, day))
    lunar = _LUNAR.get(year)
    seollal_days: list[date] = []
    chuseok_days: list[date] = []
    buddha: date | None = None
    if lunar:
        seollal = date(year, lunar[0][0], lunar[0][1])
        chuseok = date(year, lunar[1][0], lunar[1][1])
        buddha = date(year, lunar[2][0], lunar[2][1])
        seollal_days = [seollal + timedelta(days=delta) for delta in (-1, 0, 1)]
        chuseok_days = [chuseok + timedelta(days=delta) for delta in (-1, 0, 1)]
        holidays.update(seollal_days)
        holidays.update(chuseok_days)
        holidays.add(buddha)
    for month, day in _ELECTIONS.get(year, ()):
        holidays.add(date(year, month, day))

    named_other = {date(year, month, day) for month, day in _SOLAR}
    named_other.update(date(year, month, day) for month, day in _ELECTIONS.get(year, ()))
    if buddha is not None:
        named_other.add(buddha)

    triggers: list[date] = []
    for item in holidays:
        if (item.month, item.day) in _SAT_SUN_SUB and item.weekday() >= 5:
            triggers.append(item)
    if buddha is not None and buddha.weekday() >= 5:
        triggers.append(buddha)
    for cluster in (seollal_days, chuseok_days):
        if not cluster:
            continue
        if any(item.weekday() == 6 for item in cluster) or any(
            item in named_other for item in cluster
        ):
            triggers.append(max(cluster))

    extras: set[date] = set()
    for item in sorted(set(triggers)):
        extras.add(_next_open(item, holidays | extras))
    holidays.update(extras)
    return holidays


def is_red_day(day: date) -> bool:
    if day.weekday() == 6:
        return True
    if day.year < 2026 or day.year > 2031:
        return (day.month, day.day) in _SOLAR
    return day in red_days_for_year(day.year)
