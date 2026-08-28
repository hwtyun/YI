from __future__ import annotations

import pandas as pd
import streamlit as st

from src.schema import empty_schema
from src.store import AccessDenied, list_responses, replace_team_responses, set_submitted, survey_edit_status


def _empty_frame(schema: dict) -> pd.DataFrame:
    data: dict[str, pd.Series] = {}
    for column in schema.get("columns") or []:
        label = str(column["label"])
        if column.get("type") == "number":
            data[label] = pd.Series(dtype="float")
        else:
            data[label] = pd.Series(dtype="string")
    return pd.DataFrame(data)


def _rows_to_frame(schema: dict, rows: list[dict]) -> pd.DataFrame:
    if not rows:
        return _empty_frame(schema)
    records = []
    for item in rows:
        payload = item.get("payload") or {}
        records.append({str(column["label"]): payload.get(column["key"]) for column in schema.get("columns") or []})
    return pd.DataFrame(records)


def _frame_to_payloads(schema: dict, frame: pd.DataFrame) -> list[dict]:
    rows: list[dict] = []
    if frame is None or frame.empty:
        return rows
    columns = list(schema.get("columns") or [])
    for _, row in frame.iterrows():
        payload: dict = {}
        empty = True
        for column in columns:
            value = row.get(column["label"])
            if value is None or (isinstance(value, float) and pd.isna(value)):
                payload[column["key"]] = None
                continue
            text = str(value).strip()
            if text.lower() == "nan":
                payload[column["key"]] = None
                continue
            empty = False
            if column.get("type") == "number":
                try:
                    payload[column["key"]] = float(value)
                except (TypeError, ValueError):
                    payload[column["key"]] = text
            else:
                payload[column["key"]] = text
        if not empty:
            rows.append(payload)
    return rows


def render_generic_editor(username: str, team: str, survey: dict) -> None:
    survey_id = int(survey["id"])
    schema = survey.get("schema") or empty_schema()
    existing = [item for item in list_responses(username, survey_id) if item.get("team") == team]
    st.caption(schema.get("instructions") or "아래 표에 팀 데이터를 입력하세요. 항목은 이 조사에만 해당합니다.")
    edited = st.data_editor(
        _rows_to_frame(schema, existing),
        num_rows="dynamic",
        hide_index=True,
        width="stretch",
        key=f"generic_ed_{survey_id}_{team}",
    )
    can_edit, reason = survey_edit_status(username, survey_id)
    if not can_edit:
        st.warning(reason)
        return
    payloads = _frame_to_payloads(schema, edited)
    save_col, submit_col = st.columns(2)
    try:
        if save_col.button("저장", key=f"generic_save_{survey_id}_{team}"):
            replace_team_responses(username, survey_id, team, payloads)
            st.success("저장했습니다.")
        if submit_col.button("제출", type="primary", key=f"generic_submit_{survey_id}_{team}"):
            replace_team_responses(username, survey_id, team, payloads)
            set_submitted(username, survey_id, team, True)
            st.success("제출했습니다. 마감 전까지 다시 수정할 수 있습니다.")
    except AccessDenied as exc:
        st.error(str(exc))
