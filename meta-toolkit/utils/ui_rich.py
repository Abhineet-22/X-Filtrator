# """Terminal report rendering via rich."""

# from __future__ import annotations

# import json
# import re
# from typing import Any
# from datetime import datetime, timezone
# from zoneinfo import ZoneInfo

# from rich.console import Console
# from rich.panel import Panel
# from rich.table import Table
# from rich.text import Text


# def _split_camel_case(s: str) -> str:
#     """Convert camelCase and underscored strings to human-readable text."""
#     # Replace underscores with spaces
#     s = s.replace('_', ' ')
#     # Ensure a single space around any existing colons
#     s = re.sub(r'\s*:\s*', ' : ', s)
#     # Insert space before uppercase letters that follow lowercase
#     s = re.sub(r'([a-z])([A-Z])', r'\1 \2', s)
#     # Insert space before uppercase letters followed by lowercase (for sequences like 'HTTPServer')
#     s = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1 \2', s)
#     # Collapse multiple spaces
#     s = re.sub(r'\s+', ' ', s).strip()
#     return s.upper()


# def _clean_sub_key(s: str) -> str:
#     """Return a cleaned display string for sub-keys, omitting unhelpful tokens.

#     Removes tokens like IFD0, IFD1, SYSTEM, SUB, EXIF, and similar that add noise
#     to parameter names in the report.
#     """
#     disp = _split_camel_case(s)
#     tokens = [t for t in disp.split()]
#     cleaned: list[str] = []
#     for t in tokens:
#         # Omit IFD* tokens (IFD, IFD0, IFD1, ...)
#         if re.match(r"^IFD\d*$", t):
#             continue
#         # Omit common noisy tokens
#         if t in {"SYSTEM", "SUB", "EXIF", "SUBIFD", "EXIFIFD", "THUMBNAIL","COMPOSITE","FILE", "TOOL",":"}:
#             continue
#         cleaned.append(t)
#     result = " ".join(cleaned).strip()
#     return result if result else disp


# def render_report(report: dict[str, Any]) -> None:
#     """Print a structured metadata report to the terminal."""
#     console = Console()

#     summary = Table(title="File Summary", show_header=False, border_style="bold magenta")
#     summary.add_column("Field", style="bold cyan")
#     summary.add_column("Value")
#     summary.add_row("File", report.get("file", ""))
#     summary.add_row("MIME", report.get("mime_type", ""))
#     # summary.add_row("Engine", report.get("engine", ""))

#     stat = report.get("stat", {})

#     def _format_timestamp(value: Any) -> str:
#         """Return a human-friendly timestamp for police-friendly output.

#         Accepts ISO strings, epoch ints/floats, or other values and
#         returns a readable UTC timestamp when possible.
#         """
#         if value is None or value == "":
#             return ""
#         # Use IST (India Standard Time) for display
#         IST = ZoneInfo("Asia/Kolkata")

#         # Epoch seconds
#         if isinstance(value, (int, float)):
#             try:
#                 dt = datetime.fromtimestamp(float(value), tz=timezone.utc).astimezone(IST)
#                 return dt.strftime("%Y-%m-%d %H:%M:%S %Z")
#             except Exception:
#                 return str(value)
#         # ISO-formatted strings
#         if isinstance(value, str):
#             try:
#                 dt = datetime.fromisoformat(value)
#                 if dt.tzinfo is None:
#                     dt = dt.replace(tzinfo=timezone.utc)
#                 return dt.astimezone(IST).strftime("%Y-%m-%d %H:%M:%S %Z")
#             except Exception:
#                 return value
#         return str(value)

#     stat_table = Table(title="File System Stats", show_header=False, border_style="bold magenta")
#     stat_table.add_column("Field", style="bold cyan")
#     stat_table.add_column("Value")

#     # Map display labels to stat keys used elsewhere in the toolkit
#     fields = [
#         ("Size (bytes)", "size_bytes"),
#         ("Modified", "Modified at"),
#         ("Accessed", "Accessed at"),
#         ("Changed", "Created at"),
#         ("mode", "mode"),
#         ("uid", "uid"),
#         ("gid", "gid"),
#     ]

#     for label, key in fields:
#         val = stat.get(key, "")
#         if key in ("mtime", "atime", "ctime"):
#             val = _format_timestamp(val)
#         stat_table.add_row(label, str(val))

#     def _format_metadata(value: Any, indent: int = 0) -> str:
#         indent_str = "  " * indent
#         if isinstance(value, dict):
#             if not value:
#                 return f"{indent_str}(empty)"
#             key_width = max(len(str(key)) for key in value.keys())
#             lines: list[str] = []
#             for key, item in value.items():
#                 key_text = str(key).ljust(key_width)
#                 if isinstance(item, (dict, list)):
#                     lines.append(f"{indent_str}{key_text} :")
#                     lines.append(_format_metadata(item, indent + 1))
#                 else:
#                     lines.append(f"{indent_str}{key_text} : {'' if item is None else item}")
#             return "\n".join(lines)
#         if isinstance(value, list):
#             if not value:
#                 return f"{indent_str}(empty list)"
#             lines = []
#             for item in value:
#                 if isinstance(item, (dict, list)):
#                     lines.append(f"{indent_str}-")
#                     lines.append(_format_metadata(item, indent + 1))
#                 else:
#                     lines.append(f"{indent_str}- {item}")
#             return "\n".join(lines)
#         return f"{indent_str}{value}"

