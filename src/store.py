"""조사·인원·제출 데이터 접근. 역할에 따라 읽기/쓰기 범위를 제한한다."""

from __future__ import annotations

import json
from typing import Any

from src.config import (
    COMPANIES,
    EMPLOYMENT_TYPES,
    ROLE_ADMIN,
    ROLE_DIRECTOR,
    ROLE_TEAM,
    SUBMITTING_TEAMS,
    USERS,
    get_user,
    primary_role,
)
from src.db import get_connection
from src.hours import parse_work_hours
from src.schedule import is_past_deadline
from src.schema import KIND_OVERTIME, normalize_schema


class AccessDenied(PermissionError):
    """권한 없는 데이터 접근."""


OPEN_OVERTIME_TITLE = "상시 특근 입력"
OPEN_OVERTIME_START = "2000-01-01"
OPEN_OVERTIME_END = "2099-12-31"
OPEN_OVERTIME_DEADLINE = "2099-12-31T23:59:59"


def _now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()


def _role(username: str) -> str:
    return primary_role(username)


def _own_team(username: str) -> str | None:
    return get_user(username)["team"]


def _require_known_user(username: str) -> None:
    if username not in USERS:
        raise AccessDenied("알 수 없는 계정입니다.")


def _require_admin(username: str) -> None:
    _require_known_user(username)
    if _role(username) != ROLE_ADMIN:
        raise AccessDenied("관리자만 할 수 있습니다.")


def _assert_can_write_team(username: str, team: str) -> None:
    _require_known_user(username)
    role = _role(username)
    if role == ROLE_DIRECTOR:
        raise AccessDenied("공장장은 데이터를 입력할 수 없습니다.")
    if role == ROLE_ADMIN:
        if team not in SUBMITTING_TEAMS:
            raise AccessDenied("알 수 없는 팀입니다.")
        return
    if role == ROLE_TEAM:
        if team != _own_team(username):
            raise AccessDenied("다른 팀 데이터는 입력할 수 없습니다.")
        return
    raise AccessDenied("권한이 없습니다.")


def _row_dict(row: Any) -> dict[str, Any]:
    return {key: row[key] for key in row.keys()}


def _survey_dict(row: Any) -> dict[str, Any]:
    item = _row_dict(row)
    item["kind"] = item.get("kind") or KIND_OVERTIME
    raw = item.get("schema_json")
    item["schema"] = None
    if raw:
        try:
            item["schema"] = json.loads(str(raw))
        except json.JSONDecodeError:
            item["schema"] = None
    return item


def list_accounts() -> list[dict[str, Any]]:
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT username, display_name, role, team
            FROM users
            ORDER BY role, username
            """
        ).fetchall()
        return [_row_dict(row) for row in rows]
    finally:
        conn.close()


def create_survey(
    username: str,
    title: str,
    period_start: str,
    period_end: str,
    deadline_at: str,
    kind: str = KIND_OVERTIME,
    schema: dict[str, Any] | None = None,
) -> int:
    _require_admin(username)
    now = _now()
    kind_value = kind or KIND_OVERTIME
    schema_json = None
    if schema:
        schema_json = json.dumps(normalize_schema(schema), ensure_ascii=False)
    conn = get_connection()
    try:
        cursor = conn.execute(
            """
            INSERT INTO surveys (
                title, period_start, period_end, deadline_at,
                is_published, created_by, created_at, kind, schema_json
            )
            VALUES (?, ?, ?, ?, 0, ?, ?, ?, ?)
            """,
            (title, period_start, period_end, deadline_at, username, now, kind_value, schema_json),
        )
        survey_id = int(cursor.lastrowid)
        conn.commit()
        return survey_id
    finally:
        conn.close()


def publish_survey(username: str, survey_id: int) -> None:
    _require_admin(username)
    now = _now()
    conn = get_connection()
    try:
        exists = conn.execute("SELECT id FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if exists is None:
            raise ValueError("조사를 찾을 수 없습니다.")
        conn.execute("UPDATE surveys SET is_published = 1 WHERE id = ?", (survey_id,))
        for team in SUBMITTING_TEAMS:
            conn.execute(
                """
                INSERT INTO submissions (survey_id, team, is_submitted, submitted_at, updated_at)
                VALUES (?, ?, 0, NULL, ?)
                ON CONFLICT(survey_id, team) DO NOTHING
                """,
                (survey_id, team, now),
            )
        conn.commit()
    finally:
        conn.close()


def ensure_open_overtime_survey(username: str) -> dict[str, Any]:
    """특근은 배포 없이 언제든 입력한다. 상시 조사가 없으면 만들어 바로 연다."""
    _require_known_user(username)
    now = _now()
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT id FROM surveys
            WHERE IFNULL(kind, ?) = ? AND title = ?
            ORDER BY id ASC
            """,
            (KIND_OVERTIME, KIND_OVERTIME, OPEN_OVERTIME_TITLE),
        ).fetchone()
        if row is None:
            cursor = conn.execute(
                """
                INSERT INTO surveys (
                    title, period_start, period_end, deadline_at,
                    is_published, created_by, created_at, kind, schema_json
                )
                VALUES (?, ?, ?, ?, 1, ?, ?, ?, NULL)
                """,
                (
                    OPEN_OVERTIME_TITLE,
                    OPEN_OVERTIME_START,
                    OPEN_OVERTIME_END,
                    OPEN_OVERTIME_DEADLINE,
                    username,
                    now,
                    KIND_OVERTIME,
                ),
            )
            survey_id = int(cursor.lastrowid)
        else:
            survey_id = int(row["id"])
            conn.execute(
                """
                UPDATE surveys
                SET is_published = 1,
                    period_start = ?,
                    period_end = ?,
                    deadline_at = ?
                WHERE id = ?
                """,
                (OPEN_OVERTIME_START, OPEN_OVERTIME_END, OPEN_OVERTIME_DEADLINE, survey_id),
            )
        for team in SUBMITTING_TEAMS:
            conn.execute(
                """
                INSERT INTO submissions (survey_id, team, is_submitted, submitted_at, updated_at)
                VALUES (?, ?, 0, NULL, ?)
                ON CONFLICT(survey_id, team) DO NOTHING
                """,
                (survey_id, team, now),
            )
        conn.commit()
    finally:
        conn.close()
    survey = get_survey_by_id(survey_id)
    if survey is None:
        raise AccessDenied("상시 특근 조사를 열 수 없습니다.")
    return survey


