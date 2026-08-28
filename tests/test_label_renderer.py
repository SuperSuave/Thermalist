from app.core.models import Document, DocumentSection
from app.renderers.receipt_80mm import Receipt80mmRenderer


def test_label_render_centers_short_note():
    renderer = Receipt80mmRenderer(width=32)

    document = Document(
        title="Label",
        sections=[
            DocumentSection(
                kind="label",
                text="OPENED",
                metadata={
                    "date": "04/17/26",
                    "note": "Salsa",
                },
            )
        ],
    )

    receipt = renderer.render(document)
    preview = receipt.text_preview
    lines = preview.splitlines()

    assert "+------------------------------+" in lines
    assert any("OPENED" in line and line.startswith("|") and line.endswith("|") for line in lines)
    assert any("04/17/26" in line and line.startswith("|") and line.endswith("|") for line in lines)
    assert any("Salsa" in line and line.startswith("|") and line.endswith("|") for line in lines)

def test_label_render_wraps_long_note_left_aligned():
    renderer = Receipt80mmRenderer(width=32)

    document = Document(
        title="Label",
        sections=[
            DocumentSection(
                kind="label",
                text="EXPIRES",
                metadata={
                    "date": "04/17/26",
                    "note": "Leftover chicken tortilla soup",
                },
            )
        ],
    )

    receipt = renderer.render(document)
    lines = receipt.text_preview.splitlines()

    assert "+------------------------------+" in lines
    assert any("EXPIRES" in line and line.startswith("|") and line.endswith("|") for line in lines)
    assert any("04/17/26" in line and line.startswith("|") and line.endswith("|") for line in lines)

    note_lines = [
        line for line in lines
        if line.startswith("|")
        and line.endswith("|")
        and "EXPIRES" not in line
        and "04/17/26" not in line
        and line.strip("| ").strip()
    ]

    assert len(note_lines) >= 2
    combined_note = " ".join(line.strip("| ").strip() for line in note_lines)
    assert "Leftover" in combined_note
    assert "chicken" in combined_note
    assert "tortilla" in combined_note
    assert "soup" in combined_note


def test_label_render_respects_width():
    renderer = Receipt80mmRenderer(width=32)

    document = Document(
        title="Label",
        sections=[
            DocumentSection(
                kind="label",
                text="MADE",
                metadata={
                    "date": "04/17/26",
                    "note": "Broth",
                },
            )
        ],
    )

    receipt = renderer.render(document)

    for line in receipt.text_preview.splitlines():
        if line:
            assert len(line) <= 32