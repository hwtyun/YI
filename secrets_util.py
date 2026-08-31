"""Streamlit secrets 읽기. Cloud는 파일이 없고 대시보드 Secrets만 있다."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from src.config import USERS

SECRETS_TOML_TEMPLATE = """OPENAI_API_KEY = "발급받은키"
GEMINI_API_KEY = "발급받은키"
cookie_key = "긴-무작위-문자열"

[passwords]
prodadmin = "비밀번호"
director = "비밀번호"
jejo = "비밀번호"
gumae = "비밀번호"
quality = "비밀번호"
tech = "비밀번호"
jajae = "비밀번호"
"""


def on_streamlit_cloud() -> bool:
    return Path("/mount/src").exists()


def _as_mapping(value: object) -> dict[str, str]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return {str(key): str(item) for key, item in value.items()}
    try:
        return {str(key): str(item) for key, item in dict(value).items()}
    except Exception:
        pass
    result: dict[str, str] = {}
    for name in USERS:
        try:
            result[name] = str(value[name])  # type: ignore[index]
        except Exception:
            continue
    return result


def cookie_key() -> str:
    return str(st.secrets["cookie_key"]).strip()


def password_map() -> dict[str, str]:
    return _as_mapping(st.secrets["passwords"])


def missing_secret_names() -> list[str]:
    missing: list[str] = []
    try:
        if not cookie_key():
            missing.append("cookie_key")
    except Exception:
        missing.append("cookie_key")
    try:
        passwords = password_map()
    except Exception:
        return missing + ["passwords"]
    if not passwords:
        missing.append("passwords")
        return missing
    for name in USERS:
        if not str(passwords.get(name) or "").strip():
            missing.append(f"passwords.{name}")
    return missing


def render_secrets_help(missing: list[str]) -> None:
    if on_streamlit_cloud():
        st.error("Streamlit Cloud에 계정 Secrets가 없습니다. GitHub에는 비밀번호 파일을 올리지 않습니다.")
        st.markdown(
            """
1. 화면 **오른쪽 아래 Manage app** 을 엽니다.  
2. **Settings → Secrets** 로 갑니다.  
3. PC의 `.streamlit/secrets.toml` 내용을 **그대로 붙여 넣고 Save** 합니다.  
4. **Reboot app** 합니다.
            """
        )
        if missing:
            st.caption("부족한 항목: " + ", ".join(missing))
        st.code(SECRETS_TOML_TEMPLATE, language="toml")
        st.info("로컬에서 이미 쓰던 비밀번호를 그대로 넣으면 됩니다. example의 change-me 는 로그인에 쓰지 마세요.")
        return
    st.error(
        "`.streamlit/secrets.toml`이 없거나 계정 정보가 비어 있습니다. "
        "`.streamlit/secrets.toml.example`을 복사해 비밀번호를 채운 뒤 다시 실행하세요."
    )
    if missing:
        st.caption("부족한 항목: " + ", ".join(missing))
