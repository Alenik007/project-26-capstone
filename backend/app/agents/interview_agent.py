from __future__ import annotations

import json
import re
from typing import Optional, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from app.agents.prompts import SYSTEM_PROMPT
from app.core.config import get_settings
from app.rag.retriever import interview_knowledge_search_tool
from app.tools.feedback_tool import feedback_tool
from app.tools.hh_parser import hh_vacancy_parser_tool, is_headhunter_job_url
from app.tools.question_generator import question_generator_tool


class SessionState(TypedDict, total=False):
    session_id: str
    vacancy: dict
    messages: list[dict]
    interview_questions: list[dict]
    current_question_index: int
    answers: list[dict]
    feedback: list[dict]
    interview_active: bool


_ANY_HTTP_URL = re.compile(r"(https?://[^\s\]\)\"'<>]+)")


def _extract_hh_job_url(text: str) -> Optional[str]:
    for m in _ANY_HTTP_URL.finditer(text or ""):
        cand = m.group(1).rstrip(".,;)")
        if is_headhunter_job_url(cand):
            return cand.split("#")[0]
    return None


def _looks_like_vacancy_paste(text: str) -> bool:
    t = (text or "").strip()
    if len(t) < 140:
        return False
    if _ANY_HTTP_URL.search(t) and len(t) < 450:
        return False
    low = t.lower()
    keys = (
        "ваканс",
        "требова",
        "обязанност",
        "опыт",
        "зарплат",
        "условия",
        "компетенц",
        "навык",
        "образован",
        "график",
        "оформлен",
        "компани",
        "responsibilit",
        "requirement",
    )
    return sum(1 for k in keys if k in low) >= 2


def _wants_start_mock(lower: str) -> bool:
    return any(
        p in lower
        for p in (
            "начни mock",
            "начать mock",
            "start mock",
            "mock-интервью",
            "mock интервью",
            "начать mock-интервью",
            "начни mock-интервью",
            "начать интервью",
            "начни интервью",
            "мок интервью",
            "мок-интервью",
            "начать собесед",
            "начни собесед",
        )
    )


def _wants_questions(lower: str) -> bool:
    if "вопрос" not in lower:
        return False
    return any(
        x in lower
        for x in (
            "сгенер",
            "сгенерируй",
            "сгенерировать",
            "придумай",
            "составь",
            "накидай",
            "давай вопрос",
        )
    )


def _wants_finish(lower: str) -> bool:
    if not any(x in lower for x in ("заверш", "законч", "останов", "финиш")):
        return False
    return any(x in lower for x in ("интерв", "mock", "собесед", "обратн"))


def _vacancy_context_text(vacancy: dict) -> str:
    if not vacancy:
        return ""
    parts = []
    for k in ["title", "company", "requirements", "responsibilities", "experience", "location", "salary"]:
        v = vacancy.get(k)
        if v:
            parts.append(f"{k}: {v}")
    skills = vacancy.get("skills") or []
    if skills:
        parts.append("skills: " + ", ".join(skills))
    return "\n".join(parts).strip()


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, SessionState] = {}

    def get(self, session_id: str) -> SessionState:
        if session_id not in self._sessions:
            self._sessions[session_id] = {
                "session_id": session_id,
                "vacancy": {},
                "messages": [],
                "interview_questions": [],
                "current_question_index": 0,
                "answers": [],
                "feedback": [],
                "interview_active": False,
            }
        return self._sessions[session_id]

    def to_session_response(self, session_id: str) -> dict:
        s = self.get(session_id)
        return {"session_id": session_id, "messages": s.get("messages", [])}


session_store = SessionStore()


def _build_agent():
    settings = get_settings()
    llm = ChatOpenAI(model=settings.openai_model, api_key=settings.openai_api_key or None, temperature=0.2)
    tools = [
        hh_vacancy_parser_tool,
        interview_knowledge_search_tool,
        question_generator_tool,
        feedback_tool,
    ]
    return create_react_agent(llm, tools, prompt=SystemMessage(content=SYSTEM_PROMPT))


_agent = None


def get_agent():
    global _agent
    if _agent is None:
        _agent = _build_agent()
    return _agent


