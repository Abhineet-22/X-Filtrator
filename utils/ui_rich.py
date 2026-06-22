
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

    ai = report.get(
    "ai_analysis",
    {},
    )

    strings_ai = ai.get(
        "strings"
    )
    metadata= {}

    if strings_ai:

        body = Text()

        body.append(
            f"Risk Level : "
            f"{strings_ai.get('risk_level', 'unknown')}\n\n",
            style="bold yellow",
        )

        body.append(
            "Summary\n",
            style="bold green",
        )

        body.append(
            strings_ai.get(
                "summary",
                "No summary available.",
            )
        )

        body.append("\n\n")

        indicators = strings_ai.get(
            "suspicious_indicators",
            [],
        )

        if indicators:

            body.append(
                "Indicators\n",
                style="bold red",
            )

            for item in indicators:

                body.append(
                    f"• {item}\n"
                )

            body.append("\n")

        notes = strings_ai.get(
            "investigator_notes",
            [],
        )

        if notes:

            body.append(
                "Investigator Notes\n",
                style="bold cyan",
            )

            for note in notes:

                body.append(
                    f"• {note}\n"
                )

        console.print(
            Panel(
                body,
                title="AI STRINGS ANALYSIS",
                border_style="bright_blue",
            )
        )

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
        model = strings_ai.get("model", "unknown")
        inference_time = strings_ai.get("inference_time")

        if inference_time is not None:

            body.append(
                f"Model : {model}\n"
                f"Inference Time : {inference_time:.2f} seconds\n\n",
                style="bold cyan",
            )

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