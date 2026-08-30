import pytest
import httpx
from unittest.mock import AsyncMock, patch

from app.core.config import MealieConfig
from app.sources.mealie import (
    MealieSource,
    MealieClient,
    map_mealie_recipe,
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


def test_map_mealie_recipe_full_data():
    raw_recipe = {
        "id": "mealie-123",
        "name": "Guacamole ",
        "description": "Fresh avocado dip.",
        "recipeServings": 4,
        "prepTime": "10m",
        "cookTime": "0m",
        "totalTime": "10m",
        "orgURL": "https://example.com/guacamole",
        "slug": "guacamole",
        "image": "http://example.com/guacamole.jpg",
        "recipeYield": "2 cups",
        "recipeYieldQuantity": 2,
        "extras": {"rating": 5},
        "recipeIngredient": [
            {
                "id": "ing-1",
                "referenceId": "ref-1",
                "display": "2 avocados",
                "quantity": 2,
                "food": {"name": "avocados"},
                "unit": {"name": "whole"},
                "note": "ripe",
                "originalText": "2 ripe avocados",
            },
            {
                "id": "ing-2",
                "note": "1 tsp salt",
            },
        ],
        "recipeInstructions": [
            {"id": "step-1", "text": "Mash avocados."},
            {"id": "step-2", "title": "Season with salt and lime."},
        ],
        "tags": [{"name": "Dip"}, {"name": "Mexican"}, {"name": None}],
        "recipeCategory": [{"name": "Appetizer"}],
    }

    recipe_item = map_mealie_recipe(raw_recipe)

    assert recipe_item.id == "mealie-123"
    assert recipe_item.title == "Guacamole"
    assert recipe_item.description == "Fresh avocado dip."
    assert recipe_item.servings == 4
    assert recipe_item.prep_time == "10m"
    assert recipe_item.cook_time == "0m"
    assert recipe_item.total_time == "10m"
    assert recipe_item.source_url == "https://example.com/guacamole"

    # Check ingredients
    assert len(recipe_item.ingredients) == 2
    ing1 = recipe_item.ingredients[0]
    assert ing1.text == "2 avocados"
    assert ing1.quantity == "2"
    assert ing1.unit == "whole"
    assert ing1.item == "avocados"
    assert ing1.note == "ripe"
    assert ing1.original_text == "2 ripe avocados"
    assert ing1.metadata == {"mealie_id": "ing-1", "reference_id": "ref-1"}

    ing2 = recipe_item.ingredients[1]
    assert ing2.text == "1 tsp salt"
    assert ing2.note == "1 tsp salt"

    # Check steps
    assert len(recipe_item.steps) == 2
    assert recipe_item.steps[0].number == 1
    assert recipe_item.steps[0].text == "Mash avocados."
    assert recipe_item.steps[0].metadata == {"mealie_id": "step-1"}

    assert recipe_item.steps[1].number == 2
    assert recipe_item.steps[1].text == "Season with salt and lime."

    # Check labels (categories + tags)
    assert recipe_item.labels == ["Appetizer", "Dip", "Mexican"]

    # Check metadata
    assert recipe_item.metadata["slug"] == "guacamole"
    assert recipe_item.metadata["image"] == "http://example.com/guacamole.jpg"
    assert recipe_item.metadata["recipe_yield"] == "2 cups"
    assert recipe_item.metadata["recipe_yield_quantity"] == 2
    assert recipe_item.metadata["recipe_category"] == ["Appetizer"]
    assert recipe_item.metadata["tags"] == ["Dip", "Mexican"]
    assert recipe_item.metadata["extras"] == {"rating": 5}


def test_map_mealie_recipe_defaults_and_edge_cases():
    raw_recipe = {
        "id": "mealie-empty",
        "name": "   ",  # whitespace only -> fallback to Untitled Recipe
        "recipeIngredient": [
            {},  # empty ingredient dict -> filtered out
            {"display": "   "},  # whitespace display -> filtered out
            {"title": "1 cup flour"},  # valid title fallback
        ],
        "recipeInstructions": [
            {},  # empty step dict -> filtered out
            {"text": "   "},  # whitespace text -> filtered out
            {"text": "Mix well."},  # valid step
        ],
        "tags": None,
        "recipeCategory": None,
    }

    recipe_item = map_mealie_recipe(raw_recipe)

    assert recipe_item.id == "mealie-empty"
    assert recipe_item.title == "Untitled Recipe"
    assert recipe_item.description is None
    assert recipe_item.servings is None
    assert recipe_item.ingredients[0].text == "1 cup flour"
    assert len(recipe_item.ingredients) == 1
    assert len(recipe_item.steps) == 1
    assert recipe_item.steps[0].number == 1
    assert recipe_item.steps[0].text == "Mix well."
    assert recipe_item.labels == []
    assert recipe_item.metadata["tags"] == []
    assert recipe_item.metadata["recipe_category"] == []
    assert recipe_item.metadata["extras"] == {}
