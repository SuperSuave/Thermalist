from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, HttpUrl

import httpx

from app.core.models import RecipeItem
from app.services.recipe_import import RecipeImportError, import_recipe_from_url
from app.services.mealie_client import MealieClient
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


def get_mealie_client(
    settings: Annotated[Settings, Depends(get_settings)],
) -> MealieClient:
    if not settings.mealie_base_url or not settings.mealie_api_key:
        raise HTTPException(status_code=503, detail="Mealie is not configured.")

    return MealieClient(
        base_url=settings.mealie_base_url,
        api_key=settings.mealie_api_key,
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
    mealie: Annotated[MealieClient, Depends(get_mealie_client)],
    search: Annotated[str | None, Query(max_length=100)] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 50,
) -> MealieRecipeSummaryResponse:
    try:
        recipes = await mealie.list_recipes(
            search=search,
            page=page,
            per_page=per_page,
        )
        return MealieRecipeSummaryResponse(recipes=recipes)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to load Mealie recipes: {exc}",
        ) from exc


@router.get("/mealie/{slug_or_id}", response_model=MealieRecipeResponse)
async def get_mealie_recipe(
    slug_or_id: str,
    mealie: Annotated[MealieClient, Depends(get_mealie_client)],
) -> MealieRecipeResponse:
    try:
        recipe = await mealie.get_recipe(slug_or_id)
        return MealieRecipeResponse(recipe=recipe)
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to load Mealie recipes: {exc}",
        ) from exc