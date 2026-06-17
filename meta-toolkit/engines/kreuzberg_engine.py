"""Text and document metadata extraction via kreuzberg."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def _serialize_metadata(metadata: Any) -> dict[str, Any]:
    """Normalize kreuzberg metadata objects into a plain dictionary."""
    if metadata is None:
        return {}
    if isinstance(metadata, dict):
        return metadata
    if hasattr(metadata, "model_dump"):
        return metadata.model_dump()
    if hasattr(metadata, "to_dict"):
        return metadata.to_dict()
    if hasattr(metadata, "__dict__"):
        return {
            key: value
            for key, value in vars(metadata).items()
            if not key.startswith("_")
        }
    return {"value": str(metadata)}


def extract(path: Path) -> dict[str, Any]:
    """Extract text-oriented metadata using kreuzberg."""
    try:
        from kreuzberg import extract_file_sync  # type: ignore[import-untyped]
    except ImportError:
        return {
            "engine": "kreuzberg",
            "status": "stub",
            "note": "kreuzberg not installed; returning placeholder",
            "content_type": None,
            "text_preview": "",
            "metadata": {},
        }

    try:
        result = extract_file_sync(path)
        content = getattr(result, "content", "") or ""
        return {
            "engine": "kreuzberg",
            "status": "ok",
            "content_type": getattr(result, "mime_type", None),
            "text_preview": content[:500],
            "metadata": _serialize_metadata(getattr(result, "metadata", None)),
            "table_count": len(getattr(result, "tables", []) or []),
        }
    except Exception as exc:  # noqa: BLE001
        # print(f"[KREUZBERG ERROR] {exc}")
        return {
            "engine": "kreuzberg",
            "status": "error",
            "error": str(exc),
            "metadata": {},
        }
