from __future__ import annotations

from typing import Any, Literal
import httpx
from pydantic import BaseModel

from app.core.config import MealieConfig
from app.core.models import RecipeIngredient, RecipeItem, RecipeStep
from app.sources.base import Source


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


def map_mealie_recipe(raw: dict[str, Any]) -> RecipeItem:
    ingredients = []
    for item in raw.get("recipeIngredient") or []:
        if isinstance(item, str) and item.strip():
            ingredients.append(RecipeIngredient(text=item.strip(), original_text=item.strip()))
        elif isinstance(item, dict):
            orig_text = (item.get("originalText") or item.get("display") or item.get("note") or item.get("title") or "").strip()
            display_text = (item.get("display") or orig_text).strip()
            if display_text:
                food = item.get("food") or {}
                unit = item.get("unit") or {}
                ingredients.append(
                    RecipeIngredient(
                        text=display_text,
                        quantity=str(item.get("quantity")).strip() if item.get("quantity") not in (None, "") else None,
                        unit=unit.get("name") or unit.get("abbreviation"),
                        item=food.get("name"),
                        note=item.get("note"),
                        original_text=orig_text,
                        metadata={"mealie_id": item.get("id"), "reference_id": item.get("referenceId")},
                    )
                )

    steps = [
        RecipeStep(
            number=idx,
            text=(item.get("text") or item.get("title") or "").strip(),
            metadata={"mealie_id": item.get("id")},
        )
        for idx, item in enumerate(
            [s for s in (raw.get("recipeInstructions") or []) if (s.get("text") or s.get("title") or "").strip()],
            start=1,
        )
    ]

    tags = [t.get("name") for t in (raw.get("tags") or []) if t and t.get("name")]
    categories = [c.get("name") for c in (raw.get("recipeCategory") or []) if c and c.get("name")]

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
        labels=[*categories, *tags],
        metadata={
            "slug": raw.get("slug"),
            "image": raw.get("image"),
            "recipe_yield": raw.get("recipeYield"),
            "recipe_yield_quantity": raw.get("recipeYieldQuantity"),
            "recipe_category": categories,
            "tags": tags,
            "extras": raw.get("extras") or {},
        },
    )


async def fetch_mealie_recipe(
    source_config: MealieSourceConfig,
    source_options: MealieSourceOptions,
) -> RecipeItem:
    client = MealieClient(source_config)
    try:
        if source_options.recipe_id:
            try:
                raw = await client.get_recipe_by_id(source_options.recipe_id)
                return map_mealie_recipe(raw)
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code != 404 or not source_options.slug:
                    raise

        if source_options.slug:
            results = await client.search_recipes(
                slug=source_options.slug,
                query_filter=source_options.query_filter,
                per_page=source_options.per_page,
                page=source_options.page,
                order_by=source_options.order_by,
                order_direction=source_options.order_direction,
            )
            if results:
                return map_mealie_recipe(results[0])

        raise ValueError("No Mealie recipe matched the provided query")
    finally:
        await client.aclose()


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
            return {"ok": True, "source": self.name, "count": len(results)}
        except Exception as exc:
            return {"ok": False, "source": self.name, "error": str(exc)}
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
