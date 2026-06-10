"""Integration tests for the kreuzberg extraction engine."""

from __future__ import annotations

from pathlib import Path

import pytest
from kreuzberg import extract_file_sync

from engines.kreuzberg_engine import extract


pytestmark = pytest.mark.usefixtures("kreuzberg_available")


class TestKreuzbergEngineIntegration:
    def test_extract_plain_text_returns_ok(self, sample_text_file: Path) -> None:
        result = extract(sample_text_file)

        assert result["engine"] == "kreuzberg"
        assert result["status"] == "ok"
        assert result["content_type"] is not None
        assert "meta-toolkit kreuzberg integration fixture" in result["text_preview"]
        assert "MT-INTEGRATION-001" in result["text_preview"]
        assert isinstance(result["metadata"], dict)
        assert result["table_count"] == 0

    def test_extract_markdown_returns_content(self, sample_markdown_file: Path) -> None:
        result = extract(sample_markdown_file)

        assert result["status"] == "ok"
        assert "Meta Toolkit Sample" in result["text_preview"]
        assert "MT-MD-002" in result["text_preview"]

    def test_extract_matches_kreuzberg_sync_api(self, sample_text_file: Path) -> None:
        """Engine output should mirror the upstream kreuzberg sync API."""
        direct = extract_file_sync(sample_text_file)
        wrapped = extract(sample_text_file)

        assert wrapped["status"] == "ok"
        assert wrapped["content_type"] == direct.mime_type
        assert wrapped["text_preview"] == (direct.content or "")[:500]
        assert wrapped["table_count"] == len(direct.tables or [])

    def test_extract_missing_file_returns_error(self, tmp_path: Path) -> None:
        missing = tmp_path / "does-not-exist.txt"
        result = extract(missing)

        assert result["engine"] == "kreuzberg"
        assert result["status"] == "error"
        assert "error" in result
