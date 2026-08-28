"""요청 텍스트에서 취합 양식 JSON을 제안한다. API Key는 st.secrets만 사용한다."""

from __future__ import annotations

from typing import Callable

from src.schema import normalize_schema, parse_model_json

PROMPT = """당신은 공장의 팀별 취합 양식을 설계합니다.
아래는 본사에서 온 요청 메일 본문과 첨부 내용입니다.
각 팀이 웹에서 입력해야 할 표 컬럼을 추출하세요.
첨부 표의 헤더·예시 행도 참고하세요.
반드시 JSON만 출력하세요. 배포 여부, 자동 발송, 메일 발송 필드는 넣지 마세요.

형식:
{
  "title": "조사 제목",
  "instructions": "팀 담당자에게 보여줄 짧은 안내",
  "columns": [
    {"key": "item_name", "label": "한글 항목명", "type": "text", "required": true}
  ]
}

규칙:
- columns는 1개 이상 20개 이하
- type은 text, number, date 중 하나
- key는 영문으로 시작하고 영문·숫자·밑줄만 사용
- 특근 인원 조사가 아닌, 요청에 적힌 다른 취합이라고 가정합니다
- 첨부에서 이미 채워진 값은 컬럼으로만 반영하고, 배포/자동입력 하지 마세요
"""

GenerateFn = Callable[[str], str]


def gemini_api_key() -> str | None:
    try:
        import streamlit as st

        key = str(st.secrets.get("GEMINI_API_KEY") or "").strip()
        return key or None
    except Exception:
        return None


def _call_gemini(request_text: str) -> str:
    key = gemini_api_key()
    if not key:
        raise RuntimeError("GEMINI_API_KEY가 secrets.toml에 없습니다. 키를 넣거나 컬럼을 직접 작성하세요.")
    import google.generativeai as genai

    genai.configure(api_key=key)
    prompt = f"{PROMPT}\n\n요청:\n{request_text}"
    last_error: Exception | None = None
    for model_name in ("gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-flash-latest"):
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            text = getattr(response, "text", None) or ""
            if text.strip():
                return str(text)
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            continue
    raise RuntimeError(f"Gemini 호출에 실패했습니다. {last_error or ''}".strip())


def propose_schema(request_text: str, generate: GenerateFn | None = None) -> dict:
    text = str(request_text or "").strip()
    if not text:
        raise ValueError("요청 내용을 붙여 넣어 주세요.")
    raw = (generate or _call_gemini)(text)
    return normalize_schema(parse_model_json(raw))
