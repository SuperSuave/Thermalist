from __future__ import annotations

from typing import Any
from fastapi import APIRouter, HTTPException, Request

from app.api.models.requests import PrintRequest
from app.services.exceptions import SourceFetchError
from app.services.pipeline import PrintPipeline

router = APIRouter(prefix="/preview", tags=["preview"])
pipeline = PrintPipeline()


def effective_source_config(request: Request, source_name: str | None, body_source_config: dict[str, Any] | None) -> dict[str, Any] | None:
    app_cfg = request.app.state.config
    tz = app_cfg.timezone
    if body_source_config:
        cfg = body_source_config.copy()
        cfg.setdefault("timezone", tz)
        return cfg
    if not source_name:
        return None
    if source_name == "donetick":
        cfg = app_cfg.donetick
        return {"base_url": cfg.base_url, "token": cfg.token, "timezone": cfg.timezone or tz}
    if source_name == "mealie":
        cfg = app_cfg.mealie
        return {"base_url": cfg.base_url, "token": cfg.token, "timeout_seconds": cfg.timeout_seconds}
    return None


def effective_output_config(request: Request, body_output_config: dict[str, Any] | None) -> dict[str, Any]:
    app_cfg = request.app.state.config
    base = {
        "host": app_cfg.raw_tcp.host,
        "port": app_cfg.raw_tcp.port,
        "font": app_cfg.raw_tcp.font,
        "width": app_cfg.renderer.width,
        "cut": app_cfg.raw_tcp.cut,
        "initialize": app_cfg.raw_tcp.initialize,
        "dry_run": app_cfg.raw_tcp.dry_run,
    }
    if body_output_config:
        base.update(body_output_config)
    return base


def effective_render_config(request: Request, body_render_config: dict[str, Any] | None, output_cfg: dict[str, Any]) -> dict[str, Any]:
    base = dict(output_cfg)
    if body_render_config:
        base.update(body_render_config)
    return base


def effective_render_options(body: PrintRequest) -> dict[str, Any]:
    opts = body.render_options.model_dump(exclude_none=True) if hasattr(body.render_options, "model_dump") else dict(body.render_options)
    if body.module_options:
        opts.update(body.module_options)
    return opts


@router.post("")
async def preview(request: Request, body: PrintRequest) -> dict[str, Any]:
    source_cfg = effective_source_config(request, body.source_name, body.source_config)
    output_cfg = effective_output_config(request, body.output_config)
    render_cfg = effective_render_config(request, body.render_config, output_cfg)
    render_opts = effective_render_options(body)

    try:
        return await pipeline.preview(
            module_name=body.module_name,
            content=body.content,
            source_name=body.source_name,
            source_config=source_cfg if body.source_name else None,
            source_options=body.source_options,
            render_config=render_cfg,
            render_options=render_opts,
            theme_name=body.theme_name,
            timezone=request.app.state.config.timezone,
        )
    except SourceFetchError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