#     forensic = report.get("forensic", {})
#     flags = forensic.get("flags", [])
#     flag_table = Table(title=f"Forensic Flags ({forensic.get('risk_level', 'none')})", border_style="bold magenta")
#     flag_table.add_column("Rule")
#     flag_table.add_column("Severity")
#     flag_table.add_column("Detail")
#     if flags:
#         for flag in flags:
#             flag_table.add_row(
#                 flag.get("rule", ""),
#                 flag.get("severity", ""),
#                 flag.get("detail", ""),
#             )
#     else:
#         flag_table.add_row("—", "—", "No anomalies detected")

#     metadata = report.get("metadata", {})
    
#     # Build formal report sections for each tool's output (styled Text)
#     report_sections: list[Text] = []

#     for engine_name, engine_output in metadata.items():
#         section_text = Text()

#         if isinstance(engine_output, dict):
#             if engine_output.get("status") == "stub":
#                 section_text.append(f"No data available. ({engine_output.get('note')})")
#             else:
#                 # Extract key information from the engine output
#                 for key, value in engine_output.items():
#                     if key in ("status", "engine"):
#                         continue

#                     if isinstance(value, dict):
#                         if value:  # Non-empty dict
#                             header_text = key.replace('_', ' ').title()
#                             header_text = re.sub(r'\s*:\s*', ' : ', header_text)
#                             header_text = re.sub(r'\s+', ' ', header_text).strip()
#                             section_text.append(header_text)
#                             section_text.append("\n")
#                             for sub_key, sub_value in value.items():
#                                 if not isinstance(sub_value, (dict, list)):
#                                     section_text.append("  • ")
#                                     section_text.append(_clean_sub_key(sub_key), style="cyan")
#                                     section_text.append(f" : {sub_value}")
#                                     section_text.append("\n")
#                                 elif isinstance(sub_value, list) and sub_value and not isinstance(sub_value[0], (dict, list)):
#                                     section_text.append("  • ")
#                                     section_text.append(_clean_sub_key(sub_key), style="cyan")
#                                     section_text.append(f" : {', '.join(str(v) for v in sub_value)}")
#                                     section_text.append("\n")
#                     elif isinstance(value, list):
#                         if value and not isinstance(value[0], (dict, list)):
#                             list_key = key.replace('_', ' ').title()
#                             list_key = re.sub(r'\s*:\s*', ' : ', list_key)
#                             list_key = re.sub(r'\s+', ' ', list_key).strip()
#                             section_text.append("  • ")
#                             section_text.append(list_key, style="cyan")
#                             section_text.append(f" : {', '.join(str(v) for v in value[:5])}")
#                             section_text.append("\n")
#                             if len(value) > 5:
#                                 section_text.append(f"    (and {len(value) - 5} more)\n")
#                     elif value not in (None, "", "ok", "stub"):
#                         val_key = key.replace('_', ' ').title()
#                         val_key = re.sub(r'\s*:\s*', ' : ', val_key)
#                         val_key = re.sub(r'\s+', ' ', val_key).strip()
#                         section_text.append("  • ")
#                         section_text.append(val_key, style="cyan")
#                         section_text.append(f" : {value}\n")

#         if section_text.plain.strip():
#             report_sections.append(section_text)

#     # Combine all sections into a single Text report
#     combined_report = Text()
#     for i, sec in enumerate(report_sections):
#         if i:
#             combined_report.append("\n\n")
#         combined_report.append(sec)
    
#     meta_panel = Panel(
#         combined_report if combined_report else "Analysis complete. No additional details available.",
#         title=f"Analysis Output",
#         expand=False,
#         border_style="bold magenta"
#     )

#     console.print(summary)
#     console.print(stat_table)
#     console.print(flag_table)
#     console.print(meta_panel)
"""Terminal report rendering via rich."""

from __future__ import annotations

import re
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


def _split_camel_case(s: str) -> str:
    s = s.replace("_", " ")
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"([a-z])([A-Z])", r"\1 \2", s)
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", s)
    return s.upper()


def _clean_sub_key(s: str) -> str:

    disp = _split_camel_case(s)

    tokens = []

    for token in disp.split():

        if re.match(r"^IFD\d*$", token):
            continue

        if token in {
            "SYSTEM",
            "SUB",
            "EXIF",
            "SUBIFD",
            "EXIFIFD",
            "THUMBNAIL",
            "COMPOSITE",
            "FILE",
            "TOOL",
        }:
            continue

        tokens.append(token)

    cleaned = " ".join(tokens).strip()

    return cleaned if cleaned else disp


