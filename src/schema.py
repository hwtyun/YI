"""조사마다 다른 입력 컬럼 목록. 특근 조사는 kind=overtime 으로 기존 화면을 쓴다."""

from __future__ import annotations

import re
from typing import Any

KIND_OVERTIME = "overtime"
KIND_GENERIC = "generic"
ALLOWED_TYPES = ("text", "number", "date")
MAX_COLUMNS = 20


def is_generic(survey: dict[str, Any] | None) -> bool:
    if not survey:
        return False
    return str(survey.get("kind") or KIND_OVERTIME) == KIND_GENERIC


def empty_schema(title: str = "") -> dict[str, Any]:
    return {
        "title": title,
        "instructions": "",
        "columns": [
            {"key": "col_1", "label": "항목1", "type": "text", "required": True},
        ],
    }


def parse_model_json(text: str) -> dict[str, Any]:
    stripped = str(text or "").strip()
    if not stripped:
        raise ValueError("AI 응답이 비어 있습니다.")
    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", stripped, re.S)
    if fenced:
        stripped = fenced.group(1)
    else:
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start < 0 or end <= start:
            raise ValueError("AI 응답에서 JSON을 찾지 못했습니다.")
        stripped = stripped[start : end + 1]
    import json

    data = json.loads(stripped)
    if not isinstance(data, dict):
        raise ValueError("양식 JSON이 올바르지 않습니다.")
    data.pop("publish", None)
    data.pop("is_published", None)
    data.pop("auto_publish", None)
    return data


def _slug(label: str, index: int, used: set[str]) -> str:
    key = re.sub(r"[^a-zA-Z0-9_]+", "_", str(label or "")).strip("_").lower()
    if not key or not re.match(r"[a-z]", key):
        key = f"col_{index}"
    base = key
    suffix = 2
    while key in used:
        key = f"{base}_{suffix}"
        suffix += 1
    used.add(key)
    return key


def normalize_schema(raw: dict[str, Any] | None) -> dict[str, Any]:
    data = dict(raw or {})
    title = str(data.get("title") or "").strip()
    instructions = str(data.get("instructions") or data.get("description") or "").strip()
    columns_in = data.get("columns") or data.get("fields") or []
    if not isinstance(columns_in, list) or not columns_in:
        raise ValueError("입력 항목(컬럼)이 없습니다.")
    used: set[str] = set()
    columns: list[dict[str, Any]] = []
    for index, item in enumerate(columns_in, start=1):
        if len(columns) >= MAX_COLUMNS:
            break
        if not isinstance(item, dict):
            continue
        label = str(item.get("label") or item.get("name") or "").strip()
        if not label:
            continue
        given = str(item.get("key") or item.get("id") or "").strip()
        if re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", given) and given not in used:
            key = given
            used.add(key)
        else:
            key = _slug(label, index, used)
        type_name = str(item.get("type") or "text").strip().lower()
        if type_name not in ALLOWED_TYPES:
            type_name = "text"
        required = bool(item.get("required", True))
        columns.append({"key": key, "label": label, "type": type_name, "required": required})
    if not columns:
        raise ValueError("유효한 입력 항목이 없습니다.")
    return {"title": title, "instructions": instructions, "columns": columns}


def column_labels(schema: dict[str, Any]) -> list[str]:
    return [str(item["label"]) for item in schema.get("columns") or []]


_JUNK_EXACT = {
    "no",
    "n/o",
    "#",
    "번호",
    "순번",
    "연번",
    "직업",
}
_JUNK_PARTS = (
    "주민",
    "주민번호",
    "주민등록",
    "전화",
    "연락처",
    "휴대폰",
    "핸드폰",
    "휴대전화",
    "성별",
    "생년월일",
    "생일",
    "주소",
    "직업코드",
    "여권",
    "운전면허",
)
_NAME_LABELS = ("성명", "이름", "성함")
_COMPANY_LABELS = ("회사", "소속회사")
_TEAM_LABELS = ("팀", "부서", "부서명", "소속")


def _compact_label(label: str) -> str:
    return re.sub(r"\s+", "", str(label or "")).lower()


def is_template_junk(label: str) -> bool:
    compact = _compact_label(label)
    if compact in _JUNK_EXACT:
        return True
    return any(part in compact for part in _JUNK_PARTS)


