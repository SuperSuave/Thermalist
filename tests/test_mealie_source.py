import pytest
import httpx
from unittest.mock import AsyncMock, patch

from app.core.config import MealieConfig
from app.sources.mealie import (
    MealieSource,
    MealieClient,
)

pytestmark = pytest.mark.anyio


async def test_mealie_source_fetch_recipe_id():
    config = MealieConfig(base_url="http://mealie.local", token="secret-token")
    source = MealieSource(config=config)

    req = httpx.Request("GET", "http://mealie.local/api/recipes/recipe-456")
    mock_resp = httpx.Response(
        200,
        request=req,
        json={
            "id": "recipe-456",
            "name": "Spaghetti Carbonara",
            "description": "Classic Roman pasta dish.",
            "recipeIngredient": [
                {"display": "200g spaghetti", "food": {"name": "spaghetti"}, "quantity": 200, "unit": {"name": "g"}}
            ],
            "recipeInstructions": [
                {"text": "Boil pasta until al dente."}
            ],
            "tags": [{"name": "Pasta"}],
            "recipeCategory": [{"name": "Italian"}],
        },
    )

    with patch.object(httpx.AsyncClient, "get", AsyncMock(return_value=mock_resp)):
        res = await source.fetch(recipe_id="recipe-456")

        assert res["ok"] is True
        assert res["source"] == "mealie"
        recipe = res["recipe"]
        assert recipe["id"] == "recipe-456"
        assert recipe["title"] == "Spaghetti Carbonara"
        assert len(recipe["ingredients"]) == 1
        assert len(recipe["steps"]) == 1
        assert "Pasta" in recipe["labels"]
        assert "Italian" in recipe["labels"]


async def test_mealie_source_fetch_search():
    config = MealieConfig(base_url="http://mealie.local", token="secret-token")
    source = MealieSource(config=config)

    req = httpx.Request("GET", "http://mealie.local/api/recipes")
    mock_resp = httpx.Response(
        200,
        request=req,
        json={
            "data": [
                {
                    "id": "recipe-789",
                    "name": "Pizza Margherita",
                    "recipeIngredient": [],
                    "recipeInstructions": [],
                }
            ]
        },
    )

    with patch.object(httpx.AsyncClient, "get", AsyncMock(return_value=mock_resp)):
        res = await source.fetch(slug="pizza-margherita")

        assert res["ok"] is True
        assert res["recipe"]["id"] == "recipe-789"


async def test_mealie_source_test_connection_success():
    config = MealieConfig(base_url="http://mealie.local", token="secret-token")
    source = MealieSource(config=config)

    req = httpx.Request("GET", "http://mealie.local/api/recipes")
    mock_resp = httpx.Response(
        200,
        request=req,
        json={"data": [{"id": "1", "name": "Recipe"}]},
    )

    with patch.object(httpx.AsyncClient, "get", AsyncMock(return_value=mock_resp)):
        res = await source.test_connection()

        assert res["ok"] is True
        assert res["source"] == "mealie"
        assert res["count"] == 1


async def test_mealie_source_fetch_error():
    config = MealieConfig(base_url="http://mealie.local", token="secret-token")
    source = MealieSource(config=config)

    with patch.object(httpx.AsyncClient, "get", AsyncMock(side_effect=httpx.HTTPError("Network failed"))):
        res = await source.fetch(recipe_id="1")

        assert res["ok"] is False
        assert res["recipe"] is None
        assert "Network failed" in res["error"]
