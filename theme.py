"""ATEC LGMS를 참고한 상단 메뉴·달력 화면 스타일."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

try:
    from branding import SITE_TITLE
except ImportError:
    SITE_TITLE = "용인공장 특근·본사요청 취합"

ROOT = Path(__file__).resolve().parent.parent
LOGO_CANDIDATES = (
    ROOT / "static" / "atec_ci.png",
    ROOT / "ATEC 영문_기본형.png",
)

NAV_OVERTIME = "overtime"
NAV_HQ = "hq"
NAV_ADMIN = "admin"
NAV_PROFILE = "profile"

THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700&display=swap');
html, body, .stApp, [data-testid="stAppViewContainer"] {
    font-family: "Noto Sans KR", sans-serif;
    direction: ltr !important;
}
html:not([data-theme="dark"]) .stApp,
html:not([data-theme="dark"]) [data-testid="stAppViewContainer"],
html:not([data-theme="dark"]) [data-testid="stMain"],
html:not([data-theme="dark"]) .stMain,
html:not([data-theme="dark"]) section.main,
html:not([data-theme="dark"]) .block-container {
    background: #ffffff !important;
    background-color: #ffffff !important;
    color: #000000;
    color-scheme: light !important;
    --text-color: #000000 !important;
    --textColor: #000000 !important;
    --background-color: #ffffff !important;
    --st-background-color: #ffffff !important;
}
html[data-theme="dark"] .stApp,
html[data-theme="dark"] [data-testid="stAppViewContainer"],
html[data-theme="dark"] [data-testid="stMain"],
html[data-theme="dark"] .stMain,
html[data-theme="dark"] section.main,
html[data-theme="dark"] .block-container {
    background: #1b1d21 !important;
    background-color: #1b1d21 !important;
    color: #f4f6f8 !important;
    color-scheme: dark !important;
    --text-color: #f4f6f8 !important;
    --textColor: #f4f6f8 !important;
    --background-color: #1b1d21 !important;
    --st-background-color: #1b1d21 !important;
}
html:not([data-theme="dark"]) [data-testid="stHeading"],
html:not([data-theme="dark"]) [data-testid="stHeading"] *,
html:not([data-theme="dark"]) [data-testid="stCaption"],
html:not([data-theme="dark"]) [data-testid="stCaption"] *,
html:not([data-theme="dark"]) [data-testid="stCaptionContainer"],
html:not([data-theme="dark"]) [data-testid="stCaptionContainer"] *,
html:not([data-theme="dark"]) [data-testid="stWidgetLabel"],
html:not([data-theme="dark"]) [data-testid="stWidgetLabel"] *,
html:not([data-theme="dark"]) .stHeading,
html:not([data-theme="dark"]) .stHeading *,
html:not([data-theme="dark"]) .stCaption,
html:not([data-theme="dark"]) .stCaption *,
html:not([data-theme="dark"]) h1,
html:not([data-theme="dark"]) h2,
html:not([data-theme="dark"]) h3,
html:not([data-theme="dark"]) h4,
html:not([data-theme="dark"]) h5,
html:not([data-theme="dark"]) h6 {
    color: #000000 !important;
    opacity: 1 !important;
    -webkit-text-fill-color: #000000 !important;
}
html[data-theme="dark"] [data-testid="stHeading"],
html[data-theme="dark"] [data-testid="stHeading"] *,
html[data-theme="dark"] [data-testid="stCaption"],
html[data-theme="dark"] [data-testid="stCaption"] *,
html[data-theme="dark"] [data-testid="stWidgetLabel"],
html[data-theme="dark"] [data-testid="stWidgetLabel"] *,
html[data-theme="dark"] h1,
html[data-theme="dark"] h2,
html[data-theme="dark"] h3,
html[data-theme="dark"] h4,
html[data-theme="dark"] h5,
html[data-theme="dark"] h6 {
    color: #f4f6f8 !important;
    opacity: 1 !important;
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
.yi-site-title, .yi-login-caption {
    color: #000000 !important;
    opacity: 1 !important;
    -webkit-text-fill-color: #000000 !important;
}
.yi-site-title {
    font-weight: 700 !important;
    font-size: 2rem !important;
    margin: 0.15rem 0 0.4rem 0 !important;
}
.yi-login-caption {
    font-size: 0.95rem !important;
    margin: 0 0 0.7rem 0 !important;
}
div[class*="st-key-yi_login"] h1,
div[class*="st-key-yi_login"] h2,
div[class*="st-key-yi_login"] p,
div[class*="st-key-yi_login"] label,
div[class*="st-key-yi_login"] span,
div[class*="st-key-yi_login"] [data-testid="stHeading"] *,
div[class*="st-key-yi_login"] [data-testid="stCaption"] *,
div[class*="st-key-yi_login"] [data-testid="stCaptionContainer"] *,
div[class*="st-key-yi_login"] [data-testid="stWidgetLabel"],
div[class*="st-key-yi_login"] [data-testid="stWidgetLabel"] *,
div[class*="st-key-yi_login"] [data-testid="stCheckbox"] p,
div[class*="st-key-yi_login"] [data-testid="stCheckbox"] span,
div[class*="st-key-yi_login"] [data-testid="stCheckbox"] label,
div[class*="st-key-yi_login"] [data-testid="stMarkdown"] p {
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
div[class*="st-key-yi_login"] [data-testid="stTextInput"] input:-webkit-autofill,
div[class*="st-key-yi_login"] [data-testid="stTextInput"] input:-webkit-autofill:focus {
    -webkit-box-shadow: 0 0 0 1000px #87CEEB inset !important;
    -webkit-text-fill-color: #000000 !important;
}
html[dir], body[dir], [dir="rtl"], [dir="auto"] {
    direction: ltr !important;
}
input, textarea,
[data-baseweb="input"],
[data-baseweb="input"] *,
[data-baseweb="base-input"],
[data-baseweb="base-input"] *,
[data-testid="stTextInput"],
[data-testid="stTextInput"] *,
[data-testid="stTextArea"],
[data-testid="stTextArea"] * {
    direction: ltr !important;
    unicode-bidi: bidi-override !important;
    text-align: left !important;
}
input[type="text"],
input[type="password"] {
    direction: ltr !important;
    unicode-bidi: bidi-override !important;
    text-align: left !important;
}
[data-testid="stSidebar"] { display: none; }
[data-testid="stHeader"] { display: none !important; }
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"],
[data-testid="stAppDeployButton"],
.stDeployButton,
.stAppDeployButton,
#MainMenu,
footer,
header,
[class*="viewerBadge"],
iframe[title="streamlit_menu"] {
    display: none !important;
    visibility: hidden !important;
    height: 0 !important;
    min-height: 0 !important;
    pointer-events: none !important;
}
.block-container { padding-top: 0.45rem; padding-bottom: 2.4rem; max-width: 1280px; }
div[class*="st-key-yi_topbar"] {
    background: #fff;
    border: 1px solid #e6eef6;
    border-radius: 14px;
    padding: 2px 14px 2px 10px !important;
    margin-bottom: 14px;
    box-shadow: 0 8px 24px rgba(26, 54, 93, 0.06);
    width: 100% !important;
}
.yi-spacer { display: none; }
div[class*="st-key-yi_topbar"] > div[data-testid="stHorizontalBlock"],
div[class*="st-key-yi_topbar"][data-testid="stHorizontalBlock"] {
    display: flex !important;
    align-items: center !important;
    justify-content: space-between !important;
    width: 100% !important;
    min-height: 48px;
}
div[class*="st-key-yi_brand"] [data-testid="stElementContainer"],
div[class*="st-key-yi_nav"] [data-testid="stElementContainer"],
div[class*="st-key-yi_user"] [data-testid="stElementContainer"] {
    width: auto !important;
    flex: 0 0 auto !important;
}
div[class*="st-key-yi_brand"] [data-testid="stHorizontalBlock"],
div[class*="st-key-yi_nav"] [data-testid="stHorizontalBlock"],
div[class*="st-key-yi_user"] [data-testid="stHorizontalBlock"],
div[class*="st-key-yi_brand"][data-testid="stHorizontalBlock"],
div[class*="st-key-yi_nav"][data-testid="stHorizontalBlock"],
div[class*="st-key-yi_user"][data-testid="stHorizontalBlock"] {
    align-items: center !important;
}
div[class*="st-key-yi_spacer"] {
    flex: 1 1 auto !important;
    min-width: 12px !important;
    width: auto !important;
}
div[class*="st-key-yi_topbar"] > div[data-testid="stHorizontalBlock"] > [data-testid="stElementContainer"]:last-child,
div[class*="st-key-yi_user"] {
    margin-left: auto !important;
}
div[class*="st-key-yi_user"] [data-testid="stHorizontalBlock"],
div[class*="st-key-yi_user"][data-testid="stHorizontalBlock"] {
    justify-content: flex-end !important;
}
div[class*="st-key-yi_user"] [data-testid="stMarkdown"],
div[class*="st-key-yi_user"] .stMarkdown,
div[class*="st-key-yi_brand"] [data-testid="stImage"] {
    margin: 0 !important;
    padding: 0 !important;
}
div[class*="st-key-yi_brand"] img {
    height: 26px !important;
    width: auto !important;
    max-width: 108px !important;
    object-fit: contain !important;
    display: block !important;
    margin: 0 !important;
}
div[class*="st-key-yi_brand"] [data-testid="stImage"] {
    margin: 0 !important;
    display: flex !important;
    align-items: center !important;
    min-height: 40px;
}
div[class*="st-key-yi_nav"] button {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    outline: none !important;
    border-radius: 0 !important;
    min-height: 40px !important;
    height: 40px !important;
    padding: 0 12px !important;
    font-size: 0.9rem !important;
    font-weight: 500 !important;
    color: #5b6b7c !important;
    letter-spacing: -0.02em !important;
    border-bottom: 2px solid transparent !important;
    border-top: 2px solid transparent !important;
}
div[class*="st-key-yi_nav"] button:hover {
    color: #1a365d !important;
    background: transparent !important;
    border-bottom-color: #c5d4e3 !important;
}
div[class*="st-key-yi_nav"] button[aria-pressed="true"],
div[class*="st-key-yi_nav_active"] button {
    color: #1a365d !important;
    font-weight: 700 !important;
    border-bottom-color: #c41e3a !important;
}
div[class*="st-key-yi_user"] [data-testid="stMarkdown"],
div[class*="st-key-yi_user"] [data-testid="stMarkdownContainer"],
div[class*="st-key-yi_user"] [data-testid="stButton"] {
    display: flex !important;
    align-items: center !important;
    min-height: 32px !important;
    height: 32px !important;
    margin: 0 !important;
}
div[class*="st-key-yi_user"] [data-testid="stMarkdownContainer"] p {
    margin: 0 !important;
    line-height: 32px !important;
}
.yi-hello {
    color: #5b6b7c;
    font-size: 0.84rem;
    white-space: nowrap;
    line-height: 32px;
    height: 32px;
    margin: 0;
    padding: 0 8px 0 0;
}
.yi-hello strong { color: #1a365d; font-weight: 700; }
div[class*="st-key-yi_user"] button {
    background: #fff !important;
    border: 1px solid #d7e3ef !important;
    box-shadow: none !important;
    border-radius: 8px !important;
    min-height: 32px !important;
    height: 32px !important;
    padding: 0 12px !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    color: #3d4f63 !important;
}
div[class*="st-key-yi_user"] button:hover {
    color: #1a5fb4 !important;
    border-color: #1a5fb4 !important;
    background: #fff !important;
}
.yi-cal-month,
.yi-cal-month * {
    text-align: center !important;
    font-size: 1.7rem !important;
    font-weight: 700 !important;
    color: #000000 !important;
    -webkit-text-fill-color: #000000 !important;
    background: transparent !important;
    background-color: transparent !important;
    line-height: 2.4rem !important;
    margin: 0 !important;
}
html[data-theme="dark"] .yi-cal-month,
html[data-theme="dark"] .yi-cal-month * {
    color: #f4f6f8 !important;
    -webkit-text-fill-color: #f4f6f8 !important;
}
.yi-card {
    background: #fff;
    border-radius: 16px;
    padding: 16px 18px 20px 18px;
    box-shadow: 0 8px 24px rgba(26, 54, 93, 0.06);
    border: 1px solid #e6eef6;
}
div[data-testid="stButton"] > button {
    border-radius: 10px !important;
    font-weight: 600 !important;
}
div[data-testid="stButton"] > button[kind="primary"],
[data-testid="stFormSubmitButton"] button,
[data-testid="stDownloadButton"] button,
[data-testid="stFileUploader"] button {
    background: #1a5fb4 !important;
    border: 1px solid #1a5fb4 !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
}
div[data-testid="stButton"] > button[kind="primary"] *,
[data-testid="stFormSubmitButton"] button *,
[data-testid="stDownloadButton"] button *,
[data-testid="stFileUploader"] button * {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
}
div[data-testid="stButton"] > button[kind="secondary"] {
    background: #fff !important;
    color: #1a365d !important;
    -webkit-text-fill-color: #1a365d !important;
    border: 1px solid #d7e3ef !important;
}
div[data-testid="stButton"] > button[kind="secondary"] * {
    color: #1a365d !important;
    -webkit-text-fill-color: #1a365d !important;
}
.yi-chip {
    display: inline-block;
    background: #eaf3fc;
    color: #1a5fb4;
    border-radius: 999px;
    padding: 4px 10px;
    margin: 0 6px 6px 0;
    font-size: 0.78rem;
    font-weight: 600;
}
.yi-sat { color: #1a5fb4; font-weight: 700; }
.yi-sun { color: #d94848; font-weight: 700; }
.yi-day { color: #243547; font-weight: 600; }
.yi-cell {
    height: 7.6rem;
    min-height: 7.6rem;
    max-height: 7.6rem;
    padding: 4px 2px 2px 2px;
    display: flex;
    flex-direction: column;
    box-sizing: border-box;
    overflow: hidden;
}
.yi-cell-num { text-align: center; font-size: 0.95rem; margin-bottom: 2px; flex: none; }
.yi-cell-meta {
    flex: 1;
    min-height: 4.4rem;
    display: flex;
    flex-direction: column;
    justify-content: flex-start;
    gap: 2px;
}
.yi-cell-on { background: #eaf3fc; border-radius: 10px; padding: 4px 2px 2px 2px; }
.yi-tag {
    display: block;
    border-radius: 8px;
    padding: 2px 4px;
    margin: 0 2px;
    font-size: 0.64rem;
    font-weight: 600;
    text-align: center;
    line-height: 1.3;
    overflow: hidden;
}
.yi-tag-spacer { visibility: hidden; background: transparent !important; }
[data-testid="stMarkdownContainer"]:has(.yi-cell) {
    min-height: 7.6rem;
}
[data-testid="stMarkdownContainer"]:has(.yi-cell) p {
    margin: 0 !important;
}
.yi-tag-count { background: #e8f1fb; color: #1a5fb4; }
.yi-tag-meal { background: #fff4e5; color: #b35c00; }
.yi-tag-cafe { background: #e7f6ee; color: #1b7a45; }
.yi-tag-off { background: #f4f6f8; color: #7a8794; }
.yi-tag-open { background: #f4f7fb; color: #6a7b8c; }
.yi-summary {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    margin: 8px 0 12px 0;
}
.yi-metric {
    flex: 1;
    min-width: 108px;
    background: #f6f9fc;
    border-radius: 12px;
    padding: 10px 12px;
}
.yi-metric b { display: block; font-size: 1.15rem; color: #1a5fb4; }
.yi-metric span { color: #6a7b8c; font-size: 0.75rem; }
div[data-testid="stMetric"] { background: #f6f9fc; border-radius: 12px; padding: 8px; }
div[class*="st-key-yi_nav"] button {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    outline: none !important;
    border-radius: 0 !important;
    min-height: 40px !important;
    height: 40px !important;
    padding: 0 12px !important;
    font-size: 0.9rem !important;
    font-weight: 500 !important;
    color: #5b6b7c !important;
    letter-spacing: -0.02em !important;
    border-bottom: 2px solid transparent !important;
    border-top: 2px solid transparent !important;
}
div[class*="st-key-yi_nav"] button:hover {
    color: #1a365d !important;
    background: transparent !important;
    border-bottom-color: #c5d4e3 !important;
}
div[class*="st-key-yi_user"] button {
    background: #fff !important;
    border: 1px solid #d7e3ef !important;
    box-shadow: none !important;
    border-radius: 8px !important;
    min-height: 32px !important;
    height: 32px !important;
    padding: 0 12px !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    color: #3d4f63 !important;
}
div[class*="st-key-yi_user"] button:hover {
    color: #1a5fb4 !important;
    border-color: #1a5fb4 !important;
    background: #fff !important;
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
[data-testid="stTextInput"] [data-baseweb="input"],
[data-testid="stNumberInput"] [data-baseweb="input"],
[data-testid="stDateInput"] [data-baseweb="input"],
[data-testid="stTimeInput"] [data-baseweb="input"],
[data-testid="stSelectbox"] [data-baseweb="select"] > div,
[data-testid="stTextArea"] [data-baseweb="textarea"] {
    background-color: #ffffff !important;
    border: 1px solid #c5d4e3 !important;
    border-radius: 8px !important;
    box-shadow: none !important;
    overflow: hidden !important;
}
html[data-theme="dark"] [data-testid="stTextInput"] [data-baseweb="input"],
html[data-theme="dark"] [data-testid="stTextArea"] [data-baseweb="textarea"],
html[data-theme="dark"] [data-testid="stSelectbox"] [data-baseweb="select"] > div {
    background-color: #2b2f36 !important;
    border: 1px solid #3d4450 !important;
}
[data-testid="stTextInput"] [data-baseweb="base-input"],
[data-testid="stTextInput"] [data-baseweb="base-input"] > div,
[data-testid="stTextArea"] [data-baseweb="base-input"],
[data-testid="stTextArea"] [data-baseweb="base-input"] > div {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input,
[data-testid="stDateInput"] input,
[data-testid="stTimeInput"] input,
[data-testid="stSelectbox"] input,
[data-testid="stTextArea"] textarea {
    -webkit-appearance: none !important;
    appearance: none !important;
    background: transparent !important;
    color: #111111 !important;
    -webkit-text-fill-color: #111111 !important;
    caret-color: #111111 !important;
    border: none !important;
    outline: none !important;
    box-shadow: none !important;
}
html[data-theme="dark"] [data-testid="stTextInput"] input,
html[data-theme="dark"] [data-testid="stTextArea"] textarea,
html[data-theme="dark"] [data-testid="stDateInput"] input,
html[data-theme="dark"] [data-testid="stSelectbox"] input {
    color: #f4f6f8 !important;
    -webkit-text-fill-color: #f4f6f8 !important;
    caret-color: #f4f6f8 !important;
}
[data-testid="InputInstructions"],
[data-testid="InputInstructions"] * {
    color: #3d4a57 !important;
}
html[data-theme="dark"] [data-testid="InputInstructions"],
html[data-theme="dark"] [data-testid="InputInstructions"] * {
    color: #c5ccd4 !important;
}
html[data-theme="dark"] .yi-day,
html[data-theme="dark"] .yi-cell-num {
    color: #f4f6f8 !important;
}
div[class*="st-key-yi_login"] [data-testid="stTextInput"] [data-baseweb="input"],
div[class*="st-key-yi_login"] [data-testid="stTextInput"] [data-baseweb="base-input"],
div[class*="st-key-yi_login"] [data-testid="stTextInput"] input {
    background: #87CEEB !important;
    background-color: #87CEEB !important;
    color: #000000 !important;
    -webkit-text-fill-color: #000000 !important;
    caret-color: #000000 !important;
    color-scheme: light !important;
}
</style>
"""


