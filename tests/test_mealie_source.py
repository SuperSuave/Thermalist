import pytest
import httpx
from unittest.mock import AsyncMock, patch

from app.core.config import MealieConfig
from app.sources.mealie import (
    MealieSource,
    MealieClient,
    parse_ingredient_line,
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


@pytest.mark.parametrize(
    "line, expected_quantity, expected_unit, expected_item, expected_note",
    [
        ("2 cups flour", "2", "cups", "flour", None),
        ("1/2 tsp salt", "1/2", "tsp", "salt", None),
        ("1 1/2 cups milk", "11/2", "cups", "milk", None),
        ("1.5 kg sugar", "1.5", "kg", "sugar", None),
        ("1-2 cloves garlic", "1-2", "cloves", "garlic", None),
        ("Salt and black pepper", None, None, "Salt and black pepper", None),
        ("cloves garlic", None, "cloves", "garlic", None),
        ("1 cup flour (sifted)", "1", "cup", "flour", "sifted"),
        ("1 cup flour (sifted) (organic)", "1", "cup", "flour", "sifted; organic"),
        ("2 tbsp butter for frying", "2", "tbsp", "butter", "for frying"),
        ("   3   tbsp   olive   oil   ", "3", "tbsp", "olive oil", None),
        ("2 cups", "2", "cups", "2 cups", None),
        ("", None, None, "", None),
        ("   ", None, None, "", None),
    ],
)
def test_parse_ingredient_line(line, expected_quantity, expected_unit, expected_item, expected_note):
    res = parse_ingredient_line(line)
    assert res.quantity == expected_quantity
    assert res.unit == expected_unit
    assert res.item == expected_item
    assert res.note == expected_note
