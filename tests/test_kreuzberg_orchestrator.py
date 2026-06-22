"""Integration tests for orchestrator routing into the kreuzberg engine."""

from __future__ import annotations

from pathlib import Path

import pytest

from core.orchestrator import analyze_file


pytestmark = pytest.mark.usefixtures("kreuzberg_available")


class TestKreuzbergOrchestratorIntegration:
    def test_runs_all_engines_on_text_file(self, sample_text_file: Path) -> None:
        report = analyze_file(sample_text_file)

        # Verify basic structure
        assert report["mime_type"].startswith("text/")
        assert "metadata" in report
        
        # Verify all engines are present in metadata
        assert "exiftool" in report["metadata"]
        assert "kreuzberg" in report["metadata"]
        assert "mediainfo" in report["metadata"]
        assert "stego_binwalk" in report["metadata"]
        
        # Verify kreuzberg results specifically
        assert report["metadata"]["kreuzberg"]["status"] == "ok"
        assert "forensic" in report
        assert "flag_count" in report["forensic"]

    def test_runs_all_engines_on_markdown_file(self, sample_markdown_file: Path) -> None:
        report = analyze_file(sample_markdown_file)

        # Verify all engines are present in metadata
        assert "exiftool" in report["metadata"]
        assert "kreuzberg" in report["metadata"]
        assert "mediainfo" in report["metadata"]
        assert "stego_binwalk" in report["metadata"]
        
        # Verify kreuzberg results specifically
        assert report["metadata"]["kreuzberg"]["status"] == "ok"
        assert "Meta Toolkit Sample" in report["metadata"]["kreuzberg"]["text_preview"]
