import pytest

from app.services.exceptions import SourceFetchError
from app.services.pipeline import PrintPipeline


class DummySource:
    def __init__(self, payload):
        self.payload = payload

    async def fetch(self, **kwargs):
        return self.payload


class DummyModule:
    async def build(self, payload, **kwargs):
        return DummyDocument(payload)


class DummyDocument:
    def __init__(self, payload):
        self.payload = payload

    def model_dump(self):
        return {"payload": self.payload}


class DummyReceipt:
    def model_dump(self, mode="json"):
        return {"ok": True, "mode": mode}


class DummyRenderer:
    def render(self, document):
        return DummyReceipt()


pytestmark = pytest.mark.anyio


async def test_build_receipt_with_direct_content(monkeypatch):
    pipeline = PrintPipeline()

    monkeypatch.setattr(
        pipeline.module_registry,
        "create",
        lambda module_name: DummyModule(),
    )
    monkeypatch.setattr(
        pipeline,
        "_create_renderer",
        lambda render_config=None: DummyRenderer(),
    )

    document, receipt, resolved_source = await pipeline._build_receipt(
        module_name="recipe",
        content={"recipe": {"title": "Test Recipe", "ingredients": [], "steps": []}},
        render_options={},
    )

    assert resolved_source is None
    assert document.payload["recipe"]["title"] == "Test Recipe"
    assert receipt.model_dump()["ok"] is True


async def test_build_receipt_raises_on_source_failure(monkeypatch):
    pipeline = PrintPipeline()

    monkeypatch.setattr(
        pipeline.source_registry,
        "create",
        lambda source_name, source_config=None: DummySource(
            {
                "ok": False,
                "source": "mealie",
                "recipe": None,
                "fallback": False,
                "error": "boom",
            }
        ),
    )

    with pytest.raises(SourceFetchError, match="Source 'mealie' failed: boom"):
        await pipeline._build_receipt(
            module_name="recipe",
            source_name="mealie",
            source_config={"base_url": "http://example.com"},
            source_options={},
            render_options={},
        )


async def test_build_receipt_with_source_success(monkeypatch):
    pipeline = PrintPipeline()

    monkeypatch.setattr(
        pipeline.source_registry,
        "create",
        lambda source_name, source_config=None: DummySource(
            {
                "ok": True,
                "source": "mealie",
                "recipe": {
                    "title": "Soup",
                    "ingredients": [],
                    "steps": [],
                },
            }
        ),
    )
    monkeypatch.setattr(
        pipeline.module_registry,
        "create",
        lambda module_name: DummyModule(),
    )
    monkeypatch.setattr(
        pipeline,
        "_create_renderer",
        lambda render_config=None: DummyRenderer(),
    )

    document, receipt, resolved_source = await pipeline._build_receipt(
        module_name="recipe",
        source_name="mealie",
        source_config={"base_url": "http://example.com"},
        source_options={},
        render_options={},
    )

    assert resolved_source == "mealie"
    assert "recipe" in document.payload
    assert document.payload["recipe"]["title"] == "Soup"
    assert receipt.model_dump()["ok"] is True