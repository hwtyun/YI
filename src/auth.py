"""streamlit-authenticator 설정. 비밀번호는 DB 해시 우선, 없으면 secrets.toml."""

from __future__ import annotations

import re
from typing import Any

import streamlit as st
import streamlit_authenticator as stauth

from src.config import ROLE_ADMIN, USERS, primary_role
from src.db import get_password_hash, upsert_password_hash

COOKIE_NAME = "yi_factory_auth"
LOGIN_FIELDS = {
    "Form name": "로그인",
    "Username": "아이디",
    "Password": "비밀번호",
    "Login": "로그인",
    "Captcha": "캡차",
}
PASSWORD_RULE_HELP = "8~32자, 영문과 숫자를 모두 포함해야 합니다."


def credential_variants(value: str, *, lower: bool = False) -> list[str]:
    """입력칸이 좌우 반전된 경우에도 원래 값을 함께 시도한다."""
    raw = str(value or "")
    items = [raw, raw.strip(), raw[::-1], raw[::-1].strip()]
    if lower:
        items = [item.lower() for item in items]
    seen: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.append(item)
    return seen


def sign_in(authenticator, username: str, password: str) -> bool:
    """아이디·비밀번호를 확인하고, 반전 입력도 한 번 더 시도한다."""
    for user in credential_variants(username, lower=True):
        if user not in USERS:
            continue
        for pwd in credential_variants(password):
            if authenticator.authentication_controller.login(user, pwd):
                return True
        secret = None
        try:
            secret = str(st.secrets["passwords"][user])
        except Exception:
            secret = None
        if not secret:
            continue
        if secret not in credential_variants(password):
            continue
        stored = (get_password_hash(user) or "").strip()
        db_matches_secret = bool(
            stored and stauth.Hasher.is_hash(stored) and stauth.Hasher.check_pw(secret, stored)
        )
        if db_matches_secret:
            continue
        repaired = stauth.Hasher.hash(secret)
        upsert_password_hash(user, repaired)
        creds = st.session_state.get("hashed_credentials") if hasattr(st, "session_state") else None
        if creds and user in creds.get("usernames", {}):
            creds["usernames"][user]["password"] = repaired
        if authenticator.authentication_controller.login(user, secret):
            return True
    return False


def validate_new_password(password: str) -> str | None:
    if not 8 <= len(password) <= 32:
        return "비밀번호는 8자 이상 32자 이하여야 합니다."
    if not re.search(r"[A-Za-z]", password):
        return "비밀번호에 영문을 포함해 주세요."
    if not re.search(r"\d", password):
        return "비밀번호에 숫자를 포함해 주세요."
    return None


def build_credentials() -> dict[str, Any]:
    passwords = st.secrets["passwords"]
    usernames: dict[str, Any] = {}
    for username, meta in USERS.items():
        stored = (get_password_hash(username) or "").strip()
        if stored and stauth.Hasher.is_hash(stored):
            password = stored
        else:
            if username not in passwords:
                raise KeyError(f"secrets.toml의 [passwords]에 '{username}'이 없습니다.")
            password = str(passwords[username])
        usernames[username] = {
            "email": meta["email"],
            "first_name": meta["first_name"],
            "last_name": meta["last_name"],
            "password": password,
            "roles": list(meta["roles"]),
        }
    return {"usernames": usernames}


def persist_credential_hashes(credentials: dict[str, Any]) -> None:
    for username, user in credentials["usernames"].items():
        upsert_password_hash(username, str(user["password"]))


def change_own_password(
    username: str,
    current_password: str,
    new_password: str,
    new_password_repeat: str,
    credentials: dict[str, Any] | None = None,
) -> str | None:
    """성공 시 None, 실패 시 한글 오류 메시지를 반환한다."""
    if credentials is None:
        credentials = st.session_state.get("hashed_credentials")
    if not credentials or username not in credentials["usernames"]:
        return "로그인 정보를 확인할 수 없습니다. 다시 로그인하세요."

    stored_hash = str(credentials["usernames"][username]["password"])
    if not current_password:
        return "현재 비밀번호를 입력하세요."
    if not stauth.Hasher.check_pw(current_password, stored_hash):
        return "현재 비밀번호가 올바르지 않습니다."
    if new_password != new_password_repeat:
        return "새 비밀번호와 확인이 일치하지 않습니다."
    if current_password == new_password:
        return "새 비밀번호가 현재 비밀번호와 같습니다."
    rule_error = validate_new_password(new_password)
    if rule_error:
        return rule_error

    new_hash = stauth.Hasher.hash(new_password)
    credentials["usernames"][username]["password"] = new_hash
    upsert_password_hash(username, new_hash)
    if hasattr(st, "session_state"):
        try:
            st.session_state["hashed_credentials"] = credentials
        except Exception:
            pass
    return None


def refresh_passwords_from_db(credentials: dict[str, Any]) -> None:
    for username, user in credentials["usernames"].items():
        stored = get_password_hash(username)
        if stored:
            user["password"] = stored.strip()


def reset_user_password_by_admin(
    admin_username: str,
    target_username: str,
    new_password: str,
    new_password_repeat: str,
    credentials: dict[str, Any] | None = None,
) -> str | None:
    """관리자가 다른 계정 비밀번호를 초기화한다. 성공 시 None."""
    if admin_username not in USERS or primary_role(admin_username) != ROLE_ADMIN:
        return "생산관리팀(최고 관리자)만 다른 계정 비밀번호를 초기화할 수 있습니다."
    if target_username not in USERS:
        return "대상 계정을 찾을 수 없습니다."
    if target_username == admin_username:
        return "본인 비밀번호는 왼쪽의 비밀번호 변경을 이용해 주세요."
    if new_password != new_password_repeat:
        return "새 비밀번호와 확인이 일치하지 않습니다."
    rule_error = validate_new_password(new_password)
    if rule_error:
        return rule_error

    new_hash = stauth.Hasher.hash(new_password)
    upsert_password_hash(target_username, new_hash)
    if credentials is None:
        credentials = st.session_state.get("hashed_credentials") if hasattr(st, "session_state") else None
    if credentials and target_username in credentials.get("usernames", {}):
        credentials["usernames"][target_username]["password"] = new_hash
        try:
            st.session_state["hashed_credentials"] = credentials
        except Exception:
            pass
    return None


def get_authenticator(cookie_expiry_days: float) -> stauth.Authenticate:
    if "hashed_credentials" not in st.session_state:
        credentials = build_credentials()
        stauth.Hasher.hash_passwords(credentials)
        persist_credential_hashes(credentials)
        st.session_state["hashed_credentials"] = credentials
    else:
        refresh_passwords_from_db(st.session_state["hashed_credentials"])

    cookie_key = str(st.secrets["cookie_key"])
    return stauth.Authenticate(
        st.session_state["hashed_credentials"],
        COOKIE_NAME,
        cookie_key,
        cookie_expiry_days,
        auto_hash=False,
    )
