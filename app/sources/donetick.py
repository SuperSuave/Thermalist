from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import httpx

from app.core.config import DoneTickConfig
from app.sources.base import Source


class DoneTickSource(Source):
    name = "donetick"

    def __init__(self, config: DoneTickConfig | None = None) -> None:
        self.config = config or DoneTickConfig()

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if self.config.token:
            headers["secretkey"] = self.config.token
            headers["secret"] = self.config.token
        return headers

    def _resolve_tz(self) -> ZoneInfo | None:
        if not self.config.timezone:
            return None
        try:
            return ZoneInfo(self.config.timezone)
        except Exception:
            return None

    def _parse_due(self, value: Any, tz: ZoneInfo | None = None) -> datetime | None:
        if not value:
            return None
        try:
            dt = datetime.fromisoformat(str(value).strip().replace("Z", "+00:00"))
            return dt.astimezone(tz) if tz and dt.tzinfo else (dt.replace(tzinfo=tz) if tz else dt)
        except ValueError:
            return None

    def _matches_date_filter(self, due_dt: datetime | None, now: datetime, date_filter: str, include_overdue: bool) -> bool:
        if date_filter == "all":
            return True
        if due_dt is None:
            return False
        due_date, today = due_dt.date(), now.date()
        if date_filter == "overdue":
            return due_date < today
        if date_filter == "today":
            return due_date == today or (include_overdue and due_date < today)
        if date_filter == "tomorrow":
            return due_date == today + timedelta(days=1) or (include_overdue and due_date < (today + timedelta(days=1)))
        if date_filter == "next_7_days":
            return (today <= due_date <= today + timedelta(days=7)) or (include_overdue and due_date < today)
        return True

    async def test_connection(self) -> dict[str, Any]:
        url = f"{self.config.base_url.rstrip('/')}/eapi/v1/chore"
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
                res = await client.get(url, headers=self._headers())
            return {"ok": res.is_success, "status_code": res.status_code, "url": url, "body_preview": res.text[:300]}
        except Exception as exc:
            return {"ok": False, "error": str(exc), "url": url}

    @staticmethod
    def _extract_labels(raw_labels: Any) -> list[str]:
        if not isinstance(raw_labels, list):
            return []
        return [l.get("name", l) if isinstance(l, dict) else str(l) for l in raw_labels]

    def _format_task(self, chore: dict[str, Any], raw_subtasks: Any) -> dict[str, Any]:
        raw_labels = chore.get("labelsV2") or chore.get("labels") or []
        labels = self._extract_labels(raw_labels)
        due_val = chore.get("nextDueDate") or chore.get("dueDate") or chore.get("due_date")
        completed = bool(chore.get("completed") or chore.get("isCompleted") or chore.get("done") or chore.get("status") == 1)

        subtasks = []
        if isinstance(raw_subtasks, list):
            for sub in raw_subtasks:
                sub_completed = bool(sub.get("completed") or sub.get("isCompleted") or sub.get("done") or sub.get("completedAt") or sub.get("status") == 1)
                subtasks.append({
                    "id": str(sub.get("id")),
                    "title": sub.get("name") or sub.get("title") or "Untitled subtask",
                    "completed": sub_completed,
                    "labels": self._extract_labels(sub.get("labels") or []),
                    "due": sub.get("nextDueDate") or sub.get("dueDate") or sub.get("due_date"),
                    "description": sub.get("description"),
                    "metadata": sub,
                })

        return {
            "id": str(chore.get("id")),
            "title": chore.get("name") or chore.get("title") or "Untitled task",
            "completed": completed,
            "labels": labels,
            "due": due_val,
            "description": chore.get("description"),
            "metadata": chore,
            "subtasks": subtasks,
        }

    async def fetch(self, **kwargs: Any) -> dict[str, Any]:
        base = self.config.base_url.rstrip("/")
        list_url = f"{base}/eapi/v1/chore"
        label_filter = kwargs.get("label_filter") or kwargs.get("label")
        date_filter = kwargs.get("date_filter", "all")
        include_overdue = bool(kwargs.get("include_overdue", False))
        if date_filter == "overdue":
            include_overdue = False

        tz = self._resolve_tz()
        now = datetime.now(tz) if tz else datetime.now()

        try:
            async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
                res = await client.get(list_url, headers=self._headers())
                res.raise_for_status()
                data = res.json()
        except Exception as exc:
            return {"ok": False, "tasks": [], "source": self.name, "fallback": False, "error": str(exc)}

        chores = data if isinstance(data, list) else (data.get("chores") or data.get("items") or [])
        filtered = []
        for c in chores:
            labels = self._extract_labels(c.get("labelsV2") or c.get("labels") or [])
            if label_filter and label_filter not in labels:
                continue
            due_val = c.get("nextDueDate") or c.get("dueDate") or c.get("due_date")
            if not self._matches_date_filter(self._parse_due(due_val, tz), now, date_filter, include_overdue):
                continue
            filtered.append(c)

        async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
            async def fetch_subtasks(c: dict[str, Any]) -> list[dict[str, Any]]:
                raw = c.get("subTasks") or c.get("subtasks") or []
                c_id = c.get("id")
                if c_id is not None:
                    try:
                        d_res = await client.get(f"{base}/api/v1/chores/{c_id}/details", headers=self._headers())
                        d_res.raise_for_status()
                        d_json = d_res.json()
                        raw = (d_json.get("res", d_json)).get("subTasks") or raw
                    except Exception:
                        pass
                return raw

            sub_results = await asyncio.gather(*(fetch_subtasks(c) for c in filtered))

        tasks = [self._format_task(c, subs) for c, subs in zip(filtered, sub_results)]
        limit = kwargs.get("limit")
        if isinstance(limit, int) and limit > 0:
            tasks = tasks[:limit]

        return {
            "ok": True,
            "tasks": tasks,
            "source": self.name,
            "label_filter": label_filter,
            "date_filter": date_filter,
            "include_overdue": include_overdue,
            "fallback": False,
        }
