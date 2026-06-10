"""Terminal report rendering via rich."""

from __future__ import annotations

import json
from typing import Any
from datetime import datetime, timezone, timedelta

from rich.console import Console
from rich.panel import Panel
from rich.table import Table


def render_report(report: dict[str, Any]) -> None:
    """Print a structured metadata report to the terminal."""
    console = Console()

    summary = Table(title="File Summary", show_header=False)
    summary.add_column("Field", style="bold cyan")
    summary.add_column("Value")
    summary.add_row("File", report.get("file", ""))
    summary.add_row("MIME", report.get("mime_type", ""))
    summary.add_row("Engine", report.get("engine", ""))

    stat = report.get("stat", {})

    def _format_timestamp(value: Any) -> str:
        """Return a human-friendly timestamp for police-friendly output.

        Accepts ISO strings, epoch ints/floats, or other values and
        returns a readable UTC timestamp when possible.
        """
        if value is None or value == "":
            return ""
        # Use IST (India Standard Time) for display
        IST = timezone(timedelta(hours=5, minutes=30), name="IST")

        # Epoch seconds
        if isinstance(value, (int, float)):
            try:
                dt = datetime.fromtimestamp(float(value), tz=timezone.utc).astimezone(IST)
                return dt.strftime("%Y-%m-%d %H:%M:%S %Z")
            except Exception:
                return str(value)
        # ISO-formatted strings
        if isinstance(value, str):
            try:
                dt = datetime.fromisoformat(value)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(IST).strftime("%Y-%m-%d %H:%M:%S %Z")
            except Exception:
                return value
        return str(value)

    stat_table = Table(title="Filesystem Stat", show_header=False)
    stat_table.add_column("Field", style="bold cyan")
    stat_table.add_column("Value")

    # Map display labels to stat keys used elsewhere in the toolkit
    fields = [
        ("size_bytes", "size_bytes"),
        ("Modified", "mtime"),
        ("Accessed", "atime"),
        ("Changed", "ctime"),
        ("mode", "mode"),
        ("uid", "uid"),
        ("gid", "gid"),
    ]

    for label, key in fields:
        val = stat.get(key, "")
        if key in ("mtime", "atime", "ctime"):
            val = _format_timestamp(val)
        stat_table.add_row(label, str(val))

    def _format_metadata(value: Any, indent: int = 0) -> str:
        indent_str = "  " * indent
        if isinstance(value, dict):
            if not value:
                return f"{indent_str}(empty)"
            key_width = max(len(str(key)) for key in value.keys())
            lines: list[str] = []
            for key, item in value.items():
                key_text = str(key).ljust(key_width)
                if isinstance(item, (dict, list)):
                    lines.append(f"{indent_str}{key_text} :")
                    lines.append(_format_metadata(item, indent + 1))
                else:
                    lines.append(f"{indent_str}{key_text} : {'' if item is None else item}")
            return "\n".join(lines)
        if isinstance(value, list):
            if not value:
                return f"{indent_str}(empty list)"
            lines = []
            for item in value:
                if isinstance(item, (dict, list)):
                    lines.append(f"{indent_str}-")
                    lines.append(_format_metadata(item, indent + 1))
                else:
                    lines.append(f"{indent_str}- {item}")
            return "\n".join(lines)
        return f"{indent_str}{value}"

    forensic = report.get("forensic", {})
    flags = forensic.get("flags", [])
    flag_table = Table(title=f"Forensic Flags ({forensic.get('risk_level', 'none')})")
    flag_table.add_column("Rule")
    flag_table.add_column("Severity")
    flag_table.add_column("Detail")
    if flags:
        for flag in flags:
            flag_table.add_row(
                flag.get("rule", ""),
                flag.get("severity", ""),
                flag.get("detail", ""),
            )
    else:
        flag_table.add_row("—", "—", "No anomalies detected")

    metadata = report.get("metadata", {})
    metadata_text = _format_metadata(metadata)

    meta_panel = Panel(
        metadata_text,
        title=f"Engine Output ({metadata.get('status', 'unknown')})",
        expand=False,
    )

    console.print(summary)
    console.print(stat_table)
    console.print(flag_table)
    console.print(meta_panel)
