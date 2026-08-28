from app.core.models import RecipeIngredient, RecipeItem, RecipeStep


sample_recipe = RecipeItem(
    id="mealie-123",
    title="Chicken Kyiv",
    description="Garlic butter chicken with a crisp coating.",
    servings=4,
    prep_time="30 min",
    cook_time="25 min",
    total_time="55 min",
    source_url="https://example.com/chicken-kyiv",
    ingredients=[
        RecipeIngredient(
            text="2 chicken breasts",
            quantity="2",
            unit=None,
            item="chicken breasts",
        ),
        RecipeIngredient(
            text="4 tbsp butter",
            quantity="4",
            unit="tbsp",
            item="butter",
        ),
        RecipeIngredient(
            text="2 cloves garlic, minced",
            quantity="2",
            unit="cloves",
            item="garlic",
        ),
        RecipeIngredient(
            text="1 cup breadcrumbs",
            quantity="1",
            unit="cup",
            item="breadcrumbs",
        ),
    ],
    steps=[
        RecipeStep(number=1, text="Butterfly the chicken breasts."),
        RecipeStep(number=2, text="Mix butter and garlic, then chill into a small log."),
        RecipeStep(number=3, text="Wrap the butter in chicken, coat with breadcrumbs, and seal."),
        RecipeStep(number=4, text="Bake until golden brown and cooked through."),
    ],
    labels=["Dinner", "Chicken"],
)