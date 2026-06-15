"""Serialize analysis reports to JSON or CSV."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, TextIO
from typing import Iterable

from utils.ui_rich import _split_camel_case, _clean_sub_key


def export_json(report: dict[str, Any], stream: TextIO | None = None) -> None:
    """Dump the full report as formatted JSON."""
    out = stream or sys.stdout
    json.dump(report, out, indent=2, default=str)
    out.write("\n")


def export_txt(report: dict[str, Any], stream: TextIO | None = None) -> None:
    """Write a human-readable plain-text report containing all engine outputs."""
    out = stream or sys.stdout

    def write(line: str = ""):
        out.write(line + "\n")

    write(f"File: {report.get('file', '')}")
    write(f"MIME: {report.get('mime_type', '')}")
    write("")

    stat = report.get("stat", {})
    write("File System Stats:")
    for k in ("size_bytes", "mtime", "atime", "ctime", "mode", "uid", "gid"):
        write(f"  {k} : {stat.get(k, '')}")
    write("")

    forensic = report.get("forensic", {})
    write(f"Forensic: risk_level={forensic.get('risk_level', '')}  flag_count={forensic.get('flag_count', 0)}")
    flags = forensic.get("flags", [])
    if flags:
        write("")
        write("Flags:")
        for f in flags:
            write(f"  - {f.get('rule','')} [{f.get('severity','')}] : {f.get('detail','')}")

    write("")
    write("Analysis Output:")
    metadata = report.get("metadata", {})
    for engine, data in metadata.items():
        write("")
        # write(f"--- {engine} ---")
        if isinstance(data, dict):
            for key, value in data.items():
                if key in ("engine", "status"):
                    write(f"{key} : {value}")
                    continue
                if isinstance(value, dict):
                    write(f"{_split_camel_case(key)} :")
                    for sub_k, sub_v in value.items():
                        if not isinstance(sub_v, (dict, list)):
                            label = _clean_sub_key(sub_k)
                            write(f"  • {label} : {sub_v}")
                        else:
                            write(f"  • {sub_k} : {sub_v}")
                elif isinstance(value, list):
                    write(f"{_split_camel_case(key)} : {', '.join(str(x) for x in value[:10])}")
                else:
                    write(f"{_split_camel_case(key)} : {value}")



def export_to_file(report: dict[str, Any], path: Path, fmt: str = "json") -> None:
    """Write a report to disk in the requested format."""
    with path.open("w", encoding="utf-8", newline="") as handle:
        # if fmt == "csv":
        #     export_csv(report, handle)
        if fmt in ("txt", "text"):
            export_txt(report, handle)
        else:
            export_json(report, handle)
