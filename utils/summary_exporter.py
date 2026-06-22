"""
Batch analysis summary writer.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def export_summary(
    summary: dict[str, Any],
    output_dir: Path,
) -> None:

    path = output_dir / "summary.json"

    with path.open(
        "w",
        encoding="utf-8",
    ) as handle:

        json.dump(
            summary,
            handle,
            indent=2,
        )