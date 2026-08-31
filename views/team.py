from __future__ import annotations

import streamlit as st

from src.config import get_user
from src.schema import is_generic
from src.store import list_submissions, list_surveys
from src.views.generic_editor import render_generic_editor
from src.views.survey_editor import render_entry_editor


def render_team_home(username: str) -> None:
    user = get_user(username)
    team = user["team"]
    st.header("팀 입력")
    st.caption(team)
    st.info("다른 팀 자료는 보이지 않습니다. 특근할 사람만 표시하거나 엑셀을 올리세요.")

    surveys = list_surveys(username)
    if not surveys:
        st.info("아직 배포된 조사가 없습니다. 관리자가 배포하면 여기에 입력창이 열립니다.")
        return

    labels = {f"{item['title']} ({item['period_start']}~{item['period_end']})": item for item in surveys}
    selected = st.selectbox("조사 선택", list(labels.keys()))
    survey = labels[str(selected)]
    st.write(f"마감 {survey['deadline_at']}")

    subs = list_submissions(username, int(survey["id"]))
    if subs and subs[0]["is_submitted"]:
        st.caption("제출했습니다. 마감 전까지 다시 저장할 수 있습니다.")
    else:
        st.caption("저장 후 제출을 눌러 주세요.")

    if is_generic(survey):
        render_generic_editor(username, str(team), survey)
    else:
        render_entry_editor(username, str(team), survey)
