from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any
from app.core.models import Document


class Module(ABC):
    name: str

    @abstractmethod
    async def build(self, payload: dict[str, Any], **kwargs: Any) -> Document:
        raise NotImplementedError
