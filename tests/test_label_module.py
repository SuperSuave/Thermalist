import pytest

from app.modules.label import LabelModule


pytestmark = pytest.mark.anyio


async def test_label_builds_document_with_verb_date_and_note():
    module = LabelModule()

    document = await module.build(
        {
            "verb": "Opened",
            "date": "04/17/26",
            "note": "Salsa Verde Jar",
        }
    )

    assert document.title == "OPENED"
    assert len(document.sections) == 1

    section = document.sections[0]
    assert section.kind == "label"
    assert section.text == "OPENED"
    assert section.metadata["date"] == "04/17/26"
    assert section.metadata["note"] == "Salsa Verde Jar"


async def test_label_allows_blank_note():
    module = LabelModule()

    document = await module.build(
        {
            "verb": "Due",
            "date": "04/17/26",
            "note": "",
        }
    )

    section = document.sections[0]
    assert section.kind == "label"
    assert section.text == "DUE"
    assert section.metadata["date"] == "04/17/26"
    assert section.metadata["note"] == ""


async def test_label_raises_when_verb_missing():
    module = LabelModule()

    with pytest.raises(ValueError, match=r"Label payload is missing 'verb'"):
        await module.build({})

