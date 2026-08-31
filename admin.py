from __future__ import annotations

from datetime import datetime, time

import streamlit as st

from src.auth import PASSWORD_RULE_HELP, reset_user_password_by_admin
from src.config import SUBMITTING_TEAMS, get_user
from src.excel_io import build_generic_workbook, build_overtime_workbook
from src.schedule import default_deadline, default_overtime_weekend, default_survey_title
from src.schema import empty_schema, entry_schema, is_generic
from src.store import (
    AccessDenied,
    create_survey,
    list_accounts,
    list_entries,
    list_responses,
    list_submissions,
    list_surveys,
    publish_survey,
    update_survey,
)
from src.views.generic_builder import render_generic_builder
from src.views.generic_editor import render_generic_editor
from src.views.review import render_review_home

ROLE_LABELS = {
    "admin": "최고 관리자",
    "director": "공장장",
    "team": "팀 담당자",
}
TYPE_LABELS = {"text": "텍스트", "number": "숫자", "date": "날짜"}
TYPE_VALUES = {value: key for key, value in TYPE_LABELS.items()}


def _as_date(value) -> datetime:
    from datetime import date as date_cls

    text = str(value or "")[:10]
    try:
        return datetime.strptime(text, "%Y-%m-%d")
    except ValueError:
        return datetime.combine(date_cls.today(), time.min)


def _as_time(value) -> time:
    text = str(value or "")
    clock = text.split("T", 1)[1][:8] if "T" in text else "11:00:00"
    parts = (clock + ":00:00").split(":")
    try:
        return time(int(parts[0]), int(parts[1]))
    except (TypeError, ValueError):
        return time(11, 0)


def _render_survey_edit(username: str, survey: dict) -> None:
    import pandas as pd

    survey_id = int(survey["id"])
    generic = is_generic(survey)
    schema = survey.get("schema") or empty_schema(str(survey.get("title") or ""))
    st.markdown("**조사 수정**")
    st.caption("배포된 조사도 제목·안내·양식·기간을 고칠 수 있습니다. 이미 입력한 값은 그대로 둡니다.")
    title = st.text_input("제목", value=str(survey.get("title") or ""), key=f"edit_title_{survey_id}")
    period_start = st.date_input(
        "조사 시작일",
        value=_as_date(survey.get("period_start")).date(),
        key=f"edit_start_{survey_id}",
    )
    period_end = st.date_input(
        "조사 종료일",
        value=_as_date(survey.get("period_end")).date(),
        key=f"edit_end_{survey_id}",
    )
    due_date = st.date_input(
        "마감일",
        value=_as_date(survey.get("deadline_at")).date(),
        key=f"edit_due_date_{survey_id}",
    )
    due_time = st.time_input(
        "마감 시각",
        value=_as_time(survey.get("deadline_at")),
        key=f"edit_due_time_{survey_id}",
    )
    schema_payload = None
    if generic:
        instructions = st.text_area(
            "내용",
            value=str(schema.get("instructions") or ""),
            key=f"edit_help_{survey_id}",
        )
        column_rows = [
            {
                "항목명": item.get("label") or "",
                "형식": TYPE_LABELS.get(str(item.get("type") or "text"), "텍스트"),
                "필수": bool(item.get("required", True)),
            }
            for item in schema.get("columns") or []
        ]
        if not column_rows:
            column_rows = [{"항목명": "", "형식": "텍스트", "필수": True}]
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
            key=f"edit_cols_{survey_id}",
        )
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
        schema_payload = {
            "title": title.strip(),
            "instructions": instructions.strip(),
            "columns": raw_columns,
        }
    else:
        st.caption("특근 조사는 제목과 기간만 고칩니다. 입력 칸은 달력 화면을 씁니다.")

    if st.button("수정 저장", type="primary", key=f"edit_save_{survey_id}"):
        try:
            if period_end < period_start:
                st.error("종료일은 시작일보다 빠를 수 없습니다.")
                return
            deadline_at = datetime.combine(due_date, due_time).strftime("%Y-%m-%dT%H:%M:%S")
            update_survey(
                username,
                survey_id,
                title.strip() or str(survey.get("title") or ""),
                period_start.isoformat(),
                period_end.isoformat(),
                deadline_at,
                schema=schema_payload,
            )
            st.success("조사를 수정했습니다. 팀 화면에도 바로 반영됩니다.")
            st.rerun()
        except (ValueError, AccessDenied) as exc:
            st.error(str(exc))


def render_admin_home(username: str) -> None:
    render_admin_tools(username)


