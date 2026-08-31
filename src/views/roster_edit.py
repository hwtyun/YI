from __future__ import annotations

import streamlit as st

from src.config import COMPANIES, EMPLOYMENT_TYPES, ROLE_ADMIN, SUBMITTING_TEAMS, get_user, primary_role
from src.store import AccessDenied, add_employee, delete_employee, list_employees


def render_team_roster_editor(username: str, allow_all_teams: bool = False) -> None:
    user = get_user(username)
    role = primary_role(username)
    own_team = user.get("team")
    can_pick_team = allow_all_teams and role == ROLE_ADMIN

    if can_pick_team:
        st.subheader("개별 추가 · 삭제")
        st.caption("엑셀 없이 한 명씩 넣거나 지울 때 사용합니다. 팀은 목록에서 고릅니다.")
        default_team = own_team or SUBMITTING_TEAMS[0]
        team = st.selectbox(
            "팀",
            SUBMITTING_TEAMS,
            index=SUBMITTING_TEAMS.index(default_team) if default_team in SUBMITTING_TEAMS else 0,
            key="roster_edit_team",
        )
    else:
        team = str(own_team or "")
        st.subheader("인원 명부")
        st.caption(f"**{team}** 인원만 보고, 추가·삭제할 수 있습니다. 다른 팀 명부는 바꿀 수 없습니다.")
        st.write(f"팀: **{team}**")

    with st.form("add_employee_form"):
        name = st.text_input("성명")
        company = st.selectbox("회사", COMPANIES)
        employment = st.selectbox("고용형태", EMPLOYMENT_TYPES)
        added = st.form_submit_button("명부에 추가")
    if added:
        try:
            add_employee(username, name, str(company), str(team), str(employment))
            st.success(f"{name} 님을 {team} 명부에 넣었습니다. 특근인원 달력에서 바로 선택할 수 있습니다.")
            st.rerun()
        except (AccessDenied, ValueError) as exc:
            st.error(str(exc))

    rows = list_employees(username, team)
    if not rows:
        st.info("아직 이 팀 명부가 없습니다. 위에서 인원을 추가하세요.")
        return
    if not can_pick_team:
        st.markdown(f"**{team} 명단** · {len(rows)}명")
    st.dataframe(
        [
            {
                "회사": item["company"],
                "팀": item["team"],
                "성명": item["name"],
                "고용형태": item["employment_type"],
            }
            for item in rows
        ],
        hide_index=True,
        width="stretch",
    )
    labels = {
        f"{item['name']} · {item['company']} · {item['employment_type']}": int(item["id"])
        for item in rows
    }
    with st.form("delete_employee_form"):
        selected = st.selectbox("삭제할 인원", list(labels.keys()))
        removed = st.form_submit_button("명부에서 삭제")
    if removed:
        try:
            delete_employee(username, labels[str(selected)])
            st.success("명부에서 삭제했습니다.")
            st.rerun()
        except (AccessDenied, ValueError) as exc:
            st.error(str(exc))
