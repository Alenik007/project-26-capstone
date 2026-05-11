from __future__ import annotations

import glob
import os
from pathlib import Path
from typing import Iterable, List, Tuple

from langchain_openai import OpenAIEmbeddings
from qdrant_client.models import Distance, VectorParams

from app.core.config import get_settings
from app.rag.qdrant_client import get_qdrant_client


def _chunk_text(text: str, min_size: int = 800, max_size: int = 1200) -> list[str]:
    text = (text or "").strip()
    if not text:
        return []
    chunks: list[str] = []
    i = 0
    while i < len(text):
        j = min(i + max_size, len(text))
        # try to cut on newline near the end
        cut = text.rfind("\n", i, j)
        if cut != -1 and cut - i >= min_size:
            j = cut
        chunks.append(text[i:j].strip())
        i = j
    return [c for c in chunks if c]


def _load_markdown_files(kb_dir: str) -> list[tuple[str, str]]:
    paths = sorted(glob.glob(os.path.join(kb_dir, "*.md")))
    out: list[tuple[str, str]] = []
    for p in paths:
        content = Path(p).read_text(encoding="utf-8")
        out.append((os.path.basename(p), content))
    return out


def ingest_knowledge_base(kb_dir: str = "data/interview_knowledge") -> int:
    """
    Reads markdown files, chunks content, creates embeddings, and uploads to Qdrant.
    Returns number of uploaded chunks.
    """
    s = get_settings()
    client = get_qdrant_client()

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small", api_key=s.openai_api_key or None)

    # Ensure collection exists
    try:
        client.get_collection(s.qdrant_collection)
    except Exception:
        client.create_collection(
            collection_name=s.qdrant_collection,
            vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
        )

    docs = _load_markdown_files(kb_dir)

    payloads = []
    vectors = []
    ids = []
    idx = 0
    for source, content in docs:
        for chunk in _chunk_text(content):
            vec = embeddings.embed_query(chunk)
            payloads.append({"content": chunk, "source": source})
            vectors.append(vec)
            ids.append(idx)
            idx += 1

    if not ids:
        return 0

    client.upsert(
        collection_name=s.qdrant_collection,
        points=[
            {"id": ids[i], "vector": vectors[i], "payload": payloads[i]}
            for i in range(len(ids))
        ],
    )
    return len(ids)

