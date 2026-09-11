from __future__ import annotations

from typing import Any

from app.core.models import Document, DocumentSection
from app.modules.base import Module


class LabelModule(Module):
    name = "label"

    async def build(self, payload: dict[str, Any], **kwargs: Any) -> Document:
        verb = (payload.get("verb") or "").strip().upper()
        date = (payload.get("date") or "").strip()
        note = (payload.get("note") or "").strip()
        theme_name = (payload.get("theme_name") or "framed_food").strip()

        if not verb:
            raise ValueError("Label payload is missing 'verb'")

        meta = {
            k: v
            for k, v in {
                "date": date,
                "note": note,
                "theme_name": theme_name,
            }.items()
            if v is not None
        }

        return Document(
            title=verb,
            sections=[
                DocumentSection(
                    kind="label",
                    text=verb,
                    metadata=meta,
                )
            ],
            metadata={
                "module": self.name,
                "theme_name": theme_name,
            },
        )
