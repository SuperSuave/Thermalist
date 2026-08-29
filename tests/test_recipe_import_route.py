import pytest
from fastapi import FastAPI, APIRouter
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.core.models import RecipeIngredient, RecipeItem, RecipeStep
from app.services.recipe_import import RecipeImportError


pytestmark = pytest.mark.anyio


def get_all_route_paths(routes, current_prefix=""):
    paths = []
    for route in routes:
        prefix = current_prefix
        if hasattr(route, "include_context"):
            route_prefix = getattr(route.include_context, "prefix", "")
            prefix = prefix + route_prefix
        elif hasattr(route, "prefix"):
            prefix = prefix + getattr(route, "prefix", "")

        if hasattr(route, "path"):
            paths.append(prefix + route.path)

        if hasattr(route, "original_router") and hasattr(route.original_router, "routes"):
            paths.extend(get_all_route_paths(route.original_router.routes, current_prefix=prefix))
        elif hasattr(route, "routes") and route.routes and not hasattr(route, "path"):
            paths.extend(get_all_route_paths(route.routes, current_prefix=prefix))
    return paths


def test_recipes_route_is_registered():
    paths = get_all_route_paths(app.routes)
    assert "/recipes/import" in paths


def test_get_all_route_paths_supports_nested_included_routers():
    child_router = APIRouter(prefix="/child")

    @child_router.get("/endpoint")
    def child_endpoint():
        return {}

    parent_router = APIRouter(prefix="/parent")
    parent_router.include_router(child_router)

    test_app = FastAPI()
    test_app.include_router(parent_router, prefix="/api")

    paths = get_all_route_paths(test_app.routes)
    assert "/api/parent/child/endpoint" in paths


async def test_recipe_import_route_success(monkeypatch):
    from app.api.routes import recipes as recipes_route

    async def fake_import_recipe_from_url(url: str) -> RecipeItem:
        return RecipeItem(
            id="url-example-com-test-recipe",
            title="Test Recipe",
            description="A simple imported recipe.",
            servings=4,
            prep_time="15 min",
            cook_time="20 min",
            total_time="35 min",
            source_url=url,
            ingredients=[
                RecipeIngredient(
                    text="2 eggs",
                    quantity="2",
                    unit=None,
                    item="eggs",
                    original_text="2 eggs",
                )
            ],
            steps=[
                RecipeStep(number=1, text="Whisk the eggs."),
                RecipeStep(number=2, text="Cook until set."),
            ],
            labels=[],
        )

    monkeypatch.setattr(recipes_route, "import_recipe_from_url", fake_import_recipe_from_url)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/recipes/import",
            json={"url": "https://example.com/test-recipe"},
        )

    assert response.status_code == 200

    data = response.json()
    recipe = data["recipe"]

    assert recipe["title"] == "Test Recipe"
    assert recipe["source_url"] == "https://example.com/test-recipe"
    assert len(recipe["ingredients"]) == 1
    assert len(recipe["steps"]) == 2
    assert recipe["ingredients"][0]["text"] == "2 eggs"
    assert recipe["steps"][0]["text"] == "Whisk the eggs."


async def test_recipe_import_route_returns_400_on_import_error(monkeypatch):
    from app.api.routes import recipes as recipes_route

    async def fake_import_recipe_from_url(url: str):
        raise RecipeImportError("No recipe metadata found at this URL")

    monkeypatch.setattr(recipes_route, "import_recipe_from_url", fake_import_recipe_from_url)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/recipes/import",
            json={"url": "https://example.com/not-a-recipe"},
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "No recipe metadata found at this URL"
