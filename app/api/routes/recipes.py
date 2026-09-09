from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, HttpUrl

import httpx

from app.core.models import RecipeItem
from app.services.recipe_import import RecipeImportError, import_recipe_from_url
from app.sources.mealie import MealieSource, MealieSourceConfig, MealieClient, fetch_mealie_recipe, MealieSourceOptions
from app.core.config import Settings, get_settings

router = APIRouter(prefix="/recipes", tags=["recipes"])


class ImportRecipeRequest(BaseModel):
    url: HttpUrl


class ImportRecipeResponse(BaseModel):
    recipe: RecipeItem


class MealieRecipeSummary(BaseModel):
    id: str
    slug: str
    name: str


class MealieRecipeSummaryResponse(BaseModel):
    recipes: list[MealieRecipeSummary]


class MealieRecipeResponse(BaseModel):
    recipe: RecipeItem


def get_mealie_config(
    settings: Annotated[Settings, Depends(get_settings)],
) -> MealieSourceConfig:
    if not settings.mealie_base_url or not settings.mealie_api_key:
        raise HTTPException(status_code=503, detail="Mealie is not configured.")

    return MealieSourceConfig(
        base_url=settings.mealie_base_url,
        token=settings.mealie_api_key,
    )


@router.post("/import", response_model=ImportRecipeResponse)
async def import_recipe(body: ImportRecipeRequest) -> ImportRecipeResponse:
    try:
        recipe = await import_recipe_from_url(str(body.url))
        return ImportRecipeResponse(recipe=recipe)
    except RecipeImportError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=500, detail="Recipe import failed")


@router.get("/mealie", response_model=MealieRecipeSummaryResponse)
async def list_mealie_recipes(
    config: Annotated[MealieSourceConfig, Depends(get_mealie_config)],
    search: Annotated[str | None, Query(max_length=100)] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 50,
) -> MealieRecipeSummaryResponse:
    try:
        client = MealieClient(config)
        try:
            items = await client.search_recipes(
                query_filter=search,
                page=page,
                per_page=per_page,
            )
        finally:
            await client.aclose()

        recipes = [
            MealieRecipeSummary(
                id=str(item.get("id") or item.get("slug") or ""),
                slug=str(item.get("slug") or item.get("id") or ""),
                name=str(item.get("name") or "Untitled Recipe"),
            )
            for item in items
            if item.get("slug") or item.get("id")
        ]
        return MealieRecipeSummaryResponse(recipes=recipes)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to load Mealie recipes: {exc}",
        ) from exc


@router.get("/mealie/{slug_or_id}", response_model=MealieRecipeResponse)
async def get_mealie_recipe(
    slug_or_id: str,
    config: Annotated[MealieSourceConfig, Depends(get_mealie_config)],
) -> MealieRecipeResponse:
    try:
        options = MealieSourceOptions(recipe_id=slug_or_id, slug=slug_or_id)
        recipe = await fetch_mealie_recipe(config, options)
        return MealieRecipeResponse(recipe=recipe)
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to load Mealie recipes: {exc}",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to load Mealie recipes: {exc}",
        ) from exc
