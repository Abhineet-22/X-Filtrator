"""Integration tests for orchestrator routing into the kreuzberg engine."""

from __future__ import annotations

from pathlib import Path

import pytest

from core.orchestrator import analyze_file


pytestmark = pytest.mark.usefixtures("kreuzberg_available")


class TestKreuzbergOrchestratorIntegration:
    def test_routes_text_file_to_kreuzberg(self, sample_text_file: Path) -> None:
        report = analyze_file(sample_text_file)

        assert report["engine"] == "kreuzberg"
        assert report["mime_type"].startswith("text/")
        assert report["metadata"]["engine"] == "kreuzberg"
        assert report["metadata"]["status"] == "ok"
        assert "forensic" in report
        assert "flag_count" in report["forensic"]

    def test_routes_markdown_file_to_kreuzberg(self, sample_markdown_file: Path) -> None:
        report = analyze_file(sample_markdown_file)

        assert report["engine"] == "kreuzberg"
        assert report["metadata"]["status"] == "ok"
        assert "Meta Toolkit Sample" in report["metadata"]["text_preview"]
