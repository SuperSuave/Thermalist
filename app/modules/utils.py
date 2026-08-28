from __future__ import annotations

from typing import Any


def compact_metadata(data: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in data.items()
        if value is not None and value != ""
    }