from __future__ import annotations

import streamlit as st

from src.config import COMPANIES, EMPLOYMENT_TYPES, SUBMITTING_TEAMS
from src.excel_io import build_employee_template, parse_employee_roster
from src.store import AccessDenied, list_employees, replace_employee_roster


def render_roster_manager(username: str) -> None:
    st.subheader("임직원 명부")
    st.caption(
        "용인공장에서 같이 근무하는 에이텍모빌리티·에이텍컴퓨터 인원을 올립니다. "
        "팀은 웹에서 자기 팀 이름만 보고 특근 여부만 기입합니다."
    )
    st.write(
        "일용직은 자주 바뀌므로 매번 올리지 않아도 됩니다. "
        "고정 일용직만 명부에 넣으면 해당 팀 화면에 함께 나오고, 그 외는 팀이 수기로 추가합니다."
    )

    current = list_employees(username)
    down_col, up_col = st.columns(2)
    with down_col:
        st.download_button(
            "명부 양식 받기" if not current else "현재 명부 엑셀 받기",
            data=build_employee_template(current or None),
            file_name="임직원명부.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="dl_roster",
        )
    with up_col:
        uploaded = st.file_uploader("명부 엑셀 업로드 (전체 교체)", type=["xlsx"], key="up_roster")

    if uploaded is not None:
        parsed = parse_employee_roster(uploaded.getvalue())
        if parsed.errors:
            st.error("아래 행은 반영되지 않습니다.")
            for item in parsed.errors:
                st.write(f"- {item}")
        if parsed.rows:
            st.success(f"유효한 인원 {len(parsed.rows)}명")
            st.dataframe(
                [
                    {
                        "성명": item["name"],
                        "회사": item["company"],
                        "팀": item["team"],
                        "고용형태": item["employment_type"],
                    }
                    for item in parsed.rows
                ],
                hide_index=True,
                width="stretch",
            )
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

    st.markdown("**현재 명부**")
    if not current:
        st.info("아직 명부가 없습니다. 양식을 받아 성명·회사·팀·고용형태를 채운 뒤 업로드하세요.")
        st.caption(f"회사: {' · '.join(COMPANIES)} / 팀: {' · '.join(SUBMITTING_TEAMS)} / 고용형태: {' · '.join(EMPLOYMENT_TYPES)}")
        return

    st.caption(f"총 {len(current)}명 · 회사 {len({item['company'] for item in current})}곳 · 팀 {len({item['team'] for item in current})}개")
    st.dataframe(
        [
            {
                "성명": item["name"],
                "회사": item["company"],
                "팀": item["team"],
                "고용형태": item["employment_type"],
            }
            for item in current
        ],
        hide_index=True,
        width="stretch",
    )
