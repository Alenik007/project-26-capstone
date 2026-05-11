from __future__ import annotations

from qdrant_client import QdrantClient

from app.core.config import get_settings


def get_qdrant_client() -> QdrantClient:
    s = get_settings()
    return QdrantClient(url=s.qdrant_url)

