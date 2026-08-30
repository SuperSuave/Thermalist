from app.modules.recipe import build_recipe_document
from app.renderers.receipt_80mm import Receipt80mmRenderer
from app.sources.mealie import (
    MealieSourceConfig,
    MealieSourceOptions,
    fetch_mealie_recipe,
)


import asyncio


async def main() -> None:
    source_config = MealieSourceConfig(
        base_url="https://demo.mealie.io",
        token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJsb25nX3Rva2VuIjp0cnVlLCJpZCI6ImM3OTM2YWE4LWJhNzctNDRmNC1hNTVkLTlmZDU4NTM2MGI3MCIsIm5hbWUiOiJ0ZXN0MiIsImludGVncmF0aW9uX2lkIjoiZ2VuZXJpYyIsImV4cCI6MTkzNDA3ODc4OH0.TH3u0Ky-LEPDThg_6yP0gN8yfQ1qY2nQn6MLIWXkltE",
        timeout_seconds=10,
    )

    source_options = MealieSourceOptions(
        recipe_id="easy-hummus-better-than-store-bought",
        # slug="your-recipe-slug",
        # query_filter='name = "Hummus"',
        per_page=1,
        page=1,
        order_direction="asc",
    )

    recipe = await fetch_mealie_recipe(source_config, source_options)
    document = build_recipe_document(
        recipe,
        variant="full-recipe",
        include_description=True,
        include_times=True,
        include_labels=False,
        include_source_url=True,
    )

    renderer = Receipt80mmRenderer()
    result = renderer.render(document)

    print(result.text_preview)


if __name__ == "__main__":
    asyncio.run(main())
