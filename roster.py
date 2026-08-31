from __future__ import annotations

import streamlit as st

from src.config import COMPANIES, EMPLOYMENT_TYPES, ROLE_ADMIN, SUBMITTING_TEAMS, primary_role
from src.excel_io import build_employee_template, parse_employee_roster
from src.store import AccessDenied, list_employees, replace_employee_roster
from src.views.roster_edit import render_team_roster_editor


def render_roster_manager(username: str) -> None:
    if primary_role(username) != ROLE_ADMIN:
        render_team_roster_editor(username)
        return
    _render_admin_roster(username)


def _employee_table(rows: list[dict]) -> None:
    st.dataframe(
        [
            {
                "성명": item["name"],
                "회사": item["company"],
                "팀": item["team"],
                "고용형태": item["employment_type"],
            }
            for item in rows
        ],
        hide_index=True,
        width="stretch",
    )


def _render_admin_roster(username: str) -> None:
    st.subheader("재직인원 명부")
    st.caption("양식을 받아 성명·회사·팀·고용형태를 적은 뒤, 같은 화면에서 엑셀을 올리면 전체 명부가 바뀝니다.")

    current = list_employees(username)
    down_col, current_col = st.columns(2)
    with down_col:
        st.download_button(
            "재직인원 양식 다운받기",
            data=build_employee_template([]),
            file_name="재직인원_양식.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="dl_roster_template",
        )
    with current_col:
        st.download_button(
            "현재 재직인원 엑셀 받기",
            data=build_employee_template(current),
            file_name="재직인원_전체.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="dl_roster_current",
            disabled=not current,
        )

    uploaded = st.file_uploader("재직인원 엑셀 업로드", type=["xlsx"], key="up_roster")
    if uploaded is not None:
        parsed = parse_employee_roster(uploaded.getvalue())
        if parsed.errors:
            st.error("아래 행은 반영되지 않습니다.")
            for item in parsed.errors:
                st.write(f"- {item}")
        if parsed.rows:
            st.success(f"유효한 인원 {len(parsed.rows)}명")
            _employee_table(parsed.rows)
            replace_ok = st.checkbox("기존 명부를 이 파일로 바꿉니다", key="confirm_roster_replace")
            if st.button("명부 반영", type="primary", key="apply_roster"):
                if not replace_ok:
                    st.error("확인 체크를 한 뒤에 반영해 주세요.")
                else:
                    try:
                        count = replace_employee_roster(username, parsed.rows)
                        st.success(f"명부 {count}명을 반영했습니다.")
                        st.rerun()
                    except AccessDenied as exc:
                        st.error(str(exc))
        elif not parsed.errors:
            st.warning("파일에서 인원을 읽지 못했습니다.")

    st.markdown("**현재 전체 명부**")
    if not current:
        st.info("아직 명부가 없습니다. 「재직인원 양식 다운받기」로 양식을 받아 올린 뒤 확인하세요.")
        st.caption(
            f"회사: {' · '.join(COMPANIES)} / 팀: {' · '.join(SUBMITTING_TEAMS)} / 고용형태: {' · '.join(EMPLOYMENT_TYPES)}"
        )
    else:
        teams = ["전체"] + SUBMITTING_TEAMS
        selected = st.selectbox("표시 팀", teams, key="admin_roster_filter")
        shown = current if selected == "전체" else [item for item in current if item["team"] == selected]
        st.caption(
            f"표시 {len(shown)}명 · 전체 {len(current)}명 · "
            f"회사 {len({item['company'] for item in current})}곳 · 팀 {len({item['team'] for item in current})}개"
        )
        if shown:
            _employee_table(shown)
        else:
            st.info("이 팀에 등록된 인원이 없습니다.")

    st.divider()
    render_team_roster_editor(username, allow_all_teams=True)
