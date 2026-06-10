"""Serialize analysis reports to JSON or CSV."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Any, TextIO


def export_json(report: dict[str, Any], stream: TextIO | None = None) -> None:
    """Dump the full report as formatted JSON."""
    out = stream or sys.stdout
    json.dump(report, out, indent=2, default=str)
    out.write("\n")


def export_csv(report: dict[str, Any], stream: TextIO | None = None) -> None:
    """Flatten top-level report fields and forensic flags into CSV rows."""
    out = stream or sys.stdout
    writer = csv.writer(out)

    stat = report.get("stat", {})
    forensic = report.get("forensic", {})
    flags = forensic.get("flags", [])

    writer.writerow([
        "file",
        "mime_type",
        "engine",
        "size_bytes",
        "mtime",
        "risk_level",
        "flag_count",
    ])
    writer.writerow([
        report.get("file", ""),
        report.get("mime_type", ""),
        report.get("engine", ""),
        stat.get("size_bytes", ""),
        stat.get("mtime", ""),
        forensic.get("risk_level", ""),
        forensic.get("flag_count", 0),
    ])

    writer.writerow([])
    writer.writerow(["rule", "severity", "detail"])
    for flag in flags:
        writer.writerow([
            flag.get("rule", ""),
            flag.get("severity", ""),
            flag.get("detail", ""),
        ])


def export_to_file(report: dict[str, Any], path: Path, fmt: str = "json") -> None:
    """Write a report to disk in the requested format."""
    with path.open("w", encoding="utf-8", newline="") as handle:
        if fmt == "csv":
            export_csv(report, handle)
        else:
            export_json(report, handle)
