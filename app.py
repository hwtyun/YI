"""용인공장 특근 인원 조사 취합 — 진입점.

실행: 프로젝트 폴더에서
    streamlit run app.py

로그인 화면 함수는 이 파일에 둔다. Cloud가 src.theme 옛 모듈을 남기면
새 이름을 import할 때 ImportError가 나므로 src.theme에서 새 함수를 가져오지 않는다.
"""

from __future__ import annotations

import hashlib
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


def _parse_roster_bytes(data: bytes) -> dict:
    """성명·회사·팀·고용형태 양식. Cloud의 옛 src.config와 무관하게 동작한다."""
    from io import BytesIO

    from openpyxl import load_workbook

    def fold(value: str) -> str:
        return str(value or "").strip().replace(" ", "").replace("-", "").lower()

    company_map = {
        "에이텍모빌리티": "에이텍모빌리티",
        "모빌리티": "에이텍모빌리티",
        "aitechmobility": "에이텍모빌리티",
        "atecmobility": "에이텍모빌리티",
        "에이텍컴퓨터": "에이텍컴퓨터",
        "컴퓨터": "에이텍컴퓨터",
        "aitechcomputer": "에이텍컴퓨터",
        "ateccomputer": "에이텍컴퓨터",
    }
    team_map = {
        "구매팀": "구매팀",
        "구매": "구매팀",
        "제조팀": "제조팀",
        "제조": "제조팀",
        "생산관리팀": "생산관리팀",
        "생산관리": "생산관리팀",
        "용인공장": "생산관리팀",
        "공장": "생산관리팀",
        "품질보증팀": "품질보증팀",
        "품질보증": "품질보증팀",
        "품질팀": "품질보증팀",
        "생산기술파트": "생산기술파트",
        "생산기술": "생산기술파트",
        "생산기술팀": "생산기술파트",
        "자재파트": "자재파트",
        "자재": "자재파트",
        "자재팀": "자재파트",
    }
    emp_map = {
        "정규직": "정규직",
        "정규": "정규직",
        "계약직": "계약직",
        "계약": "계약직",
        "일용직": "일용직",
        "일용": "일용직",
    }

    def as_company(value: str) -> str | None:
        text = str(value or "").strip()
        if text in ("에이텍모빌리티", "에이텍컴퓨터"):
            return text
        return company_map.get(fold(text))

    def as_team(value: str) -> str | None:
        text = str(value or "").strip()
        if text in team_map.values():
            return text
        return team_map.get(fold(text)) or team_map.get(text)

    def as_employment(value: str) -> str:
        text = str(value or "").strip()
        if text in ("정규직", "계약직", "일용직"):
            return text
        mapped = emp_map.get(fold(text))
        return mapped or "정규직"

    workbook = load_workbook(BytesIO(data), data_only=True)
    sheet = workbook.active
    rows: list[dict] = []
    errors: list[str] = []
    header = None
    start = 2
    for index, row in enumerate(sheet.iter_rows(min_row=1, max_row=20, max_col=8, values_only=True), start=1):
        texts = [str(item or "").strip() for item in row]
        if "성명" in texts and "회사" in texts and "팀" in texts:
            header = texts
            start = index + 1
            break
    if header is None:
        return {"rows": [], "errors": ["성명·회사·팀 헤더를 찾지 못했습니다."]}
    name_col = header.index("성명")
    company_col = header.index("회사") if "회사" in header else 1
    team_col = header.index("팀") if "팀" in header else 2
    type_col = header.index("고용형태") if "고용형태" in header else 3
    seen: set[tuple[str, str, str]] = set()
    for excel_row, row in enumerate(sheet.iter_rows(min_row=start, max_col=8, values_only=True), start=start):
        values = list(row)

        def cell(idx: int) -> str:
            if idx >= len(values) or values[idx] is None:
                return ""
            return str(values[idx]).strip()

        name = cell(name_col)
        if not name or name == "안내" or name.startswith(("회사는", "팀은", "고용형태는", "자주", "고정")):
            continue
        company = as_company(cell(company_col))
        team_raw = cell(team_col)
        team = as_team(team_raw)
        employment = as_employment(cell(type_col))
        if company is None:
            errors.append(f"{excel_row}행 '{name}': 회사는 에이텍모빌리티 또는 에이텍컴퓨터여야 합니다.")
            continue
        if team is None:
            errors.append(f"{excel_row}행 '{name}': 팀을 확인할 수 없습니다. ({team_raw})")
            continue
        key = (name, company, team)
        if key in seen:
            errors.append(f"{excel_row}행 '{name}': 같은 회사·팀에 이름이 중복됩니다.")
            continue
        seen.add(key)
        rows.append(
            {"name": name, "company": company, "team": team, "employment_type": employment}
        )
    if not rows and not errors:
        errors.append("유효한 임직원 행이 없습니다.")
    return {"rows": rows, "errors": errors}


def _render_prodadmin_excel_roster(username: str) -> None:
    """Cloud가 옛 roster 화면만 읽어도, app.py만 올리면 엑셀 받기·올리기가 보이게 한다."""
    from src.config import COMPANIES, EMPLOYMENT_TYPES, ROLE_ADMIN, SUBMITTING_TEAMS, primary_role
    from src.excel_io import build_employee_template
    from src.store import AccessDenied, list_employees, replace_employee_roster

    if primary_role(username) != ROLE_ADMIN:
        return

    st.subheader("재직인원 명부")
    st.caption(
        "양식에 성명·회사·팀·고용형태를 적은 뒤 아래에서 엑셀만 올리면 바로 반영됩니다. "
        "고용형태에 직급(이사·책임·선임·사원 등)을 적어도 정규직으로 저장합니다."
    )
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

    st.session_state["_yi_excel_roster_shown"] = True

    uploaded = st.file_uploader("재직인원 엑셀 업로드", type=["xlsx"], key="app_up_roster")
    if uploaded is not None:
        raw = uploaded.getvalue()
        parsed = _parse_roster_bytes(raw)
        if parsed["errors"]:
            st.error("일부 행은 건너뛰었습니다.\n" + "\n".join(f"- {item}" for item in parsed["errors"]))
        rows = parsed["rows"]
        if rows:
            sig = hashlib.sha256(raw).hexdigest()
            if st.session_state.get("app_roster_sig") != sig:
                try:
                    count = replace_employee_roster(username, rows)
                    st.session_state["app_roster_sig"] = sig
                    st.success(f"재직인원 {count}명을 반영했습니다.")
                    st.rerun()
                except AccessDenied as exc:
                    st.error(str(exc))
            else:
                st.success(f"반영된 인원 {len(rows)}명")
                st.dataframe(
                    [
                        {
                            "성명": item["name"],
                            "회사": item["company"],
                            "팀": item["team"],
                            "고용형태": item["employment_type"],
                        }
                        for item in rows
                    ],
                    hide_index=True,
                    width="stretch",
                )
        elif not parsed["errors"]:
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
    try:
        import src.excel_io as excel_io
        from src.excel_io import RosterParseResult

        def patched_parse(data):
            raw = data if isinstance(data, bytes) else data.getvalue()
            parsed = _parse_roster_bytes(raw)
            return RosterParseResult(rows=parsed["rows"], errors=parsed["errors"])

        excel_io.parse_employee_roster = patched_parse
    except Exception:
        pass

    try:
        import src.views.roster as roster_mod

        def admin_roster(username: str) -> None:
            _render_prodadmin_excel_roster(username)
            st.divider()
            roster_mod.render_team_roster_editor(username, allow_all_teams=True)

        roster_mod._render_admin_roster = admin_roster
    except Exception:
        pass

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
