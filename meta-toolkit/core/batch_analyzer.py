"""
Concurrent directory analysis engine.

Analyzes every file under a directory and exports one report
per file while preserving directory structure.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from core.orchestrator import analyze_file
from utils.exporter import export_to_file


def discover_files(root: Path) -> list[Path]:
    return [p for p in root.rglob("*") if p.is_file()]


def process_file(
    file_path: Path,
    input_root: Path,
    output_root: Path,
    fmt: str,
) -> dict[str, Any]:

    report = analyze_file(file_path)

    relative = file_path.relative_to(input_root)

    report_path = (
        output_root
        / relative.parent
        / f"{relative.name}.{fmt}"
    )

    report_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    export_to_file(
        report,
        report_path,
        fmt,
    )

    return {
        "file": str(file_path),
        "report": str(report_path),
        "risk": report.get("forensic", {}).get(
            "risk_level",
            "none",
        ),
        "status": "ok",
    }


def analyze_directory(
    input_dir: str,
    output_dir: str,
    workers: int = 8,
    fmt: str = "json",
) -> dict[str, Any]:

    input_root = Path(input_dir).resolve()
    output_root = Path(output_dir).resolve()

    output_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    files = discover_files(input_root)

    summary = {
        "total_files": len(files),
        "successful": 0,
        "failed": 0,
        "high_risk": 0,
        "medium_risk": 0,
        "low_risk": 0,
        "none": 0,
        "results": [],
    }

    with ThreadPoolExecutor(
        max_workers=workers
    ) as executor:

        futures = {
            executor.submit(
                process_file,
                file_path,
                input_root,
                output_root,
                fmt,
            ): file_path
            for file_path in files
        }

        for future in as_completed(futures):

            try:
                result = future.result()

                summary["successful"] += 1

                risk = result["risk"]

                if risk == "high":
                    summary["high_risk"] += 1
                elif risk == "medium":
                    summary["medium_risk"] += 1
                elif risk == "low":
                    summary["low_risk"] += 1
                else:
                    summary["none"] += 1

                summary["results"].append(result)

            except Exception as exc:

                summary["failed"] += 1

                summary["results"].append(
                    {
                        "status": "error",
                        "error": str(exc),
                    }
                )

    return summary