"""Shared pytest fixtures for meta-toolkit integration tests."""

from __future__ import annotations

from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    return FIXTURES_DIR


@pytest.fixture(scope="session")
def sample_text_file(fixtures_dir: Path) -> Path:
    path = fixtures_dir / "sample.txt"
    assert path.is_file(), f"missing fixture: {path}"
    return path


@pytest.fixture(scope="session")
def sample_markdown_file(fixtures_dir: Path) -> Path:
    path = fixtures_dir / "sample.md"
    assert path.is_file(), f"missing fixture: {path}"
    return path


@pytest.fixture(scope="session")
def kreuzberg_available() -> None:
    pytest.importorskip("kreuzberg")
