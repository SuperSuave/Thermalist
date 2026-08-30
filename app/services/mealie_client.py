from __future__ import annotations

from typing import Any

import httpx
from app.core.models import RecipeIngredient, RecipeItem, RecipeStep


class MealieClient:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        *,
        timeout: float = 20.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    async def list_recipes(
        self,
        *,
        search: str | None = None,
        page: int = 1,
        per_page: int = 50,
    ) -> list[dict[str, str]]:
        params: dict[str, Any] = {
            "page": page,
            "perPage": per_page,
        }
        if search:
            params["search"] = search

        async with httpx.AsyncClient(
            base_url=self.base_url,
            headers=self._headers,
            timeout=self.timeout,
        ) as client:
            resp = await client.get("/api/recipes", params=params)
            resp.raise_for_status()
            data = resp.json()

        items = data.get("items") or []
        results: list[dict[str, str]] = []

        for item in items:
            slug = item.get("slug") or item.get("id") or ""
            name = item.get("name") or "Untitled Recipe"
            recipe_id = item.get("id") or slug
            if not slug:
                continue

            results.append(
                {
                    "id": str(recipe_id),
                    "slug": str(slug),
                    "name": str(name),
                }
            )

        return results

    async def get_recipe(self, slug_or_id: str) -> RecipeItem:
        async with httpx.AsyncClient(
            base_url=self.base_url,
            headers=self._headers,
            timeout=self.timeout,
        ) as client:
            resp = await client.get(f"/api/recipes/{slug_or_id}")
            if resp.status_code == 404:
                resp = await client.get(
                    "/api/recipes", params={"page": 1, "perPage": 100}
                )
                resp.raise_for_status()
                listing = resp.json().get("items") or []
                matched = next(
                    (
                        item
                        for item in listing
                        if item.get("slug") == slug_or_id
                        or item.get("id") == slug_or_id
                    ),
                    None,
                )
                if not matched:
                    raise httpx.HTTPStatusError(
                        "Recipe not found",
                        request=resp.request,
                        response=resp,
                    )

                resolved_id = matched.get("id")
                detail = await client.get(f"/api/recipes/{resolved_id}")
                detail.raise_for_status()
                data = detail.json()
            else:
                resp.raise_for_status()
                data = resp.json()

        return self._to_recipe_item(data)

    def _to_recipe_item(self, data: dict[str, Any]) -> RecipeItem:
        ingredients = self._parse_ingredients(data)
        steps = self._parse_steps(data)

        recipe_id = data.get("id")
        name = data.get("name") or "Untitled Recipe"
        description = data.get("description")

        total_time = self._combine_time_parts(
            prep=data.get("prepTime"),
            cook=data.get("cookTime"),
            total=data.get("totalTime"),
        )

        recipe_yield = (
            data.get("recipeYield") or data.get("yield") or data.get("servings")
        )

        source_url = data.get("orgURL") or data.get("sourceUrl")

        return RecipeItem(
            title=name,
            description=description,
            yield_amount=str(recipe_yield) if recipe_yield not in (None, "") else None,
            prep_time=data.get("prepTime"),
            cook_time=data.get("cookTime"),
            total_time=total_time,
            ingredients=ingredients,
            steps=steps,
            source_url=source_url,
            image_url=data.get("image"),
            tags=self._parse_tags(data),
        )

    def _parse_ingredients(self, data: dict[str, Any]) -> list[RecipeIngredient]:
        raw_ingredients = data.get("recipeIngredient") or []
        parsed: list[RecipeIngredient] = []

        for item in raw_ingredients:
            if isinstance(item, str):
                parsed.append(RecipeIngredient(text=item.strip()))
                continue

            if not isinstance(item, dict):
                continue

            note = item.get("note")
            quantity = item.get("quantity")
            unit = self._extract_name(item.get("unit"))
            food = self._extract_name(item.get("food"))
            display = item.get("display")

            parts = [
                str(quantity).strip() if quantity not in (None, "") else None,
                unit.strip() if unit else None,
                food.strip() if food else None,
            ]
            text = " ".join(part for part in parts if part)

            if note:
                text = f"{text} ({note})" if text else str(note)

            if not text and display:
                text = str(display).strip()

            if text:
                parsed.append(RecipeIngredient(text=text))

        return parsed

    def _parse_steps(self, data: dict[str, Any]) -> list[RecipeStep]:
        raw_instructions = data.get("recipeInstructions") or []
        parsed: list[RecipeStep] = []

        for index, item in enumerate(raw_instructions, start=1):
            if isinstance(item, str):
                text = item.strip()
            elif isinstance(item, dict):
                text = (
                    item.get("text")
                    or item.get("description")
                    or item.get("title")
                    or ""
                ).strip()
            else:
                text = ""

            if text:
                parsed.append(RecipeStep(number=index, text=text))

        return parsed

    def _parse_tags(self, data: dict[str, Any]) -> list[str] | None:
        raw_tags = data.get("tags") or []
        tags: list[str] = []

        for item in raw_tags:
            if isinstance(item, str):
                value = item.strip()
            elif isinstance(item, dict):
                value = str(item.get("name") or "").strip()
            else:
                value = ""

            if value:
                tags.append(value)

        return tags or None

    @staticmethod
    def _extract_name(value: Any) -> str | None:
        if isinstance(value, dict):
            name = value.get("name")
            return str(name).strip() if name else None
        if isinstance(value, str):
            return value.strip() or None
        return None

    @staticmethod
    def _combine_time_parts(
        *,
        prep: str | None,
        cook: str | None,
        total: str | None,
    ) -> str | None:
        if total:
            return str(total)

        parts: list[str] = []
        if prep:
            parts.append(f"Prep: {prep}")
        if cook:
            parts.append(f"Cook: {cook}")

        return " | ".join(parts) if parts else None
