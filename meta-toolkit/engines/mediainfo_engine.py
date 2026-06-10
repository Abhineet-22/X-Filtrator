"""Media container profiling via mediainfo subprocess."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any


def extract(path: Path) -> dict[str, Any]:
    """Run mediainfo against the target file (stub when binary absent)."""
    binary = shutil.which("mediainfo")
    if not binary:
        return {
            "engine": "mediainfo",
            "status": "stub",
            "note": "mediainfo binary not found on PATH",
            "tracks": [],
        }

    try:
        proc = subprocess.run(
            [binary, "--Output=JSON", str(path)],
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )
        if proc.returncode != 0:
            return {
                "engine": "mediainfo",
                "status": "error",
                "error": proc.stderr.strip() or f"mediainfo exited {proc.returncode}",
                "tracks": [],
            }
        payload = json.loads(proc.stdout)
        media = payload.get("media", {})
        tracks = media.get("track", [])
        if isinstance(tracks, dict):
            tracks = [tracks]
        return {
            "engine": "mediainfo",
            "status": "ok",
            "tracks": tracks,
        }
    except (subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
        return {
            "engine": "mediainfo",
            "status": "error",
            "error": str(exc),
            "tracks": [],
        }
