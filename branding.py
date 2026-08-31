"""로그인 화면·사이트 제목. app.py는 src.theme의 새 이름을 쓰지 않는다."""

from __future__ import annotations

from pathlib import Path

SITE_TITLE = "용인공장 특근·본사요청 취합"
LOGIN_CAPTION = "아이디로 로그인한 뒤 본인 화면만 사용합니다. 휴대폰에서도 입력할 수 있습니다."

ROOT = Path(__file__).resolve().parent
LOGO_CANDIDATES = (
    ROOT / "static" / "atec_ci.png",
    ROOT / "ATEC 영문_기본형.png",
)

LOGIN_CSS = """
<style>
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


def inject_login_styles() -> None:
    import streamlit as st

    try:
        st.html(LOGIN_CSS)
    except Exception:
        st.markdown(LOGIN_CSS, unsafe_allow_html=True)


def render_site_title() -> None:
    import streamlit as st

    st.markdown(
        f'<h1 class="yi-site-title" style="color:#000000 !important;'
        f'-webkit-text-fill-color:#000000 !important;opacity:1 !important;'
        f'font-weight:700;font-size:2rem;margin:0.15rem 0 0.4rem 0;">'
        f"{SITE_TITLE}</h1>",
        unsafe_allow_html=True,
    )


def render_login_caption() -> None:
    import streamlit as st

    st.markdown(
        f'<p class="yi-login-caption" style="color:#000000 !important;'
        f'-webkit-text-fill-color:#000000 !important;opacity:1 !important;'
        f'font-size:0.95rem;margin:0 0 0.7rem 0;">{LOGIN_CAPTION}</p>',
        unsafe_allow_html=True,
    )


def render_login_logo(width: int = 160) -> None:
    import streamlit as st

    for path in LOGO_CANDIDATES:
        if path.exists():
            st.image(str(path), width=width)
            return
    st.markdown('<div style="font-weight:700;color:#9b1c2e">ATEC</div>', unsafe_allow_html=True)
