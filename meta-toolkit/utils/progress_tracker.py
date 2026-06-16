"""
Rich progress display for batch jobs.
"""

from __future__ import annotations

from rich.progress import (
    Progress,
    SpinnerColumn,
    BarColumn,
    TextColumn,
    TimeRemainingColumn,
)


class BatchProgress:

    def __init__(self, total: int):

        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("{task.completed}/{task.total}"),
            TimeRemainingColumn(),
        )

        self.task = self.progress.add_task(
            "Analyzing evidence...",
            total=total,
        )

    def __enter__(self):
        self.progress.start()
        return self

    def __exit__(self, *args):
        self.progress.stop()

    def advance(self):
        self.progress.advance(self.task)