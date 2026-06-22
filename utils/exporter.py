"""Serialize analysis reports to JSON or CSV."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, TextIO

from utils.ui_rich import _split_camel_case, _clean_sub_key


_TESSERACT_LEAK_PREFIX = "ObjectCache("


def _strip_tesseract_leak_lines(text: str) -> str:
    lines = [
        line
        for line in text.splitlines()
        if line.strip() and not line.lstrip().startswith(_TESSERACT_LEAK_PREFIX)
    ]
    return "\n".join(lines)


def export_json(report: dict[str, Any], stream: TextIO | None = None) -> None:
    """Dump the full report as formatted JSON."""
    out = stream or sys.stdout
    json.dump(report, out, indent=2, default=str)
    out.write("\n")


def export_txt(
    report: dict[str, Any],
    stream: TextIO | None = None,
) -> None:
    """
    Export a human-readable forensic report.

    Mirrors the Rich terminal layout as closely as possible.
    """

    out = stream or sys.stdout

    def write(line: str = "") -> None:
        out.write(_strip_tesseract_leak_lines(line) + "\n")

    def divider(
        title: str,
        width: int = 80,
    ) -> None:

        title = f" {title} "

        remaining = max(
            0,
            width - len(title),
        )

        left = remaining // 2
        right = remaining - left

        write(
            "=" * left
            + title
            + "=" * right
        )

    def render_nested(
        value: Any,
        indent: int = 0,
    ) -> None:

        prefix = "  " * indent

        if isinstance(value, dict):

            for k, v in value.items():

                label = _clean_sub_key(
                    str(k)
                )

                if isinstance(
                    v,
                    (dict, list),
                ):

                    write(
                        f"{prefix}- {label}"
                    )

                    render_nested(
                        v,
                        indent + 1,
                    )

                else:

                    write(
                        f"{prefix}- {label} : {v}"
                    )

        elif isinstance(value, list):

            if not value:
                write(
                    f"{prefix}(empty)"
                )
                return

            for item in value:

                if isinstance(
                    item,
                    (dict, list),
                ):

                    render_nested(
                        item,
                        indent + 1,
                    )

                else:

                    write(
                        f"{prefix}- {item}"
                    )

        else:

            write(
                f"{prefix}{value}"
            )

    # --------------------------------------------------
    # FILE SUMMARY
    # --------------------------------------------------

    divider("FILE SUMMARY")

    write(
        f"File : {report.get('file', '')}"
    )

    write(
        f"MIME : {report.get('mime_type', '')}"
    )

    write()

    # --------------------------------------------------
    # FILE SYSTEM
    # --------------------------------------------------

    divider("FILE SYSTEM STATS")

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

        write(
            f"{label:<15} : {stat.get(key, '')}"
        )

    write()

    # --------------------------------------------------
    # FORENSICS
    # --------------------------------------------------

    forensic = report.get(
        "forensic",
        {},
    )

    divider(
        f"FORENSIC FLAGS ({forensic.get('risk_level', 'none').upper()})"
    )

    flags = forensic.get(
        "flags",
        [],
    )

    if not flags:

        write(
            "No anomalies detected."
        )

    else:

        for flag in flags:

            write(
                f"[{flag.get('severity','')}] "
                f"{flag.get('rule','')}"
            )

            write(
                f"  {flag.get('detail','')}"
            )

            write()

    write()

    ai = report.get(
    "ai_analysis",
    {},
    )

    strings_ai = ai.get(
        "strings"
    )

    if strings_ai:

        divider(
            "AI STRINGS ANALYSIS"
        )
        model = strings_ai.get("model")
        inference_time = strings_ai.get("inference_time")

        if model:
            write(f"Model : {model}")

        if inference_time is not None:
            write(
                f"Inference Time : "
                f"{inference_time:.2f} seconds"
            )

        write()

        write(
            f"Risk Level : "
            f"{strings_ai.get('risk_level', 'unknown')}"
        )

        write()

        write("SUMMARY")
        write("-------")

        write(
            strings_ai.get(
                "summary",
                "No summary available."
            )
        )

        write()

        indicators = strings_ai.get(
            "suspicious_indicators",
            [],
        )

        if indicators:

            write("INDICATORS")
            write("----------")

            for item in indicators:

                write(f"- {item}")

            write()

        notes = strings_ai.get(
            "investigator_notes",
            [],
        )

        if notes:

            write("INVESTIGATOR NOTES")
            write("------------------")

            for note in notes:

                write(f"- {note}")

            write()
    # --------------------------------------------------
    # ENGINE OUTPUTS
    # --------------------------------------------------

    metadata = report.get(
        "metadata",
        {},
    )

    engine_titles: dict[str, Any] = {
        "exiftool": "EXIFTOOL",
        "kreuzberg": "KREUZBERG",
        "mediainfo": "MEDIAINFO",
        "stego_binwalk": "STEGO / BINWALK",
    }

    for engine_name, engine_output in metadata.items():

        divider(engine_titles.get(engine_name,engine_name.upper()))

        if not isinstance(
            engine_output,
            dict,
        ):

            write(
                str(engine_output)
            )

            write()
            continue

        status = engine_output.get(
            "status"
        )

        if status == "stub":

            write(
                f"Unavailable: "
                f"{engine_output.get('note', '')}"
            )

            write()
            continue

        if status == "error":

            write(
                f"ERROR: "
                f"{engine_output.get('error', '')}"
            )

            write()
            continue

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
                .upper()
            )

            write(
                f"\n{header}"
            )

            write(
                "-" * len(header)
            )

            # MediaInfo is plain text
            if (
                engine_name
                == "mediainfo"
                and isinstance(
                    value,
                    str,
                )
            ):

                write(value)
                continue

            if isinstance(value, str):
                value = _strip_tesseract_leak_lines(value)

            render_nested(value)

        write()


def export_to_file(report: dict[str, Any], path: Path, fmt: str = "json") -> None:
    """Write a report to disk in the requested format."""
    with path.open("w", encoding="utf-8", newline="") as handle:
        # if fmt == "csv":
        #     export_csv(report, handle)
        if fmt in ("txt", "text"):
            export_txt(report, handle)
        else:
            export_json(report, handle)
