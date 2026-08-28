from __future__ import annotations

import streamlit as st

from src.auth import PASSWORD_RULE_HELP, change_own_password


def render_password_change(username: str) -> None:
    render_profile_page(username)


def render_profile_page(username: str) -> None:
    st.header("정보수정")
    st.caption(PASSWORD_RULE_HELP)
    with st.form("change_password_form", clear_on_submit=False):
        current_password = st.text_input("현재 비밀번호", type="password")
        new_password = st.text_input("새 비밀번호", type="password")
        new_password_repeat = st.text_input("새 비밀번호 확인", type="password")
        submitted = st.form_submit_button("비밀번호 변경")

    if submitted:
        error = change_own_password(
            username,
            current_password,
            new_password,
            new_password_repeat,
        )
        if error:
            st.error(error)
        else:
            st.success("비밀번호를 변경했습니다. 다음 로그인부터 새 비밀번호를 사용하세요.")
