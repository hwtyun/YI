from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
import streamlit as st

from src.config import COMPANIES
from src.excel_io import (
    build_overtime_workbook,
    filter_entries_for_team,
    parse_overtime_workbook,
)
from src.store import (
    AccessDenied,
    enrich_entry_from_roster,
    list_employees,
    list_entries,
    replace_team_entries,
    set_submitted,
    survey_edit_status,
)

def _period_dates(survey: dict) -> list[str]:
    start = date.fromisoformat(str(survey["period_start"]))
    end = date.fromisoformat(str(survey["period_end"]))
    if end < start:
        return [start.isoformat()]
    days: list[str] = []
    cursor = start
    while cursor <= end:
        days.append(cursor.isoformat())
        cursor += timedelta(days=1)
    return days


def _empty_roster_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "회사": pd.Series(dtype="string"),
            "성명": pd.Series(dtype="string"),
            "고용형태": pd.Series(dtype="string"),
            "특근": pd.Series(dtype="bool"),
            "근무시간": pd.Series(dtype="float"),
            "식수인원": pd.Series(dtype="float"),
            "비고": pd.Series(dtype="string"),
        }
    )


def _empty_manual_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "성명": pd.Series(dtype="string"),
            "회사": pd.Series(dtype="string"),
            "근무시간": pd.Series(dtype="float"),
            "식수인원": pd.Series(dtype="float"),
            "비고": pd.Series(dtype="string"),
        }
    )


def _match_entry(entries: list[dict], employee: dict) -> dict | None:
    name = str(employee.get("name") or "").strip()
    company = str(employee.get("company") or "").strip()
    exact = [
        item
        for item in entries
        if str(item.get("name") or "").strip() == name
        and str(item.get("company") or "").strip() == company
        and not item.get("is_manual")
    ]
    if exact:
        return exact[0]
    by_name = [
        item
        for item in entries
        if str(item.get("name") or "").strip() == name and not item.get("is_manual")
    ]
    return by_name[0] if len(by_name) == 1 else None


def _roster_frame(roster: list[dict], saved: list[dict]) -> pd.DataFrame:
    if not roster:
        return _empty_roster_frame()
    rows = []
    for employee in roster:
        found = _match_entry(saved, employee)
        rows.append(
            {
                "회사": employee.get("company") or "",
                "성명": employee.get("name") or "",
                "고용형태": employee.get("employment_type") or "",
                "특근": found is not None,
                "근무시간": found["work_hours"] if found and found.get("work_hours") is not None else 8,
                "식수인원": found["meal_count"] if found and found.get("meal_count") is not None else 1,
                "비고": (found.get("note") or "") if found else "",
            }
        )
    return pd.DataFrame(rows)


def _manual_frame(saved: list[dict]) -> pd.DataFrame:
    manuals = [item for item in saved if item.get("is_manual")]
    if not manuals:
        return _empty_manual_frame()
    return pd.DataFrame(
        [
            {
                "성명": item.get("name") or "",
                "회사": item.get("company") or COMPANIES[0],
                "근무시간": item.get("work_hours") if item.get("work_hours") is not None else 8,
                "식수인원": item.get("meal_count") if item.get("meal_count") is not None else 1,
                "비고": item.get("note") or "",
            }
            for item in manuals
        ]
    )


def _na_text(value: object) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def _number_or_default(value: object, default: float) -> float:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _roster_to_entries(frame: pd.DataFrame, work_date: str, team: str) -> list[dict]:
    entries: list[dict] = []
    if frame is None or frame.empty:
        return entries
    for _, row in frame.iterrows():
        if not bool(row.get("특근")):
            continue
        name = _na_text(row.get("성명"))
        if not name:
            continue
        entries.append(
            {
                "seq_no": len(entries) + 1,
                "name": name,
                "company": _na_text(row.get("회사")) or None,
                "employment_type": _na_text(row.get("고용형태")) or None,
                "work_date": work_date,
                "work_hours": _number_or_default(row.get("근무시간"), 8),
                "meal_count": _number_or_default(row.get("식수인원"), 1),
                "note": _na_text(row.get("비고")) or None,
                "is_manual": 0,
                "team": team,
            }
        )
    return entries


