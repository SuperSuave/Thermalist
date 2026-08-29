from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

from app.api.models.requests import PrintRequest
from app.services.pipeline import PrintPipeline

router = APIRouter(prefix="/print", tags=["print"])
pipeline = PrintPipeline()


def effective_source_config(
    request: Request,
    source_name: str | None,
    body_source_config: dict[str, Any] | None,
) -> dict[str, Any] | None:
    app_cfg = request.app.state.config
    timezone = app_cfg.timezone

    if body_source_config:
        cfg = body_source_config.copy()
        cfg.setdefault("timezone", timezone)
        return cfg

    if not source_name:
        return None

    if source_name == "donetick":
        cfg = app_cfg.donetick
        return {
            "base_url": cfg.base_url,
            "token": cfg.token,
            "timezone": cfg.timezone or timezone,
        }

    if source_name == "mealie":
        cfg = app_cfg.mealie
        return {
            "base_url": cfg.base_url,
            "token": cfg.token,
            "timeout_seconds": cfg.timeout_seconds,
        }

    return None


def effective_output_config(
    request: Request,
    body_output_config: dict[str, Any] | None,
) -> dict[str, Any]:
    app_cfg = request.app.state.config
    tcp_cfg = app_cfg.raw_tcp
    renderer_cfg = app_cfg.renderer

    base = {
        "host": tcp_cfg.host,
        "port": tcp_cfg.port,
        "font": tcp_cfg.font,
        "width": renderer_cfg.width,
        "cut": tcp_cfg.cut,
        "initialize": tcp_cfg.initialize,
        "dry_run": tcp_cfg.dry_run,
    }

    if body_output_config:
        base.update(body_output_config)

    return base


def effective_render_config(
    request: Request,
    body_render_config: dict[str, Any] | None,
    output_cfg: dict[str, Any],
) -> dict[str, Any]:
    base = dict(output_cfg)

    if body_render_config:
        base.update(body_render_config)

    app_cfg = request.app.state.config
    base.setdefault(
        "bitmap_title_font_path",
        str(app_cfg.app_dir / "fonts" / "Dongle-Regular.ttf")
        if hasattr(app_cfg, "app_dir")
        else None,
    )
    base.setdefault(
        "bitmap_body_font_path",
        str(app_cfg.app_dir / "fonts" / "ElmsSans-Regular.ttf")
        if hasattr(app_cfg, "app_dir")
        else None,
    )
    base.setdefault(
        "bitmap_output_dir",
        str(app_cfg.app_dir / "generated_images")
        if hasattr(app_cfg, "app_dir")
        else None,
    )

    return base


def effective_render_options(body: PrintRequest) -> dict[str, Any]:
    opts = (
        body.render_options.model_dump(exclude_none=True)
        if hasattr(body.render_options, "model_dump")
        else dict(body.render_options)
    )
    if body.module_options:
        opts.update(body.module_options)
    return opts


@router.post("")
async def send_print_job(request: Request, body: PrintRequest) -> dict[str, Any]:
    source_cfg = effective_source_config(request, body.source_name, body.source_config)
    output_cfg = effective_output_config(request, body.output_config)
    render_cfg = effective_render_config(request, body.render_config, output_cfg)
    render_opts = effective_render_options(body)

    return await pipeline.send(
        module_name=body.module_name,
        content=body.content,
        source_name=body.source_name,
        source_config=source_cfg if body.source_name else None,
        source_options=body.source_options,
        output_kind=body.output_kind or "raw_tcp",
        output_config=output_cfg,
        render_config=render_cfg,
        render_options=render_opts,
        theme_name=body.theme_name,
        timezone=request.app.state.config.timezone,
    )
