from __future__ import annotations

from typing import Any

from app.core.models import Document, DocumentSection
from app.modules.base import Module
from app.modules.utils import compact_metadata

class LabelModule(Module):
    name = "label"

    async def build(self, payload: dict[str, Any], **kwargs: Any) -> Document:
        verb = (payload.get("verb") or "").strip().upper()
        date = (payload.get("date") or "").strip()
        note = (payload.get("note") or "").strip()
        theme_name = (payload.get("theme_name") or "framed_food").strip()

        if not verb:
            raise ValueError("Label payload is missing 'verb'")

        return Document(
            title=verb,
            sections=[
                DocumentSection(
                    kind="label",
                    text=verb,
                    metadata=compact_metadata(
                        {
                            "date": date,
                            "note": note,
                            "theme_name": theme_name,
                        }
                    ),
                )
            ],
            metadata={
                "module": self.name,
                "theme_name": theme_name,
            },
        )