def inject_theme() -> None:
    try:
        st.html(THEME_CSS)
    except Exception:
        st.markdown(THEME_CSS, unsafe_allow_html=True)


def render_site_title() -> None:
    st.markdown(
        f'<h1 class="yi-site-title" style="color:#000000 !important;'
        f'-webkit-text-fill-color:#000000 !important;opacity:1 !important;'
        f'font-weight:700;font-size:2rem;margin:0.15rem 0 0.4rem 0;">'
        f"{SITE_TITLE}</h1>",
        unsafe_allow_html=True,
    )


def render_login_caption() -> None:
    st.markdown(
        '<p class="yi-login-caption" style="color:#000000 !important;'
        '-webkit-text-fill-color:#000000 !important;opacity:1 !important;'
        'font-size:0.95rem;margin:0 0 0.7rem 0;">'
        "아이디로 로그인한 뒤 본인 화면만 사용합니다. 휴대폰에서도 입력할 수 있습니다.</p>",
        unsafe_allow_html=True,
    )


def logo_path() -> Path | None:
    for path in LOGO_CANDIDATES:
        if path.exists():
            return path
    return None


def render_logo(width: int = 118) -> None:
    path = logo_path()
    if path is None:
        st.markdown('<div style="font-weight:700;color:#1a5fb4">ATEC</div>', unsafe_allow_html=True)
        return
    st.image(str(path), width=width)
