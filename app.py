"""용인공장 특근 인원 조사 취합 — 진입점.

실행: 프로젝트 폴더에서
    streamlit run app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
# Streamlit Cloud는 저장소를 /mount/src/<repo> 에 둡니다.
# 패키지 이름이 src 이면 /mount/src 와 충돌해 ModuleNotFoundError가 납니다.
sys.path.insert(0, str(ROOT))

# Streamlit은 app.py만 다시 읽고 src.* 는 옛 버전을 남긴다.
# auth/theme에 새 이름이 생기면 ImportError가 반복되므로 매 실행마다 비운다.
for _name in list(sys.modules):
    if _name == "src" or _name.startswith("src."):
        sys.modules.pop(_name, None)

import streamlit as st

from src.auth import get_authenticator, sign_in
from src.config import USERS
from src.db import init_db
from src.secrets_util import missing_secret_names, render_secrets_help
from src.theme import THEME_CSS, render_logo
from src.views.shell import render_signed_in

st.set_page_config(
    page_title="용인공장 특근 조사",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="collapsed",
)
init_db()


def _secrets_ready() -> bool:
    missing = missing_secret_names()
    if not missing:
        return True
    st.markdown(THEME_CSS, unsafe_allow_html=True)
    render_logo(160)
    st.title("용인공장 특근 인원 조사")
    render_secrets_help(missing)
    return False


def _authenticator():
    expiry = 30.0 if st.session_state.get("remember_login", True) else 0.0
    authenticator = get_authenticator(expiry)
    st.session_state["authenticator"] = authenticator
    return authenticator


def _restore_cookie(authenticator) -> None:
    if st.session_state.get("authentication_status"):
        return
    try:
        token = authenticator.cookie_controller.get_cookie()
    except Exception:
        return
    if token:
        authenticator.authentication_controller.login(token=token)


def _render_login(authenticator) -> None:
    st.markdown(THEME_CSS, unsafe_allow_html=True)
    render_logo(160)
    st.title("용인공장 특근 인원 조사")
    st.caption("아이디로 로그인한 뒤 본인 화면만 사용합니다. 휴대폰에서도 입력할 수 있습니다.")
    st.checkbox("로그인 상태 유지", value=True, key="remember_login")

    with st.form("yi_factory_login"):
        username = st.text_input("아이디")
        password = st.text_input("비밀번호", type="password")
        submitted = st.form_submit_button("로그인", type="primary")

    if submitted:
        if sign_in(authenticator, username, password):
            try:
                authenticator.cookie_controller.set_cookie()
            except Exception:
                pass
            st.rerun()
            return
        st.error("아이디 또는 비밀번호가 올바르지 않습니다.")
        return
    if st.session_state.get("authentication_status") is False:
        st.error("아이디 또는 비밀번호가 올바르지 않습니다.")
        return
    st.info("아이디와 비밀번호를 입력한 뒤 로그인하세요.")


def _render_app(authenticator) -> None:
    username = st.session_state.get("username")
    if not username or username not in USERS:
        st.error("로그인 정보를 확인할 수 없습니다. 다시 로그인하세요.")
        return
    render_signed_in(username, authenticator)


def main() -> None:
    if not _secrets_ready():
        return
    authenticator = _authenticator()
    _restore_cookie(authenticator)
    if st.session_state.get("authentication_status"):
        _render_app(authenticator)
        return
    _render_login(authenticator)


if __name__ == "__main__":
    main()
