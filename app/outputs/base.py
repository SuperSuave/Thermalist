from __future__ import annotations
from abc import ABC, abstractmethod
from app.core.models import RenderedReceipt


class OutputBackend(ABC):
    name: str

    @abstractmethod
    def send(self, receipt: RenderedReceipt, **kwargs) -> dict:
        raise NotImplementedError
