from PIL import Image
from app.renderers.label_bitmap import (
    FontSet,
    LabelBitmapRenderer,
    LabelData,
    LabelThemeName,
    get_theme,
)


def test_render_standard_basic():
    theme = get_theme(LabelThemeName.FRAMED_FOOD)
    fonts = FontSet()
    renderer = LabelBitmapRenderer(theme=theme, fonts=fonts)

    data = LabelData(
        verb="OPENED",
        date_text="04/17/26",
        body="Salsa Verde Jar",
        subtext="Keep refrigerated",
    )

    img = renderer.render_standard(data)
    assert isinstance(img, Image.Image)
    assert img.mode == "L"
    assert img.width == theme.paper_width_px
    assert img.height > 0


def test_render_standard_without_subtext():
    theme = get_theme(LabelThemeName.FRAMED_FOOD)
    fonts = FontSet()
    renderer = LabelBitmapRenderer(theme=theme, fonts=fonts)

    data = LabelData(
        verb="PREPARED",
        date_text="04/17/26",
        body="Beef Stew Container",
        subtext=None,
    )

    img = renderer.render_standard(data)
    assert isinstance(img, Image.Image)
    assert img.mode == "L"
    assert img.width == theme.paper_width_px
    assert img.height > 0


def test_render_standard_minimal_theme():
    theme = get_theme(LabelThemeName.MINIMAL)
    fonts = FontSet()
    renderer = LabelBitmapRenderer(theme=theme, fonts=fonts)

    data = LabelData(
        verb="USE BY",
        date_text="04/20/26",
        body="Milk",
    )

    img = renderer.render_standard(data)
    assert isinstance(img, Image.Image)
    assert img.mode == "L"
    assert img.width == theme.paper_width_px


def test_render_standard_debug_guides():
    theme = get_theme(LabelThemeName.FRAMED_FOOD)
    theme.debug_guides = True
    fonts = FontSet()
    renderer = LabelBitmapRenderer(theme=theme, fonts=fonts)

    data = LabelData(
        verb="OPENED",
        date_text="04/17/26",
        body="Salsa",
        subtext="Subtext line",
    )

    img = renderer.render_standard(data)
    assert isinstance(img, Image.Image)
    assert img.mode == "RGB"
