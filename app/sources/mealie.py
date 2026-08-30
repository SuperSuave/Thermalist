from __future__ import annotations

from typing import Any, Literal

import httpx
import re
from pydantic import BaseModel

from app.core.config import MealieConfig
from app.core.models import RecipeIngredient, RecipeItem, RecipeStep
from app.sources.base import Source

class MealieSource(Source):
    name = "mealie"

    def __init__(self, config: MealieConfig | None = None) -> None:
        self.config = config or MealieConfig()

    async def test_connection(self) -> dict[str, Any]:
        client = MealieClient(
            MealieSourceConfig(
                base_url=self.config.base_url,
                token=self.config.token,
                timeout_seconds=self.config.timeout_seconds,
            )
        )
        try:
            results = await client.search_recipes(per_page=1, page=1)
            return {
                "ok": True,
                "source": self.name,
                "count": len(results),
            }
        except Exception as exc:
            return {
                "ok": False,
                "source": self.name,
                "error": str(exc),
            }
        finally:
            await client.aclose()

    async def fetch(self, **kwargs: Any) -> dict[str, Any]:
        try:
            source_options = MealieSourceOptions(
                recipe_id=kwargs.get("recipe_id"),
                slug=kwargs.get("slug"),
                query_filter=kwargs.get("query_filter"),
                per_page=kwargs.get("per_page", 1),
                page=kwargs.get("page", 1),
                order_by=kwargs.get("order_by"),
                order_direction=kwargs.get("order_direction", "asc"),
            )

            recipe = await fetch_mealie_recipe(
                MealieSourceConfig(
                    base_url=self.config.base_url,
                    token=self.config.token,
                    timeout_seconds=self.config.timeout_seconds,
                ),
                source_options,
            )

            return {
                "ok": True,
                "source": self.name,
                "recipe": recipe.model_dump(),
                "fallback": False,
            }
        except Exception as exc:
            return {
                "ok": False,
                "source": self.name,
                "recipe": None,
                "fallback": False,
                "error": str(exc),
            }

UNIT_ALIASES = {
    "teaspoon", "teaspoons", "tsp",
    "tablespoon", "tablespoons", "tbsp",
    "cup", "cups",
    "ounce", "ounces", "oz",
    "pound", "pounds", "lb", "lbs",
    "gram", "grams", "g",
    "kilogram", "kilograms", "kg",
    "milliliter", "milliliters", "ml",
    "liter", "liters", "l",
    "clove", "cloves",
    "pinch", "dash",
    "can", "cans",
    "package", "packages",
    "slice", "slices",
    "stick", "sticks",
}

QTY_RE = re.compile(
    r"""^\s*
    (?P<quantity>
        \d+(?:\s+\d/\d)? |
        \d/\d |
        \d+(?:\.\d+)? |
        \d+\s*-\s*\d+
    )
    \s*
    (?P<rest>.*)
    $""",
    re.X,
)

PAREN_RE = re.compile(r"\(([^)]*)\)")


def parse_ingredient_line(line: str) -> RecipeIngredient:
    original = " ".join(line.split())
    quantity = None
    unit = None
    note = None
    item = original

    m = QTY_RE.match(original)
    if m:
        quantity = m.group("quantity").replace(" ", "")
        rest = m.group("rest").strip()
    else:
        rest = original

    lower = rest.lower().split()
    if lower:
        first = lower[0].rstrip(",")
        if first in UNIT_ALIASES:
            unit = first
            rest = rest[len(rest.split()[0]):].strip()

    parens = PAREN_RE.findall(rest)
    if parens:
        note = "; ".join(p.strip() for p in parens if p.strip()) or None
        rest = PAREN_RE.sub("", rest).strip()

    if " for " in rest.lower():
        head, tail = rest.split(" for ", 1)
        rest = head.strip()
        note = f"for {tail.strip()}" if tail.strip() else note

    item = " ".join(rest.split()).strip(" ,;")
    if not item:
        item = original

    return RecipeIngredient(
        text=original,
        quantity=quantity,
        unit=unit,
        item=item,
        note=note,
        original_text=original,
    )


class MealieSourceConfig(BaseModel):
    base_url: str
    token: str
    timeout_seconds: int = 10


class MealieSourceOptions(BaseModel):
    recipe_id: str | None = None
    slug: str | None = None
    query_filter: str | None = None
    per_page: int = 1
    page: int = 1
    order_by: str | None = None
    order_direction: Literal["asc", "desc"] = "asc"


