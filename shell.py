from __future__ import annotations

import streamlit as st

from src.config import ROLE_ADMIN, ROLE_DIRECTOR, get_user, primary_role
from src.theme import NAV_ADMIN, NAV_HQ, NAV_OVERTIME, NAV_PROFILE, THEME_CSS, render_logo

NAV_LABELS = {
    NAV_OVERTIME: "특근인원",
    NAV_HQ: "본사요청 취합자료",
    NAV_ADMIN: "관리자메뉴",
}


_PAGE_TEXT_CSS = """
<style>
[data-testid="stHeading"],
[data-testid="stHeading"] *,
[data-testid="stCaption"],
[data-testid="stCaption"] *,
[data-testid="stCaptionContainer"],
[data-testid="stCaptionContainer"] *,
[data-testid="stWidgetLabel"],
[data-testid="stWidgetLabel"] *,
.stHeading, .stHeading *,
.stCaption, .stCaption *,
h1, h2, h3, h4, h5, h6 {
    color: var(--yi-fg, #111111) !important;
    opacity: 1 !important;
    -webkit-text-fill-color: var(--yi-fg, #111111) !important;
}
html:not([data-theme="dark"]) [data-testid="stHeading"] *,
html:not([data-theme="dark"]) [data-testid="stWidgetLabel"] * {
    color: #000000 !important;
    -webkit-text-fill-color: #000000 !important;
}
html[data-theme="dark"] [data-testid="stHeading"] *,
html[data-theme="dark"] [data-testid="stWidgetLabel"] *,
html[data-theme="dark"] [data-testid="stCaption"] * {
    color: #f4f6f8 !important;
    -webkit-text-fill-color: #f4f6f8 !important;
}
html:not([data-theme="dark"]) input,
html:not([data-theme="dark"]) textarea,
html:not([data-theme="dark"]) select {
    color-scheme: light !important;
}
html[data-theme="dark"] input,
html[data-theme="dark"] textarea,
html[data-theme="dark"] select {
    color-scheme: dark !important;
}
[data-testid="stTextInput"] input,
[data-testid="stTextInput"] [data-baseweb="input"],
[data-testid="stTextInput"] [data-baseweb="base-input"],
[data-testid="stTextInput"] [data-baseweb="base-input"] > div,
[data-testid="stTextArea"] textarea,
[data-testid="stTextArea"] [data-baseweb="textarea"],
[data-testid="stTextArea"] [data-baseweb="base-input"],
[data-testid="stTextArea"] [data-baseweb="base-input"] > div,
[data-testid="stDateInput"] input,
[data-testid="stTimeInput"] input,
[data-testid="stNumberInput"] input,
[data-testid="stSelectbox"] [data-baseweb="select"] > div,
textarea {
    background-color: var(--yi-input-bg, #ffffff) !important;
    color: var(--yi-input-fg, #111111) !important;
    -webkit-text-fill-color: var(--yi-input-fg, #111111) !important;
    caret-color: var(--yi-input-fg, #111111) !important;
}
html[data-theme="dark"] [data-testid="stTextArea"] textarea,
html[data-theme="dark"] [data-testid="stTextArea"] [data-baseweb="base-input"],
html[data-theme="dark"] [data-testid="stTextArea"] [data-baseweb="base-input"] > div,
html[data-theme="dark"] [data-testid="stTextInput"] input,
html[data-theme="dark"] [data-testid="stDateInput"] input {
    background-color: #2b2f36 !important;
    color: #f4f6f8 !important;
    -webkit-text-fill-color: #f4f6f8 !important;
}
[data-testid="stDownloadButton"] button {
    background-color: #1f4e79 !important;
    border-color: #1f4e79 !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    opacity: 1 !important;
}
[data-testid="stDownloadButton"] button p,
[data-testid="stDownloadButton"] button span,
[data-testid="stDownloadButton"] button div {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
}
.yi-cal-month,
.yi-cal-month * {
    text-align: center !important;
    font-size: 1.7rem !important;
    font-weight: 700 !important;
    color: var(--yi-fg, #000000) !important;
    -webkit-text-fill-color: var(--yi-fg, #000000) !important;
    background: transparent !important;
    background-color: transparent !important;
    line-height: 2.4rem !important;
    margin: 0 !important;
}
</style>
"""


