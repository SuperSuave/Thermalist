from fastapi import APIRouter, HTTPException, Request

from app.core.config import DoneTickConfig
from app.sources.donetick import DoneTickSource

router = APIRouter(tags=["donetick"])


@router.get("/sources/donetick/labels")
async def get_donetick_labels(request: Request):
    cfg = request.app.state.config.source

    source = DoneTickSource(
        DoneTickConfig(
            base_url=cfg.base_url,
            token=cfg.token,
        )
    )

    result = await source.fetch()

    if not result.get("ok"):
        raise HTTPException(
            status_code=502,
            detail=result.get("error", "Failed to load DoneTick tasks"),
        )

    labels = sorted(
        {
            label.strip()
            for task in result.get("tasks", [])
            for label in (task.get("labels") or [])
            if isinstance(label, str) and label.strip()
        },
        key=str.lower,
    )

    return {
        "ok": True,
        "labels": labels,
        "count": len(labels),
    }