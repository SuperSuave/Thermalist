from __future__ import annotations

from io import BytesIO

from fastapi import APIRouter, Body
from fastapi.responses import HTMLResponse, Response

from app.renderers.theme_layout_dispatcher import ThemeLayoutRenderer
from app.renderers.label_bitmap import FontSet

from app.api.models.theme_layout import (
    LabelLayout,
    RenderPayload,
    RenderRequest,
    ThemeStyle,
    ListRowData,
)

from app.renderers.label_bitmap import (
    LabelBitmapRenderer,
    LabelData,
    FontSet,
    get_theme,
)

router = APIRouter(prefix="/label-designer", tags=["label-designer"])


@router.get("", response_class=HTMLResponse)
async def preview_page() -> str:
    return """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>ThermaList Designer</title>
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
      <option value="compact">Compact</option>
      <option value="minimal">Minimal</option>
      <option value="bold">Bold</option>
      <option value="playful">Playful</option>
      <option value="reminders_notebook">Reminders Notebook</option>
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
  const res = await fetch('/label-designer/render', { method: 'POST', body: fd });
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
async def render_label(request: RenderRequest = Body(...)) -> Response:
    style = ThemeStyle(name=request.layout.name)
    renderer = ThemeLayoutRenderer(style=style, fonts=FontSet())
    image = renderer.render(request.layout, request.payload)

    buf = BytesIO()
    image.save(buf, format="PNG")
    return Response(content=buf.getvalue(), media_type="image/png")


async def preview_render(
    theme_name: Annotated[str, Form(...)],
    verb: Annotated[str, Form(...)],
    date_text: Annotated[str, Form(...)],
    body: Annotated[str, Form(...)],
    subtext: Annotated[str, Form()] = "",
    header_text_offset_y: Annotated[int, Form()] = 0,
    body_start_offset_y: Annotated[int, Form()] = 0,
    content_shift_y: Annotated[int, Form()] = 0,
    debug_guides: Annotated[bool, Form()] = False,
    guide_color: int = 160,
) -> Response:
    base_theme = get_theme(theme_name)
    theme = replace(
        base_theme,
        header_text_offset_y=header_text_offset_y,
        body_start_offset_y=body_start_offset_y,
        content_shift_y=content_shift_y,
        debug_guides=debug_guides,
    )

    renderer = LabelBitmapRenderer(theme=theme, fonts=FontSet())
    image = renderer.render(
        LabelData(
            verb=verb,
            date_text=date_text,
            body=body,
            subtext=subtext or None,
        )
    )

    buf = BytesIO()
    image.save(buf, format="PNG")
    return Response(content=buf.getvalue(), media_type="image/png")
