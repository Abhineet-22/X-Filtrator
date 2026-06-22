"""Rule-based forensic flags for metadata inconsistencies."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def _parse_iso(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def _flag_timestomping(stat: dict[str, Any]) -> list[dict[str, str]]:
    flags: list[dict[str, str]] = []
    atime = _parse_iso(stat.get("atime", ""))
    mtime = _parse_iso(stat.get("mtime", ""))
    ctime = _parse_iso(stat.get("ctime", ""))
    now = datetime.now(tz=timezone.utc)

    if mtime and atime and mtime > atime:
        flags.append({
            "rule": "timestomping_suspect",
            "severity": "medium",
            "detail": "mtime is newer than atime",
        })

    if mtime and mtime > now:
        flags.append({
            "rule": "future_mtime",
            "severity": "high",
            "detail": "mtime is in the future",
        })

    if ctime and mtime and abs((ctime - mtime).total_seconds()) < 1:
        flags.append({
            "rule": "identical_ctime_mtime",
            "severity": "low",
            "detail": "ctime and mtime are within 1 second",
        })

    return flags


def _flag_engine_anomalies(metadata: dict[str, Any]) -> list[dict[str, str]]:
    flags: list[dict[str, str]] = []

    if metadata.get("status") == "error":
        flags.append({
            "rule": "engine_failure",
            "severity": "medium",
            "detail": metadata.get("error", "engine returned error status"),
        })

    if metadata.get("engine") == "stego_binwalk":
        binwalk = metadata.get("binwalk", [])
        if len(binwalk) > 3:
            flags.append({
                "rule": "embedded_payloads",
                "severity": "high",
                "detail": f"binwalk reported {len(binwalk)} embedded signatures",
            })

    if metadata.get("engine") == "exiftool":
        tags = metadata.get("tags", {})
        software = tags.get("EXIF:Software") or tags.get("XMP:CreatorTool")
        if software and "exiftool" in str(software).lower():
            flags.append({
                "rule": "metadata_rewrite_tool",
                "severity": "low",
                "detail": f"EXIF software tag references: {software}",
            })

    return flags


def detect_anomalies(report: dict[str, Any]) -> dict[str, Any]:
    """Evaluate a unified report and return forensic validation flags."""
    stat = report.get("stat", {})
    metadata = report.get("metadata", {})

    flags = _flag_timestomping(stat)
    flags.extend(_flag_engine_anomalies(metadata))

    return {
        "flag_count": len(flags),
        "flags": flags,
        "risk_level": _summarize_risk(flags),
    }


def _summarize_risk(flags: list[dict[str, str]]) -> str:
    severities = {f.get("severity") for f in flags}
    if "high" in severities:
        return "high"
    if "medium" in severities:
        return "medium"
    if flags:
        return "low"
    return "none"
