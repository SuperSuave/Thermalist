from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Request

from app.api.models.requests import PrintRequest
from app.api.routes.preview import (
    effective_source_config,
    effective_output_config,
    effective_render_config,
    effective_render_options,
)
from app.services.pipeline import PrintPipeline

router = APIRouter(prefix="/print", tags=["print"])
pipeline = PrintPipeline()


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
