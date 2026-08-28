from __future__ import annotations

from datetime import date

import streamlit as st

from src.config import CAFETERIA_MIN_HEADCOUNT, COMPANIES, cafeteria_operating
from src.store import (
    AccessDenied,
    ensure_open_overtime_survey,
    list_employees,
    list_entries,
    list_factory_overtime_counts,
    list_overtime_people,
    replace_team_entries,
    set_submitted,
    survey_edit_status,
)
from src.views.survey_editor import (
    _manual_frame,
    _manual_to_entries,
    _render_excel_io,
    _roster_frame,
    _roster_to_entries,
)


def _month_start(value: date) -> date:
    return date(value.year, value.month, 1)


def _shift_month(value: date, delta: int) -> date:
    month = value.month - 1 + delta
    year = value.year + month // 12
    month = month % 12 + 1
    return date(year, month, 1)


def _sunday_first_weeks(year: int, month: int) -> list[list[int]]:
    import calendar

    return calendar.Calendar(firstweekday=6).monthdayscalendar(year, month)


def _counts_by_date(entries: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in entries:
        if float(item.get("work_hours") or 0) <= 0:
            continue
        key = str(item.get("work_date") or "")
        counts[key] = counts.get(key, 0) + 1
    return counts


def _team_entries(entries: list[dict], team: str | None) -> list[dict]:
    if not team:
        return []
    return [item for item in entries if str(item.get("team") or "") == team]


def _cell_html(day_num: int, dow: int, factory_count: int, in_range: bool, selected: bool) -> str:
    css = "yi-sun" if dow == 0 else ("yi-sat" if dow == 6 else "yi-day")
    on = " yi-cell-on" if selected else ""
    tags = []
    if factory_count:
        tags.append(f"<span class='yi-tag yi-tag-count'>{factory_count}명</span>")
    if cafeteria_operating(factory_count):
        tags.append("<span class='yi-tag yi-tag-cafe'>식당운영</span>")
    elif in_range and not factory_count:
        tags.append("<span class='yi-tag yi-tag-open'>입력</span>")
    return (
        f"<div class='yi-cell{on}'>"
        f"<div class='{css} yi-cell-num'>{day_num}</div>"
        f"{''.join(tags)}"
        "</div>"
    )


def render_overtime_calendar(username: str, team: str | None, read_only: bool) -> None:
    st.header("특근인원")
    st.caption(
        "날짜를 누르면 그날 공장 전체 특근 명단을 볼 수 있습니다. "
        f"입력은 우리 팀만 가능합니다. 달력 인원 수는 공장 전체이며, {CAFETERIA_MIN_HEADCOUNT}명 이상이면 식당을 운영합니다."
    )

    today = date.today()
    if "cal_month" not in st.session_state:
        st.session_state["cal_month"] = _month_start(today)
    month_cursor: date = st.session_state["cal_month"]

    nav1, nav2, nav3, nav4 = st.columns([1, 1, 1, 5])
    if nav1.button("이전달", key="cal_prev"):
        st.session_state["cal_month"] = _shift_month(month_cursor, -1)
        st.rerun()
    if nav2.button("오늘", key="cal_today"):
        st.session_state["cal_month"] = _month_start(today)
        st.session_state["selected_date"] = today.isoformat()
        st.rerun()
    if nav3.button("다음달", key="cal_next"):
        st.session_state["cal_month"] = _shift_month(month_cursor, 1)
        st.rerun()
    nav4.markdown(f"**{month_cursor.year}년 {month_cursor.month}월**")

    survey = ensure_open_overtime_survey(username)
    factory_counts = list_factory_overtime_counts(username)
    team_counts = _counts_by_date(
        [item for item in list_overtime_people(username) if team and str(item.get("team") or "") == team]
    )

    left, right = st.columns([7, 5], gap="large")
    with left:
        st.markdown('<div class="yi-card">', unsafe_allow_html=True)
        headers = ["일", "월", "화", "수", "목", "금", "토"]
        head_cols = st.columns(7)
        for index, label in enumerate(headers):
            css = "yi-sun" if index == 0 else ("yi-sat" if index == 6 else "yi-day")
            head_cols[index].markdown(
                f"<div class='{css}' style='text-align:center'>{label}</div>",
                unsafe_allow_html=True,
            )
        selected = st.session_state.get("selected_date")
        for week in _sunday_first_weeks(month_cursor.year, month_cursor.month):
            cols = st.columns(7)
            for dow, day_num in enumerate(week):
                with cols[dow]:
                    if day_num == 0:
                        st.write("")
                        continue
                    day = date(month_cursor.year, month_cursor.month, day_num)
                    iso = day.isoformat()
                    factory_count = factory_counts.get(iso, 0)
                    st.markdown(
                        _cell_html(day_num, dow, factory_count, True, selected == iso),
                        unsafe_allow_html=True,
                    )
                    clicked = st.button(
                        "열기",
                        key=f"cal_day_{iso}",
                        type="primary" if selected == iso else "secondary",
                        width="stretch",
                    )
                    if clicked:
                        st.session_state["selected_date"] = iso
                        st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="yi-card">', unsafe_allow_html=True)
        if not st.session_state.get("selected_date"):
            st.info("달력에서 특근일을 선택하세요. 토요일은 파란색입니다.")
            st.markdown("</div>", unsafe_allow_html=True)
            return
        selected_day = date.fromisoformat(str(st.session_state["selected_date"]))
        weekday = "월화수목금토일"[selected_day.weekday()]
        st.subheader(f"{selected_day.month}/{selected_day.day} ({weekday})")
        factory_count = factory_counts.get(selected_day.isoformat(), 0)
        team_count = team_counts.get(selected_day.isoformat(), 0)
        cafe = cafeteria_operating(factory_count)
        st.markdown(
            "<div class='yi-summary'>"
            f"<div class='yi-metric'><span>공장 전체</span><b>{factory_count}명</b></div>"
            f"<div class='yi-metric'><span>식당</span><b>{'운영' if cafe else '미운영'}</b></div>"
            f"<div class='yi-metric'><span>우리 팀</span><b>{(str(team_count) + '명') if team else '-'}</b></div>"
            "</div>",
            unsafe_allow_html=True,
        )
        if cafe:
            st.success(f"특근 {factory_count}명 · 식당 운영 ({CAFETERIA_MIN_HEADCOUNT}명 이상)")
        else:
            st.caption(f"식당은 특근 {CAFETERIA_MIN_HEADCOUNT}명부터 운영합니다.")
        day_rows = list_overtime_people(username, selected_day.isoformat())
        by_company: dict[str, int] = {}
        by_team: dict[str, int] = {}
        for item in day_rows:
            company = str(item.get("company") or "미지정")
            by_company[company] = by_company.get(company, 0) + 1
            team_name = str(item.get("team") or "미지정")
            by_team[team_name] = by_team.get(team_name, 0) + 1
        if by_team:
            chips = "".join(f"<span class='yi-chip'>{name} {count}명</span>" for name, count in by_team.items())
            st.markdown(chips, unsafe_allow_html=True)
        elif by_company:
            chips = "".join(f"<span class='yi-chip'>{name} {count}명</span>" for name, count in by_company.items())
            st.markdown(chips, unsafe_allow_html=True)
        st.markdown("**공장 전체 특근 명단**")
        _render_readonly_list(day_rows)
        if read_only:
            st.caption("공장장은 조회만 가능합니다.")
        elif team:
            st.divider()
            st.markdown(f"**{team} 입력**")
            st.caption("아래 명단만 저장됩니다. 위 전체 명단은 모든 팀이 볼 수 있습니다.")
            _render_team_date_editor(username, team, survey, selected_day.isoformat())
            with st.expander("엑셀로 올리기 · 받기"):
                _render_excel_io(
                    username,
                    team,
                    survey,
                    _team_entries(list_entries(username, int(survey["id"])), team),
                )
        st.markdown("</div>", unsafe_allow_html=True)


def _render_readonly_list(rows: list[dict]) -> None:
    overtime = [item for item in rows if float(item.get("work_hours") or 0) > 0]
    if not overtime:
        st.caption("아직 특근 인원이 없습니다.")
        return
    st.dataframe(
        [
            {
                "팀": item.get("team") or "",
                "회사": item.get("company") or "-",
                "성명": item.get("name") or "",
                "고용형태": item.get("employment_type") or "-",
                "시간": item.get("work_hours"),
                "식수": item.get("meal_count") if item.get("meal_count") is not None else "-",
            }
            for item in overtime
        ],
        hide_index=True,
        width="stretch",
    )


def _render_team_date_editor(username: str, team: str, survey: dict, work_date: str) -> None:
    survey_id = int(survey["id"])
    roster = list_employees(username, team)
    saved = [
        item
        for item in _team_entries(list_entries(username, survey_id), team)
        if str(item.get("work_date")) == work_date
    ]
    if not roster:
        st.info("팀 명부가 없습니다. 관리자메뉴에서 신규 인원을 먼저 넣으세요.")
    roster_edited = st.data_editor(
        _roster_frame(roster, saved),
        hide_index=True,
        width="stretch",
        disabled=["회사", "성명", "고용형태"],
        column_config={
            "특근": st.column_config.CheckboxColumn("특근", default=False),
            "근무시간": st.column_config.NumberColumn("시간", min_value=0, max_value=24, step=0.5),
            "식수인원": st.column_config.NumberColumn("식수", min_value=0, max_value=20, step=1),
            "비고": st.column_config.TextColumn("비고"),
        },
        key=f"cal_roster_{survey_id}_{team}_{work_date}",
    )
    st.caption("일용직 추가 — 명부에 없는 사람만 적습니다.")
    manual_edited = st.data_editor(
        _manual_frame(saved),
        num_rows="dynamic",
        hide_index=True,
        width="stretch",
        column_config={
            "회사": st.column_config.SelectboxColumn("회사", options=COMPANIES),
            "근무시간": st.column_config.NumberColumn("시간", min_value=0, max_value=24, step=0.5),
            "식수인원": st.column_config.NumberColumn("식수", min_value=0, max_value=20, step=1),
        },
        key=f"cal_manual_{survey_id}_{team}_{work_date}",
    )
    can_edit, reason = survey_edit_status(username, survey_id)
    if not can_edit:
        st.warning(reason)
        return
    roster_entries = _roster_to_entries(roster_edited, work_date, team)
    collected = roster_entries + _manual_to_entries(manual_edited, work_date, team, len(roster_entries) + 1)
    others = [
        item
        for item in _team_entries(list_entries(username, survey_id), team)
        if str(item.get("work_date")) != work_date
    ]
    merged = others + collected
    save_col, submit_col = st.columns(2)
    try:
        if save_col.button("저장", key=f"cal_save_{survey_id}_{work_date}"):
            replace_team_entries(username, survey_id, team, merged)
            st.success("저장했습니다.")
            st.rerun()
        if submit_col.button("제출", type="primary", key=f"cal_submit_{survey_id}_{work_date}"):
            replace_team_entries(username, survey_id, team, merged)
            set_submitted(username, survey_id, team, True)
            st.success("제출했습니다.")
            st.rerun()
    except AccessDenied as exc:
        st.error(str(exc))