def render_admin_tools(username: str) -> None:
    st.caption("본사 요청 배포·취합은 아래에서 합니다. 재직인원 엑셀은 위 명부에서 받거나 올립니다.")
    hq_tab, survey_tab, review_tab, account_tab = st.tabs(
        ["본사 요청 양식", "조사 관리", "제출 현황 · 취합", "계정"]
    )
    with hq_tab:
        render_generic_builder(username)
    with survey_tab:
        _render_survey_manager(username)
    with review_tab:
        render_review_home(username)
    with account_tab:
        _render_ops_guide()
        accounts = list_accounts()
        _render_accounts(accounts)
        _render_data_backup()
        _render_admin_password_reset(username, accounts)


def _render_survey_manager(username: str) -> None:
    saturday, sunday = default_overtime_weekend()
    st.subheader("새 조사 생성")
    with st.form("create_survey_form"):
        title = st.text_input("조사 제목", value=default_survey_title(saturday))
        start_col, end_col = st.columns(2)
        with start_col:
            period_start = st.date_input("조사 시작일", value=saturday)
        with end_col:
            period_end = st.date_input("조사 종료일", value=sunday)
        default_due = default_deadline(period_start if period_start.weekday() == 5 else saturday)
        due_date = st.date_input("마감일", value=default_due.date())
        due_time = st.time_input("마감 시각", value=time(11, 0))
        created = st.form_submit_button("조사 생성")

    if created:
        if period_end < period_start:
            st.error("종료일은 시작일보다 빠를 수 없습니다.")
        else:
            deadline_at = datetime.combine(due_date, due_time).strftime("%Y-%m-%dT%H:%M:%S")
            survey_id = create_survey(
                username,
                title.strip() or default_survey_title(period_start),
                period_start.isoformat(),
                period_end.isoformat(),
                deadline_at,
            )
            st.success(f"조사를 만들었습니다. 아래 목록에서 확인한 뒤 배포하세요. (번호 {survey_id})")

    surveys = list_surveys(username)
    published = sum(1 for item in surveys if item["is_published"])
    st.subheader("조사 목록")
    st.caption(f"저장 {len(surveys)}건 · 배포 {published}건 · 취합 대상: {' · '.join(SUBMITTING_TEAMS)}")
    if not surveys:
        st.info("아직 조사가 없습니다. 위에서 이번 주 조사를 생성하세요.")
        return

    for survey in surveys:
        status = "배포됨" if survey["is_published"] else "대기(미배포)"
        kind_label = "범용" if is_generic(survey) else "특근"
        with st.expander(f"[{status}] [{kind_label}] {survey['title']}", expanded=True):
            st.write(
                f"기간 {survey['period_start']} ~ {survey['period_end']} · 마감 {survey['deadline_at']}"
            )
            _render_survey_edit(username, survey)
            if survey["is_published"]:
                st.success("팀이 입력할 수 있습니다.")
                subs = list_submissions(username, int(survey["id"]))
                done = sum(1 for item in subs if item["is_submitted"])
                st.caption(f"제출 {done}/{len(SUBMITTING_TEAMS)} · 상세는 「제출 현황 · 취합」 탭에서 검토합니다.")
                if is_generic(survey):
                    all_rows = list_responses(username, int(survey["id"]))
                    st.download_button(
                        "전체 팀 원본 엑셀 받기",
                        data=build_generic_workbook(
                            str(survey["title"]),
                            entry_schema(survey.get("schema") or {"columns": []}),
                            [
                                {"source_team": item.get("team"), "team": item.get("team"), **(item.get("payload") or {})}
                                for item in all_rows
                            ],
                        ),
                        file_name=f"{survey['title']}_원본.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key=f"dl_admin_{survey['id']}",
                    )
                    if get_user(username)["team"]:
                        st.markdown("**생산관리팀 입력**")
                        render_generic_editor(username, str(get_user(username)["team"]), survey)
                else:
                    all_entries = list_entries(username, int(survey["id"]))
                    st.download_button(
                        "전체 팀 원본 엑셀 받기",
                        data=build_overtime_workbook(str(survey["title"]), all_entries, include_source_team=True),
                        file_name=f"{survey['title']}_원본.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key=f"dl_admin_{survey['id']}",
                    )
                    st.caption("원본에는 0시간 인원이 포함될 수 있습니다. 취합본은 검토 탭에서 받습니다. 메일은 보내지 않습니다.")
                    st.info("특근 인원은 상단 「특근인원」 달력에서 날짜를 눌러 입력합니다.")
            else:
                if is_generic(survey):
                    st.warning("배포 전에는 팀의 「본사요청 취합자료」에 나타나지 않습니다.")
                else:
                    st.caption("특근 입력은 달력에서 언제든지 가능합니다. 이 건을 배포하면 취합 탭에서도 모을 수 있습니다.")
                if st.button("배포", key=f"publish_btn_{survey['id']}"):
                    st.session_state["pending_publish_id"] = survey["id"]
                    st.rerun()

    pending_id = st.session_state.get("pending_publish_id")
    if pending_id:
        pending = next((item for item in surveys if item["id"] == pending_id), None)
        if pending:
            _confirm_publish_dialog(username, pending)


