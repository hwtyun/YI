from __future__ import annotations

import pandas as pd
import streamlit as st

from src.schema import empty_schema, entry_schema, roster_value_for_column
from src.store import (
    AccessDenied,
    list_employees,
    list_responses,
    replace_team_responses,
    set_submitted,
    survey_edit_status,
)


def _empty_frame(schema: dict) -> pd.DataFrame:
    data: dict[str, pd.Series] = {}
    for column in schema.get("columns") or []:
        label = str(column["label"])
        if column.get("type") == "number":
            data[label] = pd.Series(dtype="float")
        else:
            data[label] = pd.Series(dtype="string")
    return pd.DataFrame(data)


def _payload_record(schema: dict, payload: dict) -> dict:
    return {str(column["label"]): payload.get(column["key"]) for column in schema.get("columns") or []}


def _employee_record(schema: dict, employee: dict) -> dict:
    return {
        str(column["label"]): roster_value_for_column(column, employee)
        for column in schema.get("columns") or []
    }


def _name_from_record(schema: dict, record: dict) -> str:
    for column in schema.get("columns") or []:
        label = str(column["label"])
        if label in {"성명", "이름", "성함"}:
            return str(record.get(label) or "").strip()
    return ""


def _rows_to_frame(schema: dict, rows: list[dict], employees: list[dict]) -> pd.DataFrame:
    records = [_payload_record(schema, item.get("payload") or {}) for item in rows]
    seen = {_name_from_record(schema, item) for item in records if _name_from_record(schema, item)}
    for employee in employees:
        name = str(employee.get("name") or "").strip()
        if name and name in seen:
            continue
        records.append(_employee_record(schema, employee))
        if name:
            seen.add(name)
    if not records:
        return _empty_frame(schema)
    frame = pd.DataFrame(records)
    for column in schema.get("columns") or []:
        label = str(column["label"])
        if label not in frame.columns:
            frame[label] = pd.NA
    labels = [str(column["label"]) for column in schema.get("columns") or []]
    return frame[labels]


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
    schema = entry_schema(survey.get("schema") or empty_schema())
    existing = [item for item in list_responses(username, survey_id) if item.get("team") == team]
    employees = list_employees(username, team)
    st.caption(
        schema.get("instructions")
        or "아래 표에는 이 조사에 필요한 칸만 나옵니다. 주민번호·주소 같은 첨부 양식 칸은 빼 두었습니다."
    )
    if employees:
        st.markdown("**우리 팀 인원**")
        st.dataframe(
            [
                {
                    "회사": item.get("company") or "",
                    "성명": item.get("name") or "",
                    "고용형태": item.get("employment_type") or "",
                }
                for item in employees
            ],
            hide_index=True,
            width="stretch",
        )
        st.caption("명부에 있는 인원을 아래 입력표에 미리 넣었습니다. 이번 조사에 해당하지 않으면 그 행을 지우면 됩니다.")
    else:
        st.caption("재직 명부가 비어 있습니다. 관리자가 명부를 올리면 인원이 자동으로 나옵니다.")
    st.caption("열을 넣거나 지울 때는 생산관리팀 관리자메뉴 「조사 관리」에서 수정합니다.")

    labels = [str(column["label"]) for column in schema.get("columns") or []]
    editor_key = f"generic_ed_{survey_id}_{team}_{'_'.join(labels)}"
    edited = st.data_editor(
        _rows_to_frame(schema, existing, employees),
        num_rows="dynamic",
        hide_index=True,
        width="stretch",
        key=editor_key,
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
