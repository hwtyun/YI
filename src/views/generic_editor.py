from __future__ import annotations

import pandas as pd
import streamlit as st

from src.config import ROLE_ADMIN, primary_role
from src.schema import (
    add_schema_column,
    empty_schema,
    entry_schema,
    is_protected_column,
    remove_schema_column,
    roster_value_for_column,
)
from src.store import (
    AccessDenied,
    list_employees,
    list_responses,
    replace_team_responses,
    set_submitted,
    survey_edit_status,
    update_survey,
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


def _persist_schema(username: str, survey: dict, schema: dict) -> None:
    update_survey(
        username,
        int(survey["id"]),
        str(survey.get("title") or ""),
        str(survey.get("period_start") or ""),
        str(survey.get("period_end") or ""),
        str(survey.get("deadline_at") or ""),
        schema=schema,
    )


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

    if primary_role(username) == ROLE_ADMIN:
        st.markdown("**열 추가 · 삭제**")
        st.caption("AI가 만든 칸이 틀리면 여기서 열을 넣거나 지울 수 있습니다. 성명·회사·팀은 유지됩니다.")
        add_col, del_col = st.columns(2)
        raw_schema = survey.get("schema") or empty_schema()
        with add_col:
            new_label = st.text_input("추가할 열 이름", key=f"ge_add_name_{survey_id}_{team}")
            if st.button("열 추가", key=f"ge_add_btn_{survey_id}_{team}"):
                try:
                    _persist_schema(username, survey, add_schema_column(raw_schema, new_label))
                    st.success(f"「{new_label.strip()}」 열을 추가했습니다.")
                    st.rerun()
                except (ValueError, AccessDenied) as exc:
                    st.error(str(exc))
        with del_col:
            removable = [
                str(item.get("label") or "")
                for item in (raw_schema.get("columns") or [])
                if not is_protected_column(str(item.get("label") or ""))
            ]
            picked = st.selectbox(
                "삭제할 열",
                removable if removable else ["(삭제할 열이 없습니다)"],
                key=f"ge_del_name_{survey_id}_{team}",
            )
            if st.button("열 삭제", key=f"ge_del_btn_{survey_id}_{team}"):
                try:
                    if not removable:
                        raise ValueError("삭제할 열이 없습니다.")
                    _persist_schema(username, survey, remove_schema_column(raw_schema, str(picked)))
                    st.success(f"「{picked}」 열을 삭제했습니다.")
                    st.rerun()
                except (ValueError, AccessDenied) as exc:
                    st.error(str(exc))

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
