from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=100)
    message: str = Field(..., min_length=1, max_length=5000)


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class SessionResponse(BaseModel):
    session_id: str
    messages: list[ChatMessage]


class HealthResponse(BaseModel):
    status: str

