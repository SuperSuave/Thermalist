from __future__ import annotations

from typing import Any, Literal

from app.core.models import Document, DocumentSection, RecipeItem
from app.modules.base import Module

class RecipeModule(Module):
    name = "recipe"

    async def build(self, payload: dict[str, Any], **kwargs: Any) -> Document:
        
        recipe_data = payload.get("recipe")
        if recipe_data is None:
            raise ValueError("Recipe payload is missing 'recipe'")

        recipe = RecipeItem(**recipe_data)

        render_options = kwargs.get("render_options") or {}
        if hasattr(render_options, "model_dump"):
            render_options = render_options.model_dump(exclude_none=True)
        variant = render_options.get("variant", "cook-card")
        include_description = render_options.get("include_description", True)
        include_times = render_options.get("include_times", True)
        include_labels = render_options.get("include_labels", False)
        include_source_url = render_options.get("include_source_url", False)
        max_steps = render_options.get("max_steps")
        max_ingredients = render_options.get("max_ingredients")

        return build_recipe_document(
            recipe,
            variant=variant,
            include_description=include_description,
            include_times=include_times,
            include_labels=include_labels,
            include_source_url=include_source_url,
            max_steps=max_steps,
            max_ingredients=max_ingredients,
        )

RecipeVariant = Literal["cook-card", "ingredients-strip", "full-recipe"]

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
    sections: list[DocumentSection] = []

    sections.append(
        DocumentSection(
            kind="title",
            text=recipe.title,
        )
    )

    time_summary = _build_time_summary(recipe) if include_times else None
    if time_summary:
        sections.append(
            DocumentSection(
                kind="text",
                text=time_summary,
            )
        )

    if include_description and recipe.description:
        sections.append(
            DocumentSection(
                kind="text",
                text=recipe.description.strip(),
            )
        )

    if include_labels and recipe.labels:
        sections.append(
            DocumentSection(
                kind="label",
                text=" • ".join(recipe.labels),
            )
        )

    ingredients = recipe.ingredients[:max_ingredients] if max_ingredients else recipe.ingredients
    steps = recipe.steps[:max_steps] if max_steps else recipe.steps

    if variant == "ingredients-strip":
        if ingredients:
            sections.append(DocumentSection(kind="divider"))
            sections.append(
                DocumentSection(
                    kind="ingredient_list",
                    ingredients=ingredients,
                    metadata={"count": len(ingredients)},
                )
            )

    elif variant == "full-recipe":
        if ingredients:
            sections.append(DocumentSection(kind="divider"))
            sections.append(
                DocumentSection(
                    kind="text",
                    text="INGREDIENTS",
                )
            )
            sections.append(
                DocumentSection(
                    kind="ingredient_list",
                    ingredients=ingredients,
                    metadata={"count": len(ingredients)},
                )
            )

        if steps:
            sections.append(DocumentSection(kind="divider"))
            sections.append(
                DocumentSection(
                    kind="text",
                    text="STEPS",
                )
            )
            sections.append(
                DocumentSection(
                    kind="step_list",
                    steps=steps,
                    metadata={"count": len(steps)},
                )
            )

    else:  # cook-card
        if ingredients:
            sections.append(DocumentSection(kind="divider"))
            sections.append(
                DocumentSection(
                    kind="ingredient_list",
                    ingredients=ingredients,
                    metadata={"count": len(ingredients)},
                )
            )

        if steps:
            sections.append(DocumentSection(kind="divider"))
            sections.append(
                DocumentSection(
                    kind="step_list",
                    steps=steps,
                    metadata={"count": len(steps)},
                )
            )

    if include_source_url and recipe.source_url:
        sections.append(DocumentSection(kind="divider"))
        sections.append(
            DocumentSection(
                kind="text",
                text=recipe.source_url,
                metadata={"role": "source_url"},
            )
        )

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


def _build_time_summary(recipe: RecipeItem) -> str | None:
    line1: list[str] = []
    line2: list[str] = []

    if recipe.servings:
        line1.append(f"Serves {recipe.servings}")
    if recipe.prep_time:
        line1.append(f"Prep: {recipe.prep_time}")
    if recipe.cook_time:
        line2.append(f"Cook: {recipe.cook_time}")
    if recipe.total_time:
        line2.append(f"Total: {recipe.total_time}")

    parts: list[str] = []
    if line1:
        parts.append(" | ".join(line1))
    if line2:
        parts.append(" | ".join(line2))

    return "\n".join(parts) if parts else None
