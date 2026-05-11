from __future__ import annotations

import json

from langchain_core.tools import tool
from langchain_openai import OpenAIEmbeddings

from app.core.config import get_settings
from app.rag.qdrant_client import get_qdrant_client


def search_interview_knowledge(query: str, limit: int = 5) -> list[dict]:
    s = get_settings()
    client = get_qdrant_client()
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small", api_key=s.openai_api_key or None)
    q = embeddings.embed_query(query)

    hits = client.search(
        collection_name=s.qdrant_collection,
        query_vector=q,
        limit=limit,
        with_payload=True,
    )

    out: list[dict] = []
    for h in hits:
        payload = h.payload or {}
        out.append({"content": payload.get("content", ""), "source": payload.get("source", "")})
    return out


@tool
def interview_knowledge_search_tool(query: str) -> str:
    """
    Searches the interview preparation knowledge base.
    Returns JSON string: {"documents": [{"content": "...", "source": "..."}]}
    """
    docs = search_interview_knowledge(query=query, limit=5)
    return json.dumps({"documents": docs}, ensure_ascii=False)

