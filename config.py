"""계정·역할·팀 상수. 비밀번호는 `.streamlit/secrets.toml`에만 둔다."""

from __future__ import annotations

from typing import Any

ROLE_ADMIN = "admin"
ROLE_DIRECTOR = "director"
ROLE_TEAM = "team"

# username -> 화면 표시명, 역할, 소속 팀
USERS: dict[str, dict[str, Any]] = {
    "prodadmin": {
        "display_name": "생산관리팀",
        "first_name": "Prod",
        "last_name": "Admin",
        "email": "prodadmin@yi-factory.local",
        "roles": [ROLE_ADMIN],
        "team": "생산관리팀",
        "description": "조사 만들기 · 취합 · 엑셀 받기",
    },
    "director": {
        "display_name": "공장장",
        "first_name": "Plant",
        "last_name": "Director",
        "email": "director@yi-factory.local",
        "roles": [ROLE_DIRECTOR],
        "team": None,
        "description": "조회만 가능합니다",
    },
    "jejo": {
        "display_name": "제조팀",
        "first_name": "Jejo",
        "last_name": "Team",
        "email": "jejo@yi-factory.local",
        "roles": [ROLE_TEAM],
        "team": "제조팀",
        "description": "본인 팀만 입력합니다",
    },
    "gumae": {
        "display_name": "구매팀",
        "first_name": "Gumae",
        "last_name": "Team",
        "email": "gumae@yi-factory.local",
        "roles": [ROLE_TEAM],
        "team": "구매팀",
        "description": "본인 팀만 입력합니다",
    },
    "quality": {
        "display_name": "품질보증팀",
        "first_name": "Quality",
        "last_name": "Team",
        "email": "quality@yi-factory.local",
        "roles": [ROLE_TEAM],
        "team": "품질보증팀",
        "description": "본인 팀만 입력합니다",
    },
    "tech": {
        "display_name": "생산기술파트",
        "first_name": "Tech",
        "last_name": "Team",
        "email": "tech@yi-factory.local",
        "roles": [ROLE_TEAM],
        "team": "생산기술파트",
        "description": "본인 팀만 입력합니다",
    },
    "jajae": {
        "display_name": "자재파트",
        "first_name": "Jajae",
        "last_name": "Team",
        "email": "jajae@yi-factory.local",
        "roles": [ROLE_TEAM],
        "team": "자재파트",
        "description": "본인 팀만 입력합니다",
    },
}

SUBMITTING_TEAMS = [
    "구매팀",
    "제조팀",
    "생산관리팀",
    "품질보증팀",
    "생산기술파트",
    "자재파트",
]

COMPANIES = ["에이텍모빌리티", "에이텍컴퓨터"]
EMPLOYMENT_TYPES = ["정규직", "계약직", "일용직"]
CAFETERIA_MIN_HEADCOUNT = 20


def cafeteria_operating(headcount: int) -> bool:
    """특근 인원이 20명 이상이면 식당을 운영한다."""
    return int(headcount or 0) >= CAFETERIA_MIN_HEADCOUNT


RANK_WORDS = {
    "수석",
    "책임",
    "선임",
    "사원",
    "주임",
    "대리",
    "과장",
    "차장",
    "부장",
    "팀장",
    "파트장",
    "수습",
    "인턴",
    "이사",
    "전무",
    "상무",
    "공장장",
    "대표",
}


def _fold(value: str) -> str:
    return str(value or "").strip().replace(" ", "").replace("-", "").lower()


def normalize_company(value: str) -> str | None:
    text = str(value or "").strip()
    if not text:
        return None
    if text in COMPANIES:
        return text
    folded = _fold(text)
    mapping = {
        "에이텍모빌리티": "에이텍모빌리티",
        "모빌리티": "에이텍모빌리티",
        "aitechmobility": "에이텍모빌리티",
        "atecmobility": "에이텍모빌리티",
        "에이텍컴퓨터": "에이텍컴퓨터",
        "컴퓨터": "에이텍컴퓨터",
        "aitechcomputer": "에이텍컴퓨터",
        "ateccomputer": "에이텍컴퓨터",
    }
    return mapping.get(folded)


def normalize_employment(value: str) -> str | None:
    text = str(value or "").strip()
    if not text:
        return None
    if text in EMPLOYMENT_TYPES:
        return text
    folded = _fold(text)
    mapping = {
        "정규직": "정규직",
        "정규": "정규직",
        "계약직": "계약직",
        "계약": "계약직",
        "일용직": "일용직",
        "일용": "일용직",
    }
    if folded in mapping:
        return mapping[folded]
    # 명부에 직급(책임·선임·사원 등)을 고용형태 칸에 적은 경우 정규직으로 본다.
    if text in RANK_WORDS or folded in {_fold(item) for item in RANK_WORDS}:
        return "정규직"
    return "정규직"


def normalize_team(value: str) -> str | None:
    text = str(value or "").strip()
    if not text:
        return None
    if text in SUBMITTING_TEAMS:
        return text
    folded = _fold(text)
    mapping = {
        "구매팀": "구매팀",
        "구매": "구매팀",
        "제조팀": "제조팀",
        "제조": "제조팀",
        "생산관리팀": "생산관리팀",
        "생산관리": "생산관리팀",
        "품질보증팀": "품질보증팀",
        "품질보증": "품질보증팀",
        "품질팀": "품질보증팀",
        "생산기술파트": "생산기술파트",
        "생산기술": "생산기술파트",
        "생산기술팀": "생산기술파트",
        "자재파트": "자재파트",
        "자재": "자재파트",
        "자재팀": "자재파트",
        "용인공장": "생산관리팀",
        "공장": "생산관리팀",
    }
    return mapping.get(folded)


def get_user(username: str) -> dict[str, Any]:
    return USERS[username]


def primary_role(username: str) -> str:
    return USERS[username]["roles"][0]


def screen_for_username(username: str) -> str:
    """로그인 후 보여줄 화면 종류: admin / director / team."""
    role = primary_role(username)
    if role == ROLE_ADMIN:
        return "admin"
    if role == ROLE_DIRECTOR:
        return "director"
    return "team"