async def chat(session_id: str, user_message: str) -> str:
    """
    Runs one assistant turn and persists session state.
    Returns assistant final message text.
    """
    state = session_store.get(session_id)
    state["messages"].append({"role": "user", "content": user_message})

    vacancy = state.get("vacancy") or {}
    lower = (user_message or "").lower()

    url = _extract_hh_job_url(user_message)
    if url:
        try:
            raw = await hh_vacancy_parser_tool.ainvoke({"url": url})
            parsed = json.loads(raw)
            if isinstance(parsed, dict) and not parsed.get("error"):
                state["vacancy"] = parsed
                vacancy = parsed
        except Exception:
            pass

    if not url and _looks_like_vacancy_paste(user_message):
        state["vacancy"] = {
            "title": "",
            "company": "",
            "requirements": "",
            "responsibilities": user_message.strip()[:14000],
            "skills": [],
            "experience": "",
            "location": "",
            "salary": "",
        }
        vacancy = state["vacancy"]

    if _wants_finish(lower):
        state["interview_active"] = False
        scores = [int(x.get("score", 0)) for x in state.get("feedback", []) if isinstance(x, dict)]
        avg = round(sum(scores) / len(scores), 1) if scores else 0
        assistant_text = (
            "Итоговый отчёт по подготовке:\n\n"
            f"- Средний балл: {avg}/10\n"
            f"- Ответов оценено: {len(scores)}\n"
            "- Что повторить: темы из слабых мест и требования вакансии.\n"
        )
        state["messages"].append({"role": "assistant", "content": assistant_text})
        return assistant_text

    if _wants_questions(lower):
        state["interview_active"] = False
        ctx = _vacancy_context_text(vacancy)
        if not ctx:
            assistant_text = (
                "Недостаточно данных о вакансии. Пришлите ссылку на вакансию (hh.ru, hh.kz и региональные сайты) "
                "или вставьте полный текст вакансии одним сообщением."
            )
            state["messages"].append({"role": "assistant", "content": assistant_text})
            return assistant_text

        role = vacancy.get("title") or "Interview"
        count = 10
        m = re.search(r"(\d+)\s*вопрос", lower)
        if m:
            try:
                count = max(1, min(30, int(m.group(1))))
            except Exception:
                count = 10
        raw = await question_generator_tool.ainvoke({"vacancy_context": ctx, "role": role, "count": count})
        data = json.loads(raw)
        qs_out = data.get("questions") or []
        state["interview_questions"] = qs_out
        state["current_question_index"] = 0
        assistant_text = "Вот вопросы для подготовки:\n\n" + "\n".join(
            [f"{q.get('id')}. [{q.get('type')}] {q.get('question')}" for q in qs_out]
        )
        state["messages"].append({"role": "assistant", "content": assistant_text})
        return assistant_text

    if _wants_start_mock(lower):
        qs = state.get("interview_questions") or []
        idx = int(state.get("current_question_index") or 0)
        if not qs:
            assistant_text = (
                "Сначала сгенерируйте вопросы по вакансии (кнопка «Сгенерировать 10 вопросов» или напишите это в чате), "
                "либо вставьте ссылку/текст вакансии и снова нажмите «Начать mock-интервью»."
            )
            state["messages"].append({"role": "assistant", "content": assistant_text})
            return assistant_text
        if idx >= len(qs):
            state["interview_active"] = False
            assistant_text = "Список вопросов уже пройден. Сгенерируйте новые вопросы или вставьте другую вакансию."
            state["messages"].append({"role": "assistant", "content": assistant_text})
            return assistant_text
        q = qs[idx]["question"]
        assistant_text = f"Начинаем mock-интервью. Вопрос {idx+1}/{len(qs)}:\n\n{q}"
        state["interview_active"] = True
        state["messages"].append({"role": "assistant", "content": assistant_text})
        return assistant_text

    qs = state.get("interview_questions") or []
    idx = int(state.get("current_question_index") or 0)
    if state.get("interview_active") and qs and idx < len(qs):
        if not _wants_questions(lower) and not _wants_start_mock(lower):
            q = qs[idx]["question"]
            ctx = _vacancy_context_text(vacancy)
            fb_raw = await feedback_tool.ainvoke({"question": q, "answer": user_message, "vacancy_context": ctx})
            fb = json.loads(fb_raw)
            state["answers"].append({"question": q, "answer": user_message})
            state["feedback"].append(fb)
            idx += 1
            state["current_question_index"] = idx
            if idx < len(qs):
                next_q = qs[idx]["question"]
                assistant_text = (
                    f"Оценка: {fb.get('score', 0)}/10\n"
                    f"Сильные стороны: {', '.join(fb.get('strengths', []))}\n"
                    f"Зоны роста: {', '.join(fb.get('weaknesses', []))}\n\n"
                    f"Следующий вопрос {idx+1}/{len(qs)}:\n\n{next_q}"
                )
            else:
                state["interview_active"] = False
                scores = [int(x.get("score", 0)) for x in state.get("feedback", []) if isinstance(x, dict)]
                avg = round(sum(scores) / len(scores), 1) if scores else 0
                assistant_text = (
                    "Интервью завершено.\n\n"
                    f"Общий средний балл: {avg}/10\n"
                    "Рекомендации: повторите темы, где были слабые места, и подготовьте 2–3 кейса по STAR.\n"
                )
            state["messages"].append({"role": "assistant", "content": assistant_text})
            return assistant_text

    # Default: let ReAct agent decide (autonomous) with available tools.
    agent = get_agent()
    ctx = _vacancy_context_text(vacancy)
    messages: list[BaseMessage] = [
        SystemMessage(content=SYSTEM_PROMPT),
        SystemMessage(content=f"Текущее состояние вакансии (если есть):\n{ctx}" if ctx else "Вакансия ещё не задана."),
        HumanMessage(content=user_message),
    ]

    result = await agent.ainvoke({"messages": messages})
    out_msgs: list[BaseMessage] = result.get("messages") or []
    last_ai = next((m for m in reversed(out_msgs) if isinstance(m, AIMessage)), None)
    assistant_text = (last_ai.content if last_ai else "") or ""
    if not assistant_text:
        assistant_text = "Не удалось сформировать ответ. Попробуйте уточнить запрос."

    state["messages"].append({"role": "assistant", "content": assistant_text})
    return assistant_text

