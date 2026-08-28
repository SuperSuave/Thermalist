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