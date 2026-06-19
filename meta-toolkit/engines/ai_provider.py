from __future__ import annotations

import os
from typing import Any
from utils.config import get_config


import requests

DEFAULT_TIMEOUT = 10

CONFIG = get_config()

AI_CONFIG = CONFIG["ai"]

PREFERRED_MODELS = AI_CONFIG.get(
    "preferred_models",
    [
        "qwen3:8b",
        "llama3.1:8b",
        "llama3:8b",
        "mistral:7b",
    ],
)

class AIProviderError(RuntimeError):
    pass


def _safe_get(
    url: str,
    timeout: int = DEFAULT_TIMEOUT,
) -> requests.Response | None:

    try:
        response = requests.get(
            url,
            timeout=timeout,
        )

        response.raise_for_status()

        return response

    except Exception:
        return None

def candidate_hosts() -> list[str]:

    hosts: list[str] = []

    env_host = os.getenv(
        "AI_HOST"
    )

    if env_host:

        hosts.append(env_host)

    hosts.extend(
        [
            "localhost",
            "127.0.0.1",

            # VirtualBox NAT
            "10.0.2.2",

            # Common Host-Only
            "192.168.56.1",
        ]
    )

    seen: set[str] = set()

    return [
        h
        for h in hosts
        if not (
            h in seen
            or seen.add(h)
        )
    ]

def discover_provider() -> dict[str, Any]:
    """
    Detect available AI backends.

    Detection order:
    1. Ollama
    2. LM Studio
    3. vLLM
    4. Generic OpenAI-compatible endpoint
    """

    # --------------------------------------------------
    # Ollama
    # --------------------------------------------------

    ollama_port = (
    AI_CONFIG["ports"]["ollama"]
)

    for host in candidate_hosts():

        url = (
            f"http://{host}:{ollama_port}"
        )

        response = _safe_get(
            f"{url}/api/tags"
        )

        if response:

            return {
                "provider": "ollama",
                "base_url": url,
            }

    # --------------------------------------------------
    # LM Studio
    # --------------------------------------------------

    lmstudio_port = (
    AI_CONFIG["ports"]["lmstudio"]
)

    for host in candidate_hosts():

        url = (
            f"http://{host}:{lmstudio_port}"
        )

        response = _safe_get(
            f"{url}/v1/models"
        )

        if response:

            return {
                "provider": "lmstudio",
                "base_url": url,
            }

    # --------------------------------------------------
    # vLLM
    # --------------------------------------------------

    vllm_port = (
    AI_CONFIG["ports"]["vllm"]
)

    for host in candidate_hosts():

        url = (
            f"http://{host}:{vllm_port}"
        )

        response = _safe_get(
            f"{url}/v1/models"
        )

        if response:

            return {
                "provider": "vllm",
                "base_url": url,
            }

    # --------------------------------------------------
    # Generic OpenAI-compatible
    # --------------------------------------------------

    endpoint = os.getenv(
        "AI_ENDPOINT"
    )

    api_key = os.getenv(
        "AI_API_KEY"
    )

    if endpoint and api_key:

        return {
            "provider": "openai_compatible",
            "base_url": endpoint,
            "api_key": api_key,
        }

    raise AIProviderError(
        "No AI provider detected."
    )


def discover_model(
    provider_info: dict[str, Any],
) -> str:

    provider = provider_info["provider"]

    # --------------------------------------------------
    # Ollama
    # --------------------------------------------------

    if provider == "ollama":

        response = requests.get(
            f"{provider_info['base_url']}/api/tags",
            timeout=10,
        )

        response.raise_for_status()

        models = [
            m["name"]
            for m in response.json().get(
                "models",
                [],
            )
        ]

    # --------------------------------------------------
    # OpenAI-compatible APIs
    # --------------------------------------------------

    else:

        response = requests.get(
            f"{provider_info['base_url']}/v1/models",
            timeout=10,
        )

        response.raise_for_status()

        models = [
            m["id"]
            for m in response.json().get(
                "data",
                [],
            )
        ]

    if not models:

        raise AIProviderError(
            "No models available."
        )

    for preferred in PREFERRED_MODELS:

        if preferred in models:
            return preferred

    return models[0]


def generate(
    prompt: str,
    timeout: int | None = None,
) -> dict[str, Any]:

    provider_info = discover_provider()

    provider = provider_info["provider"]

    model = discover_model(
        provider_info
    )

    # --------------------------------------------------
    # Ollama
    # --------------------------------------------------

    if provider == "ollama":

        response = requests.post(
            f"{provider_info['base_url']}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "format": "json",
                "stream": False,
            },
            timeout=timeout,
        )

        response.raise_for_status()

        payload = response.json()

        return {
            "provider": provider,
            "model": model,
            "text": payload["response"],
        }

    # --------------------------------------------------
    # OpenAI-compatible
    # --------------------------------------------------

    headers = {}

    if provider_info.get("api_key"):

        headers["Authorization"] = (
            f"Bearer {provider_info['api_key']}"
        )

    response = requests.post(
        f"{provider_info['base_url']}/v1/chat/completions",
        headers=headers,
        json={
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "response_format": {
                "type": "json_object"
            },
        },
        timeout=timeout,
    )

    response.raise_for_status()

    payload = response.json()

    return {
        "provider": provider,
        "model": model,
        "text": payload["choices"][0]["message"]["content"],
    }