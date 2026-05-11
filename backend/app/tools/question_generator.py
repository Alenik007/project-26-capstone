from __future__ import annotations

import json
from typing import Any, Dict, List

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
        "Верни ТОЛЬКО JSON строго в формате:\n"
        '{ "questions": [ { "id": 1, "type": "technical", "question": "..." } ] }\n'
    )


async def generate_questions(vacancy_context: str, role: str, count: int = 10) -> Dict[str, Any]:
    s = get_settings()
    llm = ChatOpenAI(model=s.openai_model, api_key=s.openai_api_key or None, temperature=0.3)
    resp = await llm.ainvoke(_build_prompt(vacancy_context, role, count))
    text = (resp.content or "").strip()
    try:
        return json.loads(text)
    except Exception:
        # fallback: wrap as plain questions
        lines = [l.strip("- ").strip() for l in text.splitlines() if l.strip()]
        qs = [{"id": i + 1, "type": "technical", "question": q} for i, q in enumerate(lines[:count])]
        return {"questions": qs}


@tool
async def question_generator_tool(vacancy_context: str, role: str, count: int = 10) -> str:
    """
    Generates interview questions for a vacancy context.
    Returns JSON string: {"questions":[...]}.
    """
    data = await generate_questions(vacancy_context=vacancy_context, role=role, count=count)
    return json.dumps(data, ensure_ascii=False)

