"""본사요청 취합 명단. 특근 재직명부와 별개로 조사마다 지정한다."""

from __future__ import annotations

import streamlit as st

from src.config import COMPANIES, EMPLOYMENT_TYPES, SUBMITTING_TEAMS
from src.schema import is_generic
from src.store import (
    AccessDenied,
    add_survey_roster_person,
    keep_survey_roster_company,
    list_survey_roster,
    overtime_people_not_on_survey,
    refill_survey_roster_from_employees,
    remove_survey_roster_person,
)


def render_survey_roster_editor(username: str, survey: dict) -> None:
    if not is_generic(survey):
        return
    survey_id = int(survey["id"])
    st.markdown("**본사요청 취합 명단**")
    st.caption(
        "특근인원 명부와 다른 자료입니다. 조사를 만들면 특근 명부 전체를 복사해 두고, "
        "여기서 빼거나 넣을 수 있습니다. 이 명단에 있는 팀·인원만 「본사요청 취합자료」에 나옵니다."
    )
    rows = list_survey_roster(username, survey_id)
    st.write(f"지정 {len(rows)}명 · 팀 {len({item['team'] for item in rows})}개")
    if rows:
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
    else:
        st.info("취합 명단이 비어 있습니다. 특근 명부에서 불러오거나 아래에서 추가하세요.")

    refill_col, mob_col, com_col = st.columns(3)
    if refill_col.button("특근 명부 전체로 채우기", key=f"hq_roster_refill_{survey_id}"):
        try:
            count = refill_survey_roster_from_employees(username, survey_id)
            st.success(f"특근 명부 {count}명을 이 조사 취합 명단으로 넣었습니다. 특근 명부는 그대로입니다.")
            st.rerun()
        except (AccessDenied, ValueError) as exc:
            st.error(str(exc))
    if mob_col.button("에이텍모빌리티만 남기기", key=f"hq_roster_mob_{survey_id}"):
        try:
            count = keep_survey_roster_company(username, survey_id, "에이텍모빌리티")
            st.success(f"에이텍모빌리티 {count}명만 남겼습니다.")
            st.rerun()
        except (AccessDenied, ValueError) as exc:
            st.error(str(exc))
    if com_col.button("에이텍컴퓨터만 남기기", key=f"hq_roster_com_{survey_id}"):
        try:
            count = keep_survey_roster_company(username, survey_id, "에이텍컴퓨터")
            st.success(f"에이텍컴퓨터 {count}명만 남겼습니다.")
            st.rerun()
        except (AccessDenied, ValueError) as exc:
            st.error(str(exc))

    leftover = overtime_people_not_on_survey(username, survey_id)
    add_col, del_col = st.columns(2)
    with add_col:
        st.markdown("**명단 추가**")
        leftover_labels = {
            f"{item['name']} · {item['company']} · {item['team']} · {item['employment_type']}": item
            for item in leftover
        }
        if leftover_labels:
            picked_add = st.selectbox(
                "특근 명부에서 추가",
                list(leftover_labels.keys()),
                key=f"hq_roster_add_pick_{survey_id}",
            )
            if st.button("선택 인원 추가", key=f"hq_roster_add_btn_{survey_id}"):
                item = leftover_labels[str(picked_add)]
                try:
                    add_survey_roster_person(
                        username,
                        survey_id,
                        item["name"],
                        item["company"],
                        item["team"],
                        item["employment_type"],
                    )
                    st.success(f"{item['name']} 님을 취합 명단에 넣었습니다.")
                    st.rerun()
                except (AccessDenied, ValueError) as exc:
                    st.error(str(exc))
        else:
            st.caption("특근 명부에 남은 인원이 없습니다. 아래에서 직접 넣을 수 있습니다.")
        with st.form(f"hq_roster_manual_{survey_id}"):
            name = st.text_input("성명")
            company = st.selectbox("회사", COMPANIES)
            team = st.selectbox("팀", SUBMITTING_TEAMS)
            employment = st.selectbox("고용형태", EMPLOYMENT_TYPES)
            added = st.form_submit_button("직접 추가")
        if added:
            try:
                add_survey_roster_person(
                    username, survey_id, name, str(company), str(team), str(employment)
                )
                st.success(f"{name} 님을 취합 명단에 넣었습니다. 특근 명부에는 넣지 않았습니다.")
                st.rerun()
            except (AccessDenied, ValueError) as exc:
                st.error(str(exc))
    with del_col:
        st.markdown("**명단 삭제**")
        labels = {
            f"{item['name']} · {item['company']} · {item['team']} · {item['employment_type']}": int(item["id"])
            for item in rows
        }
        if not labels:
            st.caption("삭제할 인원이 없습니다.")
        else:
            picked_del = st.selectbox(
                "삭제할 인원",
                list(labels.keys()),
                key=f"hq_roster_del_pick_{survey_id}",
            )
            if st.button("취합 명단에서 삭제", key=f"hq_roster_del_btn_{survey_id}"):
                try:
                    remove_survey_roster_person(username, survey_id, labels[str(picked_del)])
                    st.success("취합 명단에서 삭제했습니다. 특근 명부는 그대로입니다.")
                    st.rerun()
                except (AccessDenied, ValueError) as exc:
                    st.error(str(exc))