@st.dialog("배포하시겠습니까?")
def _confirm_publish_dialog(username: str, survey: dict) -> None:
    st.write(f"**{survey['title']}** 을(를) 팀에 배포합니다.")
    st.caption("본사 요청은 배포해야 팀이 기입합니다. 특근은 달력에서 이미 입력할 수 있습니다.")
    yes_col, no_col = st.columns(2)
    if yes_col.button("배포하기", type="primary"):
        publish_survey(username, int(survey["id"]))
        st.session_state.pop("pending_publish_id", None)
        st.rerun()
    if no_col.button("취소"):
        st.session_state.pop("pending_publish_id", None)
        st.rerun()


def _render_ops_guide() -> None:
    st.subheader("사용 안내")
    st.markdown(
        """
1. 특근: 달력에서 날짜를 눌러 입력합니다. 배포가 없어도 됩니다.  
2. 본사 요청: 양식 만들기 → **배포** 확인  
3. 취합 탭에서 **지금 취합** → 이상치 확인 → 엑셀 받기  
4. 엑셀을 검토한 뒤 공장장에게 **직접 메일** (자동 발송 없음)  
5. 파일럿 기간에는 기존 엑셀 취합과 **인원 수, 식수, 일자별 이름**을 대조하세요
        """.strip()
    )
    st.caption("아이디 7개: prodadmin, director, jejo, gumae, quality, tech, jajae. 비밀번호는 secrets에만 있고 메일은 보내지 않습니다.")


def _render_data_backup() -> None:
    from src.db import resolve_db_path

    path = resolve_db_path()
    st.subheader("데이터 백업")
    if path.exists():
        st.download_button(
            "저장 파일 받기",
            data=path.read_bytes(),
            file_name="yi_factory.db",
            mime="application/octet-stream",
            key="dl_db_backup",
        )
        st.caption("주기적으로 받아 두면 서버를 옮겨도 이어서 쓸 수 있습니다.")
    else:
        st.caption("아직 저장된 파일이 없습니다.")


def _render_accounts(accounts: list) -> None:
    st.subheader("계정 현황")
    if accounts:
        st.dataframe(
            [
                {
                    "아이디": item["username"],
                    "이름": item["display_name"] or "",
                    "역할": ROLE_LABELS.get(str(item["role"] or ""), item["role"]),
                    "팀": item["team"] or "-",
                }
                for item in accounts
            ],
            hide_index=True,
            width="stretch",
        )
    else:
        st.caption("아직 저장된 계정이 없습니다. 앱을 한 번 실행하면 계정이 DB에 저장됩니다.")


def _render_admin_password_reset(admin_username: str, accounts: list) -> None:
    others = [item for item in accounts if item["username"] != admin_username]
    st.subheader("다른 계정 비밀번호 초기화")
    st.caption("분실 시 사용합니다. 새 비밀번호는 해당 담당자에게 직접 알려 주세요. 메일은 보내지 않습니다.")
    if not others:
        st.caption("초기화할 다른 계정이 없습니다.")
        return

    labels = {
        f"{item['display_name'] or item['username']} ({item['username']})": item["username"]
        for item in others
    }
    with st.form("admin_reset_password_form"):
        selected_label = st.selectbox("대상 계정", list(labels.keys()))
        st.caption(PASSWORD_RULE_HELP)
        new_password = st.text_input("새 비밀번호", type="password")
        new_password_repeat = st.text_input("새 비밀번호 확인", type="password")
        submitted = st.form_submit_button("초기화")

    if submitted:
        error = reset_user_password_by_admin(
            admin_username,
            labels[str(selected_label)],
            new_password,
            new_password_repeat,
        )
        if error:
            st.error(error)
        else:
            st.success("비밀번호를 초기화했습니다. 대상자에게 새 비밀번호를 전달해 주세요.")
