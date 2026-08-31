import pytest
from app.api.models.theme_layout import (
    LabelLayout,
    ListColumn,
    ListElement,
    ListRowData,
    RenderPayload,
    ThemeStyle,
)
from app.renderers.label_bitmap import FontSet
from app.renderers.theme_layout_dispatcher import ThemeLayoutRenderer


@pytest.fixture
def dummy_fonts():
    return FontSet()


@pytest.fixture
def default_style():
    return ThemeStyle(name="Default")


def test_draw_list_empty_columns(default_style, dummy_fonts):
    renderer = ThemeLayoutRenderer(style=default_style, fonts=dummy_fonts)
    layout = LabelLayout(name="Test Layout", paper_width_px=384, outer_margin=10)

    element = ListElement(
        x=0,
        y=0,
        repeat=3,
        height=30,
        gap=5,
        columns=[],
    )
    layout.elements = [element]

    payload = RenderPayload(title="Test List", rows=[])
    img = renderer.render(layout, payload)

    assert img is not None
    assert img.width == 384


def test_draw_list_with_columns(default_style, dummy_fonts):
    renderer = ThemeLayoutRenderer(style=default_style, fonts=dummy_fonts)
    layout = LabelLayout(name="Test Layout", paper_width_px=384, outer_margin=10)

    cols = [
        ListColumn(type="checkbox", width=1.0),
        ListColumn(type="text", width=3.0, label="Item"),
        ListColumn(type="badge", width=2.0, label="Status"),
    ]

    element = ListElement(
        x=0,
        y=0,
        repeat=2,
        height=34,
        gap=5,
        columns=cols,
    )
    layout.elements = [element]

    rows = [
        ListRowData(checked=[True], values=["Buy milk for breakfast", "URGENT"]),
        ListRowData(checked=[False], values=["Clean kitchen table", "DONE"]),
    ]
    payload = RenderPayload(title="Todo List", rows=rows)

    img = renderer.render(layout, payload)

    assert img is not None
    assert img.width == 384


def test_draw_list_fallback_labels(default_style, dummy_fonts):
    renderer = ThemeLayoutRenderer(style=default_style, fonts=dummy_fonts)
    layout = LabelLayout(name="Test Layout", paper_width_px=384, outer_margin=10)

    cols = [
        ListColumn(type="text", width=2.0, label="Default Text"),
        ListColumn(type="badge", width=2.0, label="Default Badge"),
    ]

    element = ListElement(
        x=0,
        y=0,
        repeat=1,
        height=34,
        columns=cols,
    )
    layout.elements = [element]

    payload = RenderPayload(title="List", rows=[])
    img = renderer.render(layout, payload)

    assert img is not None
    assert img.width == 384
