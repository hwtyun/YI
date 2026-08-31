from __future__ import annotations

import streamlit as st

from src.aggregate import Aggregation, GenericAggregation, summarize, summarize_generic
from src.excel_io import build_aggregate_workbook, build_generic_workbook
from src.schedule import is_past_deadline
from src.schema import entry_schema, is_generic
from src.store import list_entries, list_responses, list_submissions, list_surveys


def render_review_home(username: str) -> None:
    st.subheader("제출 현황 · 취합")
    st.caption("표를 확인한 뒤에만 엑셀을 받습니다. 메일은 자동으로 가지 않습니다.")
    surveys = [item for item in list_surveys(username) if item["is_published"]]
    if not surveys:
        st.info("배포된 조사가 없습니다. 조사 관리에서 배포한 뒤 여기서 취합하세요.")
        return

    labels = {f"{item['title']} ({item['period_start']}~{item['period_end']})": item for item in surveys}
    selected = st.selectbox("조사 선택", list(labels.keys()), key="review_survey_select")
    survey = labels[str(selected)]
    survey_id = int(survey["id"])
    past = is_past_deadline(str(survey["deadline_at"]))
    st.write(f"마감 {survey['deadline_at']} · {'마감됨' if past else '마감 전 (이후 제출이 더 들어올 수 있습니다)'}")
    submissions = list_submissions(username, survey_id)

    if is_generic(survey):
        result = summarize_generic(
            entry_schema(survey.get("schema") or {"columns": []}),
            list_responses(username, survey_id),
            submissions,
            past_deadline=past,
        )
        _render_generic_status(result)
        hint = "「지금 취합」을 누르면 팀 입력을 한 표로 모으고 이상치를 보여 줍니다."
    else:
        result = summarize(list_entries(username, survey_id), submissions, past_deadline=past)
        _render_overtime_status(result)
        hint = "「지금 취합」을 누르면 0시간 인원을 제외한 통합표와 이상치를 보여 줍니다."

    if st.button("지금 취합", type="primary", key=f"run_aggregate_{survey_id}"):
        st.session_state["aggregated_survey_id"] = survey_id
        st.session_state.pop(f"reviewed_{survey_id}", None)
        st.rerun()

    if st.session_state.get("aggregated_survey_id") != survey_id:
        st.info(hint)
        return

    if is_generic(survey):
        _render_generic_aggregation(survey, result, past)
    else:
        _render_aggregation(survey, result, past)


def _status_table(result: Aggregation | GenericAggregation, count_label: str) -> None:
    st.dataframe(
        [
            {
                "팀": item.team,
                "상태": item.label,
                "제출시각": item.submitted_at or "-",
                "저장행": item.saved_count,
                count_label: item.overtime_count,
            }
            for item in result.team_status
        ],
        hide_index=True,
        width="stretch",
    )


def _render_overtime_status(result: Aggregation) -> None:
    st.markdown(
        f"**제출 {result.submitted_count}/{result.team_count}** · "
        f"특근 {len(result.overtime)}명 · 0시간 제외 {result.excluded_zero}명"
    )
    _status_table(result, "특근인원")


def _render_generic_status(result: GenericAggregation) -> None:
    st.markdown(
        f"**제출 {result.submitted_count}/{result.team_count}** · 입력 {len(result.rows)}행"
    )
    _status_table(result, "입력행")


def _anomaly_table(anomalies: list) -> None:
    st.markdown("**이상치**")
    if anomalies:
        st.dataframe(
            [
                {
                    "수준": "오류" if item.level == "error" else "확인",
                    "내용": item.message,
                    "일자": item.work_date or "-",
                    "성명": item.name or "-",
                    "팀": item.team or "-",
                }
                for item in anomalies
            ],
            hide_index=True,
            width="stretch",
        )
    else:
        st.caption("표시할 이상치가 없습니다.")


def _download_gate(survey_id: int, data: bytes, filename: str) -> None:
    reviewed = st.checkbox("취합 결과를 검토했습니다", key=f"reviewed_{survey_id}")
    if not reviewed:
        st.caption("검토 확인을 해야 엑셀을 받을 수 있습니다. 시스템이 메일을 보내지는 않습니다.")
        return
    st.download_button(
        "취합 엑셀 받기",
        data=data,
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key=f"dl_aggregate_{survey_id}",
    )
    st.caption("받은 파일을 다시 확인한 뒤, 공장장에게 메일을 직접 보내 주세요.")


def _render_aggregation(survey: dict, result: Aggregation, past: bool) -> None:
    survey_id = int(survey["id"])
    errors = [item for item in result.anomalies if item.level == "error"]
    warnings = [item for item in result.anomalies if item.level != "error"]
    st.success("취합했습니다. 아래 표를 확인한 뒤 다운로드하세요. (사람 확인 단계)")
    if not past:
        st.warning("아직 마감 전입니다. 이후에 팀 입력이 바뀌면 다시 취합하세요.")

    metric_cols = st.columns(4)
    metric_cols[0].metric("특근 인원", len(result.overtime))
    metric_cols[1].metric("0시간 제외", result.excluded_zero)
    metric_cols[2].metric("오류", len(errors))
    metric_cols[3].metric("확인 필요", len(warnings))

    st.markdown("**일자별 합계**")
    if result.date_totals:
        st.dataframe(
            [
                {
                    "특근일자": item.work_date,
                    "특근인원": item.headcount,
                    "식수인원": item.meal_sum,
                    "근무시간합계": item.hours_sum,
                }
                for item in result.date_totals
            ],
            hide_index=True,
            width="stretch",
        )
    else:
        st.caption("특근 인원이 없습니다.")

    _anomaly_table(result.anomalies)
    st.markdown("**취합 결과 (출처팀 포함, 0시간 제외)**")
    if result.overtime:
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
                    "수기": "예" if item.get("is_manual") else "",
                }
                for item in result.overtime
            ],
            hide_index=True,
            width="stretch",
        )
    else:
        st.caption("취합할 특근 인원이 없습니다.")

    _download_gate(
        survey_id,
        build_aggregate_workbook(
            str(survey["title"]),
            result.overtime,
            result.date_totals,
            result.anomalies,
            result.team_status,
        ),
        f"{survey['title']}_취합.xlsx",
    )


def _render_generic_aggregation(survey: dict, result: GenericAggregation, past: bool) -> None:
    survey_id = int(survey["id"])
    schema = entry_schema(survey.get("schema") or {"columns": []})
    columns = list(schema.get("columns") or [])
    errors = [item for item in result.anomalies if item.level == "error"]
    warnings = [item for item in result.anomalies if item.level != "error"]
    st.success("취합했습니다. 아래 표를 확인한 뒤 다운로드하세요. (사람 확인 단계)")
    if not past:
        st.warning("아직 마감 전입니다. 이후에 팀 입력이 바뀌면 다시 취합하세요.")

    metric_cols = st.columns(3)
    metric_cols[0].metric("입력 행", len(result.rows))
    metric_cols[1].metric("오류", len(errors))
    metric_cols[2].metric("확인 필요", len(warnings))
    _anomaly_table(result.anomalies)
    st.markdown("**취합 결과 (출처팀 포함)**")
    if result.rows:
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
        st.caption("취합할 입력이 없습니다.")

    _download_gate(
        survey_id,
        build_generic_workbook(
            str(survey["title"]),
            schema,
            result.rows,
            result.anomalies,
            result.team_status,
        ),
        f"{survey['title']}_취합.xlsx",
    )
