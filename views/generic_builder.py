from __future__ import annotations

from datetime import datetime, time

import pandas as pd
import streamlit as st

from src.extract import extract_upload_text
from src.gemini import gemini_api_key, propose_schema
from src.schema import KIND_GENERIC, empty_schema, normalize_schema
from src.schedule import default_deadline, default_overtime_weekend, default_survey_title
from src.store import create_survey

TYPE_LABELS = {"text": "텍스트", "number": "숫자", "date": "날짜"}
TYPE_VALUES = {value: key for key, value in TYPE_LABELS.items()}


def render_generic_builder(username: str) -> None:
    st.subheader("본사 요청 양식")
    st.caption(
        "본사 메일 본문과 첨부를 올리면 Gemini가 입력 칸을 제안합니다. "
        "미리보기에서 고친 뒤 조사를 만들고, 조사 관리에서 배포해야 팀이 입력할 수 있습니다."
    )
    request = st.text_area("메일 본문", height=180, key="generic_request_text")
    uploaded_files = st.file_uploader(
        "첨부 파일 (엑셀, 워드, PDF, 텍스트, 메일원문)",
        type=["txt", "csv", "md", "eml", "xlsx", "xlsm", "docx", "pdf"],
        accept_multiple_files=True,
        key="generic_request_files",
    )
    attachment_parts: list[str] = []
    for uploaded in uploaded_files or []:
        text = extract_upload_text(uploaded.name, uploaded.getvalue())
        if text.strip():
            attachment_parts.append(f"\n\n[첨부 {uploaded.name}]\n{text.strip()}")
    combined = (request or "").strip() + "".join(attachment_parts)
    if len(combined) > 24000:
        combined = combined[:24000]
        st.caption("첨부 내용이 길어 앞부분만 AI에 보냅니다.")

    propose_col, blank_col = st.columns(2)
    if propose_col.button("AI로 양식 제안", key="generic_propose"):
        if not gemini_api_key():
            st.error("GEMINI_API_KEY가 secrets.toml에 없습니다. 키를 넣거나 아래 빈 양식부터 작성하세요.")
        else:
            try:
                st.session_state["draft_schema"] = propose_schema(combined)
                st.success("양식을 제안했습니다. 아래 미리보기를 확인·수정한 뒤 조사를 만드세요.")
            except Exception as exc:  # noqa: BLE001
                st.error(str(exc))
    if blank_col.button("빈 양식부터 작성", key="generic_blank"):
        st.session_state["draft_schema"] = empty_schema("새 취합")

    draft = st.session_state.get("draft_schema")
    if not draft:
        st.info("AI 제안 또는 빈 양식 작성 후, 미리보기에서 항목을 고칩니다.")
        return

    st.markdown("**미리보기 · 수정**")
    title = st.text_input("조사 제목", value=str(draft.get("title") or ""), key="generic_draft_title")
    instructions = st.text_area(
        "팀 안내 문구",
        value=str(draft.get("instructions") or ""),
        key="generic_draft_help",
    )
    column_rows = [
        {
            "항목명": item.get("label") or "",
            "형식": TYPE_LABELS.get(str(item.get("type") or "text"), "텍스트"),
            "필수": bool(item.get("required", True)),
        }
        for item in draft.get("columns") or []
    ]
    edited = st.data_editor(
        pd.DataFrame(column_rows),
        num_rows="dynamic",
        hide_index=True,
        width="stretch",
        column_config={
            "항목명": st.column_config.TextColumn("항목명"),
            "형식": st.column_config.SelectboxColumn("형식", options=list(TYPE_LABELS.values())),
            "필수": st.column_config.CheckboxColumn("필수", default=True),
        },
        key="generic_draft_columns",
    )
    saturday, sunday = default_overtime_weekend()
    start_col, end_col = st.columns(2)
    period_start = start_col.date_input("조사 시작일", value=saturday, key="generic_start")
    period_end = end_col.date_input("조사 종료일", value=sunday, key="generic_end")
    default_due = default_deadline(period_start if period_start.weekday() == 5 else saturday)
    due_date = st.date_input("마감일", value=default_due.date(), key="generic_due_date")
    due_time = st.time_input("마감 시각", value=time(11, 0), key="generic_due_time")

    if st.button("조사 생성 (미배포)", type="primary", key="generic_create"):
        raw_columns = []
        for _, row in edited.iterrows():
            label = str(row.get("항목명") or "").strip()
            if not label:
                continue
            raw_columns.append(
                {
                    "label": label,
                    "type": TYPE_VALUES.get(str(row.get("형식") or "텍스트"), "text"),
                    "required": bool(row.get("필수")),
                }
            )
        try:
            schema = normalize_schema(
                {"title": title.strip(), "instructions": instructions.strip(), "columns": raw_columns}
            )
        except ValueError as exc:
            st.error(str(exc))
            return
        if period_end < period_start:
            st.error("종료일은 시작일보다 빠를 수 없습니다.")
            return
        deadline_at = datetime.combine(due_date, due_time).strftime("%Y-%m-%dT%H:%M:%S")
        survey_id = create_survey(
            username,
            schema["title"] or title.strip() or default_survey_title(period_start),
            period_start.isoformat(),
            period_end.isoformat(),
            deadline_at,
            kind=KIND_GENERIC,
            schema=schema,
        )
        st.session_state.pop("draft_schema", None)
        st.success(f"조사를 만들었습니다. 조사 관리에서 확인한 뒤 배포하세요. (번호 {survey_id})")
        st.caption("배포 전에는 팀의 「본사요청 취합자료」에 나타나지 않습니다. AI 결과는 자동 배포되지 않습니다.")
