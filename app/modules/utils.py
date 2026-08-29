from __future__ import annotations

from typing import Any


def compact_metadata(data: dict[str, Any]) -> dict[str, Any]:
    """
    Create a copy of metadata containing entries with values other than `None`.
    
    Parameters:
        data (dict[str, Any]): Metadata entries to compact.
    
    Returns:
        dict[str, Any]: A new dictionary excluding entries whose values are `None`.
    """
    return {
        key: value
        for key, value in data.items()
        if value is not None
    }
