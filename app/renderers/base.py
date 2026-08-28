from __future__ import annotations
from abc import ABC, abstractmethod
from app.core.models import Document, RenderedReceipt


class Renderer(ABC):
    name: str

    @abstractmethod
    def render(self, document: Document) -> RenderedReceipt:
        raise NotImplementedError
