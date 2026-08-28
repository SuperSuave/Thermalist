from __future__ import annotations

from typing import Annotated
from io import BytesIO

from fastapi import APIRouter, Form
from fastapi.responses import HTMLResponse, Response

from app.renderers.theme_layout_dispatcher import ThemeLayoutRenderer
from app.renderers.label_bitmap import FontSet  # only for fonts

from app.api.models.theme import ThemeName, get_theme, Theme
from app.api.models.theme_layout import (
    LabelLayout,
    RenderPayload,
    ThemeStyle,  # thin wrapper for now
    ListRowData,
    GridColumn,
    ListColumn,
    TitleElement,
    GridElement,
    ListElement,
    LineElement,
)

router = APIRouter(prefix="/theme-designer", tags=["theme-designer"])


def theme_to_style(theme: Theme, layout_name: str, debug_guides: bool) -> ThemeStyle:
    return ThemeStyle(
        name=layout_name,
        title_font_size=theme.title_font_size,
        body_font_size=theme.body_font_size,
        badge_font_size=theme.badge_font_size,
        border_width=theme.border_width,
        corner_radius=theme.corner_radius,
        foreground=theme.foreground,
        background=theme.background,
        threshold=theme.threshold,
        debug_guides=debug_guides,
        debug_color=theme.debug_color,
        debug_margin_px=getattr(theme, "debug_margin_px", 8),
    )


def build_quickverb_layout() -> LabelLayout:
    # kind="quickverb" will tell ThemeLayoutRenderer to use the special label geometry
    return LabelLayout(
        name="quickverb",
        kind="quickverb",
        paper_width_px=640,
        outer_margin=18,
        inner_padding=18,
        elements=[],  # geometry comes from renderer + theme for this kind
    )


def build_notebook_simple_layout() -> LabelLayout:
    return LabelLayout(
        name="reminders_notebook_simple",
        paper_width_px=640,
        outer_margin=18,
        inner_padding=18,
        elements=[
            TitleElement(
                x=0,
                y=0,
                height=60,
                align="center",
                props={"bind": "title"},
            ),
            GridElement(
                x=0,
                y=70,
                height=40,
                columns=[
                    GridColumn(label="MONTH", width=0.7),
                    GridColumn(label="YEAR", width=0.3),
                ],
            ),
            ListElement(
                x=0,
                y=130,
                height=34,
                repeat=14,
                gap=0,
                columns=[
                    ListColumn(type="checkbox", width=0.15),
                    ListColumn(type="text", label="", width=0.85),
                ],
            ),
        ],
    )


def build_notebook_badges_layout() -> LabelLayout:
    return LabelLayout(
        name="reminders_notebook_badges",
        paper_width_px=640,
        outer_margin=18,
        inner_padding=18,
        elements=[
            TitleElement(
                x=0,
                y=0,
                height=60,
                align="center",
                props={"bind": "title"},
            ),
            GridElement(
                x=0,
                y=70,
                height=40,
                columns=[
                    GridColumn(label="MONTH", width=0.6),
                    GridColumn(label="YEAR", width=0.4),
                ],
            ),
            ListElement(
                x=0,
                y=130,
                height=34,
                repeat=14,
                gap=0,
                columns=[
                    ListColumn(type="checkbox", width=0.12),
                    ListColumn(type="text", label="", width=0.63),
                    ListColumn(type="badge", label="", width=0.25),
                ],
            ),
        ],
    )


def get_layout_for_variant(variant: str) -> LabelLayout:
    if variant == "notebook_badges":
        return build_notebook_badges_layout()
    if variant == "label_quickverb":
        return build_quickverb_layout()
    # Default
    return build_notebook_simple_layout()


