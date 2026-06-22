"""Payload carving and string surfacing via binwalk/strings subprocess."""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path
from typing import Any


def _run_strings(path: Path,limit:int=20) -> list[str]:
    binary = shutil.which("strings")
    if not binary:
        return []

    proc = subprocess.run(
        [binary,"-n","8", str(path)],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    if proc.returncode != 0:
        return []

    lines = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    # Deduplicate while preserving order.
    seen: set[str] = set()
    unique: list[str] = []
    for line in lines:
        if line not in seen:
            seen.add(line)
            unique.append(line)
        if len(unique) >= limit:
            break
    return unique


def _run_binwalk(path: Path) -> list[dict[str, str]]:
    binary = shutil.which("binwalk")
    if not binary:
        return []

    proc = subprocess.run(
        [binary, str(path)],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    if proc.returncode != 0:
        return []

    entries: list[dict[str, str]] = []
    pattern = re.compile(
        r"^(?P<offset>0x[0-9A-Fa-f]+)\s+(?P<description>.+)$"
    )
    for line in proc.stdout.splitlines():
        match = pattern.match(line.strip())
        if match:
            entries.append(match.groupdict())
    return entries


def extract(path: Path) -> dict[str, Any]:
    """Surface embedded signatures and printable strings (stub when tools absent)."""
    binwalk_hits = _run_binwalk(path)
    strings_hits = _run_strings(path)

    has_binwalk = shutil.which("binwalk") is not None
    has_strings = shutil.which("strings") is not None

    if not has_binwalk and not has_strings:
        return {
            "engine": "stego_binwalk",
            "status": "stub",
            "note": "binwalk/strings binaries not found on PATH",
            "binwalk": [],
            "strings": [],
        }

    return {
        "engine": "stego_binwalk",
        "status": "ok",
        "binwalk": binwalk_hits,
        "strings": strings_hits,
    }
