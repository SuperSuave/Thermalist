from __future__ import annotations
from typing import Any
import httpx
from app.core.config import HomeAssistantConfig
from app.sources.base import Source


class HomeAssistantSource(Source):
    name = "home_assistant"

    def __init__(self, config: HomeAssistantConfig | None = None) -> None:
        self.config = config or HomeAssistantConfig()

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if self.config.token:
            headers["Authorization"] = f"Bearer {self.config.token}"
        return headers

    async def test_connection(self) -> dict[str, Any]:
        url = f"{self.config.base_url.rstrip('/')}/api/"
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
                response = await client.get(url, headers=self._headers())
            return {
                "ok": response.is_success,
                "status_code": response.status_code,
                "url": url
                }
        except Exception as exc:
            return {
                "ok": False,
                "error": str(exc),
                "url": url
                }

    async def fetch(self, **kwargs: Any) -> dict[str, Any]:
        entity_id = kwargs.get('entity_id')
        if not entity_id:
            return {
                "ok": False,
                "tasks": [],
                "source": self.name,
                "error": "entity_id required",
            }

        url = f"{self.config.base_url.rstrip('/')}/api/states/{entity_id}"
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
                response = await client.get(url, headers=self._headers())
                response.raise_for_status()
                data = response.json()
        except Exception as exc:
            return {
                "ok": False,
                "tasks": [],
                "source": self.name,
                "error": str(exc)
                }

        attrs = data.get('attributes', {})
        items = attrs.get('items', [])
        tasks = []
        for item in items:
            tasks.append({
                "id": str(item.get('uid') or item.get('id') or item.get('summary')),
                "title": item.get('summary') or item.get('title') or 'Untitled task',
                "completed": bool(item.get('status') == 'completed' or item.get('completed')),
                "labels": [],
                "due": item.get('due'),
                "description": item.get('description'),
                "metadata": item,
            })
        return {
            "ok": True,
            "tasks": tasks,
            "source": self.name,
            "entity_id": entity_id
            }
