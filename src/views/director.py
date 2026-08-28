from __future__ import annotations

import streamlit as st

from src.aggregate import collect_overtime, date_totals, summarize_generic
from src.schema import is_generic
from src.store import list_overtime_entries, list_responses, list_surveys


def render_director_home(username: str) -> None:
    st.header("공장장")
    st.caption("조회만 가능합니다. 입력·배포는 할 수 없습니다.")

    surveys = list_surveys(username)
    st.subheader("배포된 조사")
    if not surveys:
        st.caption("아직 배포된 조사가 없습니다. 제출 현황과 원본 입력 데이터는 열람할 수 없습니다.")
        return

    labels = {f"{item['title']} ({item['period_start']}~{item['period_end']})": item for item in surveys}
    selected = st.selectbox("조사 선택", list(labels.keys()), key="director_survey_select")
    survey = labels[str(selected)]
    st.write(f"기간 {survey['period_start']} ~ {survey['period_end']} · 마감 {survey['deadline_at']}")
    st.caption("제출 현황·원본 입력·배포 권한은 없습니다.")

    if is_generic(survey):
        _render_generic(username, survey)
    else:
        _render_overtime(username, survey)
    st.caption("보고 메일은 생산관리팀이 검토한 뒤 전달합니다. 이 화면에서는 파일을 받거나 보낼 수 없습니다.")


def _render_overtime(username: str, survey: dict) -> None:
    st.caption("근무시간 0인 인원은 제외된 결과입니다.")
    overtime = collect_overtime(list_overtime_entries(username, int(survey["id"])))
    totals = date_totals(overtime)
    if totals:
        st.markdown("**일자별 합계**")
        st.dataframe(
            [
                {
                    "특근일자": item.work_date,
                    "특근인원": item.headcount,
                    "식수인원": item.meal_sum,
                    "근무시간합계": item.hours_sum,
                }
                for item in totals
            ],
            hide_index=True,
            width="stretch",
        )
    if overtime:
        st.markdown("**특근 인원**")
        st.dataframe(
            [
                {
                    "출처팀": item.get("source_team") or item.get("team") or "",
                    "회사": item.get("company") or "-",
                    "성명": item.get("name") or "",
                    "고용형태": item.get("employment_type") or "-",
                    "특근일자": item.get("work_date") or "",
                    "근무시간": item.get("work_hours"),
                    "식수인원": item.get("meal_count") if item.get("meal_count") is not None else "-",
                    "비고": item.get("note") or "",
                }
                for item in overtime
            ],
            hide_index=True,
            width="stretch",
        )
    else:
        st.info("아직 취합할 특근 인원이 없습니다.")


def _render_generic(username: str, survey: dict) -> None:
    schema = survey.get("schema") or {"columns": []}
    result = summarize_generic(schema, list_responses(username, int(survey["id"])), [])
    if result.rows:
        columns = list(schema.get("columns") or [])
        st.markdown("**취합 결과**")
        st.dataframe(
            [
                {
                    "출처팀": item.get("source_team") or item.get("team") or "",
                    **{str(column["label"]): item.get(column["key"]) for column in columns},
                }
                for item in result.rows
            ],
            hide_index=True,
            width="stretch",
        )
    else:
        st.info("아직 취합할 입력이 없습니다.")
