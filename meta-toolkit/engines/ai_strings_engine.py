from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
import shutil
from unittest import result
import requests
from typing import Any
import time


OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://10.0.2.2:11434/api/generate"
)

MODEL = "qwen3:8b"


PROMPT_TEMPLATE = """
You are a digital forensic analyst.

Analyze the following extracted strings.

Identify:

1. Software names
2. Usernames
3. Email addresses
4. URLs
5. GPS indicators
6. Editing software
7. Malware indicators
8. Hidden payload indicators
9. Suspicious findings

Return a JSON object only.

Do not use markdown.
Do not use code fences.
Do not explain your reasoning.
Do not include any text before or after the JSON.

Schema:

{{
  "summary": "",
  "risk_level": "low|medium|high",
  "software": [],
  "urls": [],
  "emails": [],
  "possible_usernames": [],
  "suspicious_indicators": [],
  "investigator_notes": []
}}

format : json

Strings:

{strings}
"""


def analyze(
    strings: list[str],
) -> dict[str, Any]:
    start_time = time.perf_counter()

    if not strings:
        return {
            "engine": "ai_strings",
            "status": "empty",
        }

    strings_blob = "\n".join(
        strings[:300]
    )

    prompt = PROMPT_TEMPLATE.format(
        strings=strings_blob
    )

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "prompt": prompt,
            "format": "json",
            "stream": False,
        },timeout=180
    )

    # print("STATUS:", response.status_code)

    # print("RAW RESPONSE:")
    # print(response.text)

    response.raise_for_status()

    # raw = response.json()["response"]

    # print("MODEL OUTPUT:")
    # return raw

    raw = response.json()["response"]

    elapsed = time.perf_counter() - start_time

    try:

        result = json.loads(raw)

        result["engine"] = "ai_strings"
        result["status"] = "ok"
        result["model"] = MODEL
        result["inference_time"] = round(elapsed, 2)

        return result

    except Exception:

        return {
            "engine": "ai_strings",
            "status": "parse_error",
            "raw_response": raw,
        }
