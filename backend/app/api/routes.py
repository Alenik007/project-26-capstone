from __future__ import annotations

import asyncio
from typing import AsyncGenerator

from fastapi import APIRouter, Body, Request
from fastapi.responses import JSONResponse, StreamingResponse

from app.agents.interview_agent import chat as agent_chat
from app.agents.interview_agent import session_store
from app.api.schemas import ChatRequest, HealthResponse, SessionResponse
from app.core.rate_limit import limiter
from app.core.security import detect_prompt_injection


router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health() -> dict:
    return {"status": "ok"}


def _sse_pack(data: str) -> bytes:
    return f"data: {data}\n\n".encode("utf-8")


@router.post("/chat")
@limiter.limit("20/minute")
async def chat(request: Request, payload: dict = Body(...)):
    req = ChatRequest.model_validate(payload)

    if detect_prompt_injection(req.message):
        return JSONResponse(
            status_code=400,
            content={"error": "Запрос отклонён: обнаружена попытка изменить системные инструкции."},
        )

    async def event_stream() -> AsyncGenerator[bytes, None]:
        # For now we stream by words to satisfy SSE streaming requirement,
        # while keeping agent implementation simple and deterministic.
        text = await agent_chat(session_id=req.session_id, user_message=req.message)
        for token in text.split():
            yield _sse_pack(token + " ")
            await asyncio.sleep(0)
        yield _sse_pack("[DONE]")

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str) -> dict:
    return session_store.to_session_response(session_id)