def inject_theme() -> None:
    try:
        from branding import inject_login_styles

        inject_login_styles()
    except ImportError:
        pass
    try:
        st.html(_PAGE_TEXT_CSS)
        st.html(THEME_CSS)
    except Exception:
        st.markdown(_PAGE_TEXT_CSS, unsafe_allow_html=True)
        st.markdown(THEME_CSS, unsafe_allow_html=True)


def _nav_items(role: str) -> list[tuple[str, str]]:
    items = [(NAV_LABELS[NAV_OVERTIME], NAV_OVERTIME), (NAV_LABELS[NAV_HQ], NAV_HQ)]
    if role != ROLE_DIRECTOR:
        items.append((NAV_LABELS[NAV_ADMIN], NAV_ADMIN))
    return items


def render_top_nav(username: str, authenticator) -> str:
    user = get_user(username)
    role = primary_role(username)
    current = str(st.session_state.get("nav", NAV_OVERTIME))
    items = _nav_items(role)
    allowed = {key for _, key in items}
    if current not in allowed and current != NAV_PROFILE:
        current = NAV_OVERTIME
        st.session_state["nav"] = current

    with st.container(
        horizontal=True,
        vertical_alignment="center",
        horizontal_alignment="distribute",
        gap="small",
        wrap=False,
        key="yi_topbar",
    ):
        with st.container(
            horizontal=True,
            vertical_alignment="center",
            gap="medium",
            wrap=False,
            width="content",
            key="yi_brand",
        ):
            render_logo(96)
            with st.container(
                horizontal=True,
                vertical_alignment="center",
                gap=4,
                wrap=False,
                width="content",
                key="yi_nav",
            ):
                for label, nav_key in items:
                    if st.button(label, type="tertiary", key=f"yi_nav_{nav_key}"):
                        st.session_state["nav"] = nav_key
                        st.rerun()

        with st.container(width="stretch", key="yi_spacer"):
            st.markdown('<div class="yi-spacer"></div>', unsafe_allow_html=True)
        with st.container(
            horizontal=True,
            vertical_alignment="center",
            horizontal_alignment="right",
            gap="small",
            wrap=False,
            width="content",
            key="yi_user",
        ):
            st.markdown(
                f"<div class='yi-hello'>안녕하세요, <strong>{user['display_name']}</strong>님</div>",
                unsafe_allow_html=True,
            )
            if st.button("정보수정", type="secondary", key="nav_profile"):
                st.session_state["nav"] = NAV_PROFILE
                st.rerun()
            authenticator.logout(button_name="로그아웃", location="main", key="yi_factory_logout")

    if current in allowed:
        st.markdown(
            f"<style>div[class*='st-key-yi_nav_{current}'] button {{"
            "color:#1a365d !important;font-weight:700 !important;"
            "border-bottom-color:#c41e3a !important;}}</style>",
            unsafe_allow_html=True,
        )
    return str(st.session_state.get("nav", current))


def render_signed_in(username: str, authenticator) -> None:
    inject_theme()
    nav = render_top_nav(username, authenticator)
    role = primary_role(username)
    user = get_user(username)
    if nav == NAV_OVERTIME:
        from src.views.calendar_page import render_overtime_calendar

        render_overtime_calendar(
            username,
            team=user.get("team"),
            read_only=role == ROLE_DIRECTOR,
        )
        return
    if nav == NAV_HQ:
        from src.views.hq import render_hq_page

        render_hq_page(username)
        return
    if nav == NAV_PROFILE:
        from src.views.account import render_profile_page

        render_profile_page(username)
        return
    if nav == NAV_ADMIN and role != ROLE_DIRECTOR:
        from src.views.admin import render_admin_tools
        from src.views.roster import render_roster_manager
        from src.views.roster_edit import render_team_roster_editor

        st.header("관리자메뉴")
        if role == ROLE_ADMIN:
            render_roster_manager(username)
            st.divider()
            render_admin_tools(username)
        else:
            render_team_roster_editor(username)
