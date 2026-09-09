from __future__ import annotations

from typing import Any, Literal

from app.core.models import Document, DocumentSection, RecipeItem
from app.modules.base import Module

RecipeVariant = Literal["cook-card", "ingredients-strip", "full-recipe"]


class RecipeModule(Module):
    name = "recipe"

    async def build(self, payload: dict[str, Any], **kwargs: Any) -> Document:
        recipe_data = payload.get("recipe")
        if recipe_data is None:
            raise ValueError("Recipe payload is missing 'recipe'")

        recipe = RecipeItem(**recipe_data)
        opts = kwargs.get("render_options") or {}
        if hasattr(opts, "model_dump"):
            opts = opts.model_dump(exclude_none=True)

        return build_recipe_document(
            recipe,
            variant=opts.get("variant", "cook-card"),
            include_description=opts.get("include_description", True),
            include_times=opts.get("include_times", True),
            include_labels=opts.get("include_labels", False),
            include_source_url=opts.get("include_source_url", False),
            max_steps=opts.get("max_steps"),
            max_ingredients=opts.get("max_ingredients"),
        )


def _build_time_summary(recipe: RecipeItem) -> str | None:
    l1, l2 = [], []
    if recipe.servings:
        l1.append(f"Serves {recipe.servings}")
    if recipe.prep_time:
        l1.append(f"Prep: {recipe.prep_time}")
    if recipe.cook_time:
        l2.append(f"Cook: {recipe.cook_time}")
    if recipe.total_time:
        l2.append(f"Total: {recipe.total_time}")
    parts = [p for p in [" | ".join(l1), " | ".join(l2)] if p]
    return "\n".join(parts) if parts else None


def build_recipe_document(
    recipe: RecipeItem,
    *,
    variant: RecipeVariant = "cook-card",
    include_description: bool = True,
    include_times: bool = True,
    include_labels: bool = False,
    include_source_url: bool = False,
    max_steps: int | None = None,
    max_ingredients: int | None = None,
) -> Document:
    ingredients = recipe.ingredients[:max_ingredients] if max_ingredients else recipe.ingredients
    steps = recipe.steps[:max_steps] if max_steps else recipe.steps

    sections: list[DocumentSection] = [DocumentSection(kind="title", text=recipe.title)]

    time_summary = _build_time_summary(recipe) if include_times else None
    if time_summary:
        sections.append(DocumentSection(kind="text", text=time_summary))
    if include_description and recipe.description:
        sections.append(DocumentSection(kind="text", text=recipe.description.strip()))
    if include_labels and recipe.labels:
        sections.append(DocumentSection(kind="label", text=" • ".join(recipe.labels)))

    show_headers = (variant == "full-recipe")
    if ingredients and variant in ("cook-card", "ingredients-strip", "full-recipe"):
        sections.append(DocumentSection(kind="divider"))
        if show_headers:
            sections.append(DocumentSection(kind="text", text="INGREDIENTS"))
        sections.append(DocumentSection(kind="ingredient_list", ingredients=ingredients, metadata={"count": len(ingredients)}))

    if steps and variant in ("cook-card", "full-recipe"):
        sections.append(DocumentSection(kind="divider"))
        if show_headers:
            sections.append(DocumentSection(kind="text", text="STEPS"))
        sections.append(DocumentSection(kind="step_list", steps=steps, metadata={"count": len(steps)}))

    if include_source_url and recipe.source_url:
        sections.extend([
            DocumentSection(kind="divider"),
            DocumentSection(kind="text", text=recipe.source_url, metadata={"role": "source_url"}),
        ])

    return Document(
        title=recipe.title,
        sections=sections,
        metadata={
            "module": "recipe",
            "variant": variant,
            "recipe_id": recipe.id,
            "servings": recipe.servings,
        },
    )