class MealieClient:
    def __init__(self, config: MealieSourceConfig) -> None:
        self.config = config
        self._client = httpx.AsyncClient(
            base_url=config.base_url.rstrip("/"),
            timeout=config.timeout_seconds,
            headers={
                "Authorization": f"Bearer {config.token}",
                "Accept": "application/json",
            },
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def close(self) -> None:
        await self._client.aclose()

    async def get_recipe_by_id(self, recipe_id: str) -> dict[str, Any]:
        response = await self._client.get(f"/api/recipes/{recipe_id}")
        response.raise_for_status()
        return response.json()

    async def search_recipes(
        self,
        *,
        slug: str | None = None,
        query_filter: str | None = None,
        per_page: int = 1,
        page: int = 1,
        order_by: str | None = None,
        order_direction: str = "asc",
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {
            "perPage": per_page,
            "page": page,
            "orderDirection": order_direction,
        }
        if query_filter:
            params["queryFilter"] = query_filter
        elif slug:
            params["queryFilter"] = f'slug = "{slug}"'
        if order_by:
            params["orderBy"] = order_by

        response = await self._client.get("/api/recipes", params=params)
        response.raise_for_status()
        payload = response.json()
        return payload.get("data", [])

def _extract_ingredient_text(raw: dict[str, Any]) -> str:
    return (
        raw.get("display")
        or raw.get("note")
        or raw.get("originalText")
        or raw.get("title")
        or ""
    ).strip()


def _map_ingredient(raw: dict[str, Any]) -> RecipeIngredient:
    food = raw.get("food") or {}
    unit = raw.get("unit") or {}

    original_text = (
        raw.get("display")
        or raw.get("originalText")
        or raw.get("note")
        or raw.get("title")
        or ""
    ).strip()

    parsed = parse_ingredient_line(original_text)

    return RecipeIngredient(
        text=parsed.text or original_text,
        quantity=str(raw.get("quantity")).strip() if raw.get("quantity") not in (None, "") else parsed.quantity,
        unit=unit.get("name") or unit.get("abbreviation") or parsed.unit,
        item=food.get("name") or parsed.item,
        note=raw.get("note") or parsed.note,
        original_text=raw.get("originalText") or original_text,
        metadata={
            "mealie_id": raw.get("id"),
            "reference_id": raw.get("referenceId"),
        },
    )


def _map_step(raw: dict[str, Any], number: int) -> RecipeStep:
    return RecipeStep(
        number=number,
        text=(raw.get("text") or raw.get("title") or "").strip(),
        metadata={
            "mealie_id": raw.get("id"),
        },
    )


def map_mealie_recipe(raw: dict[str, Any]) -> RecipeItem:
    ingredients = [
        _map_ingredient(item)
        for item in raw.get("recipeIngredient", [])
        if _extract_ingredient_text(item)
    ]

    steps = [
        _map_step(item, idx)
        for idx, item in enumerate(raw.get("recipeInstructions", []), start=1)
        if (item.get("text") or item.get("title"))
    ]

    tags = [tag.get("name") for tag in raw.get("tags", []) if tag.get("name")]
    categories = [
        category.get("name")
        for category in raw.get("recipeCategory", [])
        if category.get("name")
    ]

    labels = [*categories, *tags]

    return RecipeItem(
        id=raw["id"],
        title=raw.get("name", "").strip() or "Untitled Recipe",
        description=raw.get("description"),
        servings=raw.get("recipeServings"),
        prep_time=raw.get("prepTime"),
        cook_time=raw.get("cookTime"),
        total_time=raw.get("totalTime"),
        source_url=raw.get("orgURL"),
        ingredients=ingredients,
        steps=steps,
        labels=labels,
        metadata={
            "slug": raw.get("slug"),
            "image": raw.get("image"),
            "recipe_yield": raw.get("recipeYield"),
            "recipe_yield_quantity": raw.get("recipeYieldQuantity"),
            "recipe_category": categories,
            "tags": tags,
            "extras": raw.get("extras", {}),
        },
    )


async def fetch_mealie_recipe(
    source_config: MealieSourceConfig,
    source_options: MealieSourceOptions,
) -> RecipeItem:
    client = MealieClient(source_config)
    try:
        if source_options.recipe_id:
            raw = await client.get_recipe_by_id(source_options.recipe_id)
            return map_mealie_recipe(raw)

        results = await client.search_recipes(
            slug=source_options.slug,
            query_filter=source_options.query_filter,
            per_page=source_options.per_page,
            page=source_options.page,
            order_by=source_options.order_by,
            order_direction=source_options.order_direction,
        )

        if not results:
            raise ValueError("No Mealie recipe matched the provided query")

        return map_mealie_recipe(results[0])
    finally:
        await client.aclose()
