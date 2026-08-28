from __future__ import annotations

from collections import OrderedDict
from datetime import datetime
import re
from typing import Any
from zoneinfo import ZoneInfo

from app.core.models import Document, DocumentSection, TaskItem
from app.modules.base import Module

TAG_RE = re.compile(r"<[^>]+>")


def _strip_tags(text: str | None) -> str | None:
    if text is None:
        return None
    cleaned = TAG_RE.sub("", text)
    cleaned = " ".join(cleaned.split())
    return cleaned


def _clean_text(text: str | None) -> str:
    return _strip_tags(text) or ""


def _format_due(value: Any, tz: ZoneInfo | None = None) -> str | None:
    if value is None:
        return None

    text = str(value).strip()
    if not text:
        return None

    try:
        dt_utc = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return text

    dt_local = dt_utc if tz is None else dt_utc.astimezone(tz)

    hour = dt_local.strftime("%I").lstrip("0") or "12"
    minute = dt_local.strftime("%M")
    ampm = dt_local.strftime("%p").lower()
    return f"{dt_local:%m/%d} - {hour}:{minute}{ampm}"


def _sanitize_subtask(
    sub: dict[str, Any],
    tz: ZoneInfo | None,
    *,
    show_due: bool,
    show_description: bool,
) -> dict[str, Any]:
    return {
        "id": str(sub.get("id", "")),
        "title": _clean_text(sub.get("title")),
        "completed": bool(sub.get("completed", False)),
        "labels": [],
        "due": _format_due(sub.get("due"), tz) if show_due else None,
        "description": _clean_text(sub.get("description")) if show_description else "",
        "metadata": sub.get("metadata") or {},
    }


def _sanitize_task(
    task: dict[str, Any],
    tz: ZoneInfo | None,
    *,
    show_due: bool,
    show_description: bool,
    show_subtasks: bool,
) -> dict[str, Any]:
    raw_subtasks = task.get("subtasks") or []

    return {
        "id": str(task.get("id", "")),
        "title": _clean_text(task.get("title")),
        "completed": bool(task.get("completed", False)),
        "labels": [_clean_text(lbl) for lbl in (task.get("labels") or []) if _clean_text(lbl)],
        "due": _format_due(task.get("due"), tz) if show_due else None,
        "description": _clean_text(task.get("description")) if show_description else "",
        "metadata": task.get("metadata") or {},
        "subtasks": [
            _sanitize_subtask(
                sub,
                tz,
                show_due=show_due,
                show_description=show_description,
            )
            for sub in raw_subtasks
        ] if show_subtasks else [],
    }


class TodoModule(Module):
    name = "todo"

    async def build(self, payload: dict[str, Any], **kwargs: Any) -> Document:
        tz_name = kwargs.get("timezone")
        tz = None
        if tz_name:
            try:
                tz = ZoneInfo(tz_name)
            except Exception as exc:
                print("ThermaList: failed to load timezone", tz_name, exc)
                tz = None

        render_options = kwargs.get("render_options") or {}
        if hasattr(render_options, "model_dump"):
            render_options = render_options.model_dump(exclude_none=True)
        show_labels = render_options.get("show_labels", True)
        show_due = render_options.get("show_due", True)
        show_description = render_options.get("show_description", True)
        show_subtasks = render_options.get("show_subtasks", True)

        raw_tasks = payload.get("tasks")

        tasks = [
            TaskItem(
                **_sanitize_task(
                    task,
                    tz,
                    show_due=show_due,
                    show_description=show_description,
                    show_subtasks=show_subtasks,
                )
            )
            for task in raw_tasks
        ]

        base_title = _strip_tags(payload.get("title") or payload.get("name")) or "Todo List"
        selected_label = _strip_tags(payload.get("label_filter"))
        title = selected_label or base_title

        grouped: OrderedDict[str, list[TaskItem]] = OrderedDict()

        for task in tasks:
            if selected_label and selected_label in task.labels:
                group_name = selected_label
            else:
                group_name = task.labels[0] if task.labels else "Unlabeled"

            grouped.setdefault(group_name, []).append(task)

        sections: list[DocumentSection] = [
            DocumentSection(kind="title", text=title)
        ]

        for group_name, group_tasks in grouped.items():
            should_show_group_heading = show_labels and group_name != selected_label

            if should_show_group_heading:
                sections.append(DocumentSection(kind="text", text=f"-- {group_name} --"))

            sections.append(DocumentSection(kind="task_list", tasks=group_tasks))

        return Document(
            title=title,
            sections=sections,
            metadata={
                "source": payload.get("source"),
                "label_filter": selected_label,
                "timezone": tz_name,
            },
        )
