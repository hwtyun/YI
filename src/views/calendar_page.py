from __future__ import annotations

from datetime import date

import streamlit as st

from src.config import CAFETERIA_MIN_HEADCOUNT, COMPANIES, cafeteria_operating
from src.holidays import is_red_day
from src.store import (
    AccessDenied,
    ensure_open_overtime_survey,
    list_employees,
    list_entries,
    list_factory_day_totals,
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


def _cell_html(
    day_num: int,
    dow: int,
    factory_count: int,
    in_range: bool,
    selected: bool,
    meal_count: int = 0,
    day: date | None = None,
) -> str:
    check_day = day or date(2000, 1, 3)
    css = "yi-sun" if is_red_day(check_day) else ("yi-sat" if dow == 6 else "yi-day")
    on = " yi-cell-on" if selected else ""
    if factory_count <= 0:
        meta = (
            "<span class='yi-tag yi-tag-spacer'>&nbsp;</span>"
            "<span class='yi-tag yi-tag-spacer'>&nbsp;</span>"
            "<span class='yi-tag yi-tag-spacer'>&nbsp;</span>"
        )
    else:
        cafe_on = cafeteria_operating(meal_count)
        line1 = f"<span class='yi-tag yi-tag-count'>특근 {factory_count}명</span>"
        line2 = f"<span class='yi-tag yi-tag-meal'>식수 {meal_count}명</span>"
        line3 = (
            "<span class='yi-tag yi-tag-cafe'>식당운영</span>"
            if cafe_on
            else "<span class='yi-tag yi-tag-off'>식당미운영</span>"
        )
        meta = f"{line1}{line2}{line3}"
    return (
        f"<div class='yi-cell{on}'>"
        f"<div class='{css} yi-cell-num'>{day_num}</div>"
        f"<div class='yi-cell-meta'>{meta}</div>"
        "</div>"
    )


def render_overtime_calendar(username: str, team: str | None, read_only: bool) -> None:
    st.header("특근인원")
    st.caption(
        "날짜를 누르면 그날 공장 전체 특근 명단을 볼 수 있습니다. "
        f"입력은 우리 팀만 가능합니다. 달력에는 특근인원과 식수인원을 따로 표시하며, 식수 {CAFETERIA_MIN_HEADCOUNT}명 이상이면 식당을 운영합니다."
    )

    today = date.today()
    if "cal_month" not in st.session_state:
        st.session_state["cal_month"] = _month_start(today)
    month_cursor: date = st.session_state["cal_month"]

    try:
        prev_col, month_col, next_col = st.columns([1.1, 2.2, 1.1], vertical_alignment="center")
    except TypeError:
        prev_col, month_col, next_col = st.columns([1.1, 2.2, 1.1])
    with prev_col:
        if st.button("이전달", key="cal_prev", width="stretch"):
            st.session_state["cal_month"] = _shift_month(month_cursor, -1)
            st.rerun()
    with month_col:
        label = f"{month_cursor.year}년 {month_cursor.month}월"
        html = (
            f"<div class='yi-cal-month' style='text-align:center;font-size:28px;font-weight:800;"
            f"color:#111111;-webkit-text-fill-color:#111111;opacity:1;"
            f"line-height:40px;margin:0;background:transparent;'>{label}</div>"
        )
        try:
            st.html(html)
        except Exception:
            st.markdown(
                f"<h2 style='text-align:center;margin:0.15rem 0;color:#000000;"
                f"-webkit-text-fill-color:#000000;font-size:28px;font-weight:800;'>"
                f"{label}</h2>",
                unsafe_allow_html=True,
            )
    with next_col:
        if st.button("다음달", key="cal_next", width="stretch"):
            st.session_state["cal_month"] = _shift_month(month_cursor, 1)
            st.rerun()

    survey = ensure_open_overtime_survey(username)
    factory_totals = list_factory_day_totals(username)
    factory_counts = {key: value["headcount"] for key, value in factory_totals.items()}
    factory_meals = {key: value["meals"] for key, value in factory_totals.items()}
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
                    meal_count = factory_meals.get(iso, 0)
                    st.markdown(
                        _cell_html(
                            day_num,
                            dow,
                            factory_count,
                            True,
                            selected == iso,
                            meal_count,
                            day,
                        ),
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
            st.info("달력에서 특근일을 선택하세요. 토요일은 파란색, 공휴일은 빨간색입니다.")
            st.markdown("</div>", unsafe_allow_html=True)
            return
        selected_day = date.fromisoformat(str(st.session_state["selected_date"]))
        weekday = "월화수목금토일"[selected_day.weekday()]
        st.subheader(f"{selected_day.month}/{selected_day.day} ({weekday})")
        factory_count = factory_counts.get(selected_day.isoformat(), 0)
        meal_count = factory_meals.get(selected_day.isoformat(), 0)
        team_count = team_counts.get(selected_day.isoformat(), 0)
        cafe = cafeteria_operating(meal_count)
        st.markdown(
            "<div class='yi-summary'>"
            f"<div class='yi-metric'><span>특근인원</span><b>{factory_count}명</b></div>"
            f"<div class='yi-metric'><span>식수인원</span><b>{meal_count}명</b></div>"
            f"<div class='yi-metric'><span>식당</span><b>{'운영' if cafe else '미운영'}</b></div>"
            f"<div class='yi-metric'><span>우리 팀</span><b>{(str(team_count) + '명') if team else '-'}</b></div>"
            "</div>",
            unsafe_allow_html=True,
        )
        if cafe:
            st.success(f"특근 {factory_count}명 · 식수 {meal_count}명 · 식당 운영 (식수 {CAFETERIA_MIN_HEADCOUNT}명 이상)")
        else:
            st.caption(f"식당은 식수인원 {CAFETERIA_MIN_HEADCOUNT}명부터 운영합니다.")
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
        _render_overtime_day_list(
            username,
            team,
            survey,
            selected_day.isoformat(),
            day_rows,
            read_only,
        )
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
                    work_date=selected_day.isoformat(),
                )
        st.markdown("</div>", unsafe_allow_html=True)


def _company_key(value: object) -> str:
    text = str(value or "").strip()
    return "" if text in {"", "-", "미지정"} else text


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


def _render_overtime_day_list(
    username: str,
    team: str | None,
    survey: dict,
    work_date: str,
    rows: list[dict],
    read_only: bool,
) -> None:
    overtime = [item for item in rows if float(item.get("work_hours") or 0) > 0]
    st.markdown("**공장 전체 특근 명단**")
    if not overtime:
        st.caption("아직 특근 인원이 없습니다.")
        return
    own_rows = [item for item in overtime if team and str(item.get("team") or "") == team]
    if read_only or not team or not own_rows:
        _render_readonly_list(overtime)
        if team and not read_only and not own_rows:
            st.caption("우리 팀 인원이 없어 여기서 삭제할 항목이 없습니다.")
        return

    survey_id = int(survey["id"])
    can_edit, reason = survey_edit_status(username, survey_id)
    edited = st.data_editor(
        [
            {
                "삭제": False,
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
        disabled=["팀", "회사", "성명", "고용형태", "시간", "식수"],
        column_config={"삭제": st.column_config.CheckboxColumn("삭제", default=False)},
        key=f"cal_del_{survey_id}_{team}_{work_date}",
    )
    st.caption("우리 팀 인원만 체크한 뒤 삭제할 수 있습니다. 잘못 올린 특근을 여기서 지웁니다.")
    if not can_edit:
        st.warning(reason)
        return
    if not st.button("선택한 인원 삭제", key=f"cal_del_btn_{survey_id}_{team}_{work_date}"):
        return
    records = edited.to_dict("records") if hasattr(edited, "to_dict") else list(edited)
    picked = [row for row in records if bool(row.get("삭제"))]
    own_picked = [row for row in picked if str(row.get("팀") or "") == team]
    other_picked = [row for row in picked if str(row.get("팀") or "") != team]
    if other_picked:
        st.error("다른 팀 인원은 삭제할 수 없습니다. 우리 팀만 체크해 주세요.")
        return
    if not own_picked:
        st.warning("삭제할 우리 팀 인원을 체크하세요.")
        return
    remove = {
        (str(row.get("성명") or "").strip(), _company_key(row.get("회사")))
        for row in own_picked
    }
    existing = _team_entries(list_entries(username, survey_id), team)
    kept = []
    for item in existing:
        key = (str(item.get("name") or "").strip(), _company_key(item.get("company")))
        if str(item.get("work_date") or "") == work_date and key in remove:
            continue
        kept.append(item)
    try:
        replace_team_entries(username, survey_id, team, kept)
        for key in list(st.session_state.keys()):
            text = str(key)
            if text.startswith(
                (
                    f"cal_del_{survey_id}_{team}_{work_date}",
                    f"cal_roster_{survey_id}_{team}_{work_date}",
                    f"cal_manual_{survey_id}_{team}_{work_date}",
                )
            ):
                del st.session_state[key]
        st.success(f"{len(own_picked)}명을 삭제했습니다.")
        st.rerun()
    except AccessDenied as exc:
        st.error(str(exc))


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
