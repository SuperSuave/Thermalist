import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.exceptions import SourceFetchError

pytestmark = pytest.mark.anyio


async def test_preview_returns_400_on_pipeline_value_error(monkeypatch):
    async def fake_preview(**kwargs):
        raise SourceFetchError("Source 'mealie' failed: boom")

    monkeypatch.setattr(
        "app.api.routes.preview.pipeline.preview",
        fake_preview,
    )

    payload = {
        "module_name": "recipe",
        "source_name": "mealie",
        "source_options": {"slug": "chicken-kyiv"},
        "render_options": {
            "variant": "full-recipe",
            "include_description": True,
            "include_times": True,
            "include_labels": False,
            "include_source_url": False,
        },
    }

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post("/preview", json=payload)

    assert response.status_code == 400
    assert response.json()["detail"] == "Source 'mealie' failed: boom"