def slim_schema(schema: dict[str, Any] | None) -> dict[str, Any]:
    """첨부 양식의 개인정보·순번 칸을 빼고, 팀이 적을 항목만 남긴다."""
    data = dict(schema or {})
    kept: list[dict[str, Any]] = []
    for item in data.get("columns") or []:
        if not isinstance(item, dict):
            continue
        if is_template_junk(str(item.get("label") or "")):
            continue
        kept.append(item)
    if not kept:
        kept = [
            item
            for item in (data.get("columns") or [])
            if isinstance(item, dict) and str(item.get("label") or "").strip()
        ][:3]
    data["columns"] = kept
    return data


def _pick_column(columns: list[dict[str, Any]], labels: tuple[str, ...]) -> dict[str, Any] | None:
    wanted = {_compact_label(item) for item in labels}
    for item in columns:
        if _compact_label(str(item.get("label") or "")) in wanted:
            return item
    return None


def entry_schema(schema: dict[str, Any] | None) -> dict[str, Any]:
    """입력 화면에 성명·회사·팀을 앞에 두고, 필요 항목만 이어 붙인다."""
    slim = slim_schema(schema)
    source = list(slim.get("columns") or [])
    name_col = _pick_column(source, _NAME_LABELS) or {
        "key": "name",
        "label": "성명",
        "type": "text",
        "required": True,
    }
    company_col = _pick_column(source, _COMPANY_LABELS) or {
        "key": "company",
        "label": "회사",
        "type": "text",
        "required": False,
    }
    team_col = _pick_column(source, _TEAM_LABELS) or {
        "key": "team",
        "label": "팀",
        "type": "text",
        "required": False,
    }
    columns = [name_col, company_col, team_col]
    used_keys = {str(item.get("key")) for item in columns}
    used_labels = {_compact_label(str(item.get("label") or "")) for item in columns}
    for item in source:
        key = str(item.get("key") or "")
        label = _compact_label(str(item.get("label") or ""))
        if key in used_keys or label in used_labels:
            continue
        columns.append(item)
        used_keys.add(key)
    slim["columns"] = columns
    return slim


def roster_value_for_column(column: dict[str, Any], employee: dict[str, Any]) -> str:
    label = _compact_label(str(column.get("label") or ""))
    if label in {_compact_label(item) for item in _NAME_LABELS}:
        return str(employee.get("name") or "")
    if label in {_compact_label(item) for item in _COMPANY_LABELS}:
        return str(employee.get("company") or "")
    if label in {_compact_label(item) for item in _TEAM_LABELS}:
        return str(employee.get("team") or "")
    if label in {"고용형태"}:
        return str(employee.get("employment_type") or "")
    return ""


def is_protected_column(label: str) -> bool:
    compact = _compact_label(label)
    protected = {_compact_label(item) for item in (*_NAME_LABELS, *_COMPANY_LABELS, *_TEAM_LABELS)}
    return compact in protected


def add_schema_column(
    schema: dict[str, Any] | None,
    label: str,
    type_name: str = "text",
    required: bool = False,
) -> dict[str, Any]:
    data = dict(schema or empty_schema())
    columns = [dict(item) for item in data.get("columns") or [] if isinstance(item, dict)]
    name = str(label or "").strip()
    if not name:
        raise ValueError("열 이름을 입력하세요.")
    if any(_compact_label(str(item.get("label") or "")) == _compact_label(name) for item in columns):
        raise ValueError("이미 있는 열입니다.")
    used = {str(item.get("key") or "") for item in columns}
    key = _slug(name, len(columns) + 1, used)
    kind = str(type_name or "text").strip().lower()
    if kind not in ALLOWED_TYPES:
        kind = "text"
    columns.append({"key": key, "label": name, "type": kind, "required": bool(required)})
    data["columns"] = columns
    return data


def remove_schema_column(schema: dict[str, Any] | None, label: str) -> dict[str, Any]:
    data = dict(schema or empty_schema())
    name = str(label or "").strip()
    if is_protected_column(name):
        raise ValueError("성명·회사·팀은 삭제할 수 없습니다.")
    target = _compact_label(name)
    kept = [
        item
        for item in data.get("columns") or []
        if isinstance(item, dict) and _compact_label(str(item.get("label") or "")) != target
    ]
    if len(kept) == len(list(data.get("columns") or [])):
        raise ValueError("삭제할 열을 찾지 못했습니다.")
    if not kept:
        raise ValueError("열을 모두 지울 수는 없습니다.")
    data["columns"] = kept
    return data
