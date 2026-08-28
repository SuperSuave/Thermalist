from app.modules.recipe import build_recipe_document
from app.renderers.receipt_80mm import Receipt80mmRenderer
from tests.fixtures.sample_recipe import sample_recipe


document = build_recipe_document(sample_recipe, variant="full-recipe")
print(document)
for section in document.sections:
    print(section.kind, section.ingredients, section.steps)
renderer = Receipt80mmRenderer()
result = renderer.render(document)

print(result.text_preview)