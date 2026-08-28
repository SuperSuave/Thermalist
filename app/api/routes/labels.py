from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.api.models.requests import PrintRequest
from app.renderers.label_bitmap import LabelThemeName, LabelData
from app.services.exceptions import SourceFetchError
from app.services.label_bitmap_service import LabelBitmapService

router = APIRouter(prefix="/labels", tags=["labels"])


class ThemeOption(BaseModel):
    value: str
    label: str


@router.get("/themes")
async def list_label_themes() -> list[ThemeOption]:
    return [{"value": theme.value, "label": theme.label} for theme in LabelThemeName]


@router.post("/preview")
async def preview_label(request: Request, body: PrintRequest) -> dict[str, Any]:
    try:
        data = LabelData(
            verb=(body.content or {}).get("verb", "Opened"),
            date_text=(body.content or {}).get("date", ""),
            body=(body.content or {}).get("note", ""),
            subtext=(body.content or {}).get("subtext"),
        )

        label_name = "label"

        service = LabelBitmapService(
            theme_name=body.theme_name,
            title_font_path=body.render_config.get("bitmap_title_font_path")
            if body.render_config
            else None,
            body_font_path=body.render_config.get("bitmap_body_font_path")
            if body.render_config
            else None,
        )

        result = service.render_and_save(data, label_name=label_name)

        # Convert filesystem paths to browser URLs
        gray_path = result.get("gray_path", "")
        bw_path = result.get("bw_path", "")

        from pathlib import Path as PathLib

        gray_name = PathLib(gray_path).name if gray_path else ""
        bw_name = PathLib(bw_path).name if bw_path else ""

        return {
            "gray_path": f"/generated_images/{gray_name}",
            "bw_path": f"/generated_images/{bw_name}",
            "width": result.get("width"),
            "height": result.get("height"),
            "theme_name": body.theme_name,
            "module": "label",
        }
    except SourceFetchError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/print")
async def print_label(request: Request, body: PrintRequest) -> dict[str, Any]:
    data = LabelData(
        verb=(body.content or {}).get("verb", "Opened"),
        date_text=(body.content or {}).get("date", ""),
        body=(body.content or {}).get("note", ""),
        subtext=(body.content or {}).get("subtext"),
    )

    label_name = "label"

    service = LabelBitmapService(
        theme_name=body.theme_name,
        title_font_path=body.render_config.get("bitmap_title_font_path")
        if body.render_config
        else None,
        body_font_path=body.render_config.get("bitmap_body_font_path")
        if body.render_config
        else None,
    )

    image = service.render_label(data)

    from app.services.label_bitmap_service import save_label_preview

    save_result = save_label_preview(
        image, label_name=label_name, threshold=service.theme.threshold
    )

    from app.services.label_bitmap_service import print_label_network

    app_config = request.app.state.config

    body_output_config = body.output_config or {}
    host = body_output_config.get("host", app_config.raw_tcp.host)
    port = body_output_config.get("port", app_config.raw_tcp.port)

    print_result = print_label_network(image, host=host, port=port)

    from pathlib import Path as PathLib

    gray_path = save_result.get("gray_path", "")
    bw_path = save_result.get("bw_path", "")
    gray_name = PathLib(gray_path).name if gray_path else ""
    bw_name = PathLib(bw_path).name if bw_path else ""

    return {
        **print_result,
        "gray_path": f"/generated_images/{gray_name}",
        "bw_path": f"/generated_images/{bw_name}",
        "width": save_result.get("width"),
        "height": save_result.get("height"),
        "theme_name": body.theme_name,
        "module": "label",
    }
