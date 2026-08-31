"""용인공장 특근 인원 조사 취합 — 진입점.

실행: 프로젝트 폴더에서
    streamlit run app.py

로그인 화면 함수는 이 파일에 둔다. Cloud가 src.theme 옛 모듈을 남기면
새 이름을 import할 때 ImportError가 나므로 src.theme에서 새 함수를 가져오지 않는다.
"""

from __future__ import annotations

from pathlib import Path

try:
    from boot import bind_project_package
except ImportError:
    import sys

    def bind_project_package() -> Path:
        root = str(Path(__file__).resolve().parent)
        if root not in sys.path:
            sys.path.insert(0, root)
        return Path(root)

bind_project_package()

try:
    from branding import SITE_TITLE
except ImportError:
    SITE_TITLE = "용인공장 특근·본사요청 취합"

import streamlit as st

from src.auth import get_authenticator, sign_in
from src.config import USERS
from src.db import init_db
from src.secrets_util import missing_secret_names, render_secrets_help

st.set_page_config(
    page_title=SITE_TITLE,
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="collapsed",
)
init_db()

_ROOT = Path(__file__).resolve().parent
_LOGO_CANDIDATES = (
    _ROOT / "static" / "atec_ci.png",
    _ROOT / "ATEC 영문_기본형.png",
)
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
    color: #000000 !important;
    opacity: 1 !important;
    -webkit-text-fill-color: #000000 !important;
}
</style>
"""
_LOGIN_CSS = """
<style>
html, body, .stApp, [data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"] > section,
[data-testid="stMain"], [data-testid="stMainBlockContainer"],
.stMain, section.main, .main, .block-container,
[data-testid="stHeader"], header,
div[class*="st-key-yi_login"] {
    background: #ffffff !important;
    background-color: #ffffff !important;
    color-scheme: light !important;
}
.stApp, [data-testid="stAppViewContainer"] {
    --background-color: #ffffff !important;
    --secondary-background-color: #87CEEB !important;
    --st-background-color: #ffffff !important;
}
div[class*="st-key-yi_login"] h1,
div[class*="st-key-yi_login"] h2,
div[class*="st-key-yi_login"] p,
div[class*="st-key-yi_login"] label,
div[class*="st-key-yi_login"] span,
div[class*="st-key-yi_login"] [data-testid="stWidgetLabel"],
div[class*="st-key-yi_login"] [data-testid="stWidgetLabel"] *,
div[class*="st-key-yi_login"] [data-testid="stCheckbox"] p,
div[class*="st-key-yi_login"] [data-testid="stCheckbox"] span,
div[class*="st-key-yi_login"] [data-testid="stCheckbox"] label,
div[class*="st-key-yi_login"] [data-testid="stMarkdown"] p,
.yi-site-title, .yi-login-caption {
    color: #000000 !important;
    opacity: 1 !important;
    -webkit-text-fill-color: #000000 !important;
}
div[class*="st-key-yi_login"] [data-testid="stFormSubmitButton"] button,
div[class*="st-key-yi_login"] [data-testid="stFormSubmitButton"] p,
div[class*="st-key-yi_login"] [data-testid="stFormSubmitButton"] span {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
}
div[class*="st-key-yi_login"] [data-testid="stTextInput"] [data-baseweb="input"],
div[class*="st-key-yi_login"] [data-testid="stTextInput"] [data-baseweb="base-input"],
div[class*="st-key-yi_login"] [data-testid="stTextInput"] input,
div[class*="st-key-yi_login"] [data-testid="stTextInput"] > div > div {
    background: #87CEEB !important;
    background-color: #87CEEB !important;
    color: #000000 !important;
    -webkit-text-fill-color: #000000 !important;
    caret-color: #000000 !important;
}
div[class*="st-key-yi_login"] [data-testid="stTextInput"] button,
div[class*="st-key-yi_login"] [data-testid="stTextInput"] svg {
    color: #000000 !important;
    fill: #000000 !important;
}
</style>
"""


def _inject_css(css: str) -> None:
    try:
        st.html(css)
    except Exception:
        st.markdown(css, unsafe_allow_html=True)


def _inject_login_styles() -> None:
    _inject_css(_PAGE_TEXT_CSS)
    _inject_css(_LOGIN_CSS)


def _render_site_title() -> None:
    st.markdown(
        f'<h1 class="yi-site-title" style="color:#000000 !important;'
        f'-webkit-text-fill-color:#000000 !important;opacity:1 !important;'
        f'font-weight:700;font-size:2rem;margin:0.15rem 0 0.4rem 0;">'
        f"{SITE_TITLE}</h1>",
        unsafe_allow_html=True,
    )


def _render_login_caption() -> None:
    st.markdown(
        '<p class="yi-login-caption" style="color:#000000 !important;'
        '-webkit-text-fill-color:#000000 !important;opacity:1 !important;'
        'font-size:0.95rem;margin:0 0 0.7rem 0;">'
        "아이디로 로그인한 뒤 본인 화면만 사용합니다. 휴대폰에서도 입력할 수 있습니다.</p>",
        unsafe_allow_html=True,
    )


def _render_login_logo(width: int = 160) -> None:
    for path in _LOGO_CANDIDATES:
        if path.exists():
            st.image(str(path), width=width)
            return
    st.markdown('<div style="font-weight:700;color:#9b1c2e">ATEC</div>', unsafe_allow_html=True)


def _secrets_ready() -> bool:
    missing = missing_secret_names()
    if not missing:
        return True
    _inject_login_styles()
    _render_login_logo(160)
    _render_site_title()
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
    _inject_login_styles()
    with st.container(key="yi_login"):
        _render_login_logo(160)
        _render_site_title()
        _render_login_caption()
        st.checkbox("로그인 상태 유지", value=True, key="remember_login")

        with st.form("yi_factory_login"):
            username = st.text_input("아이디", key="login_username")
            password = st.text_input("비밀번호", type="password", key="login_password")
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


def _render_prodadmin_excel_roster(username: str) -> None:
    """Cloud가 옛 roster 화면만 읽어도, app.py만 올리면 엑셀 받기·올리기가 보이게 한다."""
    from src.config import COMPANIES, EMPLOYMENT_TYPES, ROLE_ADMIN, SUBMITTING_TEAMS, primary_role
    from src.excel_io import build_employee_template, parse_employee_roster
    from src.store import AccessDenied, list_employees, replace_employee_roster

    if primary_role(username) != ROLE_ADMIN:
        return

    st.subheader("재직인원 명부")
    st.caption("양식을 다운받아 성명·회사·팀·고용형태를 적은 다음, 아래에서 엑셀을 올리세요.")
    current = list_employees(username)
    left, right = st.columns(2)
    with left:
        st.download_button(
            "재직인원 양식 다운받기",
            data=build_employee_template([]),
            file_name="재직인원_양식.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="app_dl_roster_template",
        )
    with right:
        st.download_button(
            "현재 재직인원 엑셀 받기",
            data=build_employee_template(current),
            file_name="재직인원_전체.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="app_dl_roster_current",
            disabled=not current,
        )

    uploaded = st.file_uploader("재직인원 엑셀 업로드", type=["xlsx"], key="app_up_roster")
    if uploaded is not None:
        parsed = parse_employee_roster(uploaded.getvalue())
        if parsed.errors:
            st.error("아래 행은 반영되지 않습니다.")
            for item in parsed.errors:
                st.write(f"- {item}")
        if parsed.rows:
            st.success(f"유효한 인원 {len(parsed.rows)}명")
            st.dataframe(
                [
                    {
                        "성명": item["name"],
                        "회사": item["company"],
                        "팀": item["team"],
                        "고용형태": item["employment_type"],
                    }
                    for item in parsed.rows
                ],
                hide_index=True,
                width="stretch",
            )
            replace_ok = st.checkbox("기존 명부를 이 파일로 바꿉니다", key="app_confirm_roster_replace")
            if st.button("명부 반영", type="primary", key="app_apply_roster"):
                if not replace_ok:
                    st.error("확인 체크를 한 뒤에 반영해 주세요.")
                else:
                    try:
                        count = replace_employee_roster(username, parsed.rows)
                        st.success(f"명부 {count}명을 반영했습니다.")
                        st.rerun()
                    except AccessDenied as exc:
                        st.error(str(exc))
        elif not parsed.errors:
            st.warning("파일에서 인원을 읽지 못했습니다.")

    st.markdown("**현재 전체 재직인원**")
    if not current:
        st.info(
            "아직 명부가 없습니다. 「재직인원 양식 다운받기」로 양식을 받아 올린 뒤 확인하세요. "
            f"회사: {' · '.join(COMPANIES)} / 팀: {' · '.join(SUBMITTING_TEAMS)} / 고용형태: {' · '.join(EMPLOYMENT_TYPES)}"
        )
    else:
        st.caption(f"전체 {len(current)}명")
        st.dataframe(
            [
                {
                    "성명": item["name"],
                    "회사": item["company"],
                    "팀": item["team"],
                    "고용형태": item["employment_type"],
                }
                for item in current
            ],
            hide_index=True,
            width="stretch",
        )


def _install_admin_roster_patch() -> None:
    import src.views.roster_edit as roster_edit

    original = roster_edit.render_team_roster_editor
    if getattr(original, "_yi_excel_patched", False):
        return

    def wrapped(username, allow_all_teams=False, **kwargs):
        from src.config import ROLE_ADMIN, primary_role

        if primary_role(username) == ROLE_ADMIN and not st.session_state.get("_yi_excel_roster_shown"):
            _render_prodadmin_excel_roster(username)
            st.session_state["_yi_excel_roster_shown"] = True
            st.divider()
        try:
            return original(username, allow_all_teams=allow_all_teams, **kwargs)
        except TypeError:
            return original(username)

    wrapped._yi_excel_patched = True
    roster_edit.render_team_roster_editor = wrapped


def _render_app(authenticator) -> None:
    st.session_state.pop("_yi_excel_roster_shown", None)
    _install_admin_roster_patch()
    from src.views.shell import render_signed_in

    _inject_css(_PAGE_TEXT_CSS)
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
