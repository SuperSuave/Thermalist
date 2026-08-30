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
        tz_name = self.config.timezone
        if not tz_name:
            return None
        try:
            return ZoneInfo(tz_name)
        except Exception:
            return None

    def _parse_due(self, value: Any, tz: ZoneInfo | None = None) -> datetime | None:
        if value is None:
            return None

        text = str(value).strip()
        if not text:
            return None

        try:
            dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            return None

        if tz is not None:
            if dt.tzinfo is None:
                # Treat naive as local in the configured timezone
                return dt.replace(tzinfo=tz)
            return dt.astimezone(tz)

        return dt

    def _matches_date_filter(
        self,
        due_dt: datetime | None,
        *,
        now: datetime,
        date_filter: str,
        include_overdue: bool,
    ) -> bool:
        if date_filter == "all":
            return True

        if due_dt is None:
            return False

        due_date = due_dt.date()
        today = now.date()

        if date_filter == "overdue":
            return due_date < today

        if date_filter == "today":
            return due_date == today or (include_overdue and due_date < today)

        if date_filter == "tomorrow":
            return due_date == today + timedelta(days=1) or (include_overdue and due_date < (today + timedelta(days=1)))

        if date_filter == "next_7_days":
            end_date = today + timedelta(days=7)
            in_range = today <= due_date <= end_date
            is_overdue = due_date < today
            return in_range or (include_overdue and is_overdue)

        return True

    async def test_connection(self) -> dict[str, Any]:
        url = f"{self.config.base_url.rstrip('/')}/eapi/v1/chore"
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
                response = await client.get(url, headers=self._headers())
            return {
                "ok": response.is_success,
                "status_code": response.status_code,
                "url": url,
                "body_preview": response.text[:300],
            }
        except Exception as exc:
            return {"ok": False, "error": str(exc), "url": url}

    async def fetch(self, **kwargs: Any) -> dict[str, Any]:
        base = self.config.base_url.rstrip("/")
        list_url = f"{base}/eapi/v1/chore"
        label_filter = kwargs.get("label_filter") or kwargs.get("label")
        date_filter = kwargs.get("date_filter", "all")
        include_overdue = bool(kwargs.get("include_overdue", False))

        if date_filter == "overdue":
            include_overdue = False

        tz = self._resolve_tz()
        now = datetime.now(tz) if tz is not None else datetime.now()

        try:
            async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
                list_resp = await client.get(list_url, headers=self._headers())
                list_resp.raise_for_status()
                data = list_resp.json()
        except httpx.HTTPStatusError as exc:
            return {
                "ok": False,
                "tasks": [],
                "source": self.name,
                "fallback": False,
                "error": f"HTTP {exc.response.status_code}",
                "body_preview": exc.response.text[:300],
            }
        except Exception as exc:
            return {
                "ok": False,
                "tasks": [],
                "source": self.name,
                "fallback": False,
                "error": str(exc),
            }

        chores = data if isinstance(data, list) else data.get("chores", []) or data.get("items", [])
        filtered_chores = []

        for chore in chores:
            raw_labels = chore.get("labelsV2") or chore.get("labels") or []
            labels = [
                label.get("name", label) if isinstance(label, dict) else str(label)
                for label in raw_labels
            ]

            if label_filter and label_filter not in labels:
                continue

            due_value = chore.get("nextDueDate") or chore.get("dueDate") or chore.get("due_date")
            due_dt = self._parse_due(due_value, tz)

            if not self._matches_date_filter(
                due_dt,
                now=now,
                date_filter=date_filter,
                include_overdue=include_overdue,
            ):
                continue

            filtered_chores.append((chore, labels, due_value))

        tasks: list[dict[str, Any]] = []

        async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
            async def fetch_detail(chore: dict[str, Any]) -> list[dict[str, Any]]:
                raw_subtasks = chore.get("subTasks") or chore.get("subtasks") or []
                chore_id = chore.get("id")
                if chore_id is not None:
                    detail_url = f"{base}/api/v1/chores/{chore_id}/details"
                    try:
                        detail_resp = await client.get(detail_url, headers=self._headers())
                        detail_resp.raise_for_status()
                        detail_data = detail_resp.json()
                        detail_chore = detail_data.get("res", detail_data)
                        raw_subtasks = detail_chore.get("subTasks") or raw_subtasks
                    except Exception:
                        pass
                return raw_subtasks

            subtasks_results = await asyncio.gather(
                *(fetch_detail(chore) for chore, _, _ in filtered_chores)
            )

        for (chore, labels, due_value), raw_subtasks in zip(filtered_chores, subtasks_results):
            status = chore.get("status")
            completed = bool(
                chore.get("completed")
                or chore.get("isCompleted")
                or chore.get("done")
                or status == 1
            )

            subtasks: list[dict[str, Any]] = []

            if isinstance(raw_subtasks, list):
                for sub in raw_subtasks:
                    sub_labels = sub.get("labels") or []
                    sub_labels = [
                        label.get("name", label) if isinstance(label, dict) else str(label)
                        for label in sub_labels
                    ]

                    sub_status = sub.get("status")
                    sub_completed = bool(
                        sub.get("completed")
                        or sub.get("isCompleted")
                        or sub.get("done")
                        or sub.get("completedAt")
                        or sub_status == 1
                    )

                    subtasks.append(
                        {
                            "id": str(sub.get("id")),
                            "title": sub.get("name") or sub.get("title") or "Untitled subtask",
                            "completed": sub_completed,
                            "labels": sub_labels,
                            "due": sub.get("nextDueDate") or sub.get("dueDate") or sub.get("due_date"),
                            "description": sub.get("description"),
                            "metadata": sub,
                        }
                    )

            tasks.append(
                {
                    "id": str(chore.get("id")),
                    "title": chore.get("name") or chore.get("title") or "Untitled task",
                    "completed": completed,
                    "labels": labels,
                    "due": due_value,
                    "description": chore.get("description"),
                    "metadata": chore,
                    "subtasks": subtasks,
                }
            )

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
