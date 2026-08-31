from app.modules.recipe import build_recipe_document
from app.renderers.receipt_80mm import Receipt80mmRenderer
from tests.fixtures.sample_recipe import sample_recipe


def test_recipe_preview_builds_full_recipe():
    document = build_recipe_document(sample_recipe, variant="full-recipe")
    renderer = Receipt80mmRenderer()
    result = renderer.render(document)

    assert document.title == "Chicken Kyiv"
    assert any(section.kind == "ingredient_list" for section in document.sections)
    assert any(section.kind == "step_list" for section in document.sections)

    assert "chicken kyiv" in result.text_preview.lower()
    assert "ingredients" in result.text_preview.lower()
    assert "steps" in result.text_preview.lower()
    assert "2 chicken breasts" in result.text_preview.lower()
    assert "1. butterfly the chicken breasts." in result.text_preview.lower()


def test_recipe_preview_cook_card_variant():
    document = build_recipe_document(sample_recipe, variant="cook-card")

    text_sections = [
        s.text
        for s in document.sections
        if s.kind == "text"
    ]
    assert "INGREDIENTS" not in text_sections
    assert "STEPS" not in text_sections
    assert any(s.kind == "ingredient_list" for s in document.sections)
    assert any(s.kind == "step_list" for s in document.sections)


def test_recipe_preview_ingredients_strip_variant():
    document = build_recipe_document(sample_recipe, variant="ingredients-strip")

    assert any(s.kind == "ingredient_list" for s in document.sections)
    assert not any(s.kind == "step_list" for s in document.sections)


def test_recipe_preview_options_labels_and_source_url():
    recipe_copy = sample_recipe.model_copy()
    recipe_copy.labels = ["Easy", "Dinner"]
    recipe_copy.source_url = "https://example.com/kyiv"

    document = build_recipe_document(
        recipe_copy,
        include_labels=True,
        include_source_url=True,
    )

    labels_section = next((s for s in document.sections if s.kind == "label"), None)
    assert labels_section is not None
    assert labels_section.text == "Easy • Dinner"

    source_section = next(
        (s for s in document.sections if s.kind == "text" and s.metadata.get("role") == "source_url"),
        None,
    )
    assert source_section is not None
    assert source_section.text == "https://example.com/kyiv"


def test_recipe_preview_options_max_ingredients_and_steps():
    document = build_recipe_document(
        sample_recipe,
        variant="cook-card",
        max_ingredients=1,
        max_steps=1,
    )

    ing_section = next(s for s in document.sections if s.kind == "ingredient_list")
    step_section = next(s for s in document.sections if s.kind == "step_list")

    assert len(ing_section.ingredients) == 1
    assert len(step_section.steps) == 1