def list_surveys(username: str) -> list[dict[str, Any]]:
    _require_known_user(username)
    conn = get_connection()
    try:
        if _role(username) == ROLE_ADMIN:
            rows = conn.execute(
                """
                SELECT id, title, period_start, period_end, deadline_at,
                       is_published, created_by, created_at, kind, schema_json
                FROM surveys
                ORDER BY id DESC
                """
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT id, title, period_start, period_end, deadline_at,
                       is_published, created_by, created_at, kind, schema_json
                FROM surveys
                WHERE is_published = 1
                ORDER BY id DESC
                """
            ).fetchall()
        return [_survey_dict(row) for row in rows]
    finally:
        conn.close()


def get_survey_by_id(survey_id: int) -> dict[str, Any] | None:
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT id, title, period_start, period_end, deadline_at,
                   is_published, created_by, created_at, kind, schema_json
            FROM surveys
            WHERE id = ?
            """,
            (survey_id,),
        ).fetchone()
        return None if row is None else _survey_dict(row)
    finally:
        conn.close()


def survey_edit_status(username: str, survey_id: int) -> tuple[bool, str]:
    """팀이 입력·수정할 수 있으면 (True, '')."""
    _require_known_user(username)
    survey = get_survey_by_id(survey_id)
    if survey is None:
        return False, "조사를 찾을 수 없습니다."
    if _role(username) == ROLE_DIRECTOR:
        return False, "공장장은 데이터를 입력할 수 없습니다."
    if not survey["is_published"]:
        return False, "아직 배포되지 않아 입력할 수 없습니다."
    if str(survey.get("title") or "") == OPEN_OVERTIME_TITLE:
        return True, ""
    if _role(username) == ROLE_TEAM and is_past_deadline(str(survey["deadline_at"])):
        return False, "마감되어 수정할 수 없습니다."
    return True, ""


