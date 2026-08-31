from __future__ import annotations

import streamlit as st

from src.config import ROLE_DIRECTOR, get_user, primary_role
from src.schema import entry_schema, is_generic
from src.store import list_responses, list_surveys
from src.views.generic_editor import render_generic_editor


def _survey_choice_labels(surveys: list[dict]) -> dict[str, dict]:
    labels: dict[str, dict] = {}
    for index, item in enumerate(surveys, start=1):
        label = f"{index}. {item['title']} ({item['period_start']}~{item['period_end']})"
        if label in labels:
            label = f"{label} · {item['id']}"
        labels[label] = item
    return labels


def _pick_survey(surveys: list[dict], key: str) -> dict:
    labels = _survey_choice_labels(surveys)
    options = list(labels.keys())
    st.caption(f"배포된 본사 요청 {len(options)}건. 아래에서 골라 입력하세요.")
    selected = st.radio("조사 선택", options, key=key)
    return labels[str(selected)]


def render_hq_page(username: str) -> None:
    st.header("본사요청 취합자료")
    role = primary_role(username)
    user = get_user(username)
    team = user.get("team")
    surveys = [
        item
        for item in list_surveys(username)
        if is_generic(item) and item.get("is_published")
    ]
    st.caption("관리자가 배포한 본사 요청만 여기에 보입니다. 양식 만들기는 관리자메뉴에서 합니다.")

    if role == ROLE_DIRECTOR:
        if not surveys:
            st.info("배포된 본사 요청 취합이 없습니다.")
            return
        survey = _pick_survey(surveys, "hq_survey_select")
        st.write(f"마감 {survey['deadline_at']}")
        schema = entry_schema(survey.get("schema") or {"columns": []})
        rows = list_responses(username, int(survey["id"]))
        if not rows:
            st.caption("아직 입력이 없습니다.")
            return
        st.dataframe(
            [
                {
                    "출처팀": item.get("team") or "",
                    **{
                        str(column["label"]): (item.get("payload") or {}).get(column["key"])
                        for column in schema.get("columns") or []
                    },
                }
                for item in rows
            ],
            hide_index=True,
            width="stretch",
        )
        return

    if not team:
        st.info("이 계정에는 입력할 팀이 없습니다.")
        return
    st.subheader(f"{team} 입력")
    if not surveys:
        st.info("배포된 본사 요청 취합이 없습니다.")
        return
    survey = _pick_survey(surveys, "hq_survey_select")
    st.write(f"마감 {survey['deadline_at']}")
    render_generic_editor(username, str(team), survey)