def _manual_to_entries(frame: pd.DataFrame, work_date: str, team: str, start_seq: int) -> list[dict]:
    entries: list[dict] = []
    if frame is None or frame.empty:
        return entries
    for _, row in frame.iterrows():
        name = _na_text(row.get("성명"))
        if not name:
            continue
        entries.append(
            {
                "seq_no": start_seq + len(entries),
                "name": name,
                "company": _na_text(row.get("회사")) or COMPANIES[0],
                "employment_type": "일용직",
                "work_date": work_date,
                "work_hours": _number_or_default(row.get("근무시간"), 8),
                "meal_count": _number_or_default(row.get("식수인원"), 1),
                "note": _na_text(row.get("비고")) or None,
                "is_manual": 1,
                "team": team,
            }
        )
    return entries


def _render_excel_io(username: str, team: str, survey: dict, existing: list[dict]) -> None:
    survey_id = int(survey["id"])
    can_edit, reason = survey_edit_status(username, survey_id)
    year = date.fromisoformat(str(survey["period_start"])).year
    st.markdown("**엑셀**")
    st.caption("엑셀을 올리면 지금 적어 둔 내용이 파일 내용으로 바뀝니다.")
    down_col, up_col = st.columns(2)
    with down_col:
        st.download_button(
            "엑셀 받기",
            data=build_overtime_workbook(str(survey["title"]), existing),
            file_name=f"{team}_{survey['title']}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key=f"dl_team_{survey_id}_{team}",
        )
        st.caption("메일은 자동으로 가지 않습니다.")
    with up_col:
        uploaded = st.file_uploader(
            "엑셀 올리기",
            type=["xlsx"],
            key=f"up_team_{survey_id}_{team}",
        )
    if uploaded is None:
        return
    parsed = filter_entries_for_team(parse_overtime_workbook(uploaded.getvalue(), year), team)
    for warning in parsed.warnings:
        st.warning(warning)
    if not parsed.entries:
        st.error("파일에서 인원 행을 읽지 못했습니다.")
        return
    enriched = [enrich_entry_from_roster(item, team) for item in parsed.entries]
    st.dataframe(
        [
            {
                "일자": item["work_date"],
                "성명": item["name"],
                "회사": item.get("company") or "-",
                "고용형태": item.get("employment_type") or "-",
                "근무시간": item.get("work_hours"),
                "식수인원": item.get("meal_count"),
                "수기": "예" if item.get("is_manual") else "",
            }
            for item in enriched
        ],
        hide_index=True,
        width="stretch",
    )
    if not can_edit:
        st.warning(reason)
        return
    if st.button("이 내용으로 저장", key=f"apply_xlsx_{survey_id}_{team}"):
        try:
            replace_team_entries(username, survey_id, team, enriched)
            st.success(f"{len(enriched)}명을 엑셀에서 저장했습니다.")
            st.rerun()
        except AccessDenied as exc:
            st.error(str(exc))


