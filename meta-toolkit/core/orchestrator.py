"""Route files to extraction engines and assemble a unified metadata report."""

from __future__ import annotations

import mimetypes
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from engines.exiftool_engine import extract as extract_exif
from engines.kreuzberg_engine import extract as extract_kreuzberg
from engines.mediainfo_engine import extract as extract_mediainfo
from engines.stego_binwalk_engine import extract as extract_stego
from forensic.anomaly_detector import detect_anomalies

# Common file signatures for fallback MIME detection.
_MAGIC_SIGNATURES: list[tuple[bytes, str, str]] = [
    (b"\x89PNG\r\n\x1a\n", "image/png", "exiftool"),
    (b"\xff\xd8\xff", "image/jpeg", "exiftool"),
    (b"GIF87a", "image/gif", "exiftool"),
    (b"GIF89a", "image/gif", "exiftool"),
    (b"%PDF-", "application/pdf", "kreuzberg"),
    (b"\x1f\x8b", "application/gzip", "stego_binwalk"),
    (b"PK\x03\x04", "application/zip", "stego_binwalk"),
    (b"\x00\x00\x00\x18ftyp", "video/mp4", "mediainfo"),
    (b"\x00\x00\x00\x1cftyp", "video/mp4", "mediainfo"),
    (b"ID3", "audio/mpeg", "mediainfo"),
    (b"\xff\xfb", "audio/mpeg", "mediainfo"),
    (b"RIFF", "audio/wav", "mediainfo"),
]

_ENGINE_MAP: dict[str, str] = {
    "exiftool": "exiftool",
    "kreuzberg": "kreuzberg",
    "mediainfo": "mediainfo",
    "stego_binwalk": "stego_binwalk",
}

_MIME_ENGINE_HINTS: dict[str, str] = {
    "image/": "exiftool",
    "text/": "kreuzberg",
    "application/pdf": "kreuzberg",
    "application/json": "kreuzberg",
    "application/xml": "kreuzberg",
    "video/": "mediainfo",
    "audio/": "mediainfo",
}

# Fallback when the platform mimetypes DB lacks common document extensions.
_EXTENSION_MIME: dict[str, str] = {
    ".txt": "text/plain",
    ".md": "text/markdown",
    ".markdown": "text/markdown",
    ".json": "application/json",
    ".xml": "application/xml",
}


def _stat_details(path: Path) -> dict[str, Any]:
    st = path.stat()
    return {
        "size_bytes": st.st_size,
        "inode": st.st_ino,
        "mode": oct(st.st_mode),
        "uid": st.st_uid,
        "gid": st.st_gid,
        "nlink": st.st_nlink,
        "atime": datetime.fromtimestamp(st.st_atime, tz=timezone.utc).isoformat(),
        "mtime": datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat(),
        "ctime": datetime.fromtimestamp(st.st_ctime, tz=timezone.utc).isoformat(),
    }


def _detect_mime(path: Path) -> tuple[str, str | None]:
    """Return (mime_type, engine_hint) using magic numbers then mimetypes."""
    header = path.read_bytes()[:32]

    for signature, mime, engine in _MAGIC_SIGNATURES:
        if header.startswith(signature):
            return mime, engine

    guessed, _ = mimetypes.guess_type(str(path))
    mime = guessed or _EXTENSION_MIME.get(path.suffix.lower(), "application/octet-stream")

    for prefix, engine in _MIME_ENGINE_HINTS.items():
        if mime.startswith(prefix):
            return mime, engine

    return mime, "stego_binwalk"


def _select_engine(mime: str, hint: str | None) -> str:
    if hint and hint in _ENGINE_MAP:
        return hint
    for prefix, engine in _MIME_ENGINE_HINTS.items():
        if mime.startswith(prefix):
            return engine
    return "stego_binwalk"


def _run_engine(engine: str, path: Path) -> dict[str, Any]:
    dispatch = {
        "exiftool": extract_exif,
        "kreuzberg": extract_kreuzberg,
        "mediainfo": extract_mediainfo,
        "stego_binwalk": extract_stego,
    }
    handler = dispatch.get(engine, extract_stego)
    return handler(path)


def analyze_file(file_path: str | os.PathLike[str]) -> dict[str, Any]:
    """Analyze a file using all available engines and return a unified metadata dictionary."""
    path = Path(file_path).resolve()

    if not path.is_file():
        raise FileNotFoundError(f"Not a regular file: {path}")

    mime, hint = _detect_mime(path)
    stat = _stat_details(path)
    
    # Run all engines and collect their results
    all_engines = ["exiftool", "kreuzberg", "mediainfo", "stego_binwalk"]
    metadata_results = {}
    
    for engine in all_engines:
        metadata_results[engine] = _run_engine(engine, path)

    report: dict[str, Any] = {
        "file": str(path),
        "mime_type": mime,
        "mime_hint": hint,
        "stat": stat,
        "metadata": metadata_results,
    }

    report["forensic"] = detect_anomalies(report)
    return report
