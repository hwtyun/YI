"""요청 텍스트에서 취합 양식 JSON을 제안한다. API Key는 st.secrets만 사용한다.

OpenAI(gpt-4o-mini)를 먼저 쓰고, 키가 없으면 Gemini를 쓴다.
Gemini 1.5 모델명은 더 이상 호출되지 않는다.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
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
OPENAI_MODELS = ("gpt-4o-mini", "gpt-4.1-mini", "gpt-4o")
GEMINI_MODELS = ("gemini-2.5-flash", "gemini-2.0-flash", "gemini-3.6-flash")


def _secret(name: str) -> str | None:
    try:
        import streamlit as st

        key = str(st.secrets.get(name) or "").strip()
        return key or None
    except Exception:
        return None


def openai_api_key() -> str | None:
    return _secret("OPENAI_API_KEY")


def gemini_api_key() -> str | None:
    """Gemini 키. 예전 화면 호환용으로 OpenAI 키가 있으면 그것도 반환한다."""
    return _secret("GEMINI_API_KEY") or openai_api_key()


def ai_api_key() -> str | None:
    return openai_api_key() or _secret("GEMINI_API_KEY")


def _http_json(url: str, payload: dict, headers: dict[str, str], timeout: int = 60) -> dict:
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:400]
        raise RuntimeError(f"{exc.code} {detail}".strip()) from exc


def _call_openai(request_text: str, key: str) -> str:
    last_error: Exception | None = None
    for model_name in OPENAI_MODELS:
        try:
            payload = _http_json(
                "https://api.openai.com/v1/chat/completions",
                {
                    "model": model_name,
                    "temperature": 0.2,
                    "response_format": {"type": "json_object"},
                    "messages": [
                        {"role": "system", "content": PROMPT},
                        {"role": "user", "content": request_text},
                    ],
                },
                {
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json",
                },
            )
            text = str(payload["choices"][0]["message"]["content"] or "")
            if text.strip():
                return text
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            continue
    raise RuntimeError(f"OpenAI 호출에 실패했습니다. {last_error or ''}".strip())


def _call_gemini_rest(request_text: str, key: str) -> str:
    last_error: Exception | None = None
    prompt = f"{PROMPT}\n\n요청:\n{request_text}"
    for model_name in GEMINI_MODELS:
        try:
            payload = _http_json(
                (
                    "https://generativelanguage.googleapis.com/v1beta/models/"
                    f"{model_name}:generateContent?key={key}"
                ),
                {"contents": [{"parts": [{"text": prompt}]}]},
                {"Content-Type": "application/json"},
            )
            parts = payload.get("candidates", [{}])[0].get("content", {}).get("parts", [])
            text = "".join(str(part.get("text") or "") for part in parts)
            if text.strip():
                return text
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            continue
    raise RuntimeError(f"Gemini 호출에 실패했습니다. {last_error or ''}".strip())


def _call_gemini(request_text: str) -> str:
    openai_key = openai_api_key()
    gemini_key = _secret("GEMINI_API_KEY")
    errors: list[str] = []
    if openai_key:
        try:
            return _call_openai(request_text, openai_key)
        except Exception as exc:  # noqa: BLE001
            errors.append(str(exc))
    if gemini_key:
        try:
            return _call_gemini_rest(request_text, gemini_key)
        except Exception as exc:  # noqa: BLE001
            errors.append(str(exc))
    if errors:
        raise RuntimeError(" ".join(errors))
    raise RuntimeError(
        "OPENAI_API_KEY 또는 GEMINI_API_KEY가 secrets.toml에 없습니다. "
        "키를 넣거나 컬럼을 직접 작성하세요."
    )


def propose_schema(request_text: str, generate: GenerateFn | None = None) -> dict:
    text = str(request_text or "").strip()
    if not text:
        raise ValueError("요청 내용을 붙여 넣어 주세요.")
    raw = (generate or _call_gemini)(text)
    return normalize_schema(parse_model_json(raw))
