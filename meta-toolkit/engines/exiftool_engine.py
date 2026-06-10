"""Deep image EXIF metadata extraction via exiftool subprocess."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any


def extract(path: Path) -> dict[str, Any]:
    """Run exiftool against the target file (stub when binary absent)."""
    binary = shutil.which("exiftool")
    if not binary:
        return {
            "engine": "exiftool",
            "status": "stub",
            "note": "exiftool binary not found on PATH",
            "tags": {},
        }

    try:
        proc = subprocess.run(
            [binary, "-json", "-a", "-G1", str(path)],
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )
        if proc.returncode != 0:
            return {
                "engine": "exiftool",
                "status": "error",
                "error": proc.stderr.strip() or f"exiftool exited {proc.returncode}",
                "tags": {},
            }
        payload = json.loads(proc.stdout)
        tags = payload[0] if payload else {}
        return {
            "engine": "exiftool",
            "status": "ok",
            "tags": tags,
        }
    except (subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
        return {
            "engine": "exiftool",
            "status": "error",
            "error": str(exc),
            "tags": {},
        }
