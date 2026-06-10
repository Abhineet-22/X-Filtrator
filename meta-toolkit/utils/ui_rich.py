"""Terminal report rendering via rich."""

from __future__ import annotations

from typing import Any

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
    stat_table = Table(title="Filesystem Stat", show_header=False)
    stat_table.add_column("Field", style="bold cyan")
    stat_table.add_column("Value")
    for key in ("size_bytes", "mtime", "atime", "ctime", "mode", "uid", "gid"):
        stat_table.add_row(key, str(stat.get(key, "")))

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
    meta_panel = Panel(
        str(metadata),
        title=f"Engine Output ({metadata.get('status', 'unknown')})",
        expand=False,
    )

    console.print(summary)
    console.print(stat_table)
    console.print(flag_table)
    console.print(meta_panel)