def _render_nested(
    text: Text,
    value: Any,
    indent: int = 0,
) -> None:

    prefix = "  " * indent

    if isinstance(value, dict):

        for k, v in value.items():

            label = _clean_sub_key(str(k))

            if isinstance(v, (dict, list)):

                text.append(
                    f"{prefix}• {label}\n",
                    style="cyan",
                )

                _render_nested(
                    text,
                    v,
                    indent + 1,
                )

            else:

                text.append(
                    f"{prefix}• ",
                )

                text.append(
                    label,
                    style="cyan",
                )

                text.append(
                    f" : {v}\n"
                )

    elif isinstance(value, list):

        if not value:

            text.append(
                f"{prefix}(empty)\n"
            )

            return

        for item in value:

            if isinstance(
                item,
                (dict, list),
            ):

                _render_nested(
                    text,
                    item,
                    indent + 1,
                )

            else:

                text.append(
                    f"{prefix}• {item}\n"
                )

    else:

        text.append(
            f"{prefix}{value}\n"
        )


def render_report(
    report: dict[str, Any],
) -> None:

    console = Console()

    # --------------------------------------------------
    # File Summary
    # --------------------------------------------------

    summary = Table(
        title="File Summary",
        show_header=False,
        border_style="bold magenta",
    )

    summary.add_column(
        "Field",
        style="bold cyan",
    )

    summary.add_column("Value")

    summary.add_row(
        "File",
        report.get("file", ""),
    )

    summary.add_row(
        "MIME",
        report.get("mime_type", ""),
    )

    # --------------------------------------------------
    # Filesystem
    # --------------------------------------------------

    stat_table = Table(
        title="File System Stats",
        show_header=False,
        border_style="bold magenta",
    )

    stat_table.add_column(
        "Field",
        style="bold cyan",
    )

    stat_table.add_column(
        "Value",
    )

    stat = report.get(
        "stat",
        {},
    )

    stat_fields = [
        ("Size (bytes)", "size_bytes"),
        ("Modified", "Modified at"),
        ("Accessed", "Accessed at"),
        ("Changed", "Created at"),
        ("Mode", "mode"),
        ("UID", "uid"),
        ("GID", "gid"),
        ("Inode", "inode"),
    ]

    for label, key in stat_fields:

        stat_table.add_row(
            label,
            str(
                stat.get(
                    key,
                    "",
                )
            ),
        )

    # --------------------------------------------------
    # Forensics
    # --------------------------------------------------

    forensic = report.get(
        "forensic",
        {},
    )

    flags = forensic.get(
        "flags",
        [],
    )

    flag_table = Table(
        title=f"Forensic Flags ({forensic.get('risk_level', 'none')})",
        border_style="bold magenta",
    )

    flag_table.add_column("Rule")
    flag_table.add_column("Severity")
    flag_table.add_column("Detail")

    if flags:

        for flag in flags:

            flag_table.add_row(
                flag.get(
                    "rule",
                    "",
                ),
                flag.get(
                    "severity",
                    "",
                ),
                flag.get(
                    "detail",
                    "",
                ),
            )

    else:

        flag_table.add_row(
            "—",
            "—",
            "No anomalies detected",
        )

    # --------------------------------------------------
    # Render main sections
    # --------------------------------------------------

    console.print(summary)
    console.print(stat_table)
    console.print(flag_table)

    metadata = report.get(
        "metadata",
        {},
    )

    engine_titles = {
        "exiftool": "EXIFTOOL",
        "kreuzberg": "KREUZBERG",
        "mediainfo": "MEDIAINFO",
        "stego_binwalk": "STEGO / BINWALK",
    }

    for engine_name, engine_output in metadata.items():

        body = Text()

        title = engine_titles.get(
            engine_name,
            engine_name.upper(),
        )

        if not isinstance(
            engine_output,
            dict,
        ):

            body.append(
                str(engine_output)
            )

        elif engine_output.get(
            "status"
        ) == "stub":

            body.append(
                engine_output.get(
                    "note",
                    "Unavailable",
                ),
                style="yellow",
            )

        elif engine_output.get(
            "status"
        ) == "error":

            body.append(
                engine_output.get(
                    "error",
                    "Unknown error",
                ),
                style="bold red",
            )

        else:

            for key, value in engine_output.items():

                if key in (
                    "engine",
                    "status",
                ):
                    continue

                header = (
                    key.replace(
                        "_",
                        " ",
                    )
                    .title()
                )

                body.append(
                    f"{header}\n",
                    style="bold green",
                )

                # ----------------------------------
                # MediaInfo special handling
                # ----------------------------------

                if (
                    engine_name
                    == "mediainfo"
                    and isinstance(
                        value,
                        str,
                    )
                ):

                    body.append(
                        value
                    )

                    body.append(
                        "\n\n"
                    )

                    continue

                # ----------------------------------
                # Generic recursive renderer
                # ----------------------------------

                _render_nested(
                    body,
                    value,
                )

                body.append(
                    "\n"
                )

        console.print(
            Panel(
                body,
                title=title,
                border_style="bright_magenta",
                expand=True,
            )
        )