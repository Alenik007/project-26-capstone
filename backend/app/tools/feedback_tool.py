from __future__ import annotations

import json
from typing import Any, Dict

from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

from app.core.config import get_settings


def _prompt(question: str, answer: str, vacancy_context: str) -> str:
    return (
        "Ты — интервьюер. Оцени ответ кандидата.\n"
        "Критерии: полнота, соответствие вакансии, техническая точность, структурированность, примеры опыта.\n\n"
        f"Контекст вакансии:\n{vacancy_context}\n\n"
        f"Вопрос:\n{question}\n\n"
        f"Ответ кандидата:\n{answer}\n\n"
        "Верни ТОЛЬКО JSON строго в формате:\n"
        '{ "score": 7, "strengths": ["..."], "weaknesses": ["..."], "improved_answer": "...", "next_recommendation": "..." }\n'
        "score: целое 1-10.\n"
    )


async def evaluate_answer(question: str, answer: str, vacancy_context: str) -> Dict[str, Any]:
    s = get_settings()
    llm = ChatOpenAI(model=s.openai_model, api_key=s.openai_api_key or None, temperature=0.2)
    resp = await llm.ainvoke(_prompt(question, answer, vacancy_context))
    text = (resp.content or "").strip()
    try:
        data = json.loads(text)
        # minimal normalization
        if "score" in data:
            try:
                data["score"] = int(data["score"])
            except Exception:
                data["score"] = 5
        return data
    except Exception:
        return {
            "score": 5,
            "strengths": ["Ответ дан, но недостаточно структурирован."],
            "weaknesses": ["Не хватает деталей и привязки к требованиям вакансии."],
            "improved_answer": "Попробуйте структурировать ответ (контекст → действия → результат) и добавить примеры из опыта.",
            "next_recommendation": "Повторите тему вопроса и подготовьте 1-2 конкретных кейса по STAR.",
        }


@tool
async def feedback_tool(question: str, answer: str, vacancy_context: str) -> str:
    """
    Evaluates a user's answer and returns structured feedback (JSON string).
    """
    data = await evaluate_answer(question=question, answer=answer, vacancy_context=vacancy_context)
    return json.dumps(data, ensure_ascii=False)