@router.get("", response_class=HTMLResponse)
async def preview_page() -> str:
    return """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>ThermaList Theme Designer</title>
  <style>
    body { font-family: sans-serif; margin: 20px; display: grid; grid-template-columns: 360px 1fr; gap: 20px; }
    textarea, input, select { width: 100%; box-sizing: border-box; margin-bottom: 10px; }
    img { max-width: 100%; border: 1px solid #ccc; background: #fff; }
    label { display: block; font-size: 12px; margin-top: 8px; }
  </style>
</head>
<body>
  <form id="editor">
    <label>Theme</label>
    <select name="theme_name">
      <option value="framed_food">Framed Food</option>
      <option value="minimal">Minimal</option>
      <option value="bold">Bold</option>
      <option value="playful">Playful</option>
      <option value="reminders_notebook">Reminders Notebook</option>
    </select>

    <label>Layout variant</label>
    <select name="layout_variant">
      <option value="notebook_simple">Notebook – simple</option>
      <option value="notebook_badges">Notebook – with badges</option>
      <option value="label_quickverb">Quick Verb label</option>
    </select>

    <label>Title</label>
    <input name="verb" value="REMINDERS">

    <label>Date text</label>
    <input name="date_text" value="APR 2026">

    <label>Body</label>
    <textarea name="body" rows="6">Pay rent
Buy milk
Finish label preview</textarea>

    <label>Subtext</label>
    <textarea name="subtext" rows="3"></textarea>

    <label>Header text offset Y</label>
    <input name="header_text_offset_y" type="number" value="0">

    <label>Body start offset Y</label>
    <input name="body_start_offset_y" type="number" value="0">

    <label>Content shift Y</label>
    <input name="content_shift_y" type="number" value="0">

    <label>
      <input name="debug_guides" type="checkbox">
      Debug guides
    </label>
  </form>

  <div>
    <img id="preview" alt="label preview">
  </div>

<script>
const form = document.getElementById('editor');
const preview = document.getElementById('preview');

async function refresh() {
  const fd = new FormData(form);
  const res = await fetch('/theme-designer/render', { method: 'POST', body: fd });
  const blob = await res.blob();
  preview.src = URL.createObjectURL(blob);
}

form.addEventListener('input', refresh);
refresh();
</script>
</body>
</html>
"""


@router.post("/render")
async def render_label_form(
    theme_name: Annotated[str, Form(...)],
    layout_variant: Annotated[str, Form(...)] = "notebook_simple",
    verb: Annotated[str, Form(...)] = "",
    date_text: Annotated[str, Form(...)] = "",
    body: Annotated[str, Form(...)] = "",
    subtext: Annotated[str, Form()] = "",
    header_text_offset_y: Annotated[int, Form()] = 0,
    body_start_offset_y: Annotated[int, Form()] = 0,
    content_shift_y: Annotated[int, Form()] = 0,
    debug_guides: Annotated[bool, Form()] = False,
) -> Response:
    layout = get_layout_for_variant(layout_variant)

    parts = date_text.split()
    month = parts[0] if parts else ""
    year = parts[-1] if len(parts) > 1 else ""

    rows: list[ListRowData] = []

    if layout_variant in ("notebook_simple", "notebook_badges"):
        for line in body.splitlines():
            line = line.strip()
            if not line:
                continue

            if layout_variant == "notebook_badges":
                rows.append(ListRowData(values=[line, ""], checked=[False]))
            else:
                rows.append(ListRowData(values=[line], checked=[False]))
    else:
        # label_quickverb: rows are not used for geometry yet; payload.values will carry text
        rows = []

    payload = RenderPayload(
        title=verb,
        values={
            "month": month,
            "year": year,
            "date_text": date_text,
            "body": body,
            "subtext": subtext,
        },
        rows=rows,
    )

    theme_obj = get_theme(ThemeName(theme_name))
    style = theme_to_style(theme_obj, layout.name, debug_guides=debug_guides)

    renderer = ThemeLayoutRenderer(style=style, fonts=FontSet())
    image = renderer.render(layout, payload)

    buf = BytesIO()
    image.save(buf, format="PNG")
    return Response(content=buf.getvalue(), media_type="image/png")
