"""제출 현황·특근 취합·이상치 검토. 근무시간 0은 취합에서 제외한다."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.config import SUBMITTING_TEAMS
from src.hours import is_overtime_hours, parse_work_hours


@dataclass
class Anomaly:
    level: str
    kind: str
    message: str
    work_date: str | None = None
    name: str | None = None
    team: str | None = None


@dataclass
class DateTotal:
    work_date: str
    headcount: int
    meal_sum: float
    hours_sum: float


@dataclass
class TeamStatus:
    team: str
    is_submitted: bool
    submitted_at: str | None
    saved_count: int
    overtime_count: int
    label: str


@dataclass
class Aggregation:
    overtime: list[dict[str, Any]] = field(default_factory=list)
    excluded_zero: int = 0
    date_totals: list[DateTotal] = field(default_factory=list)
    team_status: list[TeamStatus] = field(default_factory=list)
    anomalies: list[Anomaly] = field(default_factory=list)
    submitted_count: int = 0
    team_count: int = 0


def collect_overtime(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """근무시간이 0·빈값·0H인 인원을 빼고, 출처팀 컬럼을 붙인다."""
    collected: list[dict[str, Any]] = []
    for item in entries:
        hours = parse_work_hours(item.get("work_hours", 0))
        if not is_overtime_hours(hours):
            continue
        row = dict(item)
        row["work_hours"] = hours
        row["source_team"] = str(item.get("team") or "")
        collected.append(row)
    collected.sort(
        key=lambda item: (
            str(item.get("work_date") or ""),
            str(item.get("team") or ""),
            str(item.get("name") or ""),
        )
    )
    return collected


def date_totals(overtime: list[dict[str, Any]]) -> list[DateTotal]:
    grouped: dict[str, DateTotal] = {}
    for item in overtime:
        work_date = str(item.get("work_date") or "")
        if not work_date:
            continue
        current = grouped.setdefault(
            work_date,
            DateTotal(work_date=work_date, headcount=0, meal_sum=0.0, hours_sum=0.0),
        )
        current.headcount += 1
        current.hours_sum += parse_work_hours(item.get("work_hours", 0))
        meal = item.get("meal_count")
        if meal not in (None, ""):
            current.meal_sum += parse_work_hours(meal)
    return [grouped[key] for key in sorted(grouped)]


def team_status(
    entries: list[dict[str, Any]],
    submissions: list[dict[str, Any]],
) -> list[TeamStatus]:
    by_team = {item["team"]: item for item in submissions}
    counts: dict[str, list[dict[str, Any]]] = {team: [] for team in SUBMITTING_TEAMS}
    for item in entries:
        team = str(item.get("team") or "")
        counts.setdefault(team, []).append(item)
    rows: list[TeamStatus] = []
    for team in SUBMITTING_TEAMS:
        saved = counts.get(team, [])
        overtime = [item for item in saved if is_overtime_hours(item.get("work_hours", 0))]
        sub = by_team.get(team) or {}
        submitted = bool(sub.get("is_submitted"))
        if submitted:
            label = "제출완료"
        elif saved:
            label = "임시저장"
        else:
            label = "미제출"
        rows.append(
            TeamStatus(
                team=team,
                is_submitted=submitted,
                submitted_at=sub.get("submitted_at"),
                saved_count=len(saved),
                overtime_count=len(overtime),
                label=label,
            )
        )
    return rows


def _text(value: object) -> str:
    return str(value or "").strip()


def find_anomalies(
    overtime: list[dict[str, Any]],
    status_rows: list[TeamStatus],
    past_deadline: bool = False,
) -> list[Anomaly]:
    anomalies: list[Anomaly] = []
    seen: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    names_on_date: dict[tuple[str, str], list[dict[str, Any]]] = {}

    for item in overtime:
        name = _text(item.get("name"))
        team = _text(item.get("team"))
        company = _text(item.get("company"))
        work_date = _text(item.get("work_date"))
        hours = parse_work_hours(item.get("work_hours", 0))
        meal = item.get("meal_count")

        if not name or not work_date or not team:
            anomalies.append(
                Anomaly(
                    "error",
                    "missing",
                    "필수값(성명·일자·팀)이 비어 있습니다.",
                    work_date or None,
                    name or None,
                    team or None,
                )
            )
        if team and team not in SUBMITTING_TEAMS:
            anomalies.append(
                Anomaly(
                    "error",
                    "team",
                    f"팀명이 취합 대상과 다릅니다: {team}",
                    work_date or None,
                    name or None,
                    team,
                )
            )
        if hours < 0 or hours > 24:
            anomalies.append(
                Anomaly(
                    "error",
                    "hours",
                    f"근무시간이 범위를 벗어났습니다: {hours}",
                    work_date or None,
                    name or None,
                    team or None,
                )
            )
        elif hours > 12:
            anomalies.append(
                Anomaly(
                    "warning",
                    "hours",
                    f"근무시간이 12시간을 넘습니다: {hours}",
                    work_date or None,
                    name or None,
                    team or None,
                )
            )
        if not company:
            anomalies.append(
                Anomaly(
                    "warning",
                    "company",
                    "회사가 없습니다.",
                    work_date or None,
                    name or None,
                    team or None,
                )
            )
        if meal in (None, ""):
            anomalies.append(
                Anomaly(
                    "warning",
                    "meal",
                    "식수인원이 없습니다.",
                    work_date or None,
                    name or None,
                    team or None,
                )
            )
        else:
            meal_value = parse_work_hours(meal)
            if meal_value < 0 or meal_value > 10:
                anomalies.append(
                    Anomaly(
                        "warning",
                        "meal",
                        f"식수인원이 비정상입니다: {meal_value}",
                        work_date or None,
                        name or None,
                        team or None,
                    )
                )

        if name and work_date:
            seen.setdefault((name, company, work_date), []).append(item)
            names_on_date.setdefault((name, work_date), []).append(item)

    for (name, company, work_date), rows in seen.items():
        if len(rows) < 2:
            continue
        teams = ", ".join(sorted({_text(item.get("team")) for item in rows}))
        anomalies.append(
            Anomaly(
                "error",
                "duplicate",
                f"같은 회사·일자에 이름이 중복됩니다 ({company or '회사없음'} / {teams}).",
                work_date,
                name,
                teams,
            )
        )

    for (name, work_date), rows in names_on_date.items():
        companies = {_text(item.get("company")) for item in rows}
        teams = {_text(item.get("team")) for item in rows}
        if len(rows) < 2:
            continue
        if len(companies) <= 1 and len(teams) <= 1:
            continue
        anomalies.append(
            Anomaly(
                "warning",
                "duplicate_name",
                "같은 일자에 동일 성명이 다른 팀 또는 회사에 있습니다. 동명이인인지 확인해 주세요.",
                work_date,
                name,
                ", ".join(sorted(teams)),
            )
        )

    for row in status_rows:
        if row.is_submitted and row.overtime_count == 0:
            anomalies.append(
                Anomaly(
                    "warning",
                    "empty_submit",
                    "제출했지만 특근 인원이 0명입니다.",
                    None,
                    None,
                    row.team,
                )
            )
        if past_deadline and not row.is_submitted:
            anomalies.append(
                Anomaly(
                    "warning",
                    "unsubmitted",
                    "마감 후에도 미제출입니다.",
                    None,
                    None,
                    row.team,
                )
            )
    return anomalies


def summarize(
    entries: list[dict[str, Any]],
    submissions: list[dict[str, Any]],
    past_deadline: bool = False,
) -> Aggregation:
    overtime = collect_overtime(entries)
    excluded = max(0, len(entries) - len(overtime))
    status_rows = team_status(entries, submissions)
    return Aggregation(
        overtime=overtime,
        excluded_zero=excluded,
        date_totals=date_totals(overtime),
        team_status=status_rows,
        anomalies=find_anomalies(overtime, status_rows, past_deadline=past_deadline),
        submitted_count=sum(1 for item in status_rows if item.is_submitted),
        team_count=len(SUBMITTING_TEAMS),
    )


@dataclass
class GenericAggregation:
    rows: list[dict[str, Any]] = field(default_factory=list)
    team_status: list[TeamStatus] = field(default_factory=list)
    anomalies: list[Anomaly] = field(default_factory=list)
    submitted_count: int = 0
    team_count: int = 0


def summarize_generic(
    schema: dict[str, Any],
    responses: list[dict[str, Any]],
    submissions: list[dict[str, Any]],
    past_deadline: bool = False,
) -> GenericAggregation:
    columns = list(schema.get("columns") or [])
    rows: list[dict[str, Any]] = []
    fake_entries: list[dict[str, Any]] = []
    for item in responses:
        payload = dict(item.get("payload") or {})
        team = str(item.get("team") or "")
        row = {"source_team": team, "team": team, **payload}
        rows.append(row)
        fake_entries.append({"team": team, "work_hours": 1})
    status_rows = team_status(fake_entries, submissions)
    anomalies: list[Anomaly] = []
    for row in rows:
        team = str(row.get("team") or "")
        if team and team not in SUBMITTING_TEAMS:
            anomalies.append(
                Anomaly("error", "team", f"팀명이 취합 대상과 다릅니다: {team}", None, None, team)
            )
        for column in columns:
            if not column.get("required"):
                continue
            value = row.get(column["key"])
            text = "" if value is None else str(value).strip()
            if not text or text.lower() == "nan":
                anomalies.append(
                    Anomaly(
                        "error",
                        "missing",
                        f"필수 항목 '{column['label']}'이(가) 비어 있습니다.",
                        None,
                        None,
                        team or None,
                    )
                )
    for row in status_rows:
        if row.is_submitted and row.saved_count == 0:
            anomalies.append(
                Anomaly("warning", "empty_submit", "제출했지만 입력 행이 없습니다.", None, None, row.team)
            )
        if past_deadline and not row.is_submitted:
            anomalies.append(
                Anomaly("warning", "unsubmitted", "마감 후에도 미제출입니다.", None, None, row.team)
            )
    return GenericAggregation(
        rows=rows,
        team_status=status_rows,
        anomalies=anomalies,
        submitted_count=sum(1 for item in status_rows if item.is_submitted),
        team_count=len(SUBMITTING_TEAMS),
    )

