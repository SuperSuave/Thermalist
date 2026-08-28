import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


pytestmark = pytest.mark.anyio


class DummyMealieSource:
    def __init__(self, config):
        self.config = config
        self.fetched_with = None

    def init(self, payload):
        # Some sources may use this; keep a placeholder for symmetry
        self.payload = payload

    async def fetch(self, **options):
        # Record options for debugging if needed
        self.fetched_with = options

        # Minimal payload shape matching what your pipeline expects:
        # {"ok": True, "recipe": {...}}
        return {
            "ok": True,
            "recipe": {
                "id": "mealie-123",
                "title": "Chicken Kyiv",
                "description": "Garlic butter chicken with a crisp coating.",
                "servings": 4,
                "prep_time": "30 min",
                "cook_time": "25 min",
                "total_time": "55 min",
                "source_url": "https://example.com/chicken-kyiv",
                "ingredients": [
                    {
                        "text": "2 chicken breasts",
                        "quantity": "2",
                        "unit": None,
                        "item": "chicken breasts",
                    }
                ],
                "steps": [
                    {"number": 1, "text": "Butterfly the chicken breasts."},
                ],
                "labels": ["Dinner", "Chicken"],
            },
        }


async def test_preview_recipe_mealie_source(monkeypatch):
    # Patch SourceRegistry.create to return our dummy Mealie source when requested
    from app.services.registry import SourceRegistry

    original_create = SourceRegistry.create

    def fake_create(self, name, config=None):
        if name == "mealie":
            return DummyMealieSource(config)
        return original_create(self, name, config)

    monkeypatch.setattr(SourceRegistry, "create", fake_create)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "module_name": "recipe",
            "source_name": "mealie",
            "source_options": {
                "recipe_id": "dummy-id",
                "per_page": 1,
                "page": 1,
                "order_direction": "asc",
            },
            "render_config": {"width": 32},
        }

        response = await client.post("/preview", json=payload)
        assert response.status_code == 200

        data = response.json()
        document = data["document"]
        receipt = data["receipt"]

        # Document contract checks
        assert document["title"] == "Chicken Kyiv"
        assert document["metadata"]["module"] == "recipe"
        assert document["metadata"]["recipe_id"] == "mealie-123"
        assert any(s["kind"] == "ingredient_list" for s in document["sections"])
        assert any(s["kind"] == "step_list" for s in document["sections"])

        # Sanity check on rendered preview text
        preview = receipt["text_preview"].lower()
        assert "chicken kyiv" in preview
        assert "2 chicken breasts" in preview
        assert "butterfly" in preview