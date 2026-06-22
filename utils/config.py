from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


@lru_cache(maxsize=1)
def get_config() -> dict[str, Any]:

    config_path = (
        Path(__file__)
        .resolve()
        .parent.parent
        / "config"
        / "ai.json"
    )

    if config_path.exists():

        with config_path.open(
            "r",
            encoding="utf-8",
        ) as handle:

            return json.load(handle)

    return {
        "ai": {
            "enabled": True,
            "provider": "auto",
            "timeout": 480,
            "preferred_models": [
                "qwen3:8b",
                "llama3.1:8b",
                "llama3:8b",
                "mistral:7b",
            ],
            "ports": {
                "ollama": 11434,
                "lmstudio": 1234,
                "vllm": 8000,
            },
        }
    }