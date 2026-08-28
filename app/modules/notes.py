from __future__ import annotations

import re
from typing import Any

from app.core.models import Document, DocumentSection
from app.modules.base import Module
from app.modules.utils import compact_metadata


TAG_RE = re.compile(r"<[^>]+>")


def _clean_text(text: str | None) -> str | None:
    if text is None:
        return None

    cleaned = TAG_RE.sub("", text)
    lines = [" ".join(line.split()) for line in cleaned.splitlines()]
    result = "\n".join(lines).strip()
    return result or None


class NotesModule(Module):
    name = "notes"

    async def build(self, payload: dict[str, Any], **kwargs: Any) -> Document:
        title = _clean_text(
            payload.get("title")
            or payload.get("summary")
            or payload.get("name")
        ) or "Note"

        body = _clean_text(
            payload.get("body")
            or payload.get("content")
            or payload.get("description")
            or payload.get("text")
        ) or ""

        return Document(
            title=title,
            sections=[
                DocumentSection(kind="title", text=title),
                DocumentSection(kind="text", text=body),
            ],
            metadata=compact_metadata(
                {
                    "source": payload.get("source"),
                    "module": self.name,
                }
            ),
        )
