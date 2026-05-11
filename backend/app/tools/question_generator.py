from __future__ import annotations

import json
import re
from typing import Any, Dict

from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

from app.core.config import get_settings


def _build_prompt(vacancy_context: str, role: str, count: int) -> str:
    return (
        "Сгенерируй вопросы для подготовки к собеседованию под конкретную вакансию.\n"
        f"Роль: {role}\n"
        f"Контекст вакансии (требования/обязанности/навыки):\n{vacancy_context}\n\n"
        f"Нужно {count} вопросов.\n"
        "Сделай разные типы: technical, practical, behavioral, system_design, role_specific.\n"
        "Верни один JSON-объект без markdown, без блоков ```, без пояснений до или после.\n"
        "Строго в формате:\n"
        '{ "questions": [ { "id": 1, "type": "technical", "question": "..." } ] }\n'
    )


def _extract_json_payload(text: str) -> str:
    """Достаёт JSON из ответа модели (часто оборачивает в ```json ... ```)."""
    t = (text or "").strip()
    if "```" in t:
        for block in re.findall(r"```(?:json)?\s*([\s\S]*?)```", t, flags=re.IGNORECASE):
            inner = block.strip()
            if inner.startswith("{"):
                return inner
    start = t.find("{")
    end = t.rfind("}")
    if start != -1 and end != -1 and end > start:
        return t[start : end + 1].strip()
    return t


def _parse_questions_json(text: str) -> Dict[str, Any] | None:
    for candidate in (text.strip(), _extract_json_payload(text)):
        if not candidate:
            continue
        try:
            data = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict) and isinstance(data.get("questions"), list):
            return data
    return None


async def generate_questions(vacancy_context: str, role: str, count: int = 10) -> Dict[str, Any]:
    s = get_settings()
    llm = ChatOpenAI(model=s.openai_model, api_key=s.openai_api_key or None, temperature=0.3)
    resp = await llm.ainvoke(_build_prompt(vacancy_context, role, count))
    text = (resp.content or "").strip()
    parsed = _parse_questions_json(text)
    if parsed is not None:
        return parsed
    # fallback: только если это не похоже на JSON по строкам
    lines = [l.strip("- ").strip() for l in text.splitlines() if l.strip() and not l.strip().startswith(("{", "}", "[", "]"))][:count]
    if not lines:
        return {"questions": [{"id": 1, "type": "technical", "question": "Опишите ваш опыт, релевантный вакансии."}]}
    qs = [{"id": i + 1, "type": "technical", "question": q} for i, q in enumerate(lines)]
    return {"questions": qs}


@tool
async def question_generator_tool(vacancy_context: str, role: str, count: int = 10) -> str:
    """
    Generates interview questions for a vacancy context.
    Returns JSON string: {"questions":[...]}.
    """
    data = await generate_questions(vacancy_context=vacancy_context, role=role, count=count)
    return json.dumps(data, ensure_ascii=False)