def replace_team_entries(
    username: str,
    survey_id: int,
    team: str,
    entries: list[dict[str, Any]],
) -> None:
    _assert_can_write_team(username, team)
    can_edit, reason = survey_edit_status(username, survey_id)
    if not can_edit:
        raise AccessDenied(reason)
    now = _now()
    conn = get_connection()
    try:
        survey = conn.execute("SELECT id FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if survey is None:
            raise ValueError("조사를 찾을 수 없습니다.")
        conn.execute(
            "DELETE FROM entries WHERE survey_id = ? AND team = ?",
            (survey_id, team),
        )
        for index, item in enumerate(entries, start=1):
            name = str(item.get("name") or "").strip()
            work_date = str(item.get("work_date") or "").strip()
            if not name or not work_date:
                continue
            conn.execute(
                """
                INSERT INTO entries (
                    survey_id, team, seq_no, rank, name, work_date,
                    work_hours, meal_count, note, company, employment_type,
                    is_manual, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    survey_id,
                    team,
                    item.get("seq_no", index),
                    item.get("rank"),
                    name,
                    work_date,
                    parse_work_hours(item.get("work_hours", 0)),
                    item.get("meal_count"),
                    item.get("note"),
                    item.get("company"),
                    item.get("employment_type"),
                    1 if item.get("is_manual") else 0,
                    now,
                ),
            )
        conn.commit()
    finally:
        conn.close()


def list_entries(username: str, survey_id: int) -> list[dict[str, Any]]:
    _require_known_user(username)
    role = _role(username)
    if role == ROLE_DIRECTOR:
        return []
    conn = get_connection()
    try:
        if role == ROLE_TEAM:
            team = _own_team(username)
            rows = conn.execute(
                """
                SELECT id, survey_id, team, seq_no, rank, name, work_date,
                       work_hours, meal_count, note, company, employment_type,
                       is_manual, updated_at
                FROM entries
                WHERE survey_id = ? AND team = ?
                ORDER BY work_date, seq_no, id
                """,
                (survey_id, team),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT id, survey_id, team, seq_no, rank, name, work_date,
                       work_hours, meal_count, note, company, employment_type,
                       is_manual, updated_at
                FROM entries
                WHERE survey_id = ?
                ORDER BY team, work_date, seq_no, id
                """,
                (survey_id,),
            ).fetchall()
        return [_row_dict(row) for row in rows]
    finally:
        conn.close()


def list_overtime_entries(username: str, survey_id: int) -> list[dict[str, Any]]:
    """근무시간 > 0인 행만. 모든 역할이 해당 조사의 전체 팀 특근 명단을 본다. 공장장은 0시간 원본을 볼 수 없다."""
    _require_known_user(username)
    role = _role(username)
    if role == ROLE_DIRECTOR:
        survey = get_survey_by_id(survey_id)
        if survey is None or not survey["is_published"]:
            return []
    conn = get_connection()
    try:
        if role in (ROLE_TEAM, ROLE_ADMIN, ROLE_DIRECTOR):
            rows = conn.execute(
                """
                SELECT id, survey_id, team, seq_no, rank, name, work_date,
                       work_hours, meal_count, note, company, employment_type,
                       is_manual, updated_at
                FROM entries
                WHERE survey_id = ? AND work_hours > 0
                ORDER BY team, work_date, seq_no, id
                """,
                (survey_id,),
            ).fetchall()
        else:
            raise AccessDenied("권한이 없습니다.")
        return [_row_dict(row) for row in rows]
    finally:
        conn.close()


def list_factory_overtime_counts(username: str) -> dict[str, int]:
    """일자별 공장 전체 특근 인원(팀+이름 중복 제외). 모든 계정이 볼 수 있다."""
    people = list_overtime_people(username)
    counts: dict[str, int] = {}
    for item in people:
        key = str(item.get("work_date") or "")
        if not key:
            continue
        counts[key] = counts.get(key, 0) + 1
    return counts


def list_overtime_people(username: str, work_date: str | None = None) -> list[dict[str, Any]]:
    """특근(시간>0) 명단. 모든 팀이 공장 전체를 볼 수 있다. 입력은 본인 팀만."""
    _require_known_user(username)
    conn = get_connection()
    try:
        params: list[Any] = [KIND_OVERTIME, KIND_OVERTIME]
        sql = """
            SELECT e.team, e.name, e.company, e.employment_type, e.work_hours,
                   e.meal_count, e.note, e.work_date
            FROM entries e
            INNER JOIN surveys s ON s.id = e.survey_id
            WHERE IFNULL(s.kind, ?) = ?
              AND e.work_hours > 0
        """
        if work_date:
            sql += " AND e.work_date = ?"
            params.append(work_date)
        sql += " ORDER BY e.team, e.name, e.id"
        rows = conn.execute(sql, params).fetchall()
        seen: set[tuple[str, str, str]] = set()
        people: list[dict[str, Any]] = []
        for row in rows:
            item = _row_dict(row)
            stamp = (
                str(item.get("team") or ""),
                str(item.get("name") or ""),
                str(item.get("work_date") or ""),
            )
            if stamp in seen:
                continue
            seen.add(stamp)
            people.append(item)
        return people
    finally:
        conn.close()


def set_submitted(username: str, survey_id: int, team: str, submitted: bool) -> None:
    _assert_can_write_team(username, team)
    can_edit, reason = survey_edit_status(username, survey_id)
    if not can_edit:
        raise AccessDenied(reason)
    now = _now()
    submitted_at = now if submitted else None
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO submissions (survey_id, team, is_submitted, submitted_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(survey_id, team) DO UPDATE SET
                is_submitted = excluded.is_submitted,
                submitted_at = excluded.submitted_at,
                updated_at = excluded.updated_at
            """,
            (survey_id, team, 1 if submitted else 0, submitted_at, now),
        )
        conn.commit()
    finally:
        conn.close()


def list_submissions(username: str, survey_id: int) -> list[dict[str, Any]]:
    _require_known_user(username)
    role = _role(username)
    if role == ROLE_DIRECTOR:
        return []
    conn = get_connection()
    try:
        if role == ROLE_TEAM:
            team = _own_team(username)
            rows = conn.execute(
                """
                SELECT survey_id, team, is_submitted, submitted_at, updated_at
                FROM submissions
                WHERE survey_id = ? AND team = ?
                """,
                (survey_id, team),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT survey_id, team, is_submitted, submitted_at, updated_at
                FROM submissions
                WHERE survey_id = ?
                ORDER BY team
                """,
                (survey_id,),
            ).fetchall()
        return [_row_dict(row) for row in rows]
    finally:
        conn.close()


def list_employees(username: str, team: str | None = None) -> list[dict[str, Any]]:
    _require_known_user(username)
    role = _role(username)
    if role == ROLE_DIRECTOR:
        return []
    if role == ROLE_TEAM:
        team = _own_team(username)
    conn = get_connection()
    try:
        if team:
            rows = conn.execute(
                """
                SELECT id, name, company, team, employment_type, updated_at
                FROM employees
                WHERE team = ?
                ORDER BY company, employment_type, name
                """,
                (team,),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT id, name, company, team, employment_type, updated_at
                FROM employees
                ORDER BY team, company, employment_type, name
                """
            ).fetchall()
        return [_row_dict(row) for row in rows]
    finally:
        conn.close()


def replace_employee_roster(username: str, rows: list[dict[str, Any]]) -> int:
    _require_admin(username)
    now = _now()
    conn = get_connection()
    try:
        conn.execute("DELETE FROM employees")
        count = 0
        for item in rows:
            name = str(item.get("name") or "").strip()
            company = str(item.get("company") or "").strip()
            team = str(item.get("team") or "").strip()
            employment_type = str(item.get("employment_type") or "").strip()
            if not name or not company or not team or not employment_type:
                continue
            conn.execute(
                """
                INSERT INTO employees (name, company, team, employment_type, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (name, company, team, employment_type, now),
            )
            count += 1
        conn.commit()
        return count
    finally:
        conn.close()


def find_employee(
    name: str,
    team: str,
    company: str | None = None,
) -> dict[str, Any] | None:
    conn = get_connection()
    try:
        if company:
            row = conn.execute(
                """
                SELECT id, name, company, team, employment_type
                FROM employees
                WHERE name = ? AND team = ? AND company = ?
                """,
                (name, team, company),
            ).fetchone()
        else:
            matches = conn.execute(
                """
                SELECT id, name, company, team, employment_type
                FROM employees
                WHERE name = ? AND team = ?
                """,
                (name, team),
            ).fetchall()
            if len(matches) != 1:
                return None
            row = matches[0]
        return None if row is None else _row_dict(row)
    finally:
        conn.close()


def enrich_entry_from_roster(entry: dict[str, Any], team: str) -> dict[str, Any]:
    """엑셀에서 읽은 행에 명부의 회사·고용형태를 붙인다. 명부에 없으면 수기(일용직)로 본다."""
    name = str(entry.get("name") or "").strip()
    company = str(entry.get("company") or "").strip() or None
    found = find_employee(name, team, company)
    enriched = dict(entry)
    if found:
        enriched["company"] = found["company"]
        enriched["employment_type"] = found["employment_type"]
        enriched["is_manual"] = 0
        return enriched
    enriched["is_manual"] = 1
    if not enriched.get("employment_type"):
        enriched["employment_type"] = "일용직"
    return enriched


def add_employee(
    username: str,
    name: str,
    company: str,
    team: str,
    employment_type: str,
) -> int:
    """팀 담당자는 본인 팀에만 신규 인원을 넣을 수 있다. 최고 관리자는 전체 팀."""
    _require_known_user(username)
    role = _role(username)
    if role == ROLE_DIRECTOR:
        raise AccessDenied("공장장은 명부를 수정할 수 없습니다.")
    name = str(name or "").strip()
    company = str(company or "").strip()
    employment_type = str(employment_type or "").strip()
    if role == ROLE_TEAM:
        team = str(_own_team(username) or "")
    else:
        team = str(team or "").strip()
        if team not in SUBMITTING_TEAMS:
            raise AccessDenied("알 수 없는 팀입니다.")
    if not name:
        raise ValueError("성명을 입력하세요.")
    if company not in COMPANIES:
        raise ValueError("회사는 에이텍모빌리티 또는 에이텍컴퓨터여야 합니다.")
    if employment_type not in EMPLOYMENT_TYPES:
        raise ValueError("고용형태는 정규직, 계약직, 일용직 중 하나여야 합니다.")
    if find_employee(name, team, company):
        raise ValueError("같은 회사·팀에 이미 있는 이름입니다.")
    now = _now()
    conn = get_connection()
    try:
        cursor = conn.execute(
            """
            INSERT INTO employees (name, company, team, employment_type, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (name, company, team, employment_type, now),
        )
        conn.commit()
        return int(cursor.lastrowid)
    finally:
        conn.close()


def delete_employee(username: str, employee_id: int) -> None:
    _require_known_user(username)
    role = _role(username)
    if role == ROLE_DIRECTOR:
        raise AccessDenied("공장장은 명부를 수정할 수 없습니다.")
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT id, team FROM employees WHERE id = ?",
            (employee_id,),
        ).fetchone()
        if row is None:
            raise ValueError("명부에서 찾을 수 없습니다.")
        if role == ROLE_TEAM and str(row["team"]) != _own_team(username):
            raise AccessDenied("다른 팀 명부는 지울 수 없습니다.")
        conn.execute("DELETE FROM employees WHERE id = ?", (employee_id,))
        conn.commit()
    finally:
        conn.close()


def replace_team_responses(
    username: str,
    survey_id: int,
    team: str,
    rows: list[dict[str, Any]],
) -> None:
    _assert_can_write_team(username, team)
    can_edit, reason = survey_edit_status(username, survey_id)
    if not can_edit:
        raise AccessDenied(reason)
    now = _now()
    conn = get_connection()
    try:
        exists = conn.execute("SELECT id FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if exists is None:
            raise ValueError("조사를 찾을 수 없습니다.")
        conn.execute(
            "DELETE FROM responses WHERE survey_id = ? AND team = ?",
            (survey_id, team),
        )
        seq = 0
        for item in rows:
            payload = {str(key): value for key, value in dict(item).items() if key not in {"team", "source_team"}}
            if not any(str(value or "").strip() for value in payload.values() if value is not None):
                continue
            seq += 1
            conn.execute(
                """
                INSERT INTO responses (survey_id, team, seq_no, payload_json, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (survey_id, team, seq, json.dumps(payload, ensure_ascii=False), now),
            )
        conn.commit()
    finally:
        conn.close()


def list_responses(username: str, survey_id: int) -> list[dict[str, Any]]:
    """범용 취합 행. 관리자·공장장(배포된 조사)은 전체, 팀은 본인 팀만."""
    _require_known_user(username)
    role = _role(username)
    if role == ROLE_DIRECTOR:
        survey = get_survey_by_id(survey_id)
        if survey is None or not survey["is_published"]:
            return []
    conn = get_connection()
    try:
        if role == ROLE_TEAM:
            team = _own_team(username)
            rows = conn.execute(
                """
                SELECT id, survey_id, team, seq_no, payload_json, updated_at
                FROM responses
                WHERE survey_id = ? AND team = ?
                ORDER BY seq_no, id
                """,
                (survey_id, team),
            ).fetchall()
        elif role in (ROLE_ADMIN, ROLE_DIRECTOR):
            rows = conn.execute(
                """
                SELECT id, survey_id, team, seq_no, payload_json, updated_at
                FROM responses
                WHERE survey_id = ?
                ORDER BY team, seq_no, id
                """,
                (survey_id,),
            ).fetchall()
        else:
            raise AccessDenied("권한이 없습니다.")
        result: list[dict[str, Any]] = []
        for row in rows:
            item = _row_dict(row)
            try:
                payload = json.loads(str(item.get("payload_json") or "{}"))
            except json.JSONDecodeError:
                payload = {}
            if not isinstance(payload, dict):
                payload = {}
            item["payload"] = payload
            item["source_team"] = item.get("team")
            result.append(item)
        return result
    finally:
        conn.close()


