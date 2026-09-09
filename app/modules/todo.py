from __future__ import annotations

from collections import OrderedDict
from datetime import datetime
import re
from typing import Any
from zoneinfo import ZoneInfo

from app.core.models import Document, DocumentSection, TaskItem
from app.modules.base import Module

TAG_RE = re.compile(r"<[^>]+>")


def _clean_text(text: str | None) -> str:
    if not text:
        return ""
    cleaned = TAG_RE.sub("", text)
    return " ".join(cleaned.split())


def _format_due(value: Any, tz: ZoneInfo | None = None) -> str | None:
    if not value:
        return None
    text = str(value).strip()
    try:
        dt_utc = datetime.fromisoformat(text.replace("Z", "+00:00"))
        dt_local = dt_utc if tz is None else dt_utc.astimezone(tz)
        hour = dt_local.strftime("%I").lstrip("0") or "12"
        return f"{dt_local:%m/%d} - {hour}:{dt_local:%M}{dt_local.strftime('%p').lower()}"
    except ValueError:
        return text


def _sanitize_item(
    item: dict[str, Any],
    tz: ZoneInfo | None,
    *,
    show_due: bool,
    show_description: bool,
    show_subtasks: bool = False,
) -> dict[str, Any]:
    raw_subs = item.get("subtasks") or []
    return {
        "id": str(item.get("id", "")),
        "title": _clean_text(item.get("title")),
        "completed": bool(item.get("completed", False)),
        "labels": [_clean_text(l) for l in (item.get("labels") or []) if _clean_text(l)],
        "due": _format_due(item.get("due"), tz) if show_due else None,
        "description": _clean_text(item.get("description")) if show_description else "",
        "metadata": item.get("metadata") or {},
        "subtasks": [
            _sanitize_item(sub, tz, show_due=show_due, show_description=show_description, show_subtasks=False)
            for sub in raw_subs
        ] if show_subtasks else [],
    }


class TodoModule(Module):
    name = "todo"

    async def build(self, payload: dict[str, Any], **kwargs: Any) -> Document:
        tz_name = kwargs.get("timezone")
        tz = ZoneInfo(tz_name) if tz_name else None

        opts = kwargs.get("render_options") or {}
        if hasattr(opts, "model_dump"):
            opts = opts.model_dump(exclude_none=True)

        show_labels = opts.get("show_labels", True)
        show_due = opts.get("show_due", True)
        show_description = opts.get("show_description", True)
        show_subtasks = opts.get("show_subtasks", True)

        raw_tasks = payload.get("tasks") or []
        tasks = [
            TaskItem(**_sanitize_item(t, tz, show_due=show_due, show_description=show_description, show_subtasks=show_subtasks))
            for t in raw_tasks
        ]

        base_title = _clean_text(payload.get("title") or payload.get("name")) or "Todo List"
        selected_label = _clean_text(payload.get("label_filter"))
        title = selected_label or base_title

        grouped: OrderedDict[str, list[TaskItem]] = OrderedDict()
        for task in tasks:
            group_name = selected_label if (selected_label and selected_label in task.labels) else (task.labels[0] if task.labels else "Unlabeled")
            grouped.setdefault(group_name, []).append(task)

        sections: list[DocumentSection] = [DocumentSection(kind="title", text=title)]
        for group_name, group_tasks in grouped.items():
            if show_labels and group_name != selected_label:
                sections.append(DocumentSection(kind="text", text=f"-- {group_name} --"))
            sections.append(DocumentSection(kind="task_list", tasks=group_tasks))

        return Document(
            title=title,
            sections=sections,
            metadata={"source": payload.get("source"), "label_filter": selected_label, "timezone": tz_name},
        )
