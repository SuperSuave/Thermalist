from pathlib import Path

base = Path("output/thermalist-v2-scaffold")

updates = {
    "app/core/config.py": """from __future__ import annotations
from pydantic import BaseModel, Field


class DoneTickConfig(BaseModel):
    base_url: str = Field(default="http://localhost:2021")
    token: str | None = None
    timeout_seconds: float = 10.0


class HomeAssistantConfig(BaseModel):
    base_url: str = Field(default="http://homeassistant.local:8123")
    token: str | None = None
    timeout_seconds: float = 10.0


class MockOutputConfig(BaseModel):
    enabled: bool = True


class EscposOutputConfig(BaseModel):
    host: str | None = None
    port: int = 9100
    profile: str | None = None
    dry_run: bool = True


class RawTcpOutputConfig(BaseModel):
    host: str | None = None
    port: int = 9100
    timeout: int = 5
    dry_run: bool = True
""",
    "app/core/models.py": """from __future__ import annotations
from typing import Any, Literal
from pydantic import BaseModel, Field


class TaskItem(BaseModel):
    id: str
    title: str
    completed: bool = False
    labels: list[str] = Field(default_factory=list)
    due: str | None = None
    description: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class DocumentSection(BaseModel):
    kind: Literal["title", "text", "spacer", "divider", "task_list"]
    text: str | None = None
    items: list[TaskItem] = Field(default_factory=list)


class Document(BaseModel):
    title: str
    sections: list[DocumentSection] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class RenderedReceipt(BaseModel):
    text_preview: str
    raw_bytes: bytes | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
""",
    "app/sources/base.py": """from __future__ import annotations
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
""",
    "app/sources/donetick.py": """from __future__ import annotations
from typing import Any
import httpx
from app.core.config import DoneTickConfig
from app.sources.base import Source


class DoneTickSource(Source):
    name = "donetick"

    def __init__(self, config: DoneTickConfig | None = None) -> None:
        self.config = config or DoneTickConfig()

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if self.config.token:
            headers["Authorization"] = f"Bearer {self.config.token}"
        return headers

    async def test_connection(self) -> dict[str, Any]:
        url = f"{self.config.base_url.rstrip('/')}/api/v1/users/me"
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
                response = await client.get(url, headers=self._headers())
            return {
                "ok": response.is_success,
                "status_code": response.status_code,
                "url": url,
            }
        except Exception as exc:
            return {"ok": False, "error": str(exc), "url": url}

    async def fetch(self, **kwargs: Any) -> dict[str, Any]:
        tasks_url = f"{self.config.base_url.rstrip('/')}/api/v1/chores"
        label_filter = kwargs.get('label')
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
                response = await client.get(tasks_url, headers=self._headers())
                response.raise_for_status()
                data = response.json()
        except Exception:
            return {
                "tasks": [
                    {"id": "1", "title": "Take out trash", "completed": False, "labels": ["home"]},
                    {"id": "2", "title": "Replace HVAC filter", "completed": True, "labels": ["maintenance"]},
                ],
                "source": self.name,
                "fallback": True,
            }

        chores = data if isinstance(data, list) else data.get('chores', []) or data.get('items', [])
        tasks = []
        for chore in chores:
            labels = [label.get('name', label) if isinstance(label, dict) else str(label) for label in chore.get('labels', [])]
            if label_filter and label_filter not in labels:
                continue
            tasks.append({
                "id": str(chore.get('id')),
                "title": chore.get('name') or chore.get('title') or 'Untitled task',
                "completed": bool(chore.get('completed') or chore.get('isCompleted') or chore.get('done')),
                "labels": labels,
                "due": chore.get('dueDate') or chore.get('due_date'),
                "description": chore.get('description'),
                "metadata": chore,
            })

        return {"tasks": tasks, "source": self.name, "fallback": False}
""",
    "app/sources/home_assistant.py": """from __future__ import annotations
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
            return {"ok": response.is_success, "status_code": response.status_code, "url": url}
        except Exception as exc:
            return {"ok": False, "error": str(exc), "url": url}

    async def fetch(self, **kwargs: Any) -> dict[str, Any]:
        entity_id = kwargs.get('entity_id')
        if not entity_id:
            return {"tasks": [], "source": self.name, "error": "entity_id required"}

        url = f"{self.config.base_url.rstrip('/')}/api/states/{entity_id}"
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
                response = await client.get(url, headers=self._headers())
                response.raise_for_status()
                data = response.json()
        except Exception as exc:
            return {"tasks": [], "source": self.name, "error": str(exc)}

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
        return {"tasks": tasks, "source": self.name, "entity_id": entity_id}
""",
    "app/services/registry.py": """from __future__ import annotations
from app.core.config import DoneTickConfig, EscposOutputConfig, HomeAssistantConfig, MockOutputConfig, RawTcpOutputConfig
from app.outputs.escpos_python import EscposPythonOutput
from app.outputs.mock import MockOutput
from app.outputs.raw_tcp import RawTcpOutput
from app.sources.donetick import DoneTickSource
from app.sources.home_assistant import HomeAssistantSource


class SourceRegistry:
    def create(self, source_name: str, config: dict | None = None):
        config = config or {}
        if source_name == 'donetick':
            return DoneTickSource(DoneTickConfig(**config))
        if source_name == 'home_assistant':
            return HomeAssistantSource(HomeAssistantConfig(**config))
        raise ValueError(f'Unsupported source: {source_name}')


class OutputRegistry:
    def create(self, output_name: str, config: dict | None = None):
        config = config or {}
        if output_name == 'mock':
            backend = MockOutput()
            return backend, MockOutputConfig(**config)
        if output_name == 'escpos':
            backend = EscposPythonOutput()
            return backend, EscposOutputConfig(**config)
        if output_name == 'raw_tcp':
            backend = RawTcpOutput()
            return backend, RawTcpOutputConfig(**config)
        raise ValueError(f'Unsupported output: {output_name}')
""",
    "app/services/pipeline.py": """from __future__ import annotations
from typing import Any
from app.modules.todo import TodoModule
from app.renderers.receipt_80mm import Receipt80mmRenderer
from app.services.registry import OutputRegistry, SourceRegistry


class TodoPipeline:
    def __init__(self) -> None:
        self.source_registry = SourceRegistry()
        self.output_registry = OutputRegistry()
        self.module = TodoModule()
        self.renderer = Receipt80mmRenderer()

    async def preview(self, source_name: str = 'donetick', source_config: dict | None = None, source_options: dict | None = None) -> dict:
        source = self.source_registry.create(source_name, source_config)
        payload = await source.fetch(**(source_options or {}))
        document = await self.module.build(payload)
        receipt = self.renderer.render(document)
        return {
            'document': document.model_dump(),
            'receipt': receipt.model_dump(mode='json'),
            'source': source_name,
        }

    async def send(
        self,
        source_name: str = 'donetick',
        source_config: dict | None = None,
        source_options: dict | None = None,
        output_kind: str = 'mock',
        output_config: dict | None = None,
    ) -> dict:
        source = self.source_registry.create(source_name, source_config)
        payload = await source.fetch(**(source_options or {}))
        document = await self.module.build(payload)
        receipt = self.renderer.render(document)
        backend, cfg = self.output_registry.create(output_kind, output_config)
        return backend.send(receipt, **cfg.model_dump(exclude_none=True))
""",
    "app/api/routes/preview.py": """from fastapi import APIRouter
from pydantic import BaseModel, Field
from app.services.pipeline import TodoPipeline

router = APIRouter()

class PreviewRequest(BaseModel):
    source_name: str = 'donetick'
    source_config: dict = Field(default_factory=dict)
    source_options: dict = Field(default_factory=dict)

@router.post('/preview/todo')
async def preview_todo(request: PreviewRequest) -> dict:
    pipeline = TodoPipeline()
    return await pipeline.preview(**request.model_dump())
""",
    "app/api/routes/printing.py": """from fastapi import APIRouter
from pydantic import BaseModel, Field
from app.services.pipeline import TodoPipeline

router = APIRouter()

class PrintRequest(BaseModel):
    source_name: str = 'donetick'
    source_config: dict = Field(default_factory=dict)
    source_options: dict = Field(default_factory=dict)
    output_kind: str = 'mock'
    output_config: dict = Field(default_factory=dict)

@router.post('/print/todo')
async def print_todo(request: PrintRequest) -> dict:
    pipeline = TodoPipeline()
    return await pipeline.send(**request.model_dump())
""",
    "README.md": """# ThermaList v2 Scaffold

Standalone FastAPI scaffold for a modular thermal-printing app.

## Architecture

- Sources: external data providers like DoneTick and Home Assistant
- Modules: printable units like Todo
- Renderers: convert documents into receipt-oriented output
- Outputs: send rendered receipts to preview, python-escpos, or raw TCP

## Initial output strategy

- Primary: python-escpos
- Backup: raw TCP socket
- Dev/Test: mock output

## Source support

- DoneTick source with HTTP client and fallback sample data
- Home Assistant source for todo-style entity state reads
- Registry-based source/output selection

## Run

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Example preview request

```json
{
  "source_name": "donetick",
  "source_config": {
    "base_url": "http://donetick.local:2021",
    "token": "YOUR_TOKEN"
  },
  "source_options": {
    "label": "home"
  }
}
```

## Example print request

```json
{
  "source_name": "donetick",
  "source_config": {
    "base_url": "http://donetick.local:2021",
    "token": "YOUR_TOKEN"
  },
  "output_kind": "escpos",
  "output_config": {
    "host": "192.168.1.50",
    "port": 9100,
    "dry_run": true
  }
}
```
""",
}

for rel, content in updates.items():
    path = base / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)

print("updated")