def render_entry_editor(username: str, team: str, survey: dict) -> None:
    survey_id = int(survey["id"])
    dates_key = f"survey_dates_{survey_id}_{team}"
    existing = list_entries(username, survey_id)
    roster = list_employees(username, team)
    if dates_key not in st.session_state:
        dates = _period_dates(survey)
        extra = sorted({str(item["work_date"]) for item in existing if item["work_date"] not in dates})
        st.session_state[dates_key] = dates + extra

    st.caption(
        f"{team} · 이름 칸은 고칠 수 없습니다. 특근하는 사람만 표시하세요."
    )
    if not roster:
        st.info("명부가 없습니다. 관리자가 명부를 올리면 이름이 자동으로 나옵니다. 일용직은 아래 칸에 적으세요.")

    add_col, btn_col = st.columns([3, 1])
    with add_col:
        new_date = st.date_input(
            "특근일자 추가",
            value=date.fromisoformat(str(survey["period_start"])),
            key=f"add_date_{survey_id}_{team}",
        )
    with btn_col:
        st.write("")
        if st.button("일자 추가", key=f"add_date_btn_{survey_id}_{team}"):
            date_text = new_date.isoformat()
            current = list(st.session_state[dates_key])
            if date_text not in current:
                st.session_state[dates_key] = current + [date_text]
                st.rerun()

    grouped: dict[str, list[dict]] = {}
    for item in existing:
        grouped.setdefault(str(item["work_date"]), []).append(item)

    collected: list[dict] = []
    for work_date in list(st.session_state[dates_key]):
        with st.expander(f"특근일자 {work_date}", expanded=True):
            if st.button("이 일자 삭제", key=f"del_date_{survey_id}_{team}_{work_date}"):
                st.session_state[dates_key] = [
                    item for item in st.session_state[dates_key] if item != work_date
                ]
                st.rerun()
            saved = grouped.get(work_date, [])
            roster_edited = st.data_editor(
                _roster_frame(roster, saved),
                hide_index=True,
                width="stretch",
                disabled=["회사", "성명", "고용형태"],
                column_config={
                    "회사": st.column_config.TextColumn("회사"),
                    "성명": st.column_config.TextColumn("성명"),
                    "고용형태": st.column_config.TextColumn("고용형태"),
                    "특근": st.column_config.CheckboxColumn("특근", default=False),
                    "근무시간": st.column_config.NumberColumn("근무시간", min_value=0, max_value=24, step=0.5),
                    "식수인원": st.column_config.NumberColumn("식수인원", min_value=0, max_value=20, step=1),
                    "비고": st.column_config.TextColumn("비고"),
                },
                key=f"ed_roster_{survey_id}_{team}_{work_date}",
            )
            st.caption("일용직 수기 — 명부에 없는 사람만 적습니다. 고용형태는 일용직으로 저장됩니다.")
            manual_edited = st.data_editor(
                _manual_frame(saved),
                num_rows="dynamic",
                hide_index=True,
                width="stretch",
                column_config={
                    "성명": st.column_config.TextColumn("성명"),
                    "회사": st.column_config.SelectboxColumn("회사", options=COMPANIES),
                    "근무시간": st.column_config.NumberColumn("근무시간", min_value=0, max_value=24, step=0.5),
                    "식수인원": st.column_config.NumberColumn("식수인원", min_value=0, max_value=20, step=1),
                    "비고": st.column_config.TextColumn("비고"),
                },
                key=f"ed_manual_{survey_id}_{team}_{work_date}",
            )
            roster_entries = _roster_to_entries(roster_edited, work_date, team)
            collected.extend(roster_entries)
            collected.extend(_manual_to_entries(manual_edited, work_date, team, len(roster_entries) + 1))

    _render_excel_io(username, team, survey, existing)

    can_edit, reason = survey_edit_status(username, survey_id)
    if not can_edit:
        st.warning(reason)
        return

    save_col, submit_col = st.columns(2)
    try:
        if save_col.button("저장", key=f"save_{survey_id}_{team}"):
            replace_team_entries(username, survey_id, team, collected)
            st.success("저장했습니다. 특근에 표시한 인원과 일용직 수기만 남깁니다.")
        if submit_col.button("제출", type="primary", key=f"submit_{survey_id}_{team}"):
            replace_team_entries(username, survey_id, team, collected)
            set_submitted(username, survey_id, team, True)
            st.success("제출했습니다. 마감 전까지 다시 수정할 수 있습니다.")
    except AccessDenied as exc:
        st.error(str(exc))
