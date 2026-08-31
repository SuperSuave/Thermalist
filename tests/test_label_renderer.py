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


def test_save_label_preview_prevents_path_traversal():
    from PIL import Image
    from app.services.label_bitmap_service import save_label_preview, GENERATED_IMAGE_DIR

    img = Image.new("RGB", (100, 100), color="white")

    # Path traversal payload
    result = save_label_preview(img, label_name="../../traversal_test_file")

    assert result["gray_path"] == "/generated_images/traversal_test_file.png"
    assert result["bw_path"] == "/generated_images/traversal_test_file-bw.png"
    assert (GENERATED_IMAGE_DIR / "traversal_test_file.png").exists()
    assert (GENERATED_IMAGE_DIR / "traversal_test_file-bw.png").exists()

    # Clean up test files
    (GENERATED_IMAGE_DIR / "traversal_test_file.png").unlink(missing_ok=True)
    (GENERATED_IMAGE_DIR / "traversal_test_file-bw.png").unlink(missing_ok=True)


def test_save_label_preview_handles_empty_or_dot_label_name():
    from PIL import Image
    from app.services.label_bitmap_service import save_label_preview, GENERATED_IMAGE_DIR

    img = Image.new("RGB", (100, 100), color="white")

    label_png = GENERATED_IMAGE_DIR / "label.png"
    label_bw_png = GENERATED_IMAGE_DIR / "label-bw.png"

    orig_png_bytes = label_png.read_bytes() if label_png.exists() else None
    orig_bw_bytes = label_bw_png.read_bytes() if label_bw_png.exists() else None

    try:
        result = save_label_preview(img, label_name="..")

        assert result["gray_path"] == "/generated_images/label.png"
        assert result["bw_path"] == "/generated_images/label-bw.png"
        assert label_png.exists()
        assert label_bw_png.exists()
    finally:
        if orig_png_bytes is not None:
            label_png.write_bytes(orig_png_bytes)
        else:
            label_png.unlink(missing_ok=True)

        if orig_bw_bytes is not None:
            label_bw_png.write_bytes(orig_bw_bytes)
        else:
            label_bw_png.unlink(missing_ok=True)
