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
