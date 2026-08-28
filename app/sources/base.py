from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any


class Source(ABC):
    name: str

    @abstractmethod
    async def fetch(self, **kwargs: Any) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def test_connection(self) -> dict[str, Any]:
        raise NotImplementedError
