from __future__ import annotations
from app.core.models import RenderedReceipt
from app.outputs.base import OutputBackend


class MockOutput(OutputBackend):
    name = "mock"

    def send(self, receipt: RenderedReceipt, **kwargs) -> dict:
        return {"status": "ok", "backend": self.name, "preview": receipt.text_preview}
