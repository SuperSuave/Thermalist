import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from tests.fixtures.sample_recipe import sample_recipe


pytestmark = pytest.mark.anyio


async def test_preview_recipe_with_content_full_recipe_variant():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "module_name": "recipe",
            "content": {
                "recipe": sample_recipe.model_dump(),
            },
            "render_config": {"width": 32},
            "module_options": {
                "variant": "full-recipe",
                "include_description": True,
                "include_times": True,
                "include_labels": False,
                "include_source_url": False,
            },
        }

        response = await client.post("/preview", json=payload)
        assert response.status_code == 200

        data = response.json()
        document = data["document"]

        text_sections = [
            (s.get("text") or "").lower()
            for s in document["sections"]
            if s["kind"] == "text"
        ]
        assert "ingredients" in text_sections
        assert "steps" in text_sections


async def test_preview_recipe_with_content_returns_recipe_document():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "module_name": "recipe",
            "content": {
                "recipe": sample_recipe.model_dump(),
            },
            "render_config": {"width": 32},
        }

        response = await client.post("/preview", json=payload)
        assert response.status_code == 200

        data = response.json()
        document = data["document"]

        assert document["metadata"]["module"] == "recipe"
        assert document["metadata"]["recipe_id"] == "mealie-123"
        assert document["metadata"]["variant"] == "cook-card